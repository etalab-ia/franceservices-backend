import csv
import json
import time
import pandas as pd


from retrieving.retrieving import ContextRetriever
from .prompt_generation import PromptGenerator
from .llm_generation import AnswerQuestionGenerator, QuestionGenerator

from .params import (
    XML_PARSED_PATH,
    GENERATED_QUESTIONS,
    QUESTION_NB,
)


def generate_questions(
    question_generator: QuestionGenerator, reformu_generator: QuestionGenerator
):
    with open(
        XML_PARSED_PATH, "r", encoding="utf-8"
    ) as origin:  # Récupération de l'ensemble des chunks
        data = json.load(origin)

    progres, chunks_nb = 0, len(data)

    with open(
        GENERATED_QUESTIONS, "a", encoding="utf-8"
    ) as file:  # Création d'un fichier avec toutes les questions générées
        writer = csv.writer(file, delimiter=";")
        writer.writerow(["question", "url"])
        file.close()

    while progres != chunks_nb - 1:
        url_fiche = data[progres]["metadata"]["xml_url"]
        contexts = []

        while (
            progres != chunks_nb - 1
            and len(contexts) < 10
            and data[progres]["metadata"]["xml_url"] == url_fiche
        ):  # on génère les questions par rappport à une seule fiche. La taille maximale de chunks est de 10, observée en testant à la main.
            contexts.append(data[progres]["data"])
            progres += 1

        raw_questions = question_generator.get_question(contexts, QUESTION_NB)
        gen_questions = raw_questions.split("\n")

        with open(GENERATED_QUESTIONS, "a", encoding="utf-8") as file:
            writer = csv.writer(file, delimiter=";")
            for i in range(len(gen_questions)):
                question = gen_questions[i][3:]
                if (
                    len(question) > 10
                ):  # par sécurité, il arrive que des problèmes arrivent lors du split
                    reformulated_questions = reformu_generator.get_question(
                        question
                    )  # obtention des 4 questions reformulées
                    refo_questions = reformulated_questions.split("\n")

                    writer.writerow([question, url_fiche])
                    for i in range(len(refo_questions)):
                        ref_ques = refo_questions[i][3:]

                        if len(ref_ques) > 10:
                            writer.writerow([ref_ques, url_fiche])

            file.close()

        print(f"{progres} chunks utilisés sur {chunks_nb}")


class CorpusGenerator:
    def __init__(
        self,
        prompt_generator: PromptGenerator,
        llm_generator: AnswerQuestionGenerator,
        context_retriever: ContextRetriever,
    ):
        self.prompt_generator = prompt_generator
        self.llm_generator = llm_generator
        self.context_retriever = context_retriever

    def write_header(self, file_path):
        with open(file_path, "w", encoding="utf-8") as save_file:
            save_file.write(
                "question;answer;prompt;token_answer;tokens_prompt;"
                "time_taken;url_contexts;retrieving_scores;chunks_indexs\n"
            )

    def get_questions(self, file_path):
        questions = pd.read_csv(file_path, sep=";")["question"].to_list()
        return questions

    def generate_corpus(self, questions_path, corpus_path):
        self.write_header(corpus_path)
        questions = self.get_questions(questions_path)

        for index, question in enumerate(questions):
            print(f"Question {index + 1} / {len(questions) + 1}")
            self.process_question(question, corpus_path)

    def process_question(self, question, save_path):
        start_time = time.time()
        contexts = self.context_retriever.retrieve_contexts(question, n_contexts=3)
        urls = "\n".join([context["url"] for context in contexts])
        scores = "\n".join([f'{float(context["score"]):.2f}' for context in contexts])
        chunks_index = "\n".join([str(context["doc_id"]) for context in contexts])
        contexts = [context["text"] for context in contexts]
        response = self.llm_generator.get_answer(question, contexts)
        prompt = self.prompt_generator.create_prompt_messages(question, contexts)
        self.write_result(
            question,
            response,
            prompt,
            start_time,
            urls,
            scores,
            chunks_index,
            save_path,
        )

    def write_result(
        self,
        question,
        response,
        prompt,
        start_time,
        urls,
        scores,
        chunks_index,
        save_path,
    ):
        if isinstance(prompt, list):
            prompt = " ".join([message["content"] for message in prompt])
        prompt = prompt.replace(";", ",").replace('"', "'")
        response = response.replace(";", ",").replace('"', "'")
        response_lenght = self.prompt_generator.count_tokens(response)
        prompt_lenght = self.prompt_generator.count_tokens(prompt)

        time_taken = time.time() - start_time
        with open(save_path, "a", encoding="utf-8") as save_file:
            save_file.write(
                f'"{question}";"{response}";"{prompt}";"{response_lenght}";'
                + f'"{prompt_lenght}";"{time_taken:.2f}";"{urls}";"{scores}";"{chunks_index}"\n'
            )
