# FT-001 training log

## Environment

- Python: 3.13.16
- PyTorch: 2.14.1+cu130
- Transformers: 5.24.1
- Datasets: 5.2.0
- PEFT: 0.22.0
- TRL: 1.19.0
- GPU: Tesla T4; CUDA available; reported GPU memory 15.64 GB

## Dataset preprocessing

- Candidate training examples: 5
- Processed training examples: 5
- Evaluation examples: 0
- Supervised tokens by example: 159, 164, 173, 143, 165
- Total supervised tokens: 804

## LoRA parameter report

- Trainable parameters: 5,046,272
- Total parameters: 601,096,192
- Trainable percentage: 0.8395%

## Training

| Step | Training loss |
|---:|---:|
| 1 | 3.993676 |
| 2 | 3.905938 |
| 3 | 3.620902 |
| 4 | 3.552787 |
| 5 | 3.348264 |

- Epochs completed: 1/1
- Global steps: 5
- Trainer-reported training loss: 3.684313249588013
- Training call completed without a reported training exception.

The loss decreased across the five steps. With five examples and no held-out evaluation set, this is not evidence of generalization or improved tutoring behavior.

## Artifact verification

- Adapter directory saved.
- `adapter_model.safetensors` present in the local ZIP (20,236,472 bytes).
- `adapter_config.json` present.
- Tokenizer files and chat template present.
- Adapter successfully reloaded onto a fresh `Qwen/Qwen3-0.6B` base model on CUDA.
- A subsequent generation call completed.

## Inference observation

Prompt: system prompt above; user prompt: `I want to learn probability.`

Raw fine-tuned response:

> Great question! Probability is the study of chance and likelihood. It helps us understand how likely an event will happen, and how we can calculate those probabilities. Let me help you understand it better. What would you like to explore?

Initial qualitative observation: relevant and friendly, but the follow-up is broad rather than a specific guided-reasoning question.

## Pending

- Controlled base / prompted-base / fine-tuned comparison.
- Independent evaluation dataset.
- Rubric-based evaluation.
- Base-model revision/hash capture.
- Complete binary artifact upload to the repository.
