from pathlib import Path

from optimum.exporters.onnx import main_export
from transformers import AutoTokenizer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EXPORT_PATH = Path("src/ai_model")
EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)


def export_model():
    # 1. Скачиваем и сохраняем ONNX модель через Optimum
    main_export(
        model_name_or_path=MODEL_NAME,
        output=EXPORT_PATH,
        task="feature-extraction",
        framework="pt",
    )

    # 2. Сохраняем токенизатор
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    tokenizer.save_pretrained(EXPORT_PATH)

    # 3. Удаляем ненужные файлы (если есть)
    for f in EXPORT_PATH.glob("*onnx_data*"):
        f.unlink()

    for fname in [
        "config.json",
        "tokenizer_config.json",
        "special_tokens_map.json",
        "vocab.txt",
    ]:
        path = EXPORT_PATH / fname
        if path.exists():
            path.unlink()

    print(f"Модель успешно экспортирована в {EXPORT_PATH.resolve()}")


if __name__ == "__main__":
    export_model()
