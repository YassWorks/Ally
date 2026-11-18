import os

import requests
from requests.adapters import HTTPAdapter, Retry

DEFAULT_MODEL = "paraphrase-multilingual-mpnet-base-v2"
TIMEOUT = 60


class NLPCloudEmbedder:
    """Embeds text with the NLP Cloud API, using ``NLP_CLOUD_API_KEY``.

    Rate-limited requests are retried with backoff.
    """

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or DEFAULT_MODEL
        self._session = requests.Session()
        retries = Retry(
            total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504]
        )
        self._session.mount("https://", HTTPAdapter(max_retries=retries))

    def get_embeddings(self, sentences: list[str] | str) -> list[list[float]]:
        """Return one embedding per sentence."""
        if isinstance(sentences, str):
            sentences = [sentences]

        response = self._session.post(
            f"https://api.nlpcloud.io/v1/{self.model_name}/embeddings",
            json={"sentences": sentences},
            headers={"Authorization": f"Token {os.getenv('NLP_CLOUD_API_KEY')}"},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        return response.json()["embeddings"]
