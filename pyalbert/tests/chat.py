#!/bin/python

import sys

sys.path.append(".")

from pyalbert.clients import LlmClient
from pyalbert.prompt import get_prompter

model = "AgentPublic/albert-light"

################################################################################
### The Albert REPL chat
################################################################################
#
# Run me: python chat.py
#
# To integrate into pyalbert
################################################################################

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


with_history = True
mode = "rag"
limit = 7
history = []
llm_client = LlmClient(model)
debug_prompt = False
prompt_format = None
system_prompt = None

print(WELCOME)

while 1:
    # REPL
    if debug_prompt:
        query = input("(debug)>>> ")
    else:
        query = input(">>> ")
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
    stream = llm_client.generate(prompt, temperature=20, stream=True)
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
