import transformers
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch


from ..llm_generation import AnswerQuestionGenerator
from ..prompt_generation import PromptGenerator


class FalconQuestionAnswering7B(AnswerQuestionGenerator):
    def __init__(
        self,
        prompt_generator: PromptGenerator,
        model_name="tiiuae/falcon-7b-instruct",
    ) -> None:
        super().__init__(prompt_generator, model_name)
        self.model_name = model_name
        self.device = "auto"
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=True,
            device_map=self.device,
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            trust_remote_code=True,
            torch_dtype=torch.bfloat16,  # pylint: disable=no-member
            device_map=self.device,
        )
        self.pipeline = transformers.pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            torch_dtype=torch.bfloat16,  # pylint: disable=no-member
            device_map=self.device,
            trust_remote_code=True,
        )

    def count_tokens(self, contexts: list[str]) -> int:
        num_tokens = 0
        for context in contexts:
            num_tokens += len(self.tokenizer.encode(context))
        return num_tokens

    def get_answer(self, question: str, contexts: list[str]) -> str:
        prompt = self.prompt_generator.create_prompt_messages(question, contexts)
        print(f"prompting {self.model_name} with {self.count_tokens([prompt])} tokens...")
        sequences = self.pipeline(
            prompt,
            max_length=1300,
            max_new_tokens=1000,
            do_sample=True,
            top_k=10,
            num_return_sequences=1,
            eos_token_id=self.tokenizer.eos_token_id,
        )

        return " ".join([sequence["generated_text"] for sequence in sequences])


class FalconQuestionAnswering40B(AnswerQuestionGenerator):
    def __init__(
        self,
        prompt_generator: PromptGenerator,
        model_name="tiiuae/falcon-40b",
    ) -> None:
        super().__init__(prompt_generator, model_name)
        self.model_name = model_name
        self.device = "auto"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            trust_remote_code=True,
            torch_dtype=torch.bfloat16,  # pylint: disable=no-member
            device_map=self.device,
            load_in_8bit=True,
        )
        self.pipeline = transformers.pipeline("text-generation", model=self.model, tokenizer=self.tokenizer)

    def count_tokens(self, contexts: list[str]) -> int:
        num_tokens = 0
        for context in contexts:
            num_tokens += len(self.tokenizer.encode(context))
        return num_tokens

    def get_answer(self, question: str, contexts: list[str]) -> str:
        prompt = self.prompt_generator.create_prompt_messages(question, contexts)
        print(f"prompting {self.model_name} with {self.count_tokens([prompt])} tokens...")
        sequences = self.pipeline(
            prompt,
            max_length=1300,
            max_new_tokens=1000,
            do_sample=True,
            top_k=10,
            num_return_sequences=1,
            eos_token_id=self.tokenizer.eos_token_id,
        )

        return " ".join([sequence["generated_text"] for sequence in sequences])
