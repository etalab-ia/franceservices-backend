import os
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    HfArgumentParser,
    TrainingArguments,
    pipeline,
    logging,
    LlamaTokenizerFast
)
from peft import LoraConfig, PeftModel, get_peft_model
from trl import SFTTrainer

# Le modèle que nous allons utiliser dans le Hugging Face hub
model_name = "/home/planglais/llama/llama-2-13b-hf"

torch.cuda.empty_cache()

#project_directory = "~/finetuning/sigmund-spplus"

# Le nom du nouveau modèle
new_model_name = "llama-2-13b-fab-v2"

# The output directory where the model predictions and checkpoints will be written
output_dir = "./llama-2-13b-fab-v2"

# Tensorboard logs
tb_log_dir = "./llama-2-13b-fab-v2/logs"

# Nombre de steps : à ajuster selon la taille du corpus et le nombre d'epochs à faire tourner.
max_steps = 4001


# Les paramètres importants !!
per_device_train_batch_size = 3 #Nombre d'exemples envoyés par batch. En mettre plus pour aller plus vite.
learning_rate = 2e-4 #De préférence un taux d'apprentissage élevé pour un texte en français.
max_seq_length = 4096 #C'est la fenêtre contextuelle. Elle peut être portée jusqu'à 4096 tokens (mais attention à la mémoire disponible !)
save_steps = 200 # Sauvegarde des steps (permet de faire redémarrer l'entraînement si le fine-tuning ne fonctionne pas)
# Learning rate schedule (constant a bit better than cosine, and has advantage for analysis)
lr_scheduler_type = "constant"


#Les autres paramètres
local_rank = -1
per_device_eval_batch_size = 1
gradient_accumulation_steps = 4
max_grad_norm = 0.3
weight_decay = 0.001
lora_alpha = 16
lora_dropout = 0.1
lora_r = 64
# Group sequences into batches with same length (saves memory and speeds up training considerably)
group_by_length = True

# Activate 4-bit precision base model loading
use_4bit = True

# Activate nested quantization for 4-bit base models
use_nested_quant = False

# Compute dtype for 4-bit base models
bnb_4bit_compute_dtype = "float16"

# Quantization type (fp4 or nf4=
bnb_4bit_quant_type = "nf4"

# Number of training epochs
num_train_epochs = 3

# Enable fp16 training
fp16 = True

# Enable bf16 training
bf16 = False

# Use packing dataset creating
packing = False

# Enable gradient checkpointing
gradient_checkpointing = True

# Optimizer to use, original is paged_adamw_32bit
optim = "paged_adamw_32bit"

# Fraction of steps to do a warmup for
warmup_ratio = 0.03

# Log every X updates steps
logging_steps = 1

# Load the entire model on the GPU 0
device_map = {"": 0}

# Visualize training
report_to = "tensorboard"


#2. Import du tokenizer.
peft_config = LoraConfig(
    lora_alpha=lora_alpha,
    lora_dropout=lora_dropout,
    r=lora_r,
    inference_mode=False,
    task_type="CAUSAL_LM",
)

tokenizer = LlamaTokenizerFast.from_pretrained(model_name, add_eos_token=True, from_slow=True)

# This is the fix for fp16 training
tokenizer.padding_side = "right"

#3. Préparation de la base de données

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
#dataset = load_dataset("databricks/databricks-dolly-15k", split="train")
data_files = {"train": "services_publics_instruction.json"}
dataset = load_dataset("json", data_files=data_files, split="train")

# Shuffle the dataset
dataset_shuffled = dataset.shuffle(seed=42)

# Select the first 250 rows from the shuffled dataset, comment if you want 15k
#dataset = dataset_shuffled.select(range(512))

#Transformation du dataset pour utiliser le format guanaco
dataset = dataset.map(template_dataset, remove_columns=list(dataset.features))

print(dataset[40])

#4. Import du modèle

# Load tokenizer and model with QLoRA configuration
compute_dtype = getattr(torch, bnb_4bit_compute_dtype)

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
    model_name,
    device_map=device_map,
    quantization_config=bnb_config
)

model.config.use_cache = False
model.config.pretraining_tp = 1

#5. Fine-tuning

torch.cuda.empty_cache()

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
    report_to="tensorboard"
)

trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    peft_config=peft_config,
    dataset_text_field="text",
    max_seq_length=max_seq_length,
    tokenizer=tokenizer,
    args=training_arguments,
    packing=packing
)

#trainer.train()
trainer.train(resume_from_checkpoint=True)

#6. Sauvegarde

model_to_save = trainer.model.module if hasattr(trainer.model, 'module') else trainer.model  # Take care of distributed/parallel training
model_to_save.save_pretrained(new_model_name)

torch.cuda.empty_cache()

from peft import AutoPeftModelForCausalLM

model = AutoPeftModelForCausalLM.from_pretrained(new_model_name, device_map="auto", torch_dtype=torch.bfloat16)
model = model.merge_and_unload()

output_merged_dir = os.path.join(new_model_name, new_model_name)
model.save_pretrained(output_merged_dir, safe_serialization=True)

#On récupère le tokenizer pour l'inférence
import shutil
shutil.copyfile("/home/planglais/llama/llama-2-13b-hf/tokenizer.model", output_merged_dir + "/tokenizer.model")
shutil.copyfile("/home/planglais/llama/llama-2-13b-hf/special_tokens_map.json", output_merged_dir + "/special_tokens_map.json")
shutil.copyfile("/home/planglais/llama/llama-2-13b-hf/tokenizer_config.json", output_merged_dir + "/tokenizer_config.json")
