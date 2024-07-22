from code_config import Config

class Director:
    def __init__(self, config: Config):
        self.config = config
        # self.ontology = Ontology()
        # self.ontology.load(config)

        self.builder:dict[str, Builder] = {}
        self.products = {}

    def set(self, key, value):
        setattr(self, key, value)

    def get(self, key):
        return getattr(self, key)

    def run(self):
        # self.extract_papers()
        pass

class Builder:
    def __init__(self, director: Director = None, config: Config = None):
        self.director: Director = director
        self.config = config if config else director.config if config else Config()

    def build(self):
        pass