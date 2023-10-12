import nltk
from nltk.tokenize import WordPunctTokenizer
from teanga.model import Document
from teanga.service import Service

class NLTKTokenizer(Service):
    """A service that tokenizes a document using NLTK.
    This service requires a "text" layer containing the text of the document.
    It produces a "tokens" layer containing the tokens of the document.

    Example:
    --------
    >>> from teanga.model import Document
    >>> from teanga.nltk.nltk_teanga import NLTKTokenizer
    >>> doc = Document({"text": { "type": "characters" } ,
    ... "tokens": { "type": "span", "on": "text" }})
    >>> layer = doc.add_layer("text", "This is a sentence.")
    >>> tokenizer = NLTKTokenizer()
    >>> tokenizer.setup()
    >>> tokenizer.execute(doc)
    >>> list(doc.get_layer("tokens").text(doc))
    ['This', 'is', 'a', 'sentence', '.']
    """

    def __init__(self):
        super().__init__()

    def setup(self):
        nltk.download('punkt')
        self.tokenizer = WordPunctTokenizer()

    def requires(self):
        return {"text": { "type": "characters" } }

    def produces(self):
        return {"tokens": { "type": "span", "on": "text" } }

    def execute(self, doc:Document):
        text = doc.get_layer("text").text(doc)
        doc.add_layer("tokens", list(self.tokenizer.span_tokenize(text)))
    
