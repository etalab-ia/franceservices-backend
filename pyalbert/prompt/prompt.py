import os
import re
from functools import wraps
from typing import Any

from jinja2 import BaseLoader, Environment, Template, meta
from requests.exceptions import RequestException

from pyalbert.clients import AlbertClient
from pyalbert.config import LLM_TABLE
from pyalbert.lexicon import ACRONYMS


class PromptTemplate:
    mode: str
    template: Template
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


def prompt_encoder(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs) -> str | list[dict]:
        messages = func(self, *args, **kwargs)

        # Format messages
        # --
        # @FUTURE: Remove the default value at True when vllm.openai will be supported.
        do_encode_prompt = kwargs.get("do_encode_prompt", True)
        prompt_format = kwargs.get("prompt_format") or self.config.get("prompt_format")
        if do_encode_prompt and prompt_format and prompt_format != "openai":
            if prompt_format in ["llama-chat", "llama2-chat"]:
                chat_formatter = format_llama2chat_prompt
            elif prompt_format == "llama3-chat":
                chat_formatter = format_llama3chat_prompt
            elif prompt_format == "chatml":
                chat_formatter = format_chatml_prompt
            else:
                raise ValueError("Prompt format unkown: %s" % prompt_format)

            add_generation_prompt = kwargs.get("add_generation_prompt")
            encoded_prompt = chat_formatter(messages, add_generation_prompt=add_generation_prompt)
        elif do_encode_prompt and (not prompt_format or prompt_format != "openai"):
            raise ValueError("prompt_format is not defined to that template")
        else:
            encoded_prompt = messages

        return encoded_prompt

    return wrapper


def conversation_length_checker(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs) -> list[dict]:
        # Compress messages
        # default strategy is just a truncation
        messages = func(self, *args, **kwargs)

        head = []
        tail = messages
        if messages[0]["role"] == "system":
            head.append(tail.pop(0))

        # Cut history to fit the max_tokens model parameter
        words_len = sum([len(m["content"].split()) for m in (head + tail)])
        while len(tail) > 3 and words_len * 1.25 > self.sampling_params["max_tokens"] * 0.8:
            print("WARNING: conversation size overflow, reducing limit...")
            # Keep the same messages parity to avoid a confusion between a inference and a fine-tuning prompt
            [tail.pop(0) for _ in tail[:2] if tail]
            words_len = sum([len(m["content"].split()) for m in (head + tail)])

        compressed_messages = head + tail
        return compressed_messages

    return wrapper


def sources_length_checker(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs) -> list[dict]:
        messages = func(self, *args, **kwargs)
        if not self.template:
            # RAG is not activated
            return messages

        # Cut history to fit the max_tokens model parameter
        words_len = sum([len(m["content"].split()) for m in messages])
        limit = kwargs.get("limit") or 4
        while limit > 1 and words_len * 1.25 > self.sampling_params["max_tokens"] * 0.8:
            print("WARNING: RAG size overflow, reducing limit...")
            limit -= 1
            kwargs["limit"] = limit
            messages = func(self, *args, **kwargs)
            words_len = sum([len(m["content"].split()) for m in messages])

        return messages

    return wrapper


def prompts_from_llm_table(table: list[dict]) -> dict[str, PromptConfig]:
    sampling_params_supported = [
        "temperature",
        "max_tokens",
        "top_p",
        "top_k",
        "min_p",
        "presence_penalty",
        "length_penalty",
        "frequency_penalty",
        "repetition_penalty",
        "stop_token_ids",
    ]
    templates = {}
    client = AlbertClient()
    for model in table:
        model_name = model["model"]
        model_url = model["url"]
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

# Cache prompts templates to be faster
PROMPTS = {}


class Prompter:
    # Default sampling params fo a given child class
    SAMPLING_PARAMS = {
        "temperature": 0.2,
        "max_tokens": 4096,
    }

    def __init__(
        self,
        config: dict | None = None,
        template: PromptTemplate | str | None = None,
        api_key=None,
    ):
        self.api_key = api_key
        # The prompt config
        self.config = config or {}
        # The sampling params to pass to LLM generate function for inference.
        self.sampling_params = self.SAMPLING_PARAMS
        if "sampling_params" in self.config:
            self.sampling_params.update(self.config["sampling_params"])

        # Load or set the prompt template
        self.template = template
        if isinstance(template, str):
            if not os.path.exists(template):
                raise FileNotFoundError("Template not found: %s" % template)

            with open(template) as f:
                template_string = f.read()

            if template.endswith(".jinja"):
                env = Environment(loader=BaseLoader())
                t = env.from_string(template_string)
                variables = meta.find_undeclared_variables(env.parse(template_string))
                self.template = {
                    "template": t,
                    "variables": variables,
                    "default": config.get("default", {}),
                    "system_prompt": None,
                    "sampling_params": None,
                }
            else:
                raise ValueError("Template format unknown: %s" % template)

        # Eventually stores the sources returned by the last RAG prompt built
        self.sources = None

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

    @prompt_encoder
    @sources_length_checker
    @conversation_length_checker
    def make_prompt(
        self,
        expand_acronyms: bool = True,
        system_prompt: str | None = None,
        prompt_format: str | None = None,
        add_generation_prompt: bool = False,
        do_encode_prompt: bool = False,
        **kwargs,
    ) -> list[dict]:
        """Render simple to RAG prompt from template.

        Supported prompt_format
        ===
        - llama2-chat: see https://github.com/facebookresearch/llama
        - llama3-chat: see https://github.com/meta-llama/llama3
        - chatml: see huggingface and https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/chat-markup-language
        - openai: a list for {role, content}
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

        # Build template and render prompt with RAG variables if any
        if self.template:
            data = self.make_variables(kwargs, self.template["variables"], self.template["default"])
            prompt = self.template["template"].render(**data)
            system_prompt = kwargs.get("system_prompt") or self.template.get("system_prompt") or self.config.get("system_prompt")  # fmt: skip
        else:
            prompt = kwargs.get("query")
            system_prompt = kwargs.get("system_prompt") or self.config.get("system_prompt")

        messages = format_messages_prompt(prompt, system_prompt=system_prompt, history=history)
        return messages

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
        client = AlbertClient(api_key=self.api_key)

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


def format_messages_prompt(
    query: str, system_prompt: str | None = None, history: list[dict] | None = None
) -> list[dict]:
    messages = history or []

    # Do not overwrite used defined system prompt
    if system_prompt and not (messages and messages[0]["role"] == "system"):
        messages = [
            {
                "role": "system",
                "content": system_prompt,
            }
        ] + messages

    if history:
        if history[-1]["role"] == "user":
            # Inference case.
            # The query is rewritten as it can be augmented (RAG)
            messages[-1] = messages[-1].copy()
            messages[-1]["content"] = query
        elif (
            len(history) > 1
            and history[-1]["role"] == "assistant"
            and history[-2]["role"] == "user"
        ):
            # Training case.
            # query is rewritten as it can be augmented (RAG)
            # @DEBUG: enable the "continue" feature by allowing "assistant" the the last message
            messages[-2] = messages[-2].copy()
            messages[-2]["content"] = query
    else:
        messages.append({"role": "user", "content": query})

    return messages


# see https://github.com/facebookresearch/llama/blob/main/llama/generation.py#L284
# see also to implement this part in the driver management module of the llm API: https://gitlab.com/etalab-datalab/llm/albert-backend/-/issues/119
def format_llama2chat_prompt(
    messages: list[dict],
    add_generation_prompt: bool = False,
) -> str:
    # @DEBUG: this format inner system role and consecutive user or assistant message
    BOS, EOS = "<s>", "</s>"
    B_INST, E_INST = "[INST]", "[/INST]"
    B_SYS, E_SYS = "<<SYS>>\n", "\n<</SYS>>\n\n"

    if messages[0]["role"] == "system":
        messages = [
            {
                "role": messages[1]["role"],
                "content": B_SYS + messages[0]["content"] + E_SYS + messages[1]["content"],
            }
        ] + messages[2:]

    messages_list = [
        f"{BOS}{B_INST} {(prompt['content']).strip()} {E_INST} {(answer['content']).strip()} {EOS}"
        for prompt, answer in zip(messages[::2], messages[1::2])
    ]

    if not add_generation_prompt:
        messages_list.append(f"{BOS}{B_INST} {(messages[-1]['content']).strip()} {E_INST}")

    prompt = "".join(messages_list)
    return prompt


def format_llama3chat_prompt(
    messages: list[dict],
    add_generation_prompt: bool = False,
) -> str:
    BOS, EOS = "<|begin_of_text|>", "<|end_of_text|>"

    messages_list = [
        f"<|start_header_id|>{message['role']}<|end_header_id|>\n\n"
        + message["content"].strip()
        + "<|eot_id|>"
        for message in messages
    ]

    if add_generation_prompt:
        messages_list.append(EOS)
    else:
        messages_list[-1] += "<|start_header_id|>assistant<|end_header_id|>\n\n"

    messages_list = [BOS] + messages_list
    prompt = "".join(messages_list)
    return prompt


def format_chatml_prompt(
    messages: list[dict],
    add_generation_prompt: bool = False,
) -> str:
    messages_list = [
        f"<|im_start|>{message['role']}\n" + message["content"].strip() + "<|im_end|>\n"
        for message in messages
    ]

    if not add_generation_prompt:
        messages_list.append(
            f"<|im_start|>{messages[-1]['role']}\n"
            + messages[-1]["content"].strip()
            + "<|im_end|>\n"
        )

    if add_generation_prompt:
        # @DEBUG: There is no EOS for chatml ?
        pass
    else:
        messages_list[-1] += "<|im_start|>assistant\n"

    messages_list = messages_list
    prompt = "".join(messages_list)
    return prompt


def get_prompter(
    model_name: str, mode: str | None = None, prompt_format: str | None = None
) -> Prompter:
    model = next((m for m in LLM_TABLE if m["model"] == model_name), None)
    if not model:
        raise ValueError("LLM model not found in the LLM table: %s" % model_name)
    model_url = model["url"]

    global PROMPTS
    if model_name not in PROMPTS:
        # Try again to rebuild PROMPTS
        PROMPTS = prompts_from_llm_table(LLM_TABLE)

    if model_name not in PROMPTS:
        raise ValueError(
            "Failed to retrieve information for model: %s - LLM API (%s) might be down"
            % (model_name, model_url)
        )

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

    if prompt_format:
        # Overwrite prompt_format
        config["prompt_format"] = prompt_format

    return Prompter(config=config, template=template)
