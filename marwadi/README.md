# Marwadi ASR Fine-Tuning Module

This folder extends the existing `go-transcribe-ai` project for Marwadi speech-to-text and multilingual supervised fine-tuning.

## Goals
- Collect Marwadi speech audio from public sources
- Clean and normalize audio for training
- Build a supervised dataset with transcript pairs
- Fine-tune a Whisper-based ASR model
- Validate with train/validation/test splits and WER monitoring
- Prepare the model for integration back into the main ASR pipeline

## Proposed structure
- `data_collection/` - download and curate public Marwadi audio
- `preprocessing/` - normalization, silence trimming, resampling, metadata generation
- `training/` - supervised fine-tuning and validation logic

## Recommended pipeline
1. Collect raw audio from YouTube, podcast sources, and public speech datasets
2. Convert to a single format and clean metadata
3. Create a manifest CSV with columns:
   - `audio_path`
   - `text`
   - `duration`
   - `source`
4. Train/validation/test split with stratification by source where possible
5. Fine-tune Whisper using supervised ASR
6. Track WER, CER, and validation loss
7. Save checkpoints and merge back into the main app pipeline

## Training principle
Use a supervised learning setup with:
- 70% train / 15% validation / 15% test
- early stopping based on validation loss
- checkpoint saving at best validation score
- regularization (weight decay, dropout, limited epochs)
- no aggressive overtraining on tiny datasets

## Example commands
```bash
python marwadi/data_collection/youtube_scraper.py --query "marwadi speech" --max-videos 20
python marwadi/preprocessing/normalize_audio.py --input-dir data/raw_audio --output-dir data/processed_audio
python marwadi/training/whisper_finetune.py --manifest data/manifest.csv --model-name openai/whisper-small
```

## Notes
This is a foundation layer. As soon as you have enough quality data, we can upgrade to a stronger model and larger corpus.
