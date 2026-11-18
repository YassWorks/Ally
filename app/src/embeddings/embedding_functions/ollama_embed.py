DEFAULT_MODEL = "all-minilm"


class OllamaEmbedder:
    """Embeds text with a model served by a local Ollama instance."""

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or DEFAULT_MODEL

    def get_embeddings(self, sentences: list[str] | str) -> list[list[float]]:
        """Return one embedding per sentence."""
        import ollama

        return ollama.embed(model=self.model_name, input=sentences).embeddings
