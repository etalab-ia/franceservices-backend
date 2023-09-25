#!/bin/python

import spacy

#nlp = spacy.load("en_core_web_sm")
nlp = spacy.load("fr_core_news_md")
#nlp.add_pipe("entityfishing", config={"language": "fr", "extra_info": True})

text = '''Pour être éligible au prêt locatif intermédiaire à Paris ou dans une commune limitrophe, vous devez respecter certains critères de revenus maximums. Le montant total maximum des revenus annuels ne doit pas dépasser 32 715 € en 2023 pour une personne seule habituant ces zones. Toutefois, si vous avez 2 personnes à loger, le montant maximal sera de 48 894 € pour un jeune couple, de 64 094 € pour une personne seule avec une personne à charge, et de 76 525 € pour une personne seule avec 2 personnes à charge. Attention si les revenus dépassent ces montants, vous pourrez obtenir un autre type de logement social appelé logement PLI. Votre expérience vous permettra de répondre plus précisément à cette question.'''

doc = nlp(text)
for ent in doc.ents:
    print(ent.text, ' - ', ent.label_, ' (', ent.start_char, ent.end_char, ')')
