class Prompter:
    URL = "URL of the LLM API"
    SAMPLING_PARAMS = "dict of default smapling params fo a given child class"

    def __init__(self, mode=None):
        # The smapling params to pass to LLM generate function for inference.
        self.sampling_params = self.SAMPLING_PARAMS
        # A parameter used to configure the prompt (correspond to a system message for chat oriented LLM)
        self.mode = mode
        # Eventually stores the sources returns by the last RAG prompt built
        self.sources = None

    def make_prompt(self, **kwargs):
        return

    def set_mode(self, mode):
        self.mode = mode
