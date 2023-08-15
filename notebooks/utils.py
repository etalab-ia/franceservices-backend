#!/bin/python

"""Json utils (Working with list of objects)

Usage:
    utils.py copy ANSWER_FOLDER CORPUS_FILE ATTR_NAME

Command:
    copy    Given an ANSWER_FOLDER containing answers (stored in {0,1,2...}.txt),
            it will add those answers in the CORPUS_FILE, under the attribute name ATTR_NAME.
            @DEBUG: {i}.txt should match the order in hte CORPUS_FILE
"""

import json
import os

from docopt import docopt

# Extract one field:
# !cat data.json | jq '.[] | {answer_xgen: .answer_xgen}'

# Remove one field:
# !cat data.json  | jq "map(del(.answer_xgen))"


def copy_answers_to(answer_folder, corpus_file, attr_name):
    with open(corpus_file, "r") as file1:
        data = json.load(file1)

    for i in range(len(data)):
        with open(f"{answer_folder}/{i}.txt") as fn:
            text = fn.read()

        data[i][attr_name] = text.strip()

    with open(corpus_file, "w") as output:
        json.dump(data, output, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    args = docopt(__doc__)

    if args["copy"]:
        copy_answers_to(args["ANSWER_FOLDER"], args["CORPUS_FILE"], args["ATTR_NAME"])
    else:
        raise NotImplementedError
