from typing import Dict, List, Optional, Union


class Prompter:
    URL = "URL of the LLM API"
    SAMPLING_PARAMS = "dict of default smapling params fo a given child class"

    def __init__(self, mode=None):
        # The smapling params to pass to LLM generate function for inference.
        self.sampling_params = self.SAMPLING_PARAMS
        # A parameter used to configure the prompt (correspond to a system message for chat oriented LLM)
        self.mode = mode
        # Eventually stores the sources returns by the last RAG prompt built
        self.sources = None

    def make_prompt(self, **kwargs):
        return

    def set_mode(self, mode):
        self.mode = mode

    @property
    def url(self):
        return self.URL


# see https://github.com/facebookresearch/llama/blob/main/llama/generation.py#L284
def format_llama_chat_prompt(item: Union[Dict, str]):
    # An item as at least one {prompt} entry, and on optionnal {answer} entry
    # in the case of a formating for a finetuning step.
    if isinstance(item, str):
        item = {"prompt": item}

    bos, eos = "<s>", "</s>"
    B_INST, E_INST = "[INST]", "[/INST]"
    B_SYS, E_SYS = "<<SYS>>\n", "\n<</SYS>>\n\n"

    if "answer" in item:
        # Finetuning format
        prompt = f"{B_INST} {(item['prompt']).strip()} {E_INST} {(item['answer']).strip()} "
        prompt = bos + prompt + eos
    else:
        # Inference format
        prompt = f"{B_INST} {(item['prompt']).strip()} {E_INST}"
        prompt = bos + prompt

    # @hugingface: it still keep other features :o
    return {"text": prompt}
