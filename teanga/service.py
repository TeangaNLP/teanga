from abc import ABC, abstractmethod
from .document import Document
import requests

class Service(ABC):
    """A service that can do some work on documents in a Teanga corpus."""

    def __init__(self):
        pass

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

class RESTService(Service):
    """An external service implemented in REST"""

    def __init__(self, endpoint):
        """Creates a new REST service reading from the given endpoint."""
        super().__init__()
        self.endpoint = endpoint
        self._requires = None
        self._produces = None

    def requires(self) -> dict:
        """Returns a dictionary of the layers required by this service."""
        if self._requires is None:
            r = requests.get(self.endpoint + "?requires")
            self._requires = r.json()
        return self._requires

    def produces(self) -> dict:
        """Returns a dictionary of the layers produced by this service."""
        if self._produces is None:
            r = requests.get(self.endpoint + "?produces")
            self._produces = r.json()
        return self._produces

    def execute(self, input:Document):
        """Executes this service on a document."""
        r = requests.post(self.endpoint, json=input.to_json())
        return input.add_layers(r.json())

def rest_service(service, kwargs):
    """Start a service as a REST service."""
    from flask import Flask, request, jsonify
    app = Flask(__name__)

    @app.route("/", methods=["GET"])
    def get():
        if request.args.get("requires"):
            return jsonify(service.requires())
        elif request.args.get("produces"):
            return jsonify(service.produces())
        else:
            return "Hello, World!"

    @app.route("/", methods=["POST"])
    def post():
        doc = Document.from_json(request.json)
        return jsonify(service.execute(doc).to_json())

    app.run(**kwargs)
