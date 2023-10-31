import pandas as pd
from vllm import LLM, SamplingParams
import os
import json
from pprint import pprint


def get_hermes_question(user_input, mode = "interview"):
  sampling_params = SamplingParams(temperature=0.7, top_p=0.95, max_tokens=500, presence_penalty = 2)
  detailed_prompt = """<|im_start|>system
Rédige un court résumé en français de ce texte. Le résumé devrait tenir en une à deux phrases maximum et se focaliser sur l'essentiel.<|im_end|>
<|im_start|>user"""
  detailed_prompt = detailed_prompt + "\n" + user_input + "<|im_end|>\n<|im_start|>assistant\n"
  prompts = detailed_prompt
  return prompts

# Opening JSON file
f = open('sp_embeddings.json')

# returns JSON object as 
# a dictionary
data = json.load(f)
texts = []
prompts = []
identifier_text = []
for instruction in data:
  texts.append(instruction["texte"])
  prompts.append(get_hermes_question(instruction["texte"]))
  identifier_text.append(instruction["identifier_text"])

llm = LLM("mistral-hermes")
sampling_params = SamplingParams(temperature=0.2, top_p=0.95, max_tokens=500)

outputs = llm.generate(prompts, sampling_params)

generated_text = []
for output in outputs:
  output = output.outputs[0].text
  generated_text.append(output)

df = pd.DataFrame(list(zip(identifier_text, generated_text)),
               columns =["id", "summary"])

# Save the DataFrame to a TSV file
df.to_csv('summary_set.tsv', sep='\t', index=False)