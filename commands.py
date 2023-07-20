import argparse
from corpus_generation.gpt_generators.question_generators import (
    GPTQuestionGenerator,
    GPTQuestionReformulation,
)

from retrieving.bm25_retriever import BM25Retriever

# from fine_tuning import fine_tune_model
from corpus_generation import CorpusGenerator, generate_questions
from corpus_generation.xgen_generators import (
    XGENAnswerGenerator,
    XGenPromptGenerator,
    get_count_tokens_fn,
)

from corpus_generation.gpt_generators import GPTAnswerGenerator, GPTPromptGenerator

COMMANDS_PARSER = argparse.ArgumentParser(
    description="Run commands for the project",
)
COMMANDS_PARSER.add_argument(
    "--parse_xml",
    help="This command will parse the xml files, "
    "cut them into chunks of 1000 tokens and save them in a json file",
    action="store_true",
)

COMMANDS_PARSER.add_argument(
    "--fine_tune_model",
    help="This command will fine tune the model on the corpus",
    action="store_true",
)

COMMANDS_PARSER.add_argument(
    "--gpt",
    help="This command will generate the corpus using GPT-3.5-Turbo",
    action="store_true",
)

COMMANDS_PARSER.add_argument(
    "--xgen",
    help="This command will generate the corpus using XGen-7B-4K-Base",
    action="store_true",
)

COMMANDS_PARSER.add_argument(
    "--run_weaviate_migration",
    help="This command will run the migration script for weaviate, "
    "importing the xml files in a vector database",
    action="store_true",
)

COMMANDS_PARSER.add_argument(
    "--generate_questions_openai",
    help="This command will generate questions using the OpenAI API",
    action="store_true",
)


def execute_commands(**commands):
    if commands.get("fine_tune_model"):
        # fine_tune_model()
        return

    if commands.get("parse_xml"):
        return

    if commands.get("run_weaviate_migration"):
        return

    context_retriever = BM25Retriever()
    token_counter_fn = get_count_tokens_fn("Salesforce/xgen-7b-4k-base")

    if commands.get("generate_questions_openai"):
        checkpoint = "gpt-3.5-turbo"
        prompt_generator = GPTPromptGenerator(
            token_counter_fn=token_counter_fn,
            prompt_token_limit=4000,
            model_name=checkpoint,
        )
        question_generator = GPTQuestionGenerator(
            prompt_generator,
            model_name=checkpoint,
        )
        reformu_generator = GPTQuestionReformulation(
            prompt_generator,
            model_name=checkpoint,
        )
        generate_questions(question_generator, reformu_generator)
        return
    if commands.get("gpt"):
        checkpoint = "gpt-3.5-turbo"

        prompt_generator = GPTPromptGenerator(
            token_counter_fn=token_counter_fn,
            prompt_token_limit=4000,
            model_name=checkpoint,
        )
        llm_generator = GPTAnswerGenerator(
            prompt_generator,
            model_name=checkpoint,
        )

    elif commands.get("xgen"):
        checkpoint = "Salesforce/xgen-7b-4k-base"
        prompt_generator = XGenPromptGenerator(
            token_counter_fn=token_counter_fn,
            prompt_token_limit=4000,
            model_name=checkpoint,
        )

        # if loading a fine-tuned model, must starts with "./"
        checkpoint = "./fine-tuned-model"
        llm_generator = XGENAnswerGenerator(
            prompt_generator,
            model_name=checkpoint,
            max_new_tokens=100,
            repetition_penalty=1.2,
        )
    corpus_generator = CorpusGenerator(
        prompt_generator,
        llm_generator,
        context_retriever,
    )
    corpus_generator.generate_corpus(
        questions_path="./questions-test.csv",
        corpus_path="corpus-results.csv",
    )
