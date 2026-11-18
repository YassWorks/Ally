import importlib.util
import os

from app.src.core.ui import default_ui
from app.src.embeddings.rag_errors import SetupFailedError
from app.utils.paths import data_dir

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class HFEmbedder:
    """Embeds text locally with a Hugging Face model, using mean pooling.

    The model is downloaded on first use and kept in memory afterwards.

    Raises:
        SetupFailedError: If the optional ``hf`` dependencies are not installed.
    """

    def __init__(self, model_name: str | None = None):
        missing = [
            name
            for name in ("torch", "transformers")
            if not importlib.util.find_spec(name)
        ]
        if missing:
            raise SetupFailedError(
                "Hugging Face embeddings need the optional 'hf' extra "
                f"(missing: {', '.join(missing)}). Reinstall with ./setup.sh --hf "
                "or .\\setup.ps1 -HF."
            )
        self.model_name = model_name or DEFAULT_MODEL
        self._tokenizer = None
        self._model = None

    def _load(self) -> None:
        os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
        import transformers.utils.logging as hf_logging
        from transformers import AutoModel, AutoTokenizer

        hf_logging.set_verbosity_error()
        hf_logging.disable_progress_bar()
        cache_dir = data_dir("embedding_models", "ALLY_EMBEDDING_MODELS_DIR")
        with default_ui.console.status(f"Loading embedding model {self.model_name}..."):
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name, cache_dir=cache_dir
            )
            self._model = AutoModel.from_pretrained(
                self.model_name, cache_dir=cache_dir
            )
            self._model.eval()

    def get_embeddings(self, sentences: list[str] | str) -> list[list[float]]:
        """Return one normalized embedding per sentence."""
        import torch
        import torch.nn.functional as F

        if self._model is None:
            self._load()

        encoded = self._tokenizer(
            sentences, padding=True, truncation=True, return_tensors="pt"
        )
        with torch.no_grad():
            output = self._model(**encoded)

        token_embeddings = output[0]
        mask = (
            encoded["attention_mask"]
            .unsqueeze(-1)
            .expand(token_embeddings.size())
            .float()
        )
        pooled = torch.sum(token_embeddings * mask, 1) / torch.clamp(
            mask.sum(1), min=1e-9
        )
        return F.normalize(pooled, p=2, dim=1).tolist()
