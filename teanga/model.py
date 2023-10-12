# Description: This file contains the model class for the corpus.
from base64 import b64encode
from hashlib import sha256
from abc import ABC, abstractmethod
from typing import Generator
import numbers
from itertools import chain, pairwise

class Document:
    """Document class for storing and processing text data."""
    def __init__(self, meta, *args, **kwargs):
        self.meta = meta
        self.layers = {}
        for key in kwargs:
            self.add_layer(key, kwargs[key])

    def add_layer(self, name:str, value) -> 'Layer':
        """Add a layer to the document.
        
        Parameters:
        -----------
        name: str
            Name of the layer.
        value: str
            Value of the layer.
        """
        if name not in self.meta:
            raise Exception("Layer with name " + name + " does not exist.")
        if value is None and self.meta["default"] is not None:
            value = self.meta["default"]
        if self.meta[name]["type"] == "characters":
            self.layers[name] = CharacterLayer(name, self.meta[name], str(value))
        elif self.meta[name]["on"] not in self.layers:
            raise Exception("Cannot add layer " + name + " because sublayer " +
            self.meta[name]["on"] + " does not exist.")
        elif self.meta[name]["type"] == "seq":
            if not isinstance(value, list):
                raise Exception("Value of layer " + name + " must be a list.")
            if len(value) != len(self.layers[self.meta[name]["on"]]):
                raise Exception("Value of layer " + name + " must have the " +
                "same length as layer " + self.meta[name]["on"] + ".")
            self.layers[name] = SeqLayer(name, self.meta[name], value)
        elif self.meta[name]["type"] == "span":
            if not isinstance(value, list):
                raise Exception("Value of layer " + name + " must be a list.")
            self.layers[name] = SpanLayer(name, self.meta[name], value)
        elif self.meta[name]["type"] == "div":
            if not isinstance(value, list):
                raise Exception("Value of layer " + name + " must be a list.")
            self.layers[name] = DivLayer(name, self.meta[name], value)
        elif self.meta[name]["type"] == "element":
            if not isinstance(value, list):
                raise Exception("Value of layer " + name + " must be a list.")
            self.layers[name] = ElementLayer(name, self.meta[name], value)
        else:
            raise Exception("Unknown layer type " + self.meta[name]["type"] + 
            " for layer " + name + ".")
        return self.layers[name]

    def get_layer(self, name:str):
        """Return the value of a layer.

        Parameters:
        -----------

        name: str
            The name of the layer.
        """
        if name not in self.meta:
            raise Exception("Layer with name " + name + " does not exist.")
        return self.layers[name]

    def text_for_layer(self, layer_name:str) -> Generator[None,None,str]:
        """Return the text for a layer.

        Parameters:
        -----------

        layer_name: str
            The name of the layer.
        
        Returns:
        --------
        A generator that yields the text for the layer.

        Examples:
        ---------
        >>> corpus = Corpus()
        >>> corpus.add_layer_meta("text")
        >>> corpus.add_layer_meta("words", type="span", on="text")
        >>> corpus.add_layer_meta("pos", type="seq", on="words")
        >>> doc = corpus.add_doc("This is a document.")
        >>> layer = doc.add_layer("words", [[0,4], [5,7], [8,9], [10,18], [18,19]])
        >>> layer = doc.add_layer("pos", ["DT", "VBZ", "DT", "NN", "."])
        >>> list(doc.text_for_layer("text"))
        ['T', 'h', 'i', 's', ' ', 'i', 's', ' ', 'a', ' ', 'd', 'o', \
'c', 'u', 'm', 'e', 'n', 't', '.']
        >>> list(doc.text_for_layer("words"))
        ['This', 'is', 'a', 'document', '.']
        >>> list(doc.text_for_layer("pos"))
        ['This', 'is', 'a', 'document', '.']
        """
        if layer_name not in self.meta:
            raise Exception("Layer with name " + layer_name + " does not exist.")
        if self.meta[layer_name]["type"] == "characters":
            return self.layers[layer_name].text(self)
        else:
            text_layer = layer_name
            while self.meta[text_layer]["type"] != "characters":
                text_layer = self.meta[text_layer]["on"]
            indexes = self.layers[layer_name].indexes(text_layer, self)
            return (self.layers[text_layer].text(self)[start:end]
                    for start, end in indexes)


def teanga_id_for_doc(*args, **kwargs):
    """Return the Teanga ID for a document.

    Parameters:
    -----------
    This works as the add_doc method, but returns the Teanga ID for the document.
    It is not necessary to call this method directly but instead you can use it
    via the Corpus class.

    Examples:
    ---------
    >>> teanga_id_for_doc("This is a document.")
    'NE/Q'
    >>> teanga_id_for_doc(en="This is a document.", nl="Dit is een document.")
    '7HPP'
    """
    text = ""
    if len(args) == 0:
        if len(kwargs) == 0:
            raise Exception("No arguments given.")
        for key in sorted(kwargs.keys()):
            text += kwargs[key]
    elif len(args) == 1:
        text = str(args[0])
    else:
        raise Exception("Too many arguments given.")
    return b64encode(sha256(text.encode("utf-8")).digest()).decode("utf-8")[0:4]

class Layer(ABC):
    """A layer of annotation"""
    
    def __init__(self, name:str, meta:dict):
        self._name = name
        self._meta = meta

    @abstractmethod
    def data(self, doc:Document):
        """Return the data values of the layer."""
        pass

    @abstractmethod
    def text(self, doc:Document):
        """Return the underlying text grouped by the annotations of this layer."""
        pass

    def text_data(self, doc:Document):
        """Return a list of pairs of the underlying text grouped by the 
        annotations of this layer and the data values of the layer."""
        return zip(self.text(doc), self.data(doc))

    @abstractmethod
    def indexes(self, layer:str, doc:Document):
        """Return the indexes of the annotations of this layer."""
        pass

    def data_indexes(self, layer:str, doc:Document):
        """Return a list of pairs of the data values of the layer and 
        the indexes of the annotations of this layer."""
        return zip(self.text(doc), self.data(doc))

    @abstractmethod
    def __len__(self):
        """Return the number of annotations in the layer."""
        pass

class CharacterLayer(Layer):
    """A layer of characters"""
    
    def __init__(self, name:str, meta:dict, text:str):
        super().__init__(name, meta)
        self._text = text

    def data(self, doc:Document):
        """
        Return the data values of the layer.

        Examples:
        ---------
        >>> layer = CharacterLayer("text", {"type": "characters"}, 
        ...     "This is a document.")
        >>> layer.data(None)
        []
        """
        return []

    def text(self, doc:Document):
        """
        Return the underlying text grouped by the annotations of this layer.

        Examples:
        ---------
        >>> layer = CharacterLayer("text", {"type": "characters"},
        ...     "This is a document.")
        >>> layer.text(None)
        'This is a document.'
        """
        return self._text

    def indexes(self, layer:str, doc:Document):
        """
        Return the indexes of the annotations of this layer.

        Examples:
        ---------
        >>> layer = CharacterLayer("text", {"type": "characters"}, 
        ...     "This")
        >>> list(layer.indexes("text", None))
        [(0, 1), (1, 2), (2, 3), (3, 4)]
        """
        if layer != self._name:
            raise Exception("Indexing on layer that is not a sublayer.")
        return zip(range(len(self._text)), range(1, len(self._text) + 1))

    def __repr__(self):
        return "CharacterLayer(" + repr(self._text) + ")"

    def __len__(self):
        return len(self._text)

class SeqLayer(Layer):
    """A layer that is in one-to-one correspondence with its sublayer.
    Typical examples are POS tags, lemmas, etc."""
    def __init__(self, name:str, meta:dict, seq:list):
        super().__init__(name, meta)
        self.seq = seq

    def data(self, doc:Document):
        """
        Return the data values of the layer.

        Examples:
        ---------
        >>> layer = SeqLayer("words", {"type": "seq", "on": "text"}, 
        ...     ["This", "is", "a", "document", "."])
        >>> layer.data(None)
        ['This', 'is', 'a', 'document', '.']
        """
        return self.seq

    def text(self, doc:Document):
        """
        Return the underlying text grouped by the annotations of this layer.

        Examples:
        ---------
        >>> doc = Document({"text": {"type": "characters"},
        ...  "words": { "type": "seq", "on": "text"}}, text="This")
        >>> layer = doc.add_layer("words", ["A", "B", "C", "D"])
        >>> list(layer.text(doc))
        ['T', 'h', 'i', 's']
        """
        return doc.text_for_layer(self._name)

    def indexes(self, layer:str, doc:Document):
        """
        Return the indexes of the annotations of this layer.

        Examples:
        ---------
        >>> doc = Document({"text": {"type": "characters"},
        ...  "words": { "type": "seq", "on": "text"}}, text="This")
        >>> layer = doc.add_layer("words", ["A", "B", "C", "D"])
        >>> list(layer.indexes("words", doc))
        [(0, 1), (1, 2), (2, 3), (3, 4)]
        """
        if layer == self._name:
            return ((i, i+1) for i in range(len(self.seq)))
        else:
            return doc.layers[self._meta["on"]].indexes(layer, doc)

    def __repr__(self):
        return "SeqLayer(" + repr(self.seq) + ")"

    def __len__(self):
        return len(self.seq)

class StandoffLayer(Layer):
    """Common superclass of span, div and element layers. Cannot be used
    directly"""

    def data(self, doc:Document):
        """
        Return the data values of the layer.

        Examples:
        ---------
        >>> doc = Document({"text": {"type": "characters"},
        ... "words": { "type": "span", "on": "text", "data": "string"}}, 
        ... text="This is an example.")
        >>> layer = doc.add_layer("words", [[0,4,"A"], [5,7,"B"], [8,10,"C"], 
        ... [11,18,"D"]])
        >>> list(layer.data(doc))
        ['A', 'B', 'C', 'D']
        """
        if self._meta["data"] is not None:
            return (s[2] for s in self._data)

    def text(self, doc:Document):
        """
        Return the underlying text grouped by the annotations of this layer.

        Examples:
        ---------
        >>> doc = Document({"text": {"type": "characters"},
        ... "words": { "type": "span", "on": "text", "data": "string"}}, 
        ... text="This is an example.")
        >>> layer = doc.add_layer("words", [[0,4,"A"], [5,7,"B"], [8,10,"C"], 
        ... [11,18,"D"]])
        >>> list(layer.text(doc))
        ['This', 'is', 'an', 'example']
        """
        return doc.text_for_layer(self._name)

    def __len__(self):
        return len(self._data)

class SpanLayer(StandoffLayer):
    """A layer that defines spans of the sublayer which are annotated.
    Typical examples are tokens, named entities, chunks, etc."""
    def __init__(self, name:str, meta:dict, spans:list):
        super().__init__(name, meta)
        self._data = spans
        for span in self._data: 
            if not isinstance(span[0], numbers.Integral):
                raise Exception("Bad span data: " + repr(span))
            if not isinstance(span[1], numbers.Integral):
                raise Exception("Bad span data: " + repr(span))

    def indexes(self, layer:str, doc:Document):
        """
        Return the indexes of the annotations of this layer.

        Examples:
        ---------
        >>> doc = Document({"text": {"type": "characters"},
        ... "words": { "type": "span", "on": "text", "data": "string"}}, 
        ... text="This is an example.")
        >>> layer = doc.add_layer("words", [[0,4,"A"], [5,7,"B"], [8,10,"C"], 
        ... [11,18,"D"]])
        >>> list(layer.indexes("words", doc))
        [(0, 1), (1, 2), (2, 3), (3, 4)]
        >>> list(layer.indexes("text", doc))
        [(0, 4), (5, 7), (8, 10), (11, 18)]
        """
        if layer == self._name:
            return zip(range(len(self._data)), range(1, len(self._data) + 1))
        elif layer == self._meta["on"]:
            return ((s[0], s[1]) for s in self._data)
        else:
            subindexes = list(doc.layers[self._meta["on"]].indexes(layer, doc))
            return ((subindexes[s[0]], subindexes[s[1]]) for s in self._data)

    def __repr__(self):
        return "SpanLayer(" + repr(self._data) + ")"

class DivLayer(StandoffLayer):
    """A layer where the sublayer is divided into non-overlapping parts.
    As such these layers have only a start index for each annotation, and that
    annotation spans until the next annotation"""

    def __init__(self, name:str, meta:dict, spans:list):
        super().__init__(name, meta)
        self._data = spans
        for span in self._data: 
            if not isinstance(span[0], numbers.Integral):
                raise Exception("Bad span data: " + repr(span))

    def indexes(self, layer:str, doc:Document):
        """
        Return the indexes of the annotations of this layer.

        Examples:
        ---------
        >>> doc = Document({"text": {"type": "characters"},
        ... "sentences": { "type": "div", "on": "text" }},
        ... text="This is an example. This is another example.")
        >>> layer = doc.add_layer("sentences", [[0], [19]])
        >>> list(layer.indexes("sentences", doc))
        [(0, 1), (1, 2)]
        >>> list(layer.indexes("text", doc))
        [(0, 19), (19, 44)]
        """
        if layer == self._name:
            return zip(range(len(self._data)), range(1, len(self._data) + 1))
        elif layer == self._meta["on"]:
            return pairwise(chain((s[0] for s in self._data), 
                                  [len(doc.layers[self._meta["on"]])]))
        else:
            subindexes = list(doc.layers[self._meta["on"]].indexes(layer, doc))
            return pairwise(chain((subindexes[s[0]] for s in self._data), 
                                  [len(doc.layers[self._meta["on"]])]))

    def __repr__(self):
        return "DivLayer(" + repr(self._data) + ")"

class ElementLayer(StandoffLayer):
    """A layer where each annotation is an element of the sublayer. This allows
    for multiple annotations of a single element. Typical examples are
    metadata elements such a titles"""

    def __init__(self, name:str, meta:dict, spans:list):
        super().__init__(name, meta)
        self._data = spans
        for span in self._data: 
            if not isinstance(span[0], numbers.Integral):
                raise Exception("Bad span data: " + repr(span))

    def indexes(self, layer:str, doc:Document):
        """
        Return the indexes of the annotations of this layer.

        Examples:
        ---------
        >>> doc = Document({"text": {"type": "characters"},
        ... "alts": { "type": "element", "on": "text", "data": "string" }},
        ... text="Tá sé seo mar shampla.")
        >>> layer = doc.add_layer("alts", [[1, "́a"], [4, "́e"]])
        >>> list(layer.indexes("alts", doc))
        [(0, 1), (1, 2)]
        >>> list(layer.indexes("text", doc))
        [(1, 2), (4, 5)]
        """
        if layer == self._name:
            return zip(range(len(self._data)), range(1, len(self._data) + 1))
        elif layer == self._meta["on"]:
            return ((s[0], s[0] + 1) for s in self._data)
        else:
            subindexes = list(doc.layers[self._meta["on"]].indexes(layer, doc))
            return ((subindexes[s[0]], subindexes[s[0]] + 1) for s in self._data)

    def __repr__(self):
        return "ElementLayer(" + repr(self._data) + ")"

class Corpus:
    """Corpus class for storing and processing text data.
        
        Examples:
        ---------

        >>> corpus = Corpus()
        >>> corpus.add_layer_meta("text")
        >>> doc = corpus.add_doc("This is a document.")
    """
    def __init__(self):
        self.meta = {}
        self.docs = []

    def add_layer_meta(self, name:str=None,
                  type:str="characters", on:str=None, 
                  data=None, link_types:list[str]=None,
                  target:str=None, default=None):
        """Add a layer to the corpus.
        
        Parameters:
        -----------
        name: str
            Name of the layer.
        type: str
            The type of the layer, can be "characters", "span", "seq", 
            "element" or "div".
        on: str
            The name of the layer on which the new layer is based.
        data: list
            The data of the layer, this can be the value "string", "link" or 
            a list of strings, for an enumeration of values
        link_types: list
            The types of the links, if the data is links.
        target: str
            The name of the target layer, if the data is links.
        default:
            A default value if none is given
    """
        if name is None:
            raise Exception("Name of the layer is not specified.")
        if name in self.meta:
            raise Exception("Layer with name " + name + " already exists.")
        if type not in ["characters", "span", "seq", "div", "element"]:
            raise Exception("Type of the layer is not valid.")
        if type == "characters" and on is not None:
            raise Exception("Layer of type characters cannot be based on" +
            " another layer.")
        if type == "characters":
            self.meta[name] = {
                "type": "characters"
            }
            return
        if on is None:
            raise Exception("Layer of type " + type + " must be based on " +
            "another layer.")
        self.meta[name] = {
            "type": type,
            "on": on,
        }
        if data:
            self.meta[name]["data"] = data
        if data == "links":
            if link_types is not None:
                self.meta[name]["link_types"] = link_types
            if target is not None:
                self.meta[name]["target"] = target
            else:
                self.meta[name]["target"] = on
        if default:
            self.meta[name]["default"] = default

    def add_doc(self, *args, **kwargs) -> Document:
        """Add a document to the corpus.
        
        Parameters:
        -----------

        If the corpus has only a single layer, the document can be added as a
        string. If the corpus has multiple layers, the document must be added
        by specifying the names of the layers and the data for each layer as
        keyword arguments.

        Examples:
        ---------
        >>> corpus = Corpus()
        >>> corpus.add_layer_meta("text")
        >>> doc = corpus.add_doc("This is a document.")

        >>> corpus = Corpus()
        >>> corpus.add_layer_meta("en", type="characters")
        >>> corpus.add_layer_meta("nl", type="characters")
        >>> doc = corpus.add_doc(en="This is a document.", nl="Dit is een document.")

        """
        char_layers = [layer for layer in self.meta 
                       if self.meta[layer]["type"] == "characters"]
        if len(char_layers) == 0:
            raise Exception("No character layer found. " +
            "Please add at least one character layer.")
        elif len(char_layers) == 1:
            if len(args) == 1:
                doc = Document(self.meta, **{char_layers[0]: args[0]})
                self.docs.append((teanga_id_for_doc(args[0]), doc))
                return doc
            elif len(kwargs) == 1 and list(kwargs.keys())[0] == char_layers[0]["name"]:
                doc = Document(self.meta, **kwargs)
                self.docs.append((teanga_id_for_doc(**kwargs), doc))
                return doc
            else:
                raise Exception("Invalid arguments, please specify the text " +
                                "or use correct layer names.")
        else:
            if set(kwargs.keys()) == set(char_layers):
                doc = Document(self.meta, **kwargs)
                self.docs.append((teanga_id_for_doc(**kwargs),  doc))
                return doc
            else:
                raise Exception("Invalid arguments, please specify the text " +
                                "or use correct layer names.")

    def get_docs(self):
        """Return the documents in the corpus."""
        return self.docs

    def get_layers(self, layer:str):
        """Return all the values of a specific layer in the corpus.

        Parameters:
        -----------
        layer: str
            The name of the layer.

        Examples:
        ---------

        >>> corpus = Corpus()
        >>> corpus.add_layer_meta("text")
        >>> doc = corpus.add_doc("This is a document.")
        >>> list(corpus.get_layers("text"))
        [CharacterLayer('This is a document.')]
        """
        if layer not in self.meta:
            raise Exception("Layer with name " + layer + " does not exist.")
        return (doc[1].get_layer(layer) for doc in self.docs)
