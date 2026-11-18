import os

DEFAULT_MODEL = "text-embedding-3-small"


class OpenAIEmbedder:
    """Embeds text with the OpenAI embeddings API, using ``OPENAI_API_KEY``."""

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or DEFAULT_MODEL
        self._client = None

    def get_embeddings(self, sentences: list[str] | str) -> list[list[float]]:
        """Return one embedding per sentence."""
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        if isinstance(sentences, str):
            sentences = [sentences]

        response = self._client.embeddings.create(
            model=self.model_name, input=sentences
        )
        return [item.embedding for item in response.data]
