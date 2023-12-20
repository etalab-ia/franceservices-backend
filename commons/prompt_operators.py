
try:
    from app.core.operators_fs import OPERATORS
except ModuleNotFoundError as e:
    from api.app.core.operators_fs import OPERATORS
import re

def get_prompt_operators(query: str) -> str:
    final_prompt = f"""
        Réponds avec un seul mot. Voici le message d'un utilisateur : "{query}"
                
        Voici une liste d'administrations :
        - '{"'; -'".join(OPERATORS)}'
    Réponds avec un seul mot en utilisant uniquement la liste ci-dessus. Si l'administration n'est pas dans la liste, répond juste le mot "Aucun".
    """
    print(final_prompt)


def post_process_answer(answer: str) -> str:
    for operator in OPERATORS:
        if re.findall(answer, operator,re.IGNORECASE):
            return operator
    return ''
