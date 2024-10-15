import re

from .acronyms import ACRONYMS
from .institutions import INSTITUTIONS

# Preload all acronyms to be faster
ACRONYMS_KEYS = [acronym["symbol"].lower() for acronym in ACRONYMS]

def expand_acronyms(prompt: str) -> str:
    # Match potential acronyms
    # --
    # Terms that start by a number or maj, that contains at least 3 character, and that can be
    # preceded by a space, but not if the first non-space character encountered backwards is a dot.
    pattern = r"(?<!\S\. )[A-Z0-9][A-Za-z0-9]{2,}\b"
    matches = [
        (match.group(), match.start(), match.end()) for match in re.finditer(pattern, prompt)
    ]

    # Prevent extreme case (caps lock, list of items, etc)
    if len(matches) > 10:
        return prompt

    # Expand acronyms
    for match, start, end in matches[::-1]:
        try:
            i = ACRONYMS_KEYS.index(match.lower())
        except ValueError:
            continue

        acronym = ACRONYMS[i]
        look_around = 100
        text_span = (
            prompt[max(0, start - look_around) : start] + " " + prompt[end : end + look_around]
        )
        if acronym["text"].lower() not in text_span.lower():
            # I suppose we go here most of the time...
            # but I also suppose the test should be fast enough to be negligible.
            expanded = " (" + acronym["text"] + ")"
            prompt = prompt[:end] + expanded + prompt[end:]

    return prompt
