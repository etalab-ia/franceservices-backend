import json

import requests


def generate(url, conf, text):
    """OpenAI-like completion API"""
    headers = {"Content-Type": "application/json"}
    c = conf.copy()
    c["prompt"] = text
    response = requests.post(url + "/generate", json=c, stream=True, verify=False)
    res = b""
    for r in response:
        res += r
    ans = json.loads(res.decode("utf-8"))
    ans = ans["text"][0]
    return ans
