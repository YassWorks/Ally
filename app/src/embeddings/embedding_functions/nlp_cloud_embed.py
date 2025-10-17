import requests
import os


API_TOKEN = os.getenv("NLP_CLOUD_API_KEY")
MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"
API_URL = f"https://api.nlpcloud.io/v1/{MODEL_NAME}/embeddings"


class NLPCloudEmbedder:
    """Class to get embeddings using the NLP Cloud API."""

    def __init__(self, model_name=MODEL_NAME):
        self.model_name = model_name

    def get_embeddings(self, sentences: list[str] | str) -> list[list[float]]:
        """
        Get embeddings for a list of sentences using the NLP Cloud API.

        Args:
            sentences (list[str]| str): List of sentences to embed.

        Returns:
            list[list[float]]: List of embeddings for each sentence.
        """
        headers = {
            "Authorization": f"Token {API_TOKEN}",
            "Content-Type": "application/json",
        }
        payload = {"sentences": sentences}

        response = requests.post(API_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()["embeddings"]
