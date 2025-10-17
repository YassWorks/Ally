from openai import OpenAI
import os


class OpenAIEmbedder:
    """Class to get embeddings using the OpenAI API."""
    
    def __init__(self, model_name: str = "text-embedding-ada-002") -> None:
        self.model_name = model_name
        self.client = None
    
    def get_embeddings(self, sentences: list[str] | str) -> list[list[float]]:
        """
        Get embeddings for a list of sentences using the Ollama API.

        Args:
            sentences (list[str] | str): List of sentences to embed.

        Returns:
            list[list[float]]: List of embeddings for each sentence.
        """
        if self.client is None:
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        if isinstance(sentences, str):
            sentences = [sentences]
        
        response = self.client.embeddings.create(
            model=self.model_name,
            input=sentences
        )
        
        embeddings = [data['embedding'] for data in response['data']]
        return embeddings
