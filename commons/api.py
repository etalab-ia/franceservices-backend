import json

import requests


def get_embedding_e5(text: str) -> list:
    """OpenAI-like embedding API"""
    # host = "localhost:8080"
    host = "142.44.40.218"
    url = f"http://{host}/api/v2/embeddings"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2OTczNzM1NjUsImlhdCI6MTY5NzI4NzE2NSwic3ViIjoiMyJ9.Hs4fle1mhbySXyb4sjdiBTmYxOl9p5LuJeP080Oj--M",
    }
    query = {"text": text}
    res = requests.post(url, headers=headers, data=json.dumps(query), verify=False)
    try:
        out = res.json()
        if isinstance(out, dict):
            raise ValueError(str(out))
        return res.json()
    except Exception as e:
        print("Failed embedding request:", str(e))
        return []


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
