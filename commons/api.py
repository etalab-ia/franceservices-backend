import json
from datetime import datetime, timedelta

import requests
from requests.exceptions import ConnectionError

# @IMPROVE: commons & app.config unification (relative imports...)
try:
    from app.config import API_URL, API_ROUTE_VER, FIRST_ADMIN_PASSWORD, FIRST_ADMIN_USERNAME
except ModuleNotFoundError:
    from api.app.config import API_URL, API_ROUTE_VER, FIRST_ADMIN_PASSWORD, FIRST_ADMIN_USERNAME


def get_legacy_client():
    return ApiClient(
        API_URL.rstrip("/") + "/" + API_ROUTE_VER.strip("/"),
        FIRST_ADMIN_USERNAME,
        FIRST_ADMIN_PASSWORD,
    )


class ApiClient:
    def __init__(self, url, username, password):
        self.url = url.rstrip("/")
        self.username = username
        self.password = password

        # Token:
        self.token = None
        self.token_dt = None
        self.token_ttl = 3600 * 23  # seconds

    def _fetch(self, method, route, headers=None, json_data=None):
        d = {
            "POST": requests.post,
            "GET": requests.get,
            "PUT": requests.put,
            "DELETE": requests.delete,
        }
        response = d[method](f"{self.url}{route}", headers=headers, json=json_data)
        response.raise_for_status()
        return response

    def _is_token_expired(self):
        if self.token is None or self.token_dt is None:
            return True
        dt_ttl = datetime.utcnow() - timedelta(seconds=self.token_ttl)
        return self.token_dt < dt_ttl

    def _sign_in(self):
        json_data = {"username": self.username, "password": self.password}
        response = self._fetch("POST", "/sign_in", json_data=json_data)
        self.token = response.json()["token"]
        self.token_dt = datetime.utcnow()

    def _signed_in_fetch(self, method, route, json_data=None):
        if self._is_token_expired():
            self._sign_in()
        headers = {"Authorization": f"Bearer {self.token}"}
        return self._fetch(method, route, headers=headers, json_data=json_data)

    def create_embedding(self, text):
        json_data = {"text": text}
        response = self._signed_in_fetch("POST", "/embeddings", json_data=json_data)
        return response.json()

    def search(
        self,
        index_name,
        query,
        limit=10,
        similarity="bm25",
        institution=None,
        sources=None,
        should_sids=None,
        must_not_sids=None,
    ):
        json_data = {
            "name": index_name,
            "query": query,
            "limit": limit,
            "similarity": similarity,
            "institution": institution,
            "sources": sources,
            "should_sids": should_sids,
            "must_not_sids": must_not_sids,
        }
        response = self._signed_in_fetch("POST", "/indexes", json_data=json_data)
        return response.json()

    def fetch_templates_files(self, url):
        headers = {}
        response = requests.get(f"{url}/get_templates_files", headers=headers)
        response.raise_for_status()
        return response.json()


# TODO: factorize with api/app/clients/api_vllm_client.py
def generate(url, conf, text):
    """OpenAI-like completion API"""
    # headers = {"Content-Type": "application/json"}
    c = conf.copy()
    c["prompt"] = text
    c["temperature"] = c["temperature"] / 100
    response = requests.post(url + "/generate", json=c, stream=True, verify=False)
    res = b""
    for r in response:
        res += r
    ans = json.loads(res.decode("utf-8"))
    ans = ans["text"][0]
    return ans
