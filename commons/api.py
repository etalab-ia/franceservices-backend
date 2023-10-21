import json

import requests

# @IMPROVE: commons & app.config unification
try:
    from app.config import FIRST_ADMIN_USERNAME, FIRST_ADMIN_PASSWORD, PUBLIC_API_HOST
except ModuleNotFoundError as e:
    from api.app.config import FIRST_ADMIN_USERNAME, FIRST_ADMIN_PASSWORD, PUBLIC_API_HOST

try:
    response = requests.post(
        f"http://{PUBLIC_API_HOST}/api/v2/sign_in",
        headers={"Content-Type": "application/json"},
        json={"username": FIRST_ADMIN_USERNAME, "password": FIRST_ADMIN_PASSWORD},
    )
    API_TOKEN = response.json()["token"]
except Exception as e:
    API_TOKEN = None
    print("Error: unable to authenticate to LIA: %s" % str(e))


def get_embedding_e5(text: str) -> list:
    """OpenAI-like embedding API"""
    global API_TOKEN
    host = PUBLIC_API_HOST
    url = f"http://{host}/api/v2/embeddings"
    query = {"text": text}
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_TOKEN}",
        }
        res = requests.post(url, headers=headers, data=json.dumps(query), verify=False)
        out = res.json()
        if isinstance(out, dict):  # e.g: unauthorized.
            raise ValueError(str(out))
        return res.json()
    except Exception as e:
        print("Failed embedding request:", str(e))
        # retry once more with an updated token
        # ===
        response = requests.post(
            f"http://{host}/api/v2/sign_in",
            headers={"Content-Type": "application/json"},
            json={"username": FIRST_ADMIN_USERNAME, "password": FIRST_ADMIN_PASSWORD},
        )
        API_TOKEN = response.json()["token"]
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_TOKEN}",
        }
        return requests.post(url, headers=headers, data=json.dumps(query), verify=False).json()


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
