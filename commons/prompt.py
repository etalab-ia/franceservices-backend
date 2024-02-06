import os
import re
from huggingface_hub import hf_hub_download
from jinja2 import Environment, FileSystemLoader, meta
import yaml

try:
    from app.config import VLLM_ROUTING_TABLE
    from app.core.acronyms import ACRONYMS
except ModuleNotFoundError:
    from api.app.config import VLLM_ROUTING_TABLE
    from api.app.core.acronyms import ACRONYMS


class Prompt:
    mode: str
    template: str
    variables: list[str]
    system_prompt: str | None
    prompt_format: str | None
    sampling_params: dict


def prompt_templates_from_vllm_routing_table(table: list[dict]) -> dict[str, Prompt]:
    templates = []
    for model in table:
        prompt_config_file = hf_hub_download(
            repo_id=model["model_id"], filename="prompt_config.yml"
        )
        with open(prompt_config_file) as f:
            config = yaml.safe_load(f)

        sampling_params = {}
        if "max_tokens" in config:
            sampling_params["max_tokens"] = config["max_tokens"]

        template = {}
        for prompt in config["prompts"]:
            template_file = hf_hub_download(repo_id=model["model_id"], filename=prompt["template"])
            env = Environment(loader=FileSystemLoader(os.path.dirname(template_file)))
            template = env.get_template(prompt["template"])
            template_ = template.environment.loader.get_source(template.environment, template.name)
            variables = meta.find_undeclared_variables(env.parse(template_[0]))
            template[prompt["mode"]] = {
                "mode": prompt["mode"],
                "system_prompt": prompt.get("systemctl"),
                "template": template,
                "variables": variables,
                "prompt_format": model.get("prompt_format"),
                "sampling_params": sampling_params,
            }

        templates[model["model_name"]] = template
    return templates



# Preload all acronyms to be faster
ACRONYMS_KEYS = [acronym["symbol"].lower() for acronym in ACRONYMS]

# Preload all prompt template to be faster
TEMPLATES = prompt_templates_from_vllm_routing_table(VLLM_ROUTING_TABLE)


class Prompter:
    # Default sampling params fo a given child class
    SAMPLING_PARAMS = {
        "temperature": 20,
    }

    def __init__(self, url: str, template: Prompt):
        # The prompt template
        self.template = template
        # Eventually stores the sources returned by the last RAG prompt built
        self.sources = None
        # vllm url
        self.url = url
        # The sampling params to pass to LLM generate function for inference.
        self.sampling_params = self.SAMPLING_PARAMS
        if "sampling_params" in template:
            self.sampling_params.update(template["sampling_params"])

    @classmethod
    def preprocess_prompt(cls, prompt: str) -> str:
        new_prompt = cls._expand_acronyms(prompt)
        return new_prompt

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

    def make_prompt(self, llama_chat=True, expand_acronyms=True, **kwargs):
        # @TODO: use self.template.get("prompt_format") instead of llama_chat !
        #
        if expand_acronyms and "query" in kwargs:
            kwargs["query"] = self.preprocess_prompt(kwargs["query"])

        # TODO: build variable depending on what in variables + kwargs !
        data = self.make_variables(self.template["variables"])
        data.update(kwargs)

        template = self.template["template"]
        rendered_template = template.render(**data)
        return rendered_template

    def make_variables(self, variables:list[str]):
        pass


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


def get_prompter(model_name: str, mode: str | None = None):
    model = next((m for m in VLLM_ROUTING_TABLE if m["model_name"] == model_name), None)
    if not model:
        raise ValueError("Prompter unknown: %s" % model_name)

    template = TEMPLATES["model_name"].get(mode)
    if not template:
        raise ValueError("Prompt mode unknown: %s (available: %s)" % (mode, list(TEMPLATES)))

    url = model["host"] + ":" + model["port"]
    return Prompter(url, template)
