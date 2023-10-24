from .document import Document
from .utils import teanga_id_for_doc


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
                  data=None, values:list[str]=None,
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
        values: list
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
            if values is not None:
                self.meta[name]["values"] = values
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
                self.docs.append((teanga_id_for_doc(self._doc_keys(), 
                        **{ char_layers[0]: args[0]}), doc))
                return doc
            elif len(kwargs) == 1 and list(kwargs.keys())[0] == char_layers[0]["name"]:
                doc = Document(self.meta, **kwargs)
                self.docs.append((teanga_id_for_doc(self._doc_keys(), **kwargs), doc))
                return doc
            else:
                raise Exception("Invalid arguments, please specify the text " +
                                "or use correct layer names.")
        else:
            if set(kwargs.keys()) == set(char_layers):
                doc = Document(self.meta, **kwargs)
                self.docs.append((teanga_id_for_doc(self._doc_keys(), **kwargs),  doc))
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

    def _doc_keys(self):
        return [doc[0] for doc in self.docs]
