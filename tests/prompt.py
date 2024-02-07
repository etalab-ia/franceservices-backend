#!/bin/python

import sys

sys.path.append(".")

from commons.prompt_base import Prompter

# from api.app.config import (ELASTICSEARCH_CREDS, ELASTICSEARCH_IX_VER,

if __name__ == "__main__":
    p = Prompter()

    prompt_tests = [
        "Nothing TO DO",
        "Quels sont les critères à remplir pour obtenir l'AAH ?",
        "Qu'est ce que la DITP et la DINUM ?",
    ]

    for prompt in prompt_tests:
        d = p._expand_acronyms(prompt)
        print(d)
        print()
