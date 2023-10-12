from abc import ABC, abstractmethod
from teanga.model import Document

class Service(ABC):
    """A service that can do some work on documents in a Teanga corpus."""

    def __init__(self):
        pass

    @abstractmethod
    def setup(self):
        """Sets up this service, including downloading any models."""
        pass

    @abstractmethod
    def requires(self) -> dict:
        """Returns a dictionary of the layers required by this service."""
        pass

    @abstractmethod
    def produces(self) -> dict:
        """Returns a dictionary of the layers produced by this service."""
        pass

    @abstractmethod
    def execute(self, input:Document):
        """Executes this service on a document."""
        pass


