import os
from transformers import Seq2SeqTrainingArguments


TRAINING_DATA_FOLDER = "./fine_tuning/data"

TRAINING_ARGS = Seq2SeqTrainingArguments(
    output_dir=os.path.join(TRAINING_DATA_FOLDER, "models"),
    save_strategy="epoch",
    evaluation_strategy="epoch",
    num_train_epochs=5,
    per_device_train_batch_size=2,
    fp16=True,
    per_device_eval_batch_size=2,
    warmup_steps=500,  # number of warmup steps for learning rate scheduler
    weight_decay=0.01,  # strength of weight decay
    logging_dir=os.path.join(TRAINING_DATA_FOLDER, "logs"),
    logging_steps=1,
    load_best_model_at_end=True,
)

CHECKPOINT = "Salesforce/xgen-7b-4k-base"
MODEL_SAVE_FOLDER = "./fine-tuned-model"
DATASET_PATH = os.path.join(TRAINING_DATA_FOLDER, "dataset-test.csv")
