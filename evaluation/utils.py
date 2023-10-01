import json

import requests


def get_embedding_e5(text: str) -> list:
    """OpenAI-like embedding API"""
    host = "localhost:8080"
    url = f"http://{host}/api/embedding"
    headers = {"Content-Type": "application/json"}
    query = {"text": text}
    res = requests.post(url, headers=headers, data=json.dumps(query), verify=False).json()
    return res


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
