from .document import Document
from .service import Service
from .utils import teanga_id_for_doc
from .layer_desc import LayerDesc, _layer_desc_from_kwargs, _from_layer_desc

try:
    import teanga_pyo3.teanga as teangadb
    TEANGA_DB = True
except ImportError:
    TEANGA_DB = False
import shutil
import os
import json
import yaml
import gzip
from io import StringIO
from itertools import chain
from urllib.request import urlopen

class Corpus:
    """Corpus class for storing and processing text data.
        
        Examples:
        ---------

        >>> corpus = Corpus()
        >>> corpus.add_layer_meta("text")
        >>> doc = corpus.add_doc("This is a document.")
    """
    def __init__(self, db=None, new=False, db_corpus=None):
        if db_corpus:
            self.corpus = db_corpus
            self.meta = self.corpus.meta
        elif db:
            if not TEANGA_DB:
                teanga_db_fail()
            if new and os.path.exists(db):
                shutil.rmtree(db)
            self.corpus = teangadb.Corpus(db)
            self.meta = self.corpus.meta
        else:
            self.corpus = None
            self.meta = {}
            self._docs = []


    def add_meta_from_service(self, service : Service):
        """Add the meta data of a service to the corpus. This is normally 
        required to call apply to a service

        Parameters:
        -----------
        service:
            The service to add.

        Examples:
        ---------
        >>> corpus = Corpus()
        >>> class ExampleService:
        ...     def requires(self):
        ...         return {"text": {"type": "characters"}}
        ...     def produces(self):
        ...         return {"first_char": {"type": "characters"}}
        >>> corpus.add_meta_from_service(ExampleService())
        """
        for name, layer in chain(service.requires().items(), 
                                 service.produces().items()):
            if "type" not in layer:
                raise Exception("Layer type not specified." + str(layer))
            desc = _layer_desc_from_kwargs(layer)
            if name in self.meta and self.meta[name] != desc:
                raise Exception("Layer with name " + name +
                                " already exists with different meta.")
            elif name not in self.meta:
                self.add_layer_meta(name, **layer)


    def add_layer_meta(self, name:str=None,
                       layer_type:str="characters", base:str=None, 
                       data=None, link_types:list[str]=None,
                       target:str=None, default=None,
                       meta:dict={}):
        """Add a layer to the corpus.
        
        Parameters:
        -----------
        name: str
            Name of the layer.
        layer_type: str
            The type of the layer, can be "characters", "span", "seq", 
            "element" or "div".
        base: str
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
        meta: dict
            Metadata properties of the layer.
    """
        if self.corpus:
            self.corpus.add_layer_meta(
                    name, layer_type, {}, base, data, link_types, target, default)
            return
        if name is None:
            raise Exception("Name of the layer is not specified.")
        if name in self.meta:
            raise Exception("Layer with name " + name + " already exists.")
        if layer_type not in ["characters", "span", "seq", "div", "element"]:
            raise Exception("Type of the layer is not valid.")
        if layer_type == "characters" and base is not None and base != "":
            raise Exception("Layer of type characters cannot be based on" +
            " another layer.")
        if layer_type == "characters":
            self.meta[name] = LayerDesc("characters")
            return
        if base is None:
            raise Exception("Layer of type " + layer_type + " must be based on " +
            "another layer.")
        self.meta[name] = LayerDesc(layer_type, base, data, link_types, 
                                    target, default, meta)

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
        >>> corpus.add_layer_meta("en", layer_type="characters")
        >>> corpus.add_layer_meta("nl", layer_type="characters")
        >>> doc = corpus.add_doc(en="This is a document.", nl="Dit is een document.")
        """
        char_layers = [name for (name, layer) in self.meta.items()
                       if layer.layer_type == "characters"]
        if len(char_layers) == 0:
            raise Exception("No character layer found. " +
            "Please add at least one character layer.")
        elif len(char_layers) == 1:
            if len(args) == 1:
                doc_id = teanga_id_for_doc(self.doc_ids,
                        **{char_layers[0]: args[0]})
                doc = Document(self.meta, id=doc_id, **{char_layers[0]: args[0]})
                if self.corpus:
                    self.corpus.add_doc({ char_layers[0]: args[0] })
                    doc.corpus = self.corpus
                else:
                    self._docs.append((doc_id, doc))
                return doc
            elif len(kwargs) == 1 and list(kwargs.keys())[0] == char_layers[0]:
                doc_id = teanga_id_for_doc(self.doc_ids,
                                           **kwargs)
                doc = Document(self.meta, id=doc_id, **kwargs)
                if self.corpus:
                    self.corpus.add_doc(**kwargs)
                    doc.corpus = self.corpus
                else:
                    self._docs.append((doc_id, doc))
                return doc
            else:
                raise Exception("Invalid arguments, please specify the text " +
                                "or use correct layer names.")
        else:
            if len(kwargs.keys()) == 0:
                raise Exception("More than one character layer found " +
                                f"{' '.join(char_layers)} " +
                                "Please specify the layer names to add")
            if set(kwargs.keys()).issubset(set(char_layers)):
                doc_id = teanga_id_for_doc(self.doc_ids,
                                           **kwargs)
                doc = Document(self.meta, id=doc_id, **kwargs)
                if self.corpus:
                    self.corpus.add_doc(kwargs)
                    doc.corpus = self.corpus
                else:
                    self._docs.append((doc_id, doc))
                return doc
            else:
                raise Exception("Invalid arguments, please specify the text " +
                                "or use correct layer names.")

    @property
    def doc_ids(self) -> list[str]:
        """Return the document ids of the corpus.

        Examples:
        ---------
        >>> corpus = Corpus()
        >>> corpus.add_layer_meta("text")
        >>> doc = corpus.add_doc("This is a document.")
        >>> corpus.doc_ids
        ['Kjco']
        """
        if self.corpus:
            return self.corpus.order
        else:
            return [doc[0] for doc in self._docs]

    @property
    def docs(self) -> list[tuple[str, Document]]:
        """Get all the documents in the corpus

        Examples:
        ---------
        >>> corpus = Corpus()
        >>> corpus.add_layer_meta("text")
        >>> doc = corpus.add_doc("This is a document.")
        >>> corpus.docs
        [('Kjco', Document('Kjco', {'text': CharacterLayer('This is a document.')}))]
        """
        if self.corpus:
            return [(doc_id, Document(self.meta, id=doc_id, 
                                     **self.corpus.get_doc_by_id(doc_id)))
                    for doc_id in self.corpus.order]
        else:
            return self._docs

    def doc_by_id(self, doc_id:str) -> Document:
        """
        Get a document by its id.

        Parameters:
        -----------

        doc_id: str
            The id of the document.

        Examples:
        ---------

        >>> corpus = Corpus()
        >>> corpus.add_layer_meta("text")
        >>> doc = corpus.add_doc("This is a document.")
        >>> corpus.doc_by_id("Kjco")
        Document('Kjco', {'text': CharacterLayer('This is a document.')})

        >>> if TEANGA_DB:
        ...   corpus = Corpus("tmp",new=True)
        ...   corpus.add_layer_meta("text")
        ...   doc = corpus.add_doc("This is a document.")
        """
        if self.corpus:
            return Document(self.meta, id=doc_id, **self.corpus.get_doc_by_id(doc_id))
        else:
            return next(doc for doc in self._docs if doc[0] == doc_id)[1]

    @property
    def meta(self) -> dict[str, LayerDesc]:
        """Return the meta data of the corpus.

        Examples:
        ---------
        >>> corpus = Corpus()
        >>> corpus.add_layer_meta("text")
        >>> corpus.meta
        {'text': LayerDesc(layer_type='characters', base=None, data=None, \
link_types=None, target=None, default=None, meta={})}
        """
        if self.corpus:
            return {
                    key: LayerDesc(layer_type=layer.layer_type, base=layer.base,
                                  data=layer.data, link_types=layer.link_types,
                                  target=layer.target, default=layer.default,
                                  meta=layer.meta)
                    for key, layer in self.corpus.meta.items() }
        else:
            return self._meta

    @meta.setter
    def meta(self, meta: dict[str, LayerDesc]):
        if self.corpus:
            self.corpus.meta = meta
        else:
            self._meta = meta

    def to_yaml(self, path_or_buf : str):
        """Write the corpus to a yaml file.

        Parameters:
        -----------

        path_or_buf: str
            The path to the yaml file or a buffer.

        """
        if self.corpus:
            teangadb.write_corpus_to_yaml_file(path_or_buf, self.corpus)
        else:
            if isinstance(path_or_buf, str):
                with open(path_or_buf, "w") as f:
                    self._to_pretty_yaml(f)
            else:
                self._to_pretty_yaml(path_or_buf)

    def to_yaml_str(self) -> str:
        """
        Write the corpus to a yaml string.

        Examples:
        ---------
        >>> corpus = Corpus()
        >>> corpus.add_layer_meta("text")
        >>> doc = corpus.add_doc("This is a document.")
        >>> corpus.to_yaml_str()
        '_meta:\\n    text:\\n        type: characters\\n\
Kjco:\\n    text: This is a document.\\n'
        """
        if self.corpus:
            return teangadb.write_corpus_to_yaml_string(self.corpus)
        else:
            s = StringIO()
            self._to_pretty_yaml(s)
            return s.getvalue()

    def _to_pretty_yaml(self, writer):
        writer.write("_meta:\n")
        for name in sorted(self.meta.keys()):
            meta = self.meta[name]
            writer.write("    " + name + ":\n")
            writer.write("        type: " + meta.layer_type + "\n")
            if meta.base:
                writer.write("        base: " + _yaml_str(meta.base))
            if meta.data:
                writer.write("        data: " + 
                             self._dump_yaml_json(meta.data))
            if meta.link_types:
                writer.write("        link_types: " + 
                             self._dump_yaml_json(meta.link_types))
            if meta.target:
                writer.write("        target: " + 
                             self._dump_yaml_json(meta.target))
            if meta.default:
                writer.write("        default: " + 
                             self._dump_yaml_json(meta.default))
        for id, doc in self._docs:
            writer.write(id + ":\n")
            for layer_id in doc.layers:
                writer.write("    ")
                if isinstance(doc[layer_id].raw, str):
                    writer.write(layer_id)
                    writer.write(": ")
                    writer.write(_yaml_str(doc[layer_id].raw))
                else:
                    writer.write(layer_id + ": ")
                    writer.write(json.dumps(doc[layer_id].raw) + "\n")

    def _dump_yaml_json(self, obj):
        if obj is None:
            return "null"
        elif isinstance(obj, str):
            return _yaml_str(obj)
        else:
            return json.dumps(obj) + "\n"

    def to_json(self, path_or_buf):
        """Write the corpus to a JSON file.

        Parameters:
        -----------

        path_or_buf: str
            The path to the json file or a buffer.

        """
        if self.corpus:
            teangadb.write_corpus_to_json_file(path_or_buf, self.corpus)
        else:
            if isinstance(path_or_buf, str):
                with open(path_or_buf, "w") as f:
                    self._to_json(f)
            else:
                self._to_json(path_or_buf)

    def to_json_str(self) -> str:
        """
        Write the corpus to a JSON string.

        Examples:
        ---------

        >>> corpus = Corpus()
        >>> corpus.add_layer_meta("text")
        >>> doc = corpus.add_doc("This is a document.")
        >>> corpus.to_json_str()
        '{"_meta": {"text": {"type": "characters"}}, "_order": ["Kjco"], \
"Kjco": {"text": "This is a document."}}'
         """
        if self.corpus:
            return teangadb.write_corpus_to_json_string(self.corpus)
        else:
            s = StringIO()
            self._to_json(s)
            return s.getvalue()

    def _to_json(self, writer):
        dct = {}
        dct["_meta"] = {name: _from_layer_desc(data) 
                        for name, data in self.meta.items()
                        if not name.startswith("_")}
        dct["_order"] = self.doc_ids
        for doc_id, doc in self._docs:
            dct[doc_id] = {layer_id: doc[layer_id].raw 
                           for layer_id in doc.layers}
        json.dump(dct, writer)

    def apply(self, service : Service):
        """Apply a service to each document in the corpus.

        Parameters:
        -----------
        service:
            The service to apply.

        Examples:
        ---------
        >>> corpus = Corpus()
        >>> corpus.add_layer_meta("text")
        >>> corpus.add_layer_meta("first_char")
        >>> doc = corpus.add_doc(text="This is a document.")
        >>> from teanga.service import Service   
        >>> class FirstCharService(Service):
        ...     def requires(self):
        ...         return {"text": { "type": "characters"}}
        ...     def produces(self):
        ...         return {"first_char": {"type": "characters"}}
        ...     def execute(self, input):
        ...         input["first_char"] = input["text"][0]
        ...         return input
        >>> corpus.apply(FirstCharService())
        """
        self.add_meta_from_service(service)
        for _, doc in self.docs:
            service.execute(doc)

def _yaml_str(s):
    s = yaml.safe_dump(s)
    if s.endswith("\n...\n"):
        s = s[:-4]
    return s

def _corpus_hook(dct : dict) -> Corpus:
    c = Corpus()
    if "_meta" not in dct:
        return dct
    c.meta = {key: _layer_desc_from_kwargs(value) 
              for key, value in dct["_meta"].items()
              if not key.startswith("_")}
    if "_order" in dct:
        for doc_id in dct["_order"]:
            c._docs.append((doc_id, Document(c.meta, id=doc_id, **dct[doc_id])))
    else:
        for doc_id, value in dct.items():
            if not doc_id.startswith("_"):
                doc = Document(c.meta, id=doc_id, **value)
                text_fields = {
                        field: value for field, value in value.items()
                        if isinstance(value, str)
                }
                tid = teanga_id_for_doc(c.doc_ids, **text_fields)
                if tid != doc_id:
                    raise Exception("Invalid document id: " + doc_id + 
                                    " should be " + tid)
                c._docs.append((doc_id, doc))
    return c

def read_json_str(json_str:str, db_file:str=None) -> Corpus:
    """Read a corpus from a json string.

    Parameters:
    -----------

    json_str: str
        The json string.
    db_file: str
        The path to the database file, if the corpus should be stored in a
        database.

    Examples:
    ---------

    >>> corpus = read_json_str('{"_meta": {"text": {"type": \
"characters"}},"Kjco": {"text": "This is a document."}}')
    """
    if db_file:
        if not TEANGA_DB:
            teanga_db_fail()
        return Corpus(db_corpus=teangadb.read_corpus_from_json_string(
            json_str, db_file))
    else:
        return json.loads(json_str, object_hook=_corpus_hook)

def read_json(path_or_buf, db_file:str=None) -> Corpus:
    """Read a corpus from a json file.

    Parameters:
    -----------

    path_or_buf: str
        The path to the json file or a buffer.
    db_file: str
        The path to the database file, if the corpus should be stored in a
        database.
    """
    if db_file:
        if not TEANGA_DB:
            teanga_db_fail()
        return Corpus(db_corpus=teangadb.read_corpus_from_json_file(
            path_or_buf, db_file))
    else:
        return json.load(path_or_buf, object_hook=_corpus_hook)

def read_yaml(path_or_buf, db_file:str=None) -> Corpus:
    """Read a corpus from a yaml file.

    Parameters:
    -----------

    path_or_buf: str
        The path to the yaml file or a buffer.
    db_file: str
        The path to the database file, if the corpus should be stored in a
        database.
    """
    if db_file:
        if not TEANGA_DB:
            teanga_db_fail()
        return Corpus(db_corpus=teangadb.read_corpus_from_yaml_file(
            path_or_buf, db_file))
    
    else:
        return _corpus_hook(yaml.load(open(path_or_buf), Loader=yaml.FullLoader))

def read_yaml_str(yaml_str, db_file:str=None) -> Corpus:
    """Read a corpus from a yaml string.

    Parameters:
    -----------

    yaml_str: str
        The yaml string.
    db_file: str
        The path to the database file, if the corpus should be stored in a
        database.

    Examples:
    ---------
    >>> corpus = read_yaml_str("_meta:\\n  text:\\n    type: characters\\n\
Kjco:\\n   text: This is a document.\\n")
    """
    if db_file:
        if not TEANGA_DB:
            teanga_db_fail()
        return Corpus(db_corpus=teangadb.read_corpus_from_yaml_string(
            yaml_str, db_file))
    else:
        return _corpus_hook(yaml.load(yaml_str, Loader=yaml.FullLoader))

def from_url(url:str, db_file:str=None) -> Corpus:
    """Read a corpus from a URL.

    Parameters:
    -----------

    url: str
        The URL to read the corpus from.
    db_file: str
        The path to the database file, if the corpus should be stored in a
        database.
    """ 
    if db_file:
        if not TEANGA_DB:
            teanga_db_fail()
        return Corpus(db_corpus=teangadb.read_corpus_from_yaml_url(
            url, db_file))
    else:
        if url.endswith(".gz"):
            with gzip.open(urlopen(url), "rt") as f:
                return _corpus_hook(yaml.load(f, Loader=yaml.FullLoader))
        else:
            return _corpus_hook(yaml.load(urlopen(url), Loader=yaml.FullLoader))


def teanga_db_fail():
    raise Exception("Teanga database not available. Please install the Teanga "
                    + "Rust package from https://github.com/teangaNLP/teanga.rs")
