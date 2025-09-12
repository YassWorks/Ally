import ollama
import numpy as np


def get_embeddings_ollama(model: str, sentences: list[str]) -> list[list[float]]:
    """
    Get embeddings for a list of sentences using the Ollama API.

    Args:
        sentences (list[str]): List of sentences to embed.

    Returns:
        list[list[float]]: List of embeddings for each sentence.
    """
    response = ollama.embed(model=model, input=sentences)
    return np.array(response.embeddings)
