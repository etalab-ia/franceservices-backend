#!/bin/python

import sys

sys.path.append(".")

from commons import get_prompter, get_llm_client

model_name = "AgentPublic/albert-light"
query = """
Une usagère ne comprend par le montant d’allocations sociales qu’elle touche ce mois-ci. En effet, le montant a été divisé par deux par rapport aux mois précédents et elle n’a plus que 150€. Elle cherche à comprendre pourquoi le montant a ainsi diminué.

Après avoir consulté le compte CAF de l’usagère avec son accord, il semble que la CAF opère une retenue sur le montant du RSA allouée à l’usagère suite à une déclaration erronée par le passé.

La CAF peut-elle faire une saisie sur le RSA et sous quelles conditions ? Comment débloquer la situation ?
"""


# Build prompt
prompter = get_prompter(model_name)
prompt = prompter.make_prompt(query=query)

# Generate
llm_client = get_llm_client(model_name)
stream = llm_client.generate(prompt, temperature=20, stream=True)
for c in stream:
    print(c, end="", flush=True)
