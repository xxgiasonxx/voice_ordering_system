import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from datasets import load_dataset
from peft import get_peft_model, LoraConfig
from trl import SFTTrainer
from unsloth import FastLanguageModel

# 設定參數
model_name = "unsloth/Qwen3-0.6B-unsloth-bnb-4bit"  # 4-bit 量化版本
max_seq_length = 2048  # 上下文長度
dataset_path = "qwen3_dataset.json"
output_dir = "./qwen3_finetuned"

# 載入模型和 tokenizer
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=model_name,
    max_seq_length=max_seq_length,
    load_in_4bit=True,  # 啟用 4-bit 量化
    dtype=torch.bfloat16,  # 混合精度
)

# 設定 LoRA 參數
lora_config = LoraConfig(
    r=16,  # LoRA 秩
    lora_alpha=16,
    lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    bias="none",
    task_type="CAUSAL_LM",
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()  # 查看可訓練參數量

# 載入資料集
dataset = load_dataset("json", data_files=dataset_path, split="train")

# 格式化資料為對話格式
def format_conversation(example):
    conversations = example["conversations"]
    messages = [
        {"role": conv["from"], "content": conv["value"]}
        for conv in conversations
    ]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    return {"text": text}

dataset = dataset.map(format_conversation)

# 設定訓練參數
training_args = TrainingArguments(
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    warmup_steps=5,
    max_steps=60,  # 訓練步數，約 1-2 小時
    learning_rate=2e-4,
    fp16=not torch.cuda.is_bf16_supported(),
    bf16=torch.cuda.is_bf16_supported(),
    logging_steps=1,
    optim="adamw_8bit",
    weight_decay=0.01,
    lr_scheduler_type="linear",
    seed=3407,
    output_dir=output_dir,
)

# 初始化訓練器
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=max_seq_length,
    args=training_args,
    packing=False,  # 短序列不用 packing
)

# 開始訓練
trainer.train()

# 儲存微調模型
model.save_pretrained(output_dir)
tokenizer.save_pretrained(output_dir)

print("微調完成！模型已儲存到", output_dir)