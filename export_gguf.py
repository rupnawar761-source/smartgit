from unsloth import FastLanguageModel

# Load the base model together with your trained LoRA adapter
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "lora_model",  # the folder train.py saved to
    max_seq_length = 2048,
    dtype = None,
    load_in_4bit = True,
)

# Merge LoRA weights into the base model and export straight to GGUF.
# q4_k_m is a good default: small file size, minimal quality loss.
model.save_pretrained_gguf(
    "smartgit_qwen_gguf",
    tokenizer,
    quantization_method = "q4_k_m",
)

print("Done! GGUF file is in the smartgit_qwen_gguf/ folder.")