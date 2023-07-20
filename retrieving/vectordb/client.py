import os
import weaviate  # type: ignore

WEAVIATE_URL = os.environ.get("WEAVIATE_URL", "http://localhost")
WEAVIATE_PORT = os.environ.get("WEAVIATE_PORT", "")

print(f"connecting to Weaviate on host: {WEAVIATE_URL}:{WEAVIATE_PORT}...")

WEAVIATE_CLIENT = weaviate.Client(
    url=f"{WEAVIATE_URL}:{WEAVIATE_PORT}",
    additional_headers={
        "X-OpenAI-Api-Key": os.environ["OPENAI_API_KEY"],
    },
)
print("Successfully connected to Weaviate")
