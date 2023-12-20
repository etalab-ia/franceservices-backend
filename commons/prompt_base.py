import re

try:
    from app.core.acronyms import ACRONYMS
except ModuleNotFoundError as e:
    from api.app.core.acronyms import ACRONYMS


ACRONYMS_KEYS = [acronym["symbol"].lower() for acronym in ACRONYMS]


class Prompter:
    URL = "URL of the LLM API"
    SAMPLING_PARAMS = "dict of default sampling params fo a given child class"

    def __init__(self, mode=None):
        # The sampling params to pass to LLM generate function for inference.
        self.sampling_params = self.SAMPLING_PARAMS
        # A parameter used to configure the prompt (correspond to a system message for chat oriented LLM)
        self.mode = mode
        # Eventually stores the sources returned by the last RAG prompt built
        self.sources = None

    def set_mode(self, mode):
        self.mode = mode

    @property
    def url(self):
        return self.URL

    def make_prompt(self, **kwargs):
        return

    @staticmethod
    def _expand_acronyms(prompt: str) -> str:
        # Match potential acronyms
        # --
        # Terms that start by a number or maj, that contains at least 3 character, and that can be
        # preceded by a space, but not if the first non-space character encountered backwards is a dot.
        pattern = r"(?<!\S\. )[A-Z0-9][A-Za-z0-9]{2,}\b"
        matches = [
            (match.group(), match.start(), match.end()) for match in re.finditer(pattern, prompt)
        ]

        # Prevent extreme case (caps lock, list of items, etc)
        if len(matches) > 10:
            return prompt

        # Expand acronyms
        for match, start, end in matches[::-1]:
            try:
                i = ACRONYMS_KEYS.index(match.lower())
            except ValueError:
                continue

            acronym = ACRONYMS[i]
            look_around = 100
            text_span = (
                prompt[max(0, start - look_around) : start] + " " + prompt[end : end + look_around]
            )
            if not acronym["text"].lower() in text_span.lower():
                # I suppose we go here most of the time...
                # but I also suppose the test should be fast enough to be negligible.
                expanded = " (" + acronym["text"] + ")"
                prompt = prompt[:end] + expanded + prompt[end:]

        return prompt


# see https://github.com/facebookresearch/llama/blob/main/llama/generation.py#L284
def format_llama_chat_prompt(item: dict | str):
    # An item as at least one {prompt} entry, and on optionnal {answer} entry
    # in the case of a formatting for a finetuning step.
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

    # @huggingface: it still keeps other features :o
    return {"text": prompt}
