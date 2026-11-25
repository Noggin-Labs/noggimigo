# FT-001 — Noggimigo LoRA SFT pilot

**Status:** Training completed; independent evaluation pending.  
**Base model:** `Qwen/Qwen3-0.6B`  
**Method:** Supervised fine-tuning (SFT) with a LoRA adapter.

## Purpose

Test whether the Noggimigo fine-tuning pipeline can prepare a small dataset, attach a LoRA adapter, complete a training run, save the adapter, and reload it for inference.

This is a technical smoke test, not a validated model-improvement study.

## Dataset

Five manually authored, single-turn candidate examples were used across five categories:

- Socratic introduction
- Guided problem solving
- Misconception correction
- Clarification
- Neurodiversity-aware teaching preference

The examples are in [training-examples.json](training-examples.json). There were no independent evaluation examples in this run.

## Training result

- Epochs: 1
- Optimizer steps: 5
- Reported training loss: 3.684313249588013
- Trainable parameters: 5,046,272 of 601,096,192 (0.8395%)
- All five examples remained after preprocessing and had supervised tokens.

Per-step losses and environment details are in [training-log.md](training-log.md). Exact settings are in [training-config.json](training-config.json).

## Inference observation

The saved adapter was reloaded onto a fresh base-model instance successfully. One generation completed:

> Great question! Probability is the study of chance and likelihood. It helps us understand how likely an event will happen, and how we can calculate those probabilities. Let me help you understand it better. What would you like to explore?

This response is coherent and relevant, but it does not demonstrate a concrete Socratic reasoning prompt. A controlled comparison and independent evaluation remain pending.

## Reproducibility and artifacts

The adapter directory produced by the run contained:

- `adapter_model.safetensors`
- `adapter_config.json`
- `tokenizer.json`
- `tokenizer_config.json`
- `chat_template.jinja`

The text configuration files are included under [models/FT-001](../../models/FT-001/README.md). The binary adapter weights and full tokenizer JSON are not included in this commit; add them from the saved Colab ZIP before treating this repository snapshot as a complete downloadable model artifact.

The adapter requires the original `Qwen/Qwen3-0.6B` base model. It is not a standalone model.

## Limitations and next steps

1. Create a separate, reviewed evaluation set before further training.
2. Run the same prompts and generation settings against the base model, prompted base model, and fine-tuned model.
3. Score outputs with a predefined rubric and preferably blinded review.
4. Preserve raw outputs, failures, software versions, and model revision identifiers.
5. Do not interpret lower training loss as evidence of better tutoring or generalization.
