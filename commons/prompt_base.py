class Prompter:
    URL = "URL of the LLM API"
    SAMPLING_PARAMS = "dict of default smapling params fo a given child class"

    def __init__(self, mode=None):
        self.mode = mode
        self.sampling_params = self.SAMPLING_PARAMS

    def make_prompt(self, **kwargs):
        return

    def set_mode(self, mode):
        self.mode = mode
