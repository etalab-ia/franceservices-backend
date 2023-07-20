import os
import openai

from ._main import CorpusGenerator, generate_questions

openai.api_key = os.getenv("OPENAI_API_KEY")
openai.organization = os.getenv("OPENAI_ORGANIZATION_KEY")
