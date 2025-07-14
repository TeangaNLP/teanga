try:
    import spacy
except ImportError:
    raise ImportError("SpaCY is required for the SpaCY service")
from teanga import Service
import re

class SpaCy(Service):
    """A service that uses spaCy to tokenize and tag text.

    This service requires a SpaCY model name as a parameter. The model
    name is the name of a SpaCY model that has been installed on the
    system. For example, the model "en_core_web_sm" is a small English
    model that can be installed with the command:

    python -m spacy download en_core_web_sm

    Further information on SpaCY models can be found at:
    https://spacy.io/models

    The SpaCY model is loaded in the setup() method. The model is then
    applied to the text in the execute() method. The SpaCY model
    produces a number of annotations, including tokens, part-of-speech
    tags, lemmas, and dependency relations. These annotations are
    converted to the Teanga format and added to the document.

    Example:
    >>> from teanga import Document, Corpus
    >>> corpus = Corpus()
    >>> corpus.add_layer_meta("text")
    >>> service = SpaCy("en_core_web_sm")
    >>> service.setup()
    >>> doc = corpus.add_doc("This is a test.")
    >>> corpus.apply(service)
    """
    def __init__(self, model_name:str, excludes:list=[]):
        """Create a service for the SpaCY model name"""
        super().__init__()
        self.model_name = model_name
        self.exclude = excludes

    def setup(self):
        """Load the SpaCY model"""
        if not hasattr(self, "nlp") or not self.nlp:
            self.nlp = spacy.load(self.model_name)

    def requires(self):
        """Return the requirements for this service"""
        return {"text": { "type": "characters" }}

    def produces(self):
        """Return the output of this service"""
        if not hasattr(self, "nlp") or not self.nlp:
            raise Exception("SpaCY model not loaded. "
            + "Please call setup() on the service.")
        tag_labels = "string"
        dep_labels = "string"
        ner_labels = "string"
        for module, pipe in self.nlp.components:
            if module == "tagger":
                tag_labels = [t for t in pipe.labels]
            if module == "parser":
                dep_labels = [t for t in pipe.labels]
            if module == "ner":
                ner_labels = [t for t in pipe.labels]

        result = {
                "tokens": {"type": "span", "base": "text" },
                "pos": {"type": "seq", "base": "tokens", "data":
                        ["ADJ","ADP","PUNCT","ADV","AUX","SYM","INTJ",
                         "CCONJ","X","NOUN","DET","PROPN","NUM","VERB",
                         "PART","PRON","SCONJ", "SPACE", "EOL"]},
                "tag": {"type": "seq", "base": "tokens", "data": tag_labels },
                "lemma": {"type": "seq", "base": "tokens", "data": "string" },
                "morph": {"type": "seq", "base": "tokens", "data": "string" },
                "dep": {"type": "seq", "base": "tokens",
                        "data": "links", "link_types": dep_labels },
                "entity": {"type": "span", "base": "tokens", "data": ner_labels },
                "sentences": {"type": "div", "base": "tokens" }
        }

        for e in self.exclude:
            if e in result:
                del result[e]
        return result

    def execute(self, doc):
        """Execute SpaCy on the document"""
        if not hasattr(self, "nlp") or not self.nlp:
            raise Exception("SpaCY model not loaded. "
            + "Please call setup() on the service.")
        # SpaCY has problem with some long strings so we split by 2 or more newlines
        blocks = re.split(r"((?:\r?\n){2,})", doc.text.raw)
        tokens = []
        pos = []
        tag = []
        lemma = []
        morph = []
        dep = []
        entity = []
        sentences = []

        offset = 0
        token_offset = 0
        for block in self.nlp.pipe(blocks, disable=self.exclude):
            if not block.text.strip():
                offset += len(block.text)
                continue
            tokens.extend((offset + w.idx, offset + w.idx + len(w)) for w in block)
            if "pos" not in self.exclude:
                pos.extend(w.pos_ for w in block)
            if "tag" not in self.exclude:
                tag.extend(w.tag_ for w in block)
            if "lemma" not in self.exclude:
                lemma.extend(w.lemma_ for w in block)
            if "morph" not in self.exclude:
                morph.extend(str(w.morph) for w in block)
            if "dep" not in self.exclude:
                dep.extend((token_offset + w.head.i, w.dep_) for w in block)
            if "entity" not in self.exclude:
                entity.extend((token_offset + e.start, token_offset + e.end, e.label_) for e in block.ents)
            if "sentences" not in self.exclude:
                sentences.extend(token_offset + s.start for s in block.sents)
            offset += len(block.text)
            token_offset += len(block)

        doc.tokens = tokens
        if "pos" not in self.exclude:
            doc.pos = pos
        if "tag" not in self.exclude:
            doc.tag = tag
        if "lemma" not in self.exclude:
            doc.lemma = lemma
        if "morph" not in self.exclude:
            doc.morph = morph
        if "dep" not in self.exclude:
            doc.dep = dep
        if "entity" not in self.exclude:
            doc.entity = entity
        if "sentences" not in self.exclude:
            doc.sentences = sentences


