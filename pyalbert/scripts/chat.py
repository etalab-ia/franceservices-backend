#!/bin/python

import sys

sys.path.append(".")

from prompt_toolkit import PromptSession

from pyalbert import set_llm_table
from pyalbert.clients import LlmClient
from pyalbert.prompt import get_prompter

################################################################################
### The Albert REPL chat
################################################################################
#
# Run me: python chat.py
#
# To integrate into pyalbert
#
# @TODO: use ALBERT_API_TOKEN if available
# @TODO: .model {model} to change model (autocompletion...)
################################################################################

# Custom LLM_TABLE
set_llm_table(
    [
        ("AgentPublic/albertlight-7b", "http://localhost:8082"),
        ("AgentPublic/albertlight-8b", "http://localhost:8088"),
    ]
)
default_model = "AgentPublic/albertlight-8b"

WELCOME = """Welcome to Albert chat
type ".help" for more information.
"""

HELP = {
    ".mode": 'Change the mode (e.g ".mode rag", ".mode analysis"). Enter ".mode" to unset it.',
    ".format": 'Change the format of the prompt (e.g ".format chatml", ".format llama-chat"). Enter ".format" to unset it.',
    ".system": 'Change the system prompt. Enter ".system" to unset it.',
    ".limit": 'Change the limit of the RAG reference. Enter ".limit" to unset it.',
    ".clear": "Clear the chat history",
    ".debug": "Toggle debug mode: It will print the current prompt instead of generating.",
}


model = default_model
with_history = True
mode = "rag"
limit = 7
history = []
llm_client = LlmClient(model)
debug_prompt = False
prompt_format = None
system_prompt = None

print(WELCOME)


def custom_input(prompt, multiline_pattern=":::"):
    session = PromptSession()
    # Check if the input should be multiline
    initial_input = session.prompt(prompt)
    if initial_input.startswith(multiline_pattern):
        # Enter multiline mode
        lines = [
            initial_input[len(multiline_pattern) :]
        ]  # Start with the first line's content after the pattern
        while True:
            line = session.prompt("")
            if line.strip() == multiline_pattern:
                break
            lines.append(line)
        return "\n".join(lines)
    else:
        # Single line mode
        return initial_input


while True:
    # REPL
    if debug_prompt:
        query = custom_input("(debug)>>> ")
    else:
        query = custom_input(">>> ")
    query = query.strip()

    if query == ".clear":
        history = []
        continue
    elif query.startswith(".mode"):
        s = query.split()
        mode = s[1] if len(s) > 1 else None
        continue
    elif query.startswith(".limit"):
        s = query.split()
        limit = int(s[1]) if len(s) > 1 else None
        continue
    elif query.startswith(".debug"):
        debug_prompt = not debug_prompt
        continue
    elif query.startswith(".format"):
        s = query.split()
        prompt_format = s[1] if len(s) > 1 else None
        continue
    elif query.startswith(".system"):
        s = query.split()
        system_prompt = " ".join(s[1:]) if len(s) > 1 else None
        continue
    elif query.strip() == ".help":
        max_length = max(len(c) for c in HELP)
        for command, description in HELP.items():
            print(f"{command:<{max_length*3}} {description}")
        print()
        continue

    # Make prompt replace the last user query by the prompt provided
    # @DEBUG: this logic is due to the create/start stream double call...to fix!
    history.append({"role": "user", "content": query})

    # Build prompt
    prompter = get_prompter(model, mode)
    prompt = prompter.make_prompt(
        query=query,
        limit=limit,
        history=history,
        prompt_format=prompt_format,
        system_prompt=system_prompt,
    )

    if debug_prompt:
        print(prompt)
        history.pop()
        continue

    # Generate
    sampling_params = prompter.sampling_params
    stream = llm_client.generate(prompt, stream=True, **sampling_params)
    raw_response = ""
    for c in stream:
        print(c, end="", flush=True)
        raw_response += c

    history.extend(
        [
            {"role": "assistant", "content": raw_response},
        ]
    )

    print()
