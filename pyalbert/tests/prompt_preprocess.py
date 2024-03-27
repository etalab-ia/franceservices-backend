#!/bin/python

import sys

sys.path.append(".")

from pyalbert.prompt import Prompter


if __name__ == "__main__":
    p = Prompter("n/a")  # no model is used here

    prompt_tests = [
        "Nothing TO DO",
        "Quels sont les critères à remplir pour obtenir l'AAH ?",
        "Qu'est ce que la DITP et la DINUM ?",
    ]

    for prompt in prompt_tests:
        d = p._expand_acronyms(prompt)
        print(d)
        print()
