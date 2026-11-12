class BaseTask:
    def __init__(self, name, description, usage=None, examples=None):
        self.name = name
        self.description = description
        self.usage = usage
        self.examples = examples or []

    def execute(self, args):
        # Override in child class
        raise NotImplementedError("Override execute() in child class.")