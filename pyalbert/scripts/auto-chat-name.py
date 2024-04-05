#!/bin/python

import sys

sys.path.append(".")

from pyalbert.clients import LlmClient
from pyalbert.prompt import get_prompter

model = "AgentPublic/albert-light"
query = """
Une usagère ne comprend par le montant d’allocations sociales qu’elle touche ce mois-ci. En effet, le montant a été divisé par deux par rapport aux mois précédents et elle n’a plus que 150€. Elle cherche à comprendre pourquoi le montant a ainsi diminué.

Après avoir consulté le compte CAF de l’usagère avec son accord, il semble que la CAF opère une retenue sur le montant du RSA allouée à l’usagère suite à une déclaration erronée par le passé.

La CAF peut-elle faire une saisie sur le RSA et sous quelles conditions ? Comment débloquer la situation ?
"""

query = f"Synthétise la demande suivante en un court titre de quelque mots (pas plus de 8 mots) permettant d'identifier la thématique. Le titre doit être court, clair et accrocheur:\n\n{query}"


# Build prompt
prompter = get_prompter(model)
prompt = prompter.make_prompt(query=query)

# Generate
llm_client = LlmClient(model)
chat_name = llm_client.generate(prompt, temperature=20)
print(chat_name)
