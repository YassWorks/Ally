import ollama


class OllamaEmbedder:
    """Class to get embeddings using the Ollama API."""
    
    def __init__(self, model_name: str = "all-minilm") -> None:
        self.model_name = model_name
    
    def get_embeddings(self, sentences: list[str] | str) -> list[list[float]]:  # 384
        """
        Get embeddings for a list of sentences using the Ollama API.

        Args:
            sentences (list[str] | str): List of sentences to embed.

        Returns:
            list[list[float]]: List of embeddings for each sentence.
        """
        response = ollama.embed(model=self.model_name, input=sentences)
        return response.embeddings
