from sentence_transformers import SentenceTransformer


def get_embeddings_hf(model: str, sentences: list[str]) -> list[list[float]]:
    """
    Get embeddings for a list of sentences using the Hugging Face SentenceTransformer.

    Args:
        sentences (list[str]): List of sentences to embed.

    Returns:
        list[list[float]]: List of embeddings, one for each sentence.
    """
    model = SentenceTransformer(model)
    embeddings = model.encode(sentences)

    return embeddings
