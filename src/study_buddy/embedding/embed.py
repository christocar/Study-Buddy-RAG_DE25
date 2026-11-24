# embed.py - Texter in, vectors ut. Samma funktion för alla spår
# Kod: Engelska
# Kommentarer: Svenska

"""
The embedding function that every track calls.

The ingestion embeds the chunks and the retrieval embeds the questions with the SAME
function and the SAME model.

Texts go in, vectors come out in the same order.
"""

import os
from itertools import batched

from openai import OpenAI

from study_buddy.embedding.constants import (
    BATCH_SIZE,
    EMBEDDING_MODEL,
    GRUNDEN_BASE_URL,
)


# ===== 1: Klienten byggs på ETT ställe =====
# Skapas först när funktionen anropas och ALDRIG vid import. CI har ingen nyckel
def get_embedding_client() -> OpenAI:
    """
    Client for Grunden.ai through the OpenAI package.

    Retries: The clients default is 2, if Grunden.ai starts failing then raise it.
    """
    return OpenAI(
        api_key=os.environ["GRUNDEN_API_KEY"],
        base_url=GRUNDEN_BASE_URL,
    )


# ===== 2: Text goes in, vectors goes out =====
def embed_texts(client: OpenAI, texts: list[str]) -> list[list[float]]:
    """
    Embeds texts in BATCHES of at most BATCH_SIZE and
    returns the vectors in the SAME order as the texts.
    """
    vectors: list[list[float]] = []
    # batched() ger tuples om HÖGST 32, den sista kan vara kortare
    for batch in batched(texts, BATCH_SIZE):
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=list(batch),
            encoding_format="float",  # BE OM FLOAT, annars kommer paketet be om base64 vilket inte är bra.
        )
        # Sortera på index och lita inte på att servern svarar i samma ordning som det skickas ut
        vectors.extend(
            d.embedding for d in sorted(response.data, key=lambda d: d.index)
        )

    # SKRIK OCH FAILA HÖGT: tappar servern en text hamnar varje vector efter den på FEL TEXT
    if len(vectors) != len(texts):
        raise RuntimeError(
            f"Sent {len(texts)} texts, received {len(vectors)} vectors back."
        )
    return vectors
