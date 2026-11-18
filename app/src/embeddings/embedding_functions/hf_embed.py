from app.src.core.ui import default_ui
from app.utils.paths import data_dir

_DISPLAYED_DOWNLOADING_MESSAGE = False


class HFEmbedder:
    def __init__(self, model_name: str):
        self.model_name = model_name

    # Mean Pooling - Take attention mask into account for correct averaging
    @staticmethod
    def _mean_pooling(model_output, attention_mask):
        import torch

        token_embeddings = model_output[
            0
        ]  # First element of model_output contains all token embeddings
        input_mask_expanded = (
            attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        )
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(
            input_mask_expanded.sum(1), min=1e-9
        )

    def get_embeddings(self, sentences: list[str] | str) -> list[list[float]]:
        """
        Get embeddings for a list of sentences using a Hugging Face model.

        Args:
            sentences (list[str] | str): List of sentences to embed or a single sentence.

        Returns:
            list[list[float]]: List of embeddings for each sentence.
        """
        global _DISPLAYED_DOWNLOADING_MESSAGE

        import torch
        import torch.nn.functional as F
        import transformers.utils.logging as hf_logging
        from transformers import AutoModel, AutoTokenizer

        hf_logging.set_verbosity_error()
        models_dir = data_dir("embedding_models", "ALLY_EMBEDDING_MODELS_DIR")

        if not _DISPLAYED_DOWNLOADING_MESSAGE and not any(models_dir.iterdir()):
            with default_ui.console.status("Downloading embedding model..."):
                tokenizer = AutoTokenizer.from_pretrained(
                    self.model_name, cache_dir=models_dir
                )
                model = AutoModel.from_pretrained(self.model_name, cache_dir=models_dir)
            _DISPLAYED_DOWNLOADING_MESSAGE = True
        else:
            tokenizer = AutoTokenizer.from_pretrained(
                self.model_name, cache_dir=models_dir
            )
            model = AutoModel.from_pretrained(self.model_name, cache_dir=models_dir)

        encoded_input = tokenizer(
            sentences, padding=True, truncation=True, return_tensors="pt"
        )

        with torch.no_grad():
            model_output = model(**encoded_input)

        sentence_embeddings = self._mean_pooling(
            model_output, encoded_input["attention_mask"]
        )
        sentence_embeddings = F.normalize(sentence_embeddings, p=2, dim=1)

        return sentence_embeddings.tolist()
