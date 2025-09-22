from transformers import AutoTokenizer, AutoModel
from app.utils.constants import DEFAULT_PATHS
from app.src.helpers.valid_dir import validate_dir_name
import torch.nn.functional as F
import torch
import os
from pathlib import Path
from app.src.core.ui import default_ui


# configure embedding models path
EMBEDDING_MODEL_PATH = ""
if "ALLY_EMBEDDING_MODELS_DIR" in os.environ:
    EMBEDDING_MODEL_PATH = Path(os.getenv("ALLY_EMBEDDING_MODELS_DIR"))
    if not validate_dir_name(str(EMBEDDING_MODEL_PATH)):
        EMBEDDING_MODEL_PATH = ""
        default_ui.warning(
            "Invalid directory path found in $ALLY_EMBEDDING_MODELS_DIR. Reverting to default path."
        )

if not EMBEDDING_MODEL_PATH:
    EMBEDDING_MODEL_PATH = DEFAULT_PATHS["embedding_models"]
    if os.name == "nt":
        EMBEDDING_MODEL_PATH = Path(os.path.expandvars(EMBEDDING_MODEL_PATH))
    else:
        EMBEDDING_MODEL_PATH = Path(os.path.expanduser(EMBEDDING_MODEL_PATH))


class HFEmbedder:
    
    def __init__(self, model_name: str):
        self.model_name = model_name
    
    # Mean Pooling - Take attention mask into account for correct averaging
    @staticmethod
    def _mean_pooling(model_output, attention_mask):
        token_embeddings = model_output[
            0
        ]  # First element of model_output contains all token embeddings
        input_mask_expanded = (
            attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        )
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(
            input_mask_expanded.sum(1), min=1e-9
        )


    def get_embeddings_hf(self, sentences: list[str] | str) -> list[list[float]]:  
        """
        Get embeddings for a list of sentences using a Hugging Face model.
        Args:
            sentences (list[str] | str): List of sentences to embed or a single sentence.
            model_name (str): Name of the Hugging Face model to use.

        Returns:
            list[list[float]]: List of embeddings for each sentence.
        """
        tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        model = AutoModel.from_pretrained(self.model_name)

        encoded_input = tokenizer(
            sentences, padding=True, truncation=True, return_tensors="pt"
        )

        with torch.no_grad():
            model_output = model(**encoded_input)

        sentence_embeddings = self._mean_pooling(model_output, encoded_input["attention_mask"])
        sentence_embeddings = F.normalize(sentence_embeddings, p=2, dim=1)

        return sentence_embeddings.tolist()
