# test_ingestion_embedding.py - Tester för embed_texts() funktionen utan nätverk och utan nyckel.
# Kod: Engelska
# Kommentarer: Svenska
#
# Grunden ersätts av en fake client(duck typing, if it sounds like a duck it is a duck)
# Syfte: Att testa logiken KRING anropen och INTE om grunden fungerar.
#
# A: Ingen text ger inga anrop och en TOM lista.
# B: Batcharna: 1, 32, 33 och 63 texter
# C: Ordningen: Servern svarar i annan ordning än väntat, vectors ska ändå hamna i rätt ordning.
# D: En tappad vector ska krascha HÖGT(Fail LOUDLY) DIREKT och inte kontaminera vår data.
# E: Modellen och formatet ska skickas i VARJE anrop.
# f: Klienten utan NYCKEL ska ge KeyError med rätt namn.

from types import SimpleNamespace

import pytest

from study_buddy.ingestion.constants import EMBEDDING_MODEL
from study_buddy.ingestion.embedding import embed_texts, get_embedding_client


# ===== FAKE EMBEDDINGS: Generera FAKE embeddings i samma form som OpenAI klienten =====
class FakeEmbeddings:
    """
    Stand-in for client.embeddings. Records every call and returns FAKE vectors.

    The fake vector for a text is its LENGTH(LEN), repeated dim times.
    This way every vector can be traced back to its next since
    testing the order relies on that.
    """

    def __init__(self, *, dim=4, reverse=False, drop_last=False):
        self.calls = []  # Varje anrop SPARAS så att testerna kan räknas och granskas
        self.dim = dim
        self.reverse = reverse  # Svarar i OMVÄND ordning men med RÄTT index
        self.drop_last = drop_last  # Tappar sista vectorn i svaret med FLIT

    def create(self, *, model, input, encoding_format):
        self.calls.append(
            {"model": model, "input": input, "encoding_format": encoding_format}
        )
        # Samma form som Grunden.ai's svar: resp.data[i].index + resp.data[i].embedding
        data = [
            SimpleNamespace(index=i, embedding=[float(len(text))] * self.dim)
            for i, text in enumerate(input)
        ]
        if self.reverse:
            data.reverse()
        if self.drop_last:
            data.pop()
        return SimpleNamespace(data=data)


# ===== FAKE CLIENT: Samma form som OpenAI klienten, INGET NÄTVERK KRÄVS =====
class FakeClient:
    """
    Stand-in for the OpenAI client only.
    .embeddings is used by embed_texts() function.
    """

    def __init__(self, **kwargs):
        self.embeddings = FakeEmbeddings(**kwargs)


# ===== TESTERNA =====
#
# A:
def test_embed_texts_no_texts_makes_no_calls():
    client = FakeClient()

    # assert nr 2 är hela meningen. Inte ett enda anrop ska göras
    assert embed_texts(client, []) == []
    assert client.embeddings.calls == []


# Decorator
@pytest.mark.parametrize(
    "n_texts, expected_batch_sizes",
    [
        (1, [1]),
        (32, [32]),  # EXAKTA taket(32) en omgång, inte två
        (33, [32, 1]),  # Ett över satta gränsen: en till, kort omgång
        (63, [32, 31]),
    ],
)

# B
def test_embed_texts_batches_at_32(n_texts, expected_batch_sizes):
    client = FakeClient()
    texts = [f"text {i}" for i in range(n_texts)]

    vectors = embed_texts(client, texts)

    # Storleken på varje batch som embeddas i exakt den ordning de skickades
    assert [len(c["input"]) for c in client.embeddings.calls] == expected_batch_sizes
    assert len(vectors) == n_texts


# C
def test_embed_texts_keeps_text_order_when_server_reorders():
    client = FakeClient(dim=1, reverse=True)

    # Texter som är olika långa så att varje vektor går att "känna igen": "a" -> [1.0]
    vectors = embed_texts(client, ["a", "bb", "ccc"])

    assert vectors == [[1.0], [2.0], [3.0]]


# D
def test_embed_texts_raises_when_server_drops_a_vector():
    client = FakeClient(drop_last=True)

    with pytest.raises(RuntimeError):
        embed_texts(client, ["a", "bb", "ccc"])


# E
def test_embed_texts_sends_model_and_float_format():
    client = FakeClient()

    # 40 texter blir TVÅ omgångar pga batch gränsen går vid 32. Påståendet ska gälla VARJE anrop
    # 32 + 8 == 40
    embed_texts(client, [f"text {i}" for i in range(40)])

    # Utan den här raden passerar for-loopen även om inget anrop gjordes
    assert len(client.embeddings.calls) == 2
    for call in client.embeddings.calls:
        assert call["model"] == EMBEDDING_MODEL
        assert call["encoding_format"] == "float"


# F
def test_client_without_key_raises_keyerror_with_the_right_name(monkeypatch):
    # monkeypatch tar bort nyckeln bara under testet och lägger tillbaka den efteråt
    monkeypatch.delenv("GRUNDEN_API_KEY", raising=False)

    with pytest.raises(KeyError, match="GRUNDEN_API_KEY"):
        get_embedding_client()
