import os
import pandas as pd
from vllm import LLM, SamplingParams
import os
import pprint


evaluation_set = pd.read_excel("benchmark_llm.xlsx", sheet_name="ServicesPublics.fr")

custom_prompt = "Peux-tu répondre à ce QCM après la lecture de texte et donner la bonne réponse ? Identifie les éléments du texte pertinents et tente de déduire la réponse la plus probable."
#custom_prompt = "Tu es Félix, le chatbot des services publics français. Tu dois apporter une réponse courtoise à la question qui t'es posée en utilisant un language précis et administratif"
format_prompt = "INST"

print(evaluation_set)

list_query = []
list_ids = []
list_correction = []
for index, row in evaluation_set.iterrows():
    identifier, question, text, exercise, correction = row['id_experience'], row['Question'], row['Texte'], row['Exercice'], row['Correction']
    list_ids.append(identifier)
    list_correction.append(correction)
    if format_prompt == "INST":
        query_model = """<s>[INST] <<SYS>>
Vous êtes Vigogne, un assistant IA créé par Zaion Lab. Vous suivez extrêmement bien les instructions. Aidez autant que vous le pouvez.
<</SYS>>

""" + custom_prompt + "\n\n" + question + "\n\n" + exercise + "\n\n\nLe texte : " + text + " [/INST] "
        list_query.append(query_model)

llm = LLM("vigostral")
sampling_params = SamplingParams(temperature=0.6, top_p=0.95, max_tokens=500)

outputs = llm.generate(list_query, sampling_params)

generated_text = []
for output in outputs:
  output = output.outputs[0].text
  generated_text.append(output)

df = pd.DataFrame(list(zip(list_ids, generated_text, list_correction)),
               columns =["id", "result", "correction"])

# Save the DataFrame to a TSV file
df.to_csv('result_vigostral.tsv', sep='\t', index=False)