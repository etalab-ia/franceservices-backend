from commons.prompt_albert import AlbertLightPrompter
from commons.prompt_fabrique import FabriquePrompter, FabriqueReferencePrompter


def get_prompter(model_name, mode=None):
    # All pompter class derived from the following bastract class
    #
    # class Prompter:
    #
    #    def make_prompt(**kwargs):
    #        return

    if model_name == "fabrique-miaou":
        return FabriquePrompter()
    elif model_name == "fabrique-reference":
        return FabriqueReferencePrompter(mode)
    elif model_name == "albert-light":
        return AlbertLightPrompter()
    else:
        return ValueError("Prompter unknown: %s" % model_name)
