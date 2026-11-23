# constants.py script för Embeddingens fakta på EN plats
# Kod: Engelska
# Kommentarer: Svenska

"""
The facts about the embedding provider and the model.

Meant to be a constant to be used and imported by ingestion, retrieval and storage.
These values belong in the INDEX and not the environment. Changing of EMBEDDING_MODEL or EMBEDDING_DIM
means that we need to run the embedding for everything again, otherwise questions and documents live on
two different maps.

Only the key lives in .env (GRUNDEN_API_KEY).
"""

# ===== Leverantören av embedding modell: Grunden.ai =====
GRUNDEN_BASE_URL = "https://api.grunden.ai/v1"
BATCH_SIZE = 32  # Grundens tak(limit) per anrop. 64 ger kod 422 (mätt 23 november)

# ===== Modellen: Dokument + fråga MÅSTE embeddas med SAMMA modell =====
EMBEDDING_MODEL = "bge-m3"
EMBEDDING_DIM = 1024  # Storage behöver det här för LanceDB-tabellen


# ===== Chunking: PRELIMINÄRA värden, ses över i phase 1 =====
# Modellens tak. Längre texter kapas TYST utan felmeddelanden.
# Chunkingens egna params (CHUNK SIZE + OVERLAP) läggs här som konstant när vi är där
MAX_INPUT_TOKENS = 8192
