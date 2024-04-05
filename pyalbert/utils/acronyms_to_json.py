#!/bin/python
from pprint import pprint

if __name__ == "__main__":
    with open("_data/acronyms.txt") as f:
        lines = f.read().split("\n")

    out = []
    for line in lines:
        if not line:
            continue

        text, symbol = line.split("(")
        symbol = symbol.rstrip(")")
        out.append({"text": text.strip(), "symbol": symbol})

    out_file = "api/app/core/acronyms.py"

    with open(out_file, "w") as f:
        f.write("# DO NOT EDIT\n\nACRONYMS = ")
        pprint(out, stream=f, indent=2)
