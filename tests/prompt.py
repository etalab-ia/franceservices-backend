#!/bin/python

import sys
from pprint import pprint

sys.path.append(".")

from commons.prompt_base import Prompter

# from api.app.config import (ELASTICSEARCH_CREDS, ELASTICSEARCH_IX_VER,

if __name__ == "__main__":
    p = Prompter()

    prompt_test = "Quels sont les critères à remplir pour obtenir l'AAH ?"
    d = p._expand_acronyms(prompt_test)
    print(d)
