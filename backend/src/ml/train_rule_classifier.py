from __future__ import annotations

import json
import random
from pathlib import Path

import numpy as np
import torch
from datasets import Dataset
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    EarlyStoppingCallback,
    Trainer,
    TrainingArguments,
)

MODEL_NAME = "DeepPavlov/rubert-base-cased"
DATA_PATH = Path("data/rules_dataset_3000.jsonl")
OUTPUT_DIR = Path("models/rule_classifier")
SEED = 42
MAX_LENGTH = 384


def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Файл датасета не найден: {path.resolve()}")

    rows = []
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"Ошибка JSON в строке {i}: {e}") from e
    return rows


def validate_rows(rows: list[dict]) -> list[dict]:
    clean_rows = []

    for i, row in enumerate(rows, start=1):
        text = str(row.get("text", "")).strip()
        label = row.get("label")

        if not text:
            print(f"[WARN] Пустой text в записи {i}, пропускаю")
            continue

        if label not in (0, 1):
            print(f"[WARN] Неверный label в записи {i}: {label}, пропускаю")
            continue

        clean_rows.append({
            "text": text,
            "label": int(label),
        })

    if not clean_rows:
        raise ValueError("После валидации датасет пуст.")

    labels = [r["label"] for r in clean_rows]
    unique = sorted(set(labels))
    if len(unique) < 2:
        raise ValueError(
            f"В датасете должны быть оба класса 0 и 1, сейчас есть только: {unique}"
        )

    return clean_rows


def tokenize_function(batch, tokenizer):
    return tokenizer(
        batch["text"],
        truncation=True,
        max_length=MAX_LENGTH,
    )


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=1)

    return {
        "accuracy": accuracy_score(labels, preds),
        "precision": precision_score(labels, preds, zero_division=0),
        "recall": recall_score(labels, preds, zero_division=0),
        "f1": f1_score(labels, preds, zero_division=0),
    }


class WeightedTrainer(Trainer):
    def __init__(self, class_weights: torch.Tensor | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.class_weights = class_weights

    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        logits = outputs.logits

        if self.class_weights is not None:
            loss_fct = torch.nn.CrossEntropyLoss(
                weight=self.class_weights.to(logits.device)
            )
        else:
            loss_fct = torch.nn.CrossEntropyLoss()

        loss = loss_fct(logits, labels)

        return (loss, outputs) if return_outputs else loss


def main():
    set_seed(SEED)

    print("[INFO] Старт обучения rule classifier")
    print(f"[INFO] DATA_PATH = {DATA_PATH.resolve()}")
    print(f"[INFO] OUTPUT_DIR = {OUTPUT_DIR.resolve()}")

    rows = load_jsonl(DATA_PATH)
    print(f"[INFO] Загружено строк: {len(rows)}")

    rows = validate_rows(rows)
    print(f"[INFO] Валидных строк: {len(rows)}")

    label_counts = {0: 0, 1: 0}
    for row in rows:
        label_counts[row["label"]] += 1
    print(f"[INFO] Распределение классов: {label_counts}")

    train_rows, temp_rows = train_test_split(
        rows,
        test_size=0.2,
        random_state=SEED,
        stratify=[r["label"] for r in rows],
    )

    val_rows, test_rows = train_test_split(
        temp_rows,
        test_size=0.5,
        random_state=SEED,
        stratify=[r["label"] for r in temp_rows],
    )

    print(f"[INFO] Train size: {len(train_rows)}")
    print(f"[INFO] Val size: {len(val_rows)}")
    print(f"[INFO] Test size: {len(test_rows)}")

    train_ds = Dataset.from_list(train_rows)
    val_ds = Dataset.from_list(val_rows)
    test_ds = Dataset.from_list(test_rows)

    print(f"[INFO] Загружаю токенизатор: {MODEL_NAME}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    train_ds = train_ds.map(lambda x: tokenize_function(x, tokenizer), batched=True)
    val_ds = val_ds.map(lambda x: tokenize_function(x, tokenizer), batched=True)
    test_ds = test_ds.map(lambda x: tokenize_function(x, tokenizer), batched=True)

    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    print(f"[INFO] Загружаю модель: {MODEL_NAME}")
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=2,
        id2label={0: "not_rule", 1: "rule"},
        label2id={"not_rule": 0, "rule": 1},
    )

    train_labels = [r["label"] for r in train_rows]
    class_counts = np.bincount(train_labels)
    class_weights = len(train_labels) / (2 * class_counts)
    class_weights = torch.tensor(class_weights, dtype=torch.float)
    print(f"[INFO] Class weights: {class_weights.tolist()}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_strategy="steps",
        logging_steps=10,
        learning_rate=2e-5,
        warmup_ratio=0.1,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        num_train_epochs=6,
        weight_decay=0.01,
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        report_to="none",
        save_total_limit=2,
        fp16=torch.cuda.is_available(),
        seed=SEED,
        disable_tqdm=False,
    )

    trainer = WeightedTrainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
        class_weights=class_weights,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
    )

    print("[INFO] Начинаю train()")
    trainer.train()
    print("[INFO] train() завершён")

    val_metrics = trainer.evaluate(eval_dataset=val_ds)
    print("[INFO] Validation metrics:", val_metrics)

    test_metrics = trainer.evaluate(eval_dataset=test_ds)
    print("[INFO] Test metrics:", test_metrics)

    print("[INFO] Сохраняю модель")
    trainer.save_model(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))

    print("[INFO] Готово. Модель сохранена в:", OUTPUT_DIR.resolve())


if __name__ == "__main__":
    main()