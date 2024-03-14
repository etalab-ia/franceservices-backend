import re
from typing import Any

from jinja2 import BaseLoader, Environment, meta
from requests.exceptions import RequestException

from commons.api import get_albert_client

try:
    from app.config import LLM_TABLE
    from app.core.acronyms import ACRONYMS
except ModuleNotFoundError:
    from api.app.config import LLM_TABLE
    from api.app.core.acronyms import ACRONYMS


class PromptTemplate:
    mode: str
    template: str
    variables: set[str]
    default: dict
    # Overwrite the default config
    system_prompt: str | None
    sampling_params: dict


class PromptConfig:
    # Global prompt config
    config: dict
    # The key is the prompt **mode**
    templates: dict[str, PromptTemplate] | None


def prompts_from_llm_table(table: list[tuple]) -> dict[str, PromptConfig]:
    sampling_params_supported = [
        "temperature",
        "max_tokens",
        "top_p",
        "top_k",
        "presence_penalty",
    ]
    templates = {}
    client = get_albert_client()
    for model_name, model_url in table:
        try:
            config = client.get_prompt_config(model_url)
        except RequestException as err:
            print(f"Error: Failed to fetch templates file for url {model_url} ({err}), passing...")
            continue

        # Default prompt system
        system_prompt = config.get("system_prompt")

        # Default sampling paramerters
        sampling_params = {}
        for param in sampling_params_supported:
            if param in config:
                sampling_params[param] = config[param]
        config["sampling_params"] = sampling_params

        # Parse templates
        prompt_templates = {}
        for prompt in config.get("prompts", []):
            # Overwrite system prompt
            mode_system_prompt = prompt.get("system_prompt", system_prompt)
            # Overwrite sampling params
            mode_sampling_params = sampling_params.copy()
            for param in sampling_params_supported:
                if param in prompt:
                    mode_sampling_params[param] = prompt[param]

            # Template from file template
            # --
            # template_file = hf_hub_download(repo_id=model["hf_repo_id"], filename=prompt["template"])
            # env = Environment(loader=FileSystemLoader(os.path.dirname(template_file)))
            # template = env.get_template(prompt["template"])
            # template_ = template.environment.loader.get_source(template.environment, template.name)
            # Template from string template
            template_string = prompt["template"]
            env = Environment(loader=BaseLoader())
            template = env.from_string(template_string)
            variables = meta.find_undeclared_variables(env.parse(template_string))
            prompt_templates[prompt["mode"]] = {
                "mode": prompt["mode"],
                "template": template,
                "variables": variables,
                "default": prompt.get("default", {}),
                "system_prompt": mode_system_prompt,
                "sampling_params": mode_sampling_params,
            }

        templates[model_name] = {"config": config, "templates": prompt_templates}
    return templates


# Preload all acronyms to be faster
ACRONYMS_KEYS = [acronym["symbol"].lower() for acronym in ACRONYMS]

# Preload all prompt template to be faster
PROMPTS = prompts_from_llm_table(LLM_TABLE)


class Prompter:
    # Default sampling params fo a given child class
    SAMPLING_PARAMS = {
        "temperature": 20,
        "max_tokens": 4096,
    }

    def __init__(
        self,
        url: str,
        config=dict | None,
        template: PromptTemplate | None = None,
    ):
        # The prompt template
        self.config = config
        self.template = template
        # Eventually stores the sources returned by the last RAG prompt built
        self.sources = None
        # vllm url
        self.url = url
        # The sampling params to pass to LLM generate function for inference.
        self.sampling_params = self.SAMPLING_PARAMS
        if "sampling_params" in config:
            self.sampling_params.update(config["sampling_params"])

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
            if acronym["text"].lower() not in text_span.lower():
                # I suppose we go here most of the time...
                # but I also suppose the test should be fast enough to be negligible.
                expanded = " (" + acronym["text"] + ")"
                prompt = prompt[:end] + expanded + prompt[end:]

        return prompt

    def make_prompt(self, system_prompt=None, prompt_format=None, expand_acronyms=True, **kwargs):
        """Render simple to RAG prompt from template.

        Supported prompt_format
        ===
        - llama-chat : see https://github.com/facebookresearch/llama
        - null : force no chat template (to avoid conflict with the prompt_format template config)
        """
        if expand_acronyms and "query" in kwargs:
            kwargs["query"] = self.preprocess_prompt(kwargs["query"])

        # Set search query
        kwargs["seach_query"] = kwargs.get("query")
        history = kwargs.get("history")
        if history:
            history = history.copy()
            # Use the three last user prompt to build the search query (embedding)
            kwargs["search_query"] = "; ".join(
                [x["content"] for i, x in enumerate(history) if x["role"] == "user"][-3:]
            )

        # Set default prompt_format
        prompt_format = prompt_format or self.config.get("prompt_format")

        # Build template and render prompt with variables if any
        if self.template:
            data = self.make_variables(kwargs, self.template["variables"], self.template["default"])
            prompt = self.template["template"].render(**data)
            system_prompt = system_prompt or self.template.get("system_prompt") or self.config.get("system_prompt")  # fmt: skip
        else:
            prompt = kwargs.get("query")
            system_prompt = system_prompt or self.config.get("system_prompt")

        # Format prompt
        # --
        if prompt_format:
            if prompt_format == "llama-chat":
                chat_formatter = format_llama2chat_prompt
            elif prompt_format == "chatml":
                chat_formatter = format_chatml_prompt
            else:
                raise ValueError("Prompt format unkown: %s" % prompt_format)

            raw_prompt = chat_formatter(prompt, system_prompt=system_prompt, history=history)[
                "text"
            ]

            # Cut history to fit the max_tokens model para
            while (
                history
                and len(raw_prompt.split()) * 1.25 > self.sampling_params["max_tokens"] * 0.8
            ):
                # Keep the same history parity to avoid a confusion between a inference and a fine-tuning prompt
                [history.pop(0) for _ in history[:2] if history]
                raw_prompt = chat_formatter(prompt, system_prompt=system_prompt, history=history)[
                    "text"
                ]
        else:
            raw_prompt = prompt

        return raw_prompt

    def make_variables(
        self, passed_data: dict[str, Any], variables: list[str], default: dict[str, Any]
    ) -> dict[str, Any]:
        """This method will compute the variables corresponding to the names passed in arguments.
        These variable should be documented as available to devellop prompt template for albert.

        Arguments
        ===
        variables: The list of variables used in the jinja templatess
        passed_data: Potential given values for variables
        default: Potential default value for variables or meta variable (e.g {limit})

        Available Variables in Prompt Templates
        ===
        query: str        # passed in the query
        search_query: str # passed in the query
        context: str      # passed in the query
        links: str        # passed in the query
        institution: str  # passed in the query
        most_similar_experience: str
        experience_chunks: list[dict]
        sheet_chunks: list[dict]
        """
        data = passed_data.copy()
        for k, v in default.items():
            if not data.get(k):
                data[k] = v

        search_query = data.get("search_query", data.get("query"))
        client = get_albert_client()

        # Extract one similar value in a collection from query
        if "most_similar_experience" in variables:
            # Using LLM
            # rep1 = llm_client.generate(prompt, stream=False,  max_tokens=500, **FabriquePrompter.SAMPLING_PARAMS)
            # rep1 = "".join(rep1)
            # Using similar experience
            skip_first = data.get("skip_first")
            n_exp = 1
            if skip_first:
                n_exp = 2
            hits = client.search(
                "experiences",
                search_query,
                limit=n_exp,
                similarity="e5",
                institution=data.get("institution"),
            )
            if skip_first:
                hits = hits[1:]
            data["most_similar_experience"] = hits[0]["description"]

        # List of semantic similar value from query
        chunks_allowed = ["experience_chunks", "sheet_chunks"]
        chunks_matches = [v for v in variables if v.endswith("_chunks") and v in chunks_allowed]
        for v in chunks_matches:
            if v.split("_")[0] == "experience":
                collection_name = "experience"
                id_key = "id_experience"
            elif v.split("_")[0] == "sheet":
                collection_name = "chunks"
                id_key = "hash"
            else:
                raise ValueError("chunks identifier (%s) unknown in prompt template." % v)

            limit = data.get("limit") or 3
            skip_first = data.get("skip_first")
            if skip_first:
                limit += 1
            hits = client.search(
                collection_name,
                search_query,
                institution=data.get("institution"),
                limit=limit,
                similarity="e5",
                sources=data.get("sources"),
                should_sids=data.get("should_sids"),
                must_not_sids=data.get("must_not_sids"),
            )
            if skip_first:
                hits = hits[1:]
            self.sources = [x[id_key] for x in hits]
            data[v] = hits

        return data


# see https://github.com/facebookresearch/llama/blob/main/llama/generation.py#L284
# see also to implement this part in the driver management module of the llm API: https://gitlab.com/etalab-datalab/llm/albert-backend/-/issues/119
def format_llama2chat_prompt(
    query: str, system_prompt: str | None = None, history: list[dict] | None = None
) -> dict:
    messages = history or []
    if history:
        if history[-1]["role"] == "user":
            messages[-1] = messages[-1].copy()
            messages[-1]["content"] = query
        elif (
            len(history) > 1
            and history[-1]["role"] == "assistant"
            and history[-2]["role"] == "user"
        ):
            messages[-2] = messages[-2].copy()
            messages[-2]["content"] = query
    else:
        messages = [{"role": "user", "content": query}]

    BOS, EOS = "<s>", "</s>"
    B_INST, E_INST = "[INST]", "[/INST]"
    B_SYS, E_SYS = "<<SYS>>\n", "\n<</SYS>>\n\n"

    if system_prompt:
        messages = [
            {
                "role": messages[0]["role"],
                "content": B_SYS + system_prompt + E_SYS + messages[0]["content"],
            }
        ] + messages[1:]

    messages_list = [
        f"{BOS}{B_INST} {(prompt['content']).strip()} {E_INST} {(answer['content']).strip()} {EOS}"
        for prompt, answer in zip(messages[::2], messages[1::2])
    ]

    if len(messages) % 2 != 0:
        messages_list.append(f"{BOS}{B_INST} {(messages[-1]['content']).strip()} {E_INST}")

    prompt = "".join(messages_list)

    # @huggingface: it still keeps other features :o
    return {"text": prompt}


def format_chatml_prompt(
    query: str, system_prompt: str | None = None, history: list[dict] | None = None
) -> dict:
    messages = history or []
    if history:
        if history[-1]["role"] == "user":
            messages[-1] = messages[-1].copy()
            messages[-1]["content"] = query
        elif (
            len(history) > 1
            and history[-1]["role"] == "assistant"
            and history[-2]["role"] == "user"
        ):
            messages[-2] = messages[-2].copy()
            messages[-2]["content"] = query
    else:
        messages = [{"role": "user", "content": query}]

    sysprompt = ""
    if system_prompt:
        sysprompt = "<|im_start|>system\n" + system_prompt + "<|im_end|>\n"

    first_even = len(messages) if len(messages) % 2 == 0 else len(messages) - 1
    messages_list = [
        f"<|im_start|>{message['role']}\n" + message["content"].strip() + "<|im_end|>\n"
        for message in messages[:first_even]
    ]

    if len(messages) % 2 != 0:
        messages_list.append(
            f"<|im_start|>{messages[-1]['role']}\n"
            + messages[-1]["content"].strip()
            + "<|im_end|>\n"
            + "<|im_start|>assistant\n"
        )

    messages_list = [sysprompt] + messages_list
    prompt = "".join(messages_list)

    # @huggingface: it still keeps other features :o
    return {"text": prompt}


def get_prompter(model_name: str, mode: str | None = None) -> Prompter:
    model = next((m for m in LLM_TABLE if m[0] == model_name), None)
    if not model:
        raise ValueError("LLM model not found: %s" % model_name)

    model_url = model[1]
    global PROMPTS
    if model_name not in PROMPTS:
        # Try again to rebuild PROMPTS
        PROMPTS = prompts_from_llm_table(LLM_TABLE)

    prompt_config = PROMPTS[model_name]
    config = prompt_config["config"]
    template = None

    # Find template according to mode
    templates = prompt_config.get("templates", {})
    if templates.get(mode):
        template = templates[mode]
        if "sampling_params" in template:
            config["sampling_params"].update(template["sampling_params"])
        if "prompt_format" in template:
            config["prompt_format"] = template["prompt_format"]

    if mode and not template:
        raise ValueError(
            "Prompt mode unknown: %s (available: %s)"
            % (mode, list(prompt_config.get("templates", {})))
        )

    return Prompter(model_url, config=config, template=template)
