# Noggimigo FT-001 adapter

This directory records the LoRA adapter configuration produced by experiment FT-001.

**Base model:** [Qwen/Qwen3-0.6B](https://huggingface.co/Qwen/Qwen3-0.6B)  
**Adapter type:** LoRA  
**Rank:** 8  
**Alpha:** 16  
**Dropout:** 0.05

## Files

- `adapter_config.json` — included.
- `tokenizer_config.json` — included.
- `chat_template.jinja` — included.
- `adapter_model.safetensors` — binary weights; add from the FT-001 Colab ZIP.
- `tokenizer.json` — tokenizer asset; add from the FT-001 Colab ZIP if a self-contained tokenizer folder is desired.

The adapter is not a standalone model. Load it with the exact compatible base model and PEFT.

## Add the remaining local artifacts

Extract `noggimigo-ft-001-adapter.zip` and copy `adapter_model.safetensors` and `tokenizer.json` into this directory. The ZIP was approximately 20.5 MB; the adapter weights were 20,236,472 bytes.

Do not describe this artifact as a validated tutoring improvement. See [FT-001 experiment notes](../../experiments/FT-001/README.md).
