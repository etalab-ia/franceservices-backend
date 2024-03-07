#!/bin/python

import sys

sys.path.append(".")

from commons import get_prompter, get_llm_client

model_name = "AgentPublic/albert-light"

################################################################################
### The Albert REPL chat
################################################################################
#
# Run me: python chat.py
#
# To integrate into pyalbert
################################################################################

with_history = True
mode = "rag"
limit = 7
history = []
llm_client = get_llm_client(model_name)
debug_prompt = False
prompt_format = None
system_prompt = None

while 1:
    # REPL
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

    # Make prompt replace the last user query by the prompt provided
    # @DEBUG: this logic is due to the create/start stream double call...to fix!
    history.append({"role": "user", "content": query})

    # Build prompt
    prompter = get_prompter(model_name, mode)
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
