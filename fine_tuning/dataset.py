import pandas as pd
from datasets import Dataset, load_dataset
from transformers import AutoTokenizer


def get_dataset(q_a_file: str, tokenizer: AutoTokenizer) -> tuple[Dataset, Dataset]:
    data_df = pd.read_csv(q_a_file, delimiter=";")
    if "full_prompt" not in data_df.columns:
        data_df["full_prompt"] = data_df["prompt"] + "\n>>>ANSWER<<<\n" + data_df["answer"] + tokenizer.eos_token
        data_df["full_prompt"].to_csv(q_a_file.replace(".csv", ".only-full-prompt.csv"), sep=";", index=False)

    def tokenize_function(dataset_element):
        full_prompt = dataset_element["full_prompt"]
        prompt_tokens = tokenizer(
            full_prompt,
            truncation=True,
            max_length=4000,
        )
        return {**prompt_tokens}

    datasets = load_dataset(
        "csv",
        data_files=q_a_file,
        delimiter=";",
        split="train",
        column_names=["full_prompt"],
    ).train_test_split(test_size=0.1, seed=42, shuffle=True)

    tokenized_datasets = datasets.map(
        tokenize_function,
        remove_columns=["full_prompt"],
        batched=True,
    )
    train_dataset, test_dataset = (
        tokenized_datasets["train"],
        tokenized_datasets["test"],
    )

    return train_dataset, test_dataset
