import torch
from transformers import AutoModelForCausalLM
from peft import PeftConfig, PeftModel

from .tokenizer import get_tokenizer
from ..llm_generation import AnswerQuestionGenerator
from ..prompt_generation import PromptGenerator


class XGENAnswerGenerator(AnswerQuestionGenerator):
    def __init__(
        self,
        prompt_generator: PromptGenerator,
        model_name: str,
        max_new_tokens: int = 100,
        repetition_penalty: float = 1.2,
    ) -> None:
        super().__init__(prompt_generator, model_name, max_new_tokens, repetition_penalty)
        self.tokenizer = get_tokenizer(self.prompt_generator.model_name)
        if self.model_name.startswith("./"):
            self.model = self.load_local_model(self.model_name)
        else:
            print(f"loading pre-trained model {self.model_name}...")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                torch_dtype=torch.bfloat16,  # pylint: disable=no-member
            )

    def load_local_model(self, model_name: str) -> AutoModelForCausalLM:
        config = PeftConfig.from_pretrained(model_name)
        print(f"loading fine-tuned model {config.base_model_name_or_path} from {model_name}...")
        model = AutoModelForCausalLM.from_pretrained(
            config.base_model_name_or_path,
            return_dict=True,
            load_in_8bit=True,
            device_map="auto",
        )
        model = PeftModel.from_pretrained(model, model_name)
        return model

    def get_answer(self, question: str, contexts: list[str]) -> str:
        prompt = self.prompt_generator.create_prompt_messages(question, contexts)
        print(f"prompting {self.model_name} with " f"{self.prompt_generator.count_tokens(prompt)} tokens...")
        inputs = self.tokenizer(prompt, return_tensors="pt").to("cuda")
        response = self.model.generate(
            **inputs,
            max_new_tokens=self.max_new_tokens,
            repetition_penalty=self.repetition_penalty,
        )

        return self.tokenizer.decode(response[0]).replace(prompt, "")
