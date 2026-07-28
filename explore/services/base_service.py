from abc import ABC, abstractmethod

class BaseDescriptionAI(ABC):
    @abstractmethod
    def generate(self, input_data: str):
        pass

    @abstractmethod
    def _build_prompt(self, input_data: str) -> str:
        pass

    @abstractmethod
    def _parse(self, raw: str):
        pass