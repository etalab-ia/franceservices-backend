import os
import shutil

import torch
from datasets import load_dataset
from peft import (AutoPeftModelForCausalLM, LoraConfig, PeftModel,
                  get_peft_model)
from transformers import (AutoModelForCausalLM, AutoTokenizer,
                          BitsAndBytesConfig, HfArgumentParser,
                          LlamaTokenizerFast, TrainingArguments, logging,
                          pipeline)
from trl import SFTTrainer

# @EXPLORE techniques to make training better, stronger, faster :
# - FlashAttention: https://arxiv.org/abs/2307.08691
# - DeepSpeed: https://github.com/microsoft/DeepSpeed
# - Self-chat ? : https://arxiv.org/abs/2304.01196
# -> Mentioned in this **Vigogne**: https://github.com/bofenghuang/vigogne

#
# 1. Parametrization
#

model_name = "NousResearch/Llama-2-13b-chat-hf"  # Base model
new_model_name = "albert-light-v0"  # new model name
output_dir = f"_data/models/{new_model_name}"  # The output directory where the model predictions and checkpoints will be written
tb_log_dir = f"{output_dir}/logs"  # Tensorboard logs

# Training parameters !
per_device_train_batch_size = (
    12  # Nombre d'exemples envoyés par batch. En mettre plus pour aller plus vite.
)
learning_rate = 2e-4  # De préférence un taux d'apprentissage élevé pour un texte en français.
max_seq_length = 2028  # C'est la fenêtre contextuelle. Elle peut être portée jusqu'à 4096 tokens (mais attention à la mémoire disponible !)
save_steps = 200  # Sauvegarde des steps (permet de faire redémarrer l'entraînement si le fine-tuning ne fonctionne pas)
lr_scheduler_type = "constant"  # Learning rate schedule (constant a bit better than cosine, and has advantage for analysis)
gradient_accumulation_steps = 4
max_grad_norm = 0.3
lora_r = 64
lora_alpha = 16
lora_dropout = 0.1
group_by_length = True  # Group sequences into batches with same length (saves memory and speeds up training considerably)
warmup_ratio = 0.03  # Fraction of steps to do a warmup for
optim = "paged_adamw_32bit"  # Optimizer to use, original is paged_adamw_32bit
logging_steps = 10  # Log every X updates steps

# To adjust given the traning size and epoch number
max_steps = 4001

# Unused ?
local_rank = -1
per_device_eval_batch_size = 1
weight_decay = 0.001
num_train_epochs = 1
gradient_checkpointing = True  # Enable gradient checkpointing

# Quantization
use_4bit = True  # Activate 4-bit precision base model loading
use_nested_quant = False  # Activate nested quantization for 4-bit base models
bnb_4bit_compute_dtype = "float16"  # Compute dtype for 4-bit base models
bnb_4bit_quant_type = "nf4"  # Quantization type (fp4 or nf4)
compute_dtype = getattr(torch, bnb_4bit_compute_dtype)

fp16 = True  # Enable fp16 training
bf16 = False  # Enable bf16 training

# Use packing dataset creating
packing = False

# Load the entire model on the GPU 0
device_map = {"": 0}

# Visualize training
report_to = "tensorboard"

#
# 2. Load training data
#

# Préparation de la base de données
def format_alpaca(sample):
    instruction = f"<s>{sample['instruction']}\n\n###Réponse : \n"
    context = None
    response = f"{sample['output']}"
    # join all the parts together
    prompt = "".join([i for i in [instruction, context, response] if i is not None])
    return prompt


# template dataset to add prompt to each sample
def template_dataset(sample):
    sample["text"] = f"{format_alpaca(sample)}{tokenizer.eos_token}"
    return sample


# Chargement du dataset.
# dataset = load_dataset("databricks/databricks-dolly-15k", split="train")
data_files = {"train": "services_publics_instruction.json"}
dataset = load_dataset("json", data_files=data_files, split="train")
dataset_shuffled = dataset.shuffle(seed=42) # Shuffle the dataset
dataset = dataset.map(template_dataset, remove_columns=list(dataset.features))

#
# 3. Load model and tokenizer
#

tokenizer = LlamaTokenizerFast.from_pretrained(model_name, add_eos_token=True, from_slow=True)
tokenizer.padding_side = "right"  # This is the fix for fp16 training

# Load tokenizer and model with QLoRA configuration
bnb_config = BitsAndBytesConfig(
    load_in_4bit=use_4bit,
    bnb_4bit_quant_type=bnb_4bit_quant_type,
    bnb_4bit_compute_dtype=compute_dtype,
    bnb_4bit_use_double_quant=use_nested_quant,
)

if compute_dtype == torch.float16 and use_4bit:
    major, _ = torch.cuda.get_device_capability()
    if major >= 8:
        print("=" * 80)
        print("Your GPU supports bfloat16, you can accelerate training with the argument --bf16")
        print("=" * 80)

model = AutoModelForCausalLM.from_pretrained(
    model_name, device_map=device_map, quantization_config=bnb_config
)

model.config.use_cache = False
model.config.pretraining_tp = 1

#
# 4. Fine-tuning
#

training_arguments = TrainingArguments(
    output_dir=output_dir,
    per_device_train_batch_size=per_device_train_batch_size,
    gradient_accumulation_steps=gradient_accumulation_steps,
    optim=optim,
    save_steps=save_steps,
    logging_steps=logging_steps,
    learning_rate=learning_rate,
    fp16=fp16,
    bf16=bf16,
    max_grad_norm=max_grad_norm,
    max_steps=max_steps,
    warmup_ratio=warmup_ratio,
    group_by_length=group_by_length,
    lr_scheduler_type=lr_scheduler_type,
    report_to=report_to,
)

peft_config = LoraConfig(
    lora_alpha=lora_alpha,
    lora_dropout=lora_dropout,
    r=lora_r,
    inference_mode=False,
    task_type="CAUSAL_LM",
)

trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    peft_config=peft_config,
    dataset_text_field="text",
    max_seq_length=max_seq_length,
    tokenizer=tokenizer,
    args=training_arguments,
    packing=packing,
)

trainer.train(resume_from_checkpoint=True)

#
# 5. Sauvegarde
#

model_to_save = (
    trainer.model.module if hasattr(trainer.model, "module") else trainer.model
)  # Take care of distributed/parallel training
model_to_save.save_pretrained(new_model_name)


#
# 6. Merged...
#
torch.cuda.empty_cache()

model = AutoPeftModelForCausalLM.from_pretrained(
    new_model_name, device_map="auto", torch_dtype=torch.bfloat16
)
model = model.merge_and_unload()

output_merged_dir = os.path.join(new_model_name, new_model_name)
model.save_pretrained(output_merged_dir, safe_serialization=True)

# On récupère le tokenizer pour l'inférence
#
# @FIX: how to do that in a clean way ?

#shutil.copyfile(
#    "/home/planglais/llama/llama-2-13b-hf/tokenizer.model", output_merged_dir + "/tokenizer.model"
#)
#shutil.copyfile(
#    "/home/planglais/llama/llama-2-13b-hf/special_tokens_map.json",
#    output_merged_dir + "/special_tokens_map.json",
#)
#shutil.copyfile(
#    "/home/planglais/llama/llama-2-13b-hf/tokenizer_config.json",
#    output_merged_dir + "/tokenizer_config.json",
#)
