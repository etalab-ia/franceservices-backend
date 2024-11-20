from copy import deepcopy
from functools import wraps
from pathlib import Path
from typing import Any, Optional

import yaml
from huggingface_hub import hf_hub_download
from huggingface_hub.utils._errors import EntryNotFoundError, RepositoryNotFoundError
from jinja2 import BaseLoader, Environment, Template, meta
from pydantic import BaseModel

from pyalbert import get_logger
from pyalbert.clients import SearchEngineClient
from pyalbert.config import DO_ENCODE_PROMPT, HF_TOKEN, LLM_TABLE
from pyalbert.lexicon import expand_acronyms

logger = get_logger()


def fetch_hf_file(
    hf_repo_id: str, filename: str, fail_if_notfound=False, local=False
) -> str | None:
    """Fetch a HF or local file"""
    if local:
        return filename

    file_path = None
    try:
        file_path = hf_hub_download(
            repo_id=hf_repo_id,
            filename=filename,
            # local_dir=args.model,
            # cache_dir=args.model,
            token=HF_TOKEN,
        )
    except EntryNotFoundError as err:
        if fail_if_notfound:
            raise err
        else:
            logger.warning(f"File {filename} not found in Hugginface repository {hf_repo_id}.")
    except RepositoryNotFoundError as err:
        if fail_if_notfound:
            raise err
        else:
            logger.warning(f"Hugginface repository {hf_repo_id} not found.")

    return file_path


def fetch_hf_prompt_config(hf_repo_id: str, config_filename: str, local=False) -> dict | None:
    """Return the parsed prompt_config yaml from huggingfacen repo if the file is found in the repo
    else, returns a empty dict. If local is True read local file instead.
    Return any linked template as string.
    """
    config = None
    config_file_path = fetch_hf_file(hf_repo_id, config_filename, local=local)
    if not config_file_path:
        return config

    with open(config_file_path) as file:
        config = yaml.safe_load(file)

    # open the prompt templates
    for i, prompt in enumerate(config.get("prompts", [])):
        if not prompt.get("template"):
            continue
        template_filename = prompt["template"]
        if local:
            template_filename = Path(config_filename).resolve().parent / template_filename

        template_path = fetch_hf_file(hf_repo_id, template_filename, local=local)
        if template_path is None:
            raise ValueError(f"{template_path} not found in remote model repository.")

        with open(template_path) as file:
            config["prompts"][i]["template_string"] = file.read()

    return config


class SamplingParams(BaseModel):
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    min_p: Optional[float] = None
    presence_penalty: Optional[float] = None
    length_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    repetition_penalty: Optional[float] = None
    stop_token_ids: Optional[list[int]] = None


class GlobalConfig(SamplingParams):
    system_prompt: str | None = None


class PromptTemplate(SamplingParams):
    mode: str
    template: str | None = None
    template_string: str | None = None
    variables: list[str] | None = None
    default: dict | None = None
    # Overwrite the default config
    system_prompt: str | None = None


class ModelConfig(SamplingParams):
    model_kind: str
    prompt_format: str | None = None


class PromptConfig(BaseModel):
    # The sampling params precedence from higher to lower is
    # 1) models,  2) prompts, 3) global_config.
    # Remark: the precedence of models is actually implemented in get_prompter, not in set_defaults
    # ---
    # Global prompt config
    global_config: GlobalConfig
    # Specific model configuration
    models: list[ModelConfig] | None = None
    # Specific prompt config (called "mode"), with optional template.
    prompts: list[PromptTemplate] | None = None

    @staticmethod
    def parse_config(config):
        return {
            "global_config": config,
            "prompts": config.pop("prompts", []),
            "models": config.pop("models", []),
        }

    @classmethod
    def from_hf(cls, hf_repo_id):
        config_files = ["prompt_config.yml", "prompt_config.yaml"]
        for config_filename in config_files:
            config = fetch_hf_prompt_config(hf_repo_id, config_filename)
            if config:
                config = cls.parse_config(config)
                break

        if not config:
            logger.info(f"prompt_config configuration not found for repo {hf_repo_id}")
            config = {"global_config": {}}

        return cls(**config, exclude_unset=True)

    @classmethod
    def from_file(cls, config_filename):
        config = fetch_hf_prompt_config("file://", config_filename, local=True)
        config = cls.parse_config(config)
        return cls(**config)

    def set_defaults(self) -> dict:
        """Set default params and variables values for this prompt configuration.
        Sampling params are moved into a 'sampling_params' attribute for clarity.
        Additionally, parse the template and prerender jinja Template.
        """
        config = self.model_dump(exclude_unset=True)
        global_config = config["global_config"]
        prompts = config.get("prompts") or []

        # Default prompt system
        system_prompt = global_config.get("system_prompt")

        # Extract default sampling parameters
        sampling_params = {
            k: global_config.pop(k) for k in list(global_config) if k in SamplingParams.model_fields
        }
        global_config["sampling_params"] = sampling_params

        # Extract model sampling params
        if config.get("models"):
            for model in config["models"]:
                model_sampling_params = {
                    k: model.pop(k) for k in list(model) if k in SamplingParams.model_fields
                }
                model["sampling_params"] = model_sampling_params

        # Parse templates
        for prompt in prompts:
            # Overwrite system prompt
            mode_system_prompt = prompt.get("system_prompt", system_prompt)
            prompt["system_prompt"] = mode_system_prompt
            # Extract and overwrite sampling params
            mode_sampling_params = deepcopy(sampling_params)
            mode_sampling_params.update(
                {k: prompt.pop(k) for k in list(prompt) if k in SamplingParams.model_fields}
            )
            prompt["sampling_params"] = mode_sampling_params

            # Template from file template
            if not prompt.get("template_string"):
                continue
            template_string = prompt["template_string"]
            env = Environment(loader=BaseLoader())
            variables = meta.find_undeclared_variables(env.parse(template_string))
            prompt["_template"] = env.from_string(template_string)
            prompt["variables"] = list(variables)

        # Convert the list of template to a dict with mode as key.
        config["prompts"] = {d["mode"]: d for d in prompts}
        return config


def prompt_encoder(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs) -> str | list[dict]:
        messages = func(self, *args, **kwargs)

        # Format messages
        # --
        do_encode_prompt = kwargs.get("do_encode_prompt") or self.config.get("do_encode_prompt")
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


def prompts_from_llm_table(table: list[dict]) -> dict[str, dict]:
    """Returns a dict of prompt configs per model with precomputed templates"""
    templates = {}
    for model in table:
        pconfig = {"model": model["model"], "type": model["type"]}
        if model["type"] in ["text-generation"]:
            # @old: we used to fetch the template from huggingface model directly.
            # pconfig.update(PromptConfig.from_hf(model["model"]).set_defaults())

            prompt_config_file = Path(__file__).resolve().parent / "templates" / "prompt_config.yml"
            pconfig.update(PromptConfig.from_file(prompt_config_file).set_defaults())

        templates[model["model"]] = pconfig

    return templates


# Cache prompts templates to be faster
PROMPTS = {}


class Prompter:
    # Default sampling params fo a given child class
    SAMPLING_PARAMS = {
        "temperature": 0.3,
        "max_tokens": 4096,
    }

    def __init__(
        self,
        config: dict | None = None,
        template: PromptTemplate | str | None = None,
    ):
        # The prompt config
        self.config = config or {}
        # The sampling params to pass to LLM generate function for inference.
        self.sampling_params = self.SAMPLING_PARAMS
        if "sampling_params" in self.config:
            self.sampling_params.update(self.config["sampling_params"])

        if "do_encode_prompt" not in self.config:
            self.config["do_encode_prompt"] = DO_ENCODE_PROMPT

        # Load or set the prompt template
        self.template = None
        if isinstance(template, str):
            if not Path(template).exists():
                raise FileNotFoundError("Template not found: %s" % template)

            with open(template) as f:
                template_string = f.read()

            if template.endswith(".jinja"):
                env = Environment(loader=BaseLoader())
                t = env.from_string(template_string)
                variables = meta.find_undeclared_variables(env.parse(template_string))
                self.template = {
                    "template": template,
                    "template_string": template_string,
                    "_template": t,
                    "variables": list(variables),
                    "default": config.get("default"),
                    "system_prompt": None,
                    "sampling_params": None,
                }
            else:
                raise ValueError("Template format unknown: %s" % template)
        elif isinstance(template, dict):
            self.template = template
        elif template is not None:
            raise ValueError("Template format unknown: %s" % type(template))

        if self.template:
            self.template["default"] = self.template.get("default") or {}

        # Eventually stores the sources returned by the last RAG prompt built
        self.sources = None

    @prompt_encoder
    @sources_length_checker
    @conversation_length_checker
    def make_prompt(
        self,
        system_prompt: str | None = None,
        prompt_format: str | None = None,
        add_generation_prompt: bool = False,
        do_expand_acronyms: bool = True,
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

        history = kwargs.get("history")
        if not kwargs.get("query"):
            if not history:
                raise ValueError("Either history or query must be set")
            kwargs["query"] = history[-1]["content"]

        if do_expand_acronyms and "query" in kwargs:
            kwargs["query"] = expand_acronyms(kwargs["query"])

        # Set search query
        kwargs["seach_query"] = kwargs["query"]
        if history:
            history = history.copy()
            # Use the three last user prompt to build the search query (embedding)
            kwargs["search_query"] = "; ".join(
                [x["content"] for i, x in enumerate(history) if x["role"] == "user"][-3:]
            )

        # Build template and render prompt with RAG variables if any
        if self.template:
            data = self.make_variables(
                passed_data=kwargs,
                variables=self.template["variables"],
                default=self.template["default"],
            )
            prompt = self.template["_template"].render(**data)
            print("prompt", prompt)
            system_prompt = kwargs.get("system_prompt") or self.template.get("system_prompt") or self.config.get("system_prompt")  # fmt: skip
        else:
            prompt = kwargs["query"]
            system_prompt = kwargs.get("system_prompt") or self.config.get("system_prompt")

        messages = format_messages_prompt(
            prompt, system_prompt=system_prompt, history=history, model=self.config.get("model")
        )
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
        query: str        # collection query search.
        search_query: str # overwrite {query} if given.
        limit: int        # max number in colection search.
        skip_first: int   # skip the first result in collection search.
        {index-name}_collection: list[dict]
        {var}: str        # anything else in passed_data.
        """
        data = passed_data.copy()
        for k, v in default.items():
            if not data.get(k):
                data[k] = v

        search_query = data.get("search_query", data["query"])
        se_client = SearchEngineClient()

        # List of collections search variables asked in the template.
        collection_matches = [v for v in variables if v.endswith("_collection")]
        for v in collection_matches:
            collection_name = "_".join(v.split("_")[:-1])
            if collection_name.startswith("spp_"):
                id_key = "id_experience"
            elif collection_name == "chunks":
                id_key = "hash"
            else:
                raise ValueError("chunks identifier (%s) unknown in prompt template." % v)

            limit = data.get("limit") or 3
            skip_first = data.get("skip_first")
            if skip_first:
                limit += 1
            hits = se_client.search(
                collection_name,
                search_query,
                limit=limit,
                filters=dict(
                    institution=data.get("institution"),
                    sources=data.get("sources"),
                    should_sids=data.get("should_sids"),
                    must_not_sids=data.get("must_not_sids"),
                ),
            )
            if skip_first:
                hits = hits[1:]
            self.sources = [x[id_key] for x in hits]
            data[v] = hits

        return data

    def get_upstream_sampling_params(self):
        sampling_params = self.sampling_params.copy()
        # Remove sampling_params as it will cause the completion to fail if max_tokens is set to the
        # maximum context length.
        sampling_params.pop("max_tokens")
        return sampling_params


def format_messages_prompt(
    query: str, system_prompt: str | None = None, history: list[dict] | None = None, model=None
) -> list[dict]:
    messages = (history or []).copy()

    # Do not overwrite user defined system prompt
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

    if model:
        messages = messages_compatibility(model, messages)

    return messages


def messages_compatibility(model: str, messages: list, msg_separator="\n\n---\n\n") -> list:
    """Return an updated version of messages that make it compatible with certain model limitations"""
    messages = messages.copy()
    has_system_msg = False
    if messages[0]["role"] == "system":
        has_system_msg = True

    # Some model does only support alternate user/assistant messages
    # -> Merge two consecutive identical role messages.
    indices = [
        i for i in range(len(messages) - 1) if (messages[i]["role"] == messages[i + 1]["role"])
    ]
    for i in reversed(indices):
        next_message = messages.pop(i + 1)
        messages[i]["content"] += msg_separator + next_message["content"]

    # -> some model does not support when first message is from assistant
    if (has_system_msg and len(messages) > 1 and messages[1]["role"] == "assistant") or (
        messages[0]["role"] == "assistant"
    ):
        empty_user_msg = {"role": "user", "content": ""}
        if has_system_msg:
            messages.insert(1, empty_user_msg)
        else:
            messages.insert(0, empty_user_msg)

    # Merge system prompt into the first user message.
    model_name = model.split("/")[-1]
    if model_name.startswith("gemma") and has_system_msg:
        system = messages.pop(0)
        index = next((i for i, d in enumerate(messages) if d["role"] == "user"), None)
        if index is not None:
            item = messages[index].copy()
            item["content"] = msg_separator.join([system["content"], item["content"]])
            messages[index] = item

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
    """Return a Prompter class by building the configuration automatically given a model name
    from the LLM table en the yaml prompt config."""

    model = next((m for m in LLM_TABLE if m["model"] == model_name), None)
    if not model:
        raise ValueError("LLM model not found: %s" % model_name)
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
    config = deepcopy(prompt_config["global_config"])
    config.update({k: prompt_config[k] for k in ["model", "type"]})
    template = None

    # Model specific configuration if any
    model_ = model_name.split("/")[-1]
    model_config = next(
        (d for d in prompt_config.get("models", []) if model_.startswith(d["model_kind"])), None
    )

    # Find template according to mode
    templates = prompt_config.get("prompts", {})
    if templates.get(mode):
        template = templates[mode]

        # Overwrite sampling_params
        if "sampling_params" in template:
            config["sampling_params"].update(template["sampling_params"])
        if model_config and model_config.get("sampling_params"):
            config["sampling_params"].update(model_config["sampling_params"])

        # Overwrite prompt_format
        if "prompt_format" in template:
            config["prompt_format"] = template["prompt_format"]

    if mode and not template:
        raise ValueError(
            "Prompt mode unknown: %s (available: %s)"
            % (mode, list(prompt_config.get("prompts", {})))
        )

    if prompt_format:
        # Overwrite prompt_format
        config["prompt_format"] = prompt_format

    return Prompter(config=config, template=template)
