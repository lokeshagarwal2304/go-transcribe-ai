#!/usr/bin/env python3
"""Fine-tune Whisper for Marwadi / multilingual speech recognition.

This is a supervised ASR setup intended for a small but robust domain-specific corpus.
It is built for stable training and validation, not blind overtraining.
"""

import argparse
from pathlib import Path

import pandas as pd
import torch
from datasets import Dataset
from transformers import AutoProcessor, WhisperForConditionalGeneration, Seq2SeqTrainingArguments, Seq2SeqTrainer


MODEL_MAP = {
    "tiny": "openai/whisper-tiny",
    "base": "openai/whisper-base",
    "small": "openai/whisper-small",
    "medium": "openai/whisper-medium",
}


def prepare_dataset(manifest_path: str, audio_dir: str):
    df = pd.read_csv(manifest_path)
    df = df.dropna(subset=["audio_path", "text"])

    dataset = []
    for _, row in df.iterrows():
        audio_file = Path(audio_dir) / Path(row["audio_path"]).name
        if not audio_file.exists():
            raise FileNotFoundError(f"Missing audio file: {audio_file}")

        dataset.append({
            "audio": str(audio_file),
            "text": str(row["text"]),
        })

    return Dataset.from_list(dataset)


def tokenize_batch(batch, processor):
    audio = [sample["array"] for sample in batch["audio"]]
    texts = [sample["text"] for sample in batch["text"]]

    features = processor(audio=audio, sampling_rate=16000, text=texts, return_tensors="pt", padding=True)
    input_ids = features["input_ids"]
    labels = features["labels"]
    return {"input_ids": input_ids, "labels": labels, "attention_mask": features["attention_mask"]}


def train_whisper(manifest_path: str, audio_dir: str, model_name: str, output_dir: str, epochs: int = 8, batch_size: int = 4):
    processor = AutoProcessor.from_pretrained(model_name)
    model = WhisperForConditionalGeneration.from_pretrained(model_name)

    ds = prepare_dataset(manifest_path, audio_dir)
    ds = ds.train_test_split(test_size=0.15, seed=42)
    train_ds = ds["train"]
    val_ds = ds["test"]

    # Keep the dataset compatible with the audio/text tokenization flow
    def map_to_features(examples):
        audios = [
            {"array": audio, "sampling_rate": 16000}
            for audio in [
                __import__("soundfile").SoundFile(str(audio_path)).read()
                for audio_path in [Path(audio_dir) / Path(path).name for path in examples["audio"]]
            ]
        ]
        texts = examples["text"]
        enc = processor(audio=audios, sampling_rate=16000, text=texts, return_tensors="pt", padding=True)
        enc = {k: v for k, v in enc.items()}
        labels = enc.pop("labels")
        enc["labels"] = labels
        return enc

    train_ds = train_ds.map(map_to_features, batched=True, batch_size=batch_size)
    val_ds = val_ds.map(map_to_features, batched=True, batch_size=batch_size)

    args = Seq2SeqTrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        learning_rate=1e-5,
        warmup_steps=50,
        num_train_epochs=epochs,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        logging_steps=20,
        save_total_limit=3,
        predict_with_generate=True,
        fp16=torch.cuda.is_available(),
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        dataloader_num_workers=0,
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        tokenizer=processor,
    )

    trainer.train()
    trainer.save_model(output_dir)
    print(f"[INFO] Training complete. Best checkpoint saved in: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fine-tune a Whisper ASR model on Marwadi speech data")
    parser.add_argument("--manifest", type=str, required=True, help="CSV manifest containing audio_path and text columns")
    parser.add_argument("--audio-dir", type=str, required=True, help="Directory containing audio files")
    parser.add_argument("--model-name", type=str, default="openai/whisper-small", help="Base Whisper checkpoint")
    parser.add_argument("--output-dir", type=str, default="models/marwadi-whisper", help="Output directory for fine-tuned model")
    parser.add_argument("--epochs", type=int, default=8, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=4, help="Per-device batch size")
    args = parser.parse_args()

    train_whisper(
        manifest_path=args.manifest,
        audio_dir=args.audio_dir,
        model_name=args.model_name,
        output_dir=args.output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
    )
