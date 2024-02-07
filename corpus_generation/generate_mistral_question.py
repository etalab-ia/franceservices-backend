import pandas as pd
from vllm import LLM, SamplingParams
import json
from pprint import pprint


def get_hermes_question(user_input, mode = "interview"):
  sampling_params = SamplingParams(temperature=0.7, top_p=0.95, max_tokens=500, presence_penalty = 2)
  detailed_prompt = """<|im_start|>system
Ecrit une question en français dont le texte suivant sera la réponse.<|im_end|>
<|im_start|>user"""
  detailed_prompt = detailed_prompt + "\n" + user_input + "<|im_end|>\n<|im_start|>assistant\n"
  prompts = detailed_prompt
  return prompts

current_text = """Plusieurs structures peuvent vous apporter du soutien en tant que victime d'une infraction de nature sexuelle.\nLe site Parcours-Victimes\n vous guide à chaque étape.\nViolences Femmes Info - 3919\nÉcoute, informe et oriente les femmes victimes de violences, et les témoins de ces violences.\nTraite les violences physiques, verbales ou psychologiques, à la maison ou au travail, et de toute nature (dont les harcèlements sexuels, les coups et blessures et les viols).\nNe traite pas les situations d'urgence (ce n'est pas un service de police ou de gendarmerie).\nPour les autres types de violences, le 3919 assure une réponse de premier niveau et oriente ou transfère vers un numéro utile.\nPar téléphone.\n\n39 19 (appel gratuit depuis un téléphone fixe ou mobile en métropole et dans les DOM\n).\nOuvert 24h sur 24 et 7 jours sur 7.\nAppel anonyme.\nAppel ne figurant pas sur les factures de téléphone.\n\n116 006 - Numéro d'aide aux victimes\nFrance Victimes\nÉcoute, informe et conseille les victimes d'infractions ainsi que leurs proches.\nPar téléphone.\n\n116 006.\nAppel gratuit.\nOuvert 7 jours sur 7 de 9h à 19h.\nLe service est également accessible en composant le +33 (0)1 80 52 33 76 (numéro à tarification normale).\n\nPar courriel.\n\nvictimes@france-victimes.fr.\n\nBureau d'aide aux victimes\nbav\n\nMinistère chargé de la justice\n\nVous pouvez aussi faire appel à un avocat si vous souhaitez faire une action en justice.\nAvocat\navocat_conseil_national\n\nConseil national des barreaux"""

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

pprint(prompts)

llm = LLM("mistral-hermes")
sampling_params = SamplingParams(temperature=0.2, top_p=0.95, max_tokens=500)

outputs = llm.generate(prompts, sampling_params, use_tqdm = False)

generated_text = []
for output in outputs:
  output = output.outputs[0].text
  generated_text.append(output)

pprint(generated_text)

df = pd.DataFrame(list(zip(identifier_text, generated_text)),
               columns =["id", "question"])

# Save the DataFrame to a TSV file
df.to_csv('instruction_set.tsv', sep='\t', index=False)