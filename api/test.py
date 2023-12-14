import json

import requests
from app.config import FIRST_ADMIN_EMAIL, FIRST_ADMIN_PASSWORD

url = "http://127.0.0.1:8000"

# Sign In:
response = requests.post(
    f"{url}/sign_in", json={"email": FIRST_ADMIN_EMAIL, "password": FIRST_ADMIN_PASSWORD}
)
try:
    token = response.json()["token"]
except:
    print(response, response.text)
    exit()


# Create Stream:
headers = {
    "Authorization": f"Bearer {token}",
}
data = {
    "user_text": "Merci pour le service Service-Public+. Bien à vous.",
    "query": "Quel est la limite d'age pour voter en france, et quelle sont les échances électorales ?",
    "model_name": "albert-light",
    # "sources": ["travail-emploi"],
}
response = requests.post(f"{url}/stream", json=data, headers=headers)

try:
    stream_id = response.json()["id"]
except:
    print(response, response.text)
    exit()

# Start Stream:
data = {"stream_id": stream_id}
response = requests.get(f"{url}/stream/{stream_id}/start", json=data, headers=headers, stream=True)
print("-> Waiting for the response stream:")
for line in response.iter_lines():
    if not line:
        continue
    _, _, data = line.decode("utf-8").partition("data: ")
    text = json.loads(data)
    if text == "[DONE]":
        break
    print(text, end="", flush=True)
