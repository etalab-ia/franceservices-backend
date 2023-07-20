import os

from transformers import (
    Seq2SeqTrainer,
    DataCollatorForLanguageModeling,
    AutoTokenizer,
)
from datasets import Dataset

from corpus_generation.xgen_generators.tokenizer import get_tokenizer

from .load_model import load_model
from .dataset import get_dataset
from .params import (
    TRAINING_DATA_FOLDER,
    TRAINING_ARGS,
    CHECKPOINT,
    MODEL_SAVE_FOLDER,
    DATASET_PATH,
)


def get_trainer(
    train_dataset: Dataset,
    test_dataset: Dataset,
    tokenizer: AutoTokenizer,
) -> Seq2SeqTrainer:
    model = load_model()

    trainer = Seq2SeqTrainer(
        model=model,
        args=TRAINING_ARGS,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False),
    )
    return trainer


def fine_tune_model() -> None:
    tokenizer = get_tokenizer(CHECKPOINT)
    train_dataset, test_dataset = get_dataset(
        os.path.join(TRAINING_DATA_FOLDER, DATASET_PATH),
        tokenizer,
    )
    trainer = get_trainer(train_dataset, test_dataset, tokenizer)
    trainer.train()
    trainer.save_model(MODEL_SAVE_FOLDER)
