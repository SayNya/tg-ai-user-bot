import logging
from pathlib import Path

from optimum.exporters.onnx import main_export
from transformers import AutoTokenizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

MODEL_NAME = "ai-forever/sbert_large_nlu_ru"
EXPORT_PATH = Path("src/ai_model")
EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)


def export_model():
    logger.info(f"Starting model export for {MODEL_NAME}")

    # 1. Скачиваем и сохраняем ONNX модель через Optimum
    logger.info("Exporting model to ONNX format...")
    main_export(
        model_name_or_path=MODEL_NAME,
        output=EXPORT_PATH,
        task="feature-extraction",
        framework="pt",
    )
    logger.info("ONNX model export completed")

    # 2. Сохраняем токенизатор
    logger.info("Saving tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    tokenizer.save_pretrained(EXPORT_PATH)
    logger.info("Tokenizer saved successfully")

    # 3. Удаляем ненужные файлы (если есть)
    logger.info("Cleaning up unnecessary files...")
    for f in EXPORT_PATH.glob("*onnx_data*"):
        f.unlink()
        logger.debug(f"Removed file: {f}")

    for fname in [
        "config.json",
        "tokenizer_config.json",
        "special_tokens_map.json",
        "vocab.txt",
    ]:
        path = EXPORT_PATH / fname
        if path.exists():
            path.unlink()
            logger.debug(f"Removed file: {path}")

    logger.info(f"Model successfully exported to {EXPORT_PATH.resolve()}")


if __name__ == "__main__":
    export_model()
