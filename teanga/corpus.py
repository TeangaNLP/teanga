from typing import TYPE_CHECKING
from .document import Document
from .service import Service
from .utils import teanga_id_for_doc
from .layer_desc import LayerDesc, _layer_desc_from_kwargs, _from_layer_desc
if TYPE_CHECKING:
    from .groups import GroupedCorpus
    from .transforms import TransformedCorpus
from .stream import CorpusStream, CorpusWriter

try:
    import teanga_pyo3.teanga as teanga_pyo3
    TEANGA_PYO3 = True
except ImportError:
    TEANGA_PYO3 = False
import shutil
import os
import json
import yaml
try:
    from yaml import CLoader as YamlLoader
except ImportError:
    from yaml import FullLoader as YamlLoader
import gzip
import tempfile
from io import StringIO
from itertools import chain
from typing import Iterator, Union, Callable, Iterable, Tuple, List, Optional
from abc import ABC, abstractmethod
from collections import Counter, defaultdict
from urllib.request import urlopen
import re


class ImmutableCorpus(ABC):
    """An abstract base class for immutable corpora.
    This class provides a read-only interface to the corpus, allowing
    access to documents and their metadata without modification.
    """

    @property
    @abstractmethod
    def doc_ids(self) -> Iterable[str]:
        """Return the document ids of the corpus."""
        pass

    @abstractmethod
    def doc_by_id(self, doc_id: str) -> Document:
        """Get a document by its id.

        Args:
            doc_id: str
                The id of the document.

        Returns:
            A Document object.
        """
        pass

    @property
    def docs(self) -> Iterator[Document]:
        """Get all the documents in the corpus.

        Returns:
            An iterator over Document objects.
        """
        for doc_id in self.doc_ids:
            yield self.doc_by_id(doc_id)

    @property
    @abstractmethod
    def meta(self) -> dict[str, LayerDesc]:
        """Return the metadata of the corpus.

        Returns:
            A dictionary with layer names as keys and LayerDesc objects as values.
        """
        pass

    @property
    def order(self) -> list[str]:
        """Return a list of the document ids in the order they appear in the corpus.

        Returns:
            A list of document ids in the order they appear in the corpus.
        """
        return list(self.doc_ids)

    def __getitem__(self, key:str) -> Document:
        """Get a document by its id.

        Args:
            key: Union[str, int, slice]
                The id of the document. Strings use document identifiers, while integers use the order of the documents in the corpus.

        Examples:
            >>> corpus = text_corpus()
            >>> doc = corpus.add_doc("This is a document.")
            >>> corpus["Kjco"]
            Document('Kjco', {'text': 'This is a document.'})
            >>> corpus[0]
            Document('Kjco', {'text': 'This is a document.'})
            >>> corpus[:1]
            [Document('Kjco', {'text': 'This is a document.'})]
        """
        if isinstance(key, int):
            return self.doc_by_id(self.order[key])
        elif isinstance(key, slice):
            doc_ids = self.order
            return [self.doc_by_id(doc_id) for doc_id in doc_ids[key]]
        elif isinstance(key, str):
            return self.doc_by_id(key)
        else:
            raise Exception("Invalid key type.")

    def view(self, *args):
        """Create a view on the corpus.

        Parameters:
        -----------
            args: str
                The names of the layers to view.

        Examples:
        ---------

        >>> corpus = Corpus()
        >>> corpus.add_layer_meta("text")
        >>> corpus.add_layer_meta("words", layer_type="span", base="text")
        >>> corpus.add_layer_meta("sentences", layer_type="div", base="words")
        >>> doc = corpus.add_doc("This is a sentence. This is another sentence.")
        >>> doc.words = [(0, 4), (5, 7), (8, 9), (10, 18), (20, 24), (25, 27),
        ...               (28, 35), (36, 44)]
        >>> doc.sentences = [0, 4]
        >>> doc.view("words", "sentences")
        [['This', 'is', 'a', 'sentence'], ['This', 'is', 'another', 'sentence']]
        """
        for doc_id, doc in self.docs:
            yield doc.view(*args)

    def text_freq(self, layer:str,
                  condition : Union[str,
            Callable[[str], bool], list] = None) -> dict[str, int]:
        """Get the frequence of a text string in the corpus.

        Args:
            layer
                The layer to get the frequency of (e.g. "text")
            condition
                A filter to match to. If a single string is given, the frequency
                of this single word is returned. If a list of strings is given, the
                frequency of each string is returned. If a function is given, all
                strings are returned for which the function returns True.

        Returns:
            A dictionary with the frequency of each string.

        Examples:
            >>> corpus = text_corpus()
            >>> doc = corpus.add_doc("This is a document.")
            >>> doc.tokens = [(0, 4), (5, 7), (8, 9), (10, 18)]
            >>> corpus.text_freq("tokens")
            Counter({'This': 1, 'is': 1, 'a': 1, 'document': 1})
            >>> corpus.text_freq("tokens", lambda x: "i" in x)
            Counter({'This': 1, 'is': 1})
        """
        if condition is None:
            return Counter(word
                for doc in self.docs
                for word in doc[layer].text)
        elif isinstance(condition, str):
            return Counter(word
                for doc in self.docs
                           for word in doc[layer].text
                           if word == condition)
        elif callable(condition):
            return Counter(word
                for doc in self.docs
                for word in doc[layer].text
                           if condition(word))
        else:
            return Counter(word
                for doc in self.docs
                for word in doc[layer].text
                           if word in condition)

    def val_freq(self, layer:str,
                 condition = None) -> Counter:
        """Get the frequency of a value in a layer.

        Args:
            layer
                The layer to get the frequency of (e.g. "pos")
            condition
                The value to get the frequency of. If a single value is given, the
                frequency of this single value is returned. If a list of values is
                given, the frequency of each value is returned. If a function is
                given, all values are returned for which the function returns True.

        Returns:
            A dictionary with the frequency of each value.

        Examples:
            >>> corpus = Corpus()
            >>> corpus.add_layer_meta("text")
            >>> corpus.add_layer_meta("words", layer_type="span", base="text")
            >>> corpus.add_layer_meta("pos", layer_type="seq", base="words",
            ...                        data=["NOUN", "VERB", "ADJ"])
            >>> doc = corpus.add_doc("Colorless green ideas sleep furiously.")
            >>> doc.words = [(0, 9), (10, 15), (16, 21), (22, 28), (29, 37)]
            >>> doc.pos = ["ADJ", "ADJ", "NOUN", "VERB", "ADV"]
            >>> corpus.val_freq("pos")
            Counter({'ADJ': 2, 'NOUN': 1, 'VERB': 1, 'ADV': 1})
            >>> corpus.val_freq("pos", ["NOUN", "VERB"])
            Counter({'NOUN': 1, 'VERB': 1})
            >>> corpus.val_freq("pos", lambda x: x[0] == "A")
            Counter({'ADJ': 2, 'ADV': 1})
        """
        if condition is None:
            return Counter(val
                for doc in self.docs
                for val in doc[layer].data)
        elif isinstance(condition, str):
            return Counter(val
                for doc in self.docs
                for val in doc[layer].data
                           if val == condition)
        elif callable(condition):
            return Counter(val
                for doc in self.docs
                for val in doc[layer].data
                           if condition(val))
        else:
            return Counter(val
                for doc in self.docs
                for val in doc[layer].data
                           if val in condition)

    def by_doc(self) -> 'GroupedCorpus':
        """Group the corpus by document to enable analysis such as frequency
        analysis on a per document basis.

        Examples:
            >>> corpus = text_corpus()
            >>> doc1 = corpus.add_doc("This is a document")
            >>> doc1.tokens = [(0, 4), (5, 7), (8, 9), (10, 18)]
            >>> doc2 = corpus.add_doc("This is another document.")
            >>> doc2.tokens = [(0, 4), (5, 7), (8, 15), (16, 24)]
            >>> group = corpus.by_doc()
            >>> group.text_freq("tokens")
            {'HP5c': Counter({'This': 1, 'is': 1, 'a': 1, 'document': 1}), 'eDFn': Counter({'This': 1, 'is': 1, 'another': 1, 'document': 1})}
        """
        from .groups import GroupedCorpus
        return GroupedCorpus(self,
                             {doc_id: [doc_id] for doc_id in self.doc_ids})


    def by(self, layer:str) -> 'GroupedCorpus':
        """Group the corpus according to which documents have specific values
        of a layer. Mostly used for metadata layers (e.g., "author", "genre")
        
        Args:
            layer: str
                The name of the layer to group by.
        Returns:
            A GroupedCorpus object that groups documents by the values in the specified layer.
        Examples:
            >>> corpus = text_corpus()
            >>> corpus.add_layer_meta("author")
            >>> doc1 = corpus.add_doc(text="This is a document", author="John")
            >>> doc2 = corpus.add_doc(text="This is another document", author="Mary")
            >>> group = corpus.by("author")
            >>> group["John"][0].text
            'This is a document'
        """
        from .groups import GroupedCorpus
        grouping = defaultdict(list)
        for doc in self.docs:
            if layer in doc:
                if self.meta[layer].data is None:
                    for value in doc[layer].text:
                        grouping[value].append(doc.id)
                else:
                    for value in doc[layer].data:
                        grouping[value].append(doc.id)
        return GroupedCorpus(self, grouping)

    def subset(self, values: Union[Iterable[str], Iterable[int]]) -> 'ImmutableCorpus':
        """Create a new corpus that is a subset of the current corpus.

        Args:
            values: Union[iterable[str], iterable[int]]
                The document ids or indices to include in the subset.

        Returns:
            A new Corpus object that contains only the documents specified by

        Examples:
            >>> corpus = text_corpus()
            >>> doc1 = corpus.add_doc("This is a document.")
            >>> doc2 = corpus.add_doc("This is another document.")
            >>> doc3 = corpus.add_doc("This is yet another document.")
            >>> subset = corpus.subset(["Kjco", "eDFn"])
            >>> list(subset.doc_ids)
            ['Kjco', 'eDFn']
            >>> subset = corpus.subset(range(2))
            >>> list(subset.doc_ids)
            ['Kjco', 'eDFn']
        """
        val_ids = []
        doc_ids = list(self.doc_ids)
        for value in values:
            if isinstance(value, str):
                val_ids.append(value)
            elif isinstance(value, int):
                val_ids.append(doc_ids[value])
            else:
                raise Exception("Invalid value type: " + str(type(value)))
        from .filter import SubsetCorpus
        return SubsetCorpus(self, val_ids)

    def sample(self, k: int) -> 'ImmutableCorpus':
        """Create a new corpus that is a random sample of the current corpus.

        Args:
            k: int
                The number of documents to sample from the corpus.

        Returns:
            A new Corpus object that contains a random sample of k documents.

        Examples:
            >>> corpus = text_corpus()
            >>> doc1 = corpus.add_doc("This is a document.")
            >>> doc2 = corpus.add_doc("This is another document.")
            >>> doc3 = corpus.add_doc("This is yet another document.")
            >>> sampled_corpus = corpus.sample(2)
            >>> len(list(sampled_corpus.doc_ids))
            2
        """
        from .filter import SubsetCorpus
        import random
        doc_ids = list(self.doc_ids)
        if k > len(doc_ids):
            raise ValueError("Sample size k cannot be greater than the number of documents in the corpus.")
        sampled_ids = random.sample(doc_ids, k)
        return SubsetCorpus(self, sampled_ids)


    def filter(self, filter_func: Callable[Document, bool]) -> 'ImmutableCorpus':
        """Create a new corpus that is a filtered version of the current corpus.

        Args:
            filter_func: Callable[Document, bool]
                A function that takes a Document object and returns True if the
                document should be included in the filtered corpus.

        Returns:
            A new Corpus object that contains only the documents that match the filter.

        Examples:
            >>> corpus = text_corpus()
            >>> doc1 = corpus.add_doc("This is a document.")
            >>> doc2 = corpus.add_doc("This is another document.")
            >>> doc3 = corpus.add_doc("This is yet another document.")
            >>> filter_func = lambda doc: "y" in doc.text
            >>> filtered_corpus = corpus.filter(filter_func)
            >>> list(filtered_corpus.doc_ids)
            ['fpwP']
        """
        from .filter import FilterCorpus
        return FilterCorpus(self, filter_func)

    def view(self, *args):
        """Create a view on the corpus.

        Parameters:
        -----------
            args: str
                The names of the layers to view.

        Examples:
        ---------

        >>> corpus = Corpus()
        >>> corpus.add_layer_meta("text")
        >>> corpus.add_layer_meta("words", layer_type="span", base="text")
        >>> corpus.add_layer_meta("sentences", layer_type="div", base="words")
        >>> doc = corpus.add_doc("This is a sentence. This is another sentence.")
        >>> doc.words = [(0, 4), (5, 7), (8, 9), (10, 18), (20, 24), (25, 27),
        ...               (28, 35), (36, 44)]
        >>> doc.sentences = [0, 4]
        >>> doc.view("words", "sentences")
        [['This', 'is', 'a', 'sentence'], ['This', 'is', 'another', 'sentence']]
        """
        for doc_id, doc in self.docs:
            yield doc.view(*args)

    def text_freq(self, layer:str,
                  condition : Union[str,
            Callable[[str], bool], list] = None) -> dict[str, int]:
        """Get the frequency of a text string in the corpus.

        Args:
            layer
                The layer to get the frequency of (e.g. "text")
            condition
                A filter to match to. If a single string is given, the frequency
                of this single word is returned. If a list of strings is given, the
                frequency of each string is returned. If a function is given, all
                strings are returned for which the function returns True.

        Returns:
            A dictionary with the frequency of each string.

        Examples:
            >>> corpus = text_corpus()
            >>> doc = corpus.add_doc("This is a document.")
            >>> doc.tokens = [(0, 4), (5, 7), (8, 9), (10, 18)]
            >>> corpus.text_freq("tokens")
            Counter({'This': 1, 'is': 1, 'a': 1, 'document': 1})
            >>> corpus.text_freq("tokens", lambda x: "i" in x)
            Counter({'This': 1, 'is': 1})
        """
        if condition is None:
            return Counter(word
                for doc in self.docs
                for word in doc[layer].text)
        elif isinstance(condition, str):
            return Counter(word
                for doc in self.docs
                           for word in doc[layer].text
                           if word == condition)
        elif callable(condition):
            return Counter(word
                for doc in self.docs
                for word in doc[layer].text
                           if condition(word))
        else:
            return Counter(word
                for doc in self.docs
                for word in doc[layer].text
                           if word in condition)

    def val_freq(self, layer:str,
                 condition = None) -> Counter:
        """Get the frequency of a value in a layer.

        Args:
            layer
                The layer to get the frequency of (e.g. "pos")
            condition
                The value to get the frequency of. If a single value is given, the
                frequency of this single value is returned. If a list of values is
                given, the frequency of each value is returned. If a function is
                given, all values are returned for which the function returns True.

        Returns:
            A dictionary with the frequency of each value.

        Examples:
            >>> corpus = Corpus()
            >>> corpus.add_layer_meta("text")
            >>> corpus.add_layer_meta("words", layer_type="span", base="text")
            >>> corpus.add_layer_meta("pos", layer_type="seq", base="words",
            ...                        data=["NOUN", "VERB", "ADJ"])
            >>> doc = corpus.add_doc("Colorless green ideas sleep furiously.")
            >>> doc.words = [(0, 9), (10, 15), (16, 21), (22, 28), (29, 37)]
            >>> doc.pos = ["ADJ", "ADJ", "NOUN", "VERB", "ADV"]
            >>> corpus.val_freq("pos")
            Counter({'ADJ': 2, 'NOUN': 1, 'VERB': 1, 'ADV': 1})
            >>> corpus.val_freq("pos", ["NOUN", "VERB"])
            Counter({'NOUN': 1, 'VERB': 1})
            >>> corpus.val_freq("pos", lambda x: x[0] == "A")
            Counter({'ADJ': 2, 'ADV': 1})
        """
        if condition is None:
            return Counter(val
                for doc in self.docs
                for val in doc[layer].data)
        elif isinstance(condition, str):
            return Counter(val
                for doc in self.docs
                for val in doc[layer].data
                           if val == condition)
        elif callable(condition):
            return Counter(val
                for doc in self.docs
                for val in doc[layer].data
                           if condition(val))
        else:
            return Counter(val
                for doc in self.docs
                for val in doc[layer].data
                           if val in condition)



    def search(self, query=None, **kwargs) -> Iterator[str]:
        """Search for documents in the corpus.

        Args:
            kwargs, query:
                The search criteria. The keys are the layer names and the values
                can be either a string, a list of strings or a dictionary with values
                describing the search criteria.

                If the value is a string the search is interpreted as an exact
                match. If the layer has no data this is applied to the text
                otherwise it is applied to the data.

                If the value is a list of strings, the search is interpreted as a
                search for any of the strings in the list.

                For dictionaries, the following keys are supported:
                `$text`: The value on the base character layer equal this value.
                `$text_ne`: The value on the base character layer must not equal this value.
                `$eq`: The value must be equal to this value.
                `$ne`: The value must not be equal to this value.
                `$gt`: The value must be greater than this value.
                `$lt`: The value must be less than this value.
                `$gte`: The value must be greater than or equal to this value.
                `$lte`: The value must be less than or equal to this value.
                `$in`: The value must be in this list.
                `$nin`: The value must not be in this list.
                `$text_in`: The value on the base character layer must be in this list.
                `$text_nin`: The value on the base character layer must not be in this list.
                `$regex`: The value must match this regular expression.
                `$text_regex`: The value on the base character layer must match
                    this regular expression.
                `$and`: All the conditions in this list must be true.
                `$or`: At least one of the conditions in this list must be true.
                `$not`: The condition in this list must not be true.
                `$exists`: A particular layer must exist.

        Returns:
            An iterator over the document ids that match the search criteria.

        Examples:
            >>> corpus = Corpus()
            >>> corpus.add_layer_meta("text")
            >>> corpus.add_layer_meta("words", layer_type="span", base="text")
            >>> corpus.add_layer_meta("pos", layer_type="seq", base="words",
            ...                        data=["NOUN", "VERB", "ADJ"])
            >>> corpus.add_layer_meta("lemma", layer_type="seq", base="words",
            ...                        data="string")
            >>> doc = corpus.add_doc("Colorless green ideas sleep furiously.")
            >>> doc.words = [(0, 9), (10, 15), (16, 21), (22, 27), (28, 37)]
            >>> doc.pos = ["ADJ", "ADJ", "NOUN", "VERB", "ADV"]
            >>> doc.lemma = ["colorless", "green", "idea", "sleep", "furiously"]
            >>> list(corpus.search(pos="NOUN"))
            ['9wpe']
            >>> list(corpus.search(pos=["NOUN", "VERB"]))
            ['9wpe']
            >>> list(corpus.search(pos={"$in": ["NOUN", "VERB"]}))
            ['9wpe']
            >>> list(corpus.search(pos={"$regex": "N.*"}))
            ['9wpe']
            >>> list(corpus.search(pos="VERB", lemma="sleep"))
            ['9wpe']
            >>> list(corpus.search(pos="VERB", words="idea"))
            []
            >>> list(corpus.search(pos="VERB", words="ideas"))
            ['9wpe']
            >>> list(corpus.search({"pos": "VERB", "lemma": "sleep"}))
            ['9wpe']
            >>> list(corpus.search({"$and": {"pos": "VERB", "lemma": "sleep"}}))
            ['9wpe']
        """
        if kwargs and query:
            raise Exception("Cannot specify both query and kwargs.")
        if kwargs:
            for doc in self.docs:
                if all(next(doc[layer].matches(value), None)
                       for layer, value in kwargs.items()):
                    yield doc.id
        else:
            for doc in self.docs:
                for key, value in query.items():
                    if not self._doc_matches(doc, key, value):
                        break
                else:
                    yield doc.id

    def _doc_matches(self, doc, key, value):
        if key == "$exists":
            return value in doc.layers
        elif key == "$and":
            return all(self._doc_matches(doc, k, v) for k, v in value.items())
        elif key == "$or":
            return any(self._doc_matches(doc, k, v) for k, v in value.items())
        elif key == "$not":
            if isinstance(value, dict):
                return all(self._doc_matches(doc, k, v) for k, v in value.items())
            else:
                raise Exception("Invalid $not query.")
        elif key in self.meta:
            return doc[key].matches(value)
        else:
            raise Exception("Invalid key: " + key)


    def normalise_query(self, query):
        """Normalise a query by replacing all field values with either `$eq` or
        `$text`
        """
        q2 = {}
        for key, value in query.items():
            if isinstance(value, list):
                if all(isinstance(v, str) for v in value):
                    if key in self.meta and self.meta[key].data is None:
                        q2[key] = {"$text_in": value}
                    else:
                        q2[key] = {"$in": value}
            elif isinstance(value, dict):
                q2[key] = value
            elif key in self.meta and self.meta[key].data is None:
                q2[key] = {"$text": value}
            else:
                q2[key] = {"$eq": value}
        return q2

    def all(self, layer_name: str) -> Iterator:
        """Get the combined value of a single layer in the order of the corpus.
        This will return the characters for layers without data and the data for layers with data.

        Args:
            layer_name: str
                The name of the layer to get the values from.

        Returns:
            An iterator over the values of the layer in the order of the corpus.

        Examples:
            >>> corpus = text_corpus()
            >>> corpus.add_layer_meta("pos", layer_type="seq", base="tokens",
            ...                        data=["NOUN", "VERB", "ADJ"])
            >>> doc1 = corpus.add_doc("This is a document.")
            >>> doc1.tokens = [(0, 4), (5, 7), (8, 9), (10, 18)]
            >>> doc1.pos = ["ADJ", "VERB", "NOUN", "VERB"]
            >>> doc2 = corpus.add_doc("This is another document.")
            >>> doc2.tokens = [(0, 4), (5, 7), (8, 15), (16, 24)]
            >>> doc2.pos = ["ADJ", "VERB", "NOUN", "VERB"]
            >>> list(corpus.all("text"))
            ['This is a document.', 'This is another document.']
            >>> list(corpus.all("tokens"))
            ['This', 'is', 'a', 'document', 'This', 'is', 'another', 'document']
            >>> list(corpus.all("pos"))
            ['ADJ', 'VERB', 'NOUN', 'VERB', 'ADJ', 'VERB', 'NOUN', 'VERB']
        """
        if layer_name not in self.meta:
            raise KeyError("Layer " + layer_name + " not found in corpus.")
        if self.meta[layer_name].data is None:
            return self.all_text(layer_name)
        else:
            return self.all_data(layer_name)

    def all_text(self, layer_name: str) -> Iterator[str]:
        """Get the combined text of a single layer in the order of the corpus.
        This will return the characters for layers without data.

        Args:
            layer_name: str
                The name of the layer to get the values from.

        Returns:
            An iterator over the text values of the layer in the order of the corpus.

        Examples:
            >>> corpus = text_corpus()
            >>> corpus.add_layer_meta("pos", layer_type="seq", base="tokens",
            ...                        data=["NOUN", "VERB", "ADJ"])
            >>> doc1 = corpus.add_doc("This is a document.")
            >>> doc1.tokens = [(0, 4), (5, 7), (8, 9), (10, 18)]
            >>> doc1.pos = ["ADJ", "VERB", "NOUN", "VERB"]
            >>> doc2 = corpus.add_doc("This is another document.")
            >>> doc2.tokens = [(0, 4), (5, 7), (8, 15), (16, 24)]
            >>> doc2.pos = ["ADJ", "VERB", "NOUN", "VERB"]
            >>> list(corpus.all_text("tokens"))
            ['This', 'is', 'a', 'document', 'This', 'is', 'another', 'document']
            >>> list(corpus.all_text("pos"))
            ['This', 'is', 'a', 'document', 'This', 'is', 'another', 'document']
        """
        if layer_name not in self.meta:
            raise Exception("Layer " + layer_name + " not found in corpus.")
        for doc in self.docs:
            if layer_name in doc:
                for text in doc[layer_name].text:
                    yield text

    def all_data(self, layer_name: str) -> Iterator:
        """Get the combined data of a single layer in the order of the corpus.
        This will return the data for layers with data.

        Args:
            layer_name: str
                The name of the layer to get the values from.

        Returns:
            An iterator over the data values of the layer in the order of the corpus.

        Examples:
            >>> corpus = text_corpus()
            >>> corpus.add_layer_meta("pos", layer_type="seq", base="tokens",
            ...                        data=["NOUN", "VERB", "ADJ"])
            >>> doc1 = corpus.add_doc("This is a document.")
            >>> doc1.tokens = [(0, 4), (5, 7), (8, 9), (10, 18)]
            >>> doc1.pos = ["ADJ", "VERB", "NOUN", "VERB"]
            >>> doc2 = corpus.add_doc("This is another document.")
            >>> doc2.tokens = [(0, 4), (5, 7), (8, 15), (16, 24)]
            >>> doc2.pos = ["ADJ", "VERB", "NOUN", "VERB"]
            >>> list(corpus.all_data("pos"))
            ['ADJ', 'VERB', 'NOUN', 'VERB', 'ADJ', 'VERB', 'NOUN', 'VERB']
        """
        if layer_name not in self.meta:
            raise Exception("Layer " + layer_name + " not found in corpus.")
        for doc in self.docs:
            if layer_name in doc:
                for data in doc[layer_name].data:
                    yield data

    def to_yaml(self, path_or_buf : str):
        """Write the corpus to a yaml file.

        Args:
            path_or_buf: str
                The path to the yaml file or a buffer.

        """
        if isinstance(path_or_buf, str):
            with open(path_or_buf, "w") as f:
                self._to_pretty_yaml(f)
        else:
            self._to_pretty_yaml(path_or_buf)

    def to_yaml_str(self) -> str:
        """
        Write the corpus to a yaml string.

        Examples:
            >>> corpus = Corpus()
            >>> corpus.add_layer_meta("text")
            >>> doc = corpus.add_doc("This is a document.")
            >>> corpus.to_yaml_str()
            '_meta:\\n    text:\\n        type: characters\\n\
Kjco:\\n    text: This is a document.\\n'
        """
        s = StringIO()
        self._to_pretty_yaml(s)
        return s.getvalue()

    def _to_pretty_yaml(self, writer):
        """
        """
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
        for id in self.doc_ids:
            doc = self.doc_by_id(id)
            if re.match(r"^[-+]?(0b[0-1_]+|0o[0-7_]+|0x[0-9a-fA-F_]+|[0-9][0-9_]*)$", id) or id == "true" or id == "True" or id == "TRUE" or id == "false" or id == "False" or id == "FALSE":
                writer.write("\"" + id + "\":\n")
            else:
                writer.write(id + ":\n")
            for layer_id in sorted(doc.layers):
                writer.write("    ")
                if isinstance(doc[layer_id].raw, str):
                    writer.write(layer_id)
                    writer.write(": ")
                    writer.write(_yaml_str(doc[layer_id].raw))
                else:
                    writer.write(layer_id + ": ")
                    writer.write(json.dumps(doc[layer_id].raw) + "\n")
            for key, value in doc.metadata.items():
                writer.write("    _" + key + ": " + _yaml_str(value))

    def _dump_yaml_json(self, obj):
        """
        """
        if obj is None:
            return "null"
        elif isinstance(obj, str):
            return _yaml_str(obj)
        else:
            return json.dumps(obj) + "\n"

    def to_json(self, path_or_buf):
        """Write the corpus to a JSON file.

        Args:
            path_or_buf: str
                The path to the json file or a buffer.

        """
        if isinstance(path_or_buf, str):
            with open(path_or_buf, "w") as f:
                self._to_json(f)
        else:
            self._to_json(path_or_buf)

    def to_json_str(self) -> str:
        """
        Write the corpus to a JSON string.

        Examples:
            >>> corpus = Corpus()
            >>> corpus.add_layer_meta("text")
            >>> doc = corpus.add_doc("This is a document.")
            >>> corpus.to_json_str()
            '{"_meta": {"text": {"type": "characters"}}, "_order": ["Kjco"], "Kjco": {"text": "This is a document."}}'
         """
        s = StringIO()
        self._to_json(s)
        return s.getvalue()

    def _to_json(self, writer):
        dct = {}
        dct["_meta"] = {name: _from_layer_desc(data)
                        for name, data in self.meta.items()
                        if not name.startswith("_")}
        dct["_order"] = list(self.doc_ids)
        for doc_id in self.doc_ids:
            doc = self.doc_by_id(doc_id)
            dct[doc_id] = {layer_id: doc[layer_id].raw
                           for layer_id in doc.layers}
            dct[doc_id].update({"_" + key: value
                                for key, value in doc.metadata.items()})
        json.dump(dct, writer)

    def to_cuac(self, path:str):
        """Write the corpus to a Cuac file.

        Args:
            path: str
                The path to the Cuac file.
        """
        if not TEANGA_PYO3:
            teanga_db_fail()
        tmpfile = tempfile.mkstemp()[1]
        self.to_json(tmpfile)
        tmppath = tempfile.mkdtemp()
        corpus = teanga_pyo3.read_corpus_from_json_file(tmpfile, tmppath)
        teanga_pyo3.write_corpus_to_cuac(corpus, path)

    def lower(self) -> 'TransformedCorpus':
        """Lowercase all the text in the corpus.

        Examples:
            >>> corpus = Corpus()
            >>> corpus.add_layer_meta("text")
            >>> doc = corpus.add_doc("This is a document.")
            >>> corpus = corpus.lower()
            >>> list(corpus.docs)
            [Document('Kjco', {'text': 'this is a document.'})]
        """
        from .transforms import TransformedCorpus
        text_layers = [layer for layer in self.meta
                       if self.meta[layer].layer_type == "characters"]
        return TransformedCorpus(self, {layer: lambda x: x.lower()
                                        for layer in text_layers})

    def upper(self) -> 'TransformedCorpus':
        """Uppercase all the text in the corpus.

        Examples:
            >>> corpus = text_corpus()
            >>> doc = corpus.add_doc("This is a document.")
            >>> corpus = corpus.upper()
            >>> list(corpus.docs)
            [Document('Kjco', {'text': 'THIS IS A DOCUMENT.'})]
        """
        from .transforms import TransformedCorpus
        text_layers = [layer for layer in self.meta
                       if self.meta[layer].layer_type == "characters"]
        return TransformedCorpus(self, {layer: lambda x: x.upper()
                                        for layer in text_layers})

    def transform(self, layer: str, transform:
                  Callable[[str], str]) -> 'TransformedCorpus':
        """Transform a layer in the corpus.

        Args:
            layer: str
                The name of the layer to transform.
            transform: Callable[[str], str]
                The transformation function.

        Examples:
            >>> corpus = text_corpus()
            >>> doc = corpus.add_doc("This is a document.")
            >>> corpus = corpus.transform("text", lambda x: x[:10])
            >>> list(corpus.docs)
            [Document('Kjco', {'text': 'This is a '})]
        """
        from .transforms import TransformedCorpus
        return TransformedCorpus(self, {layer: transform})

    def writer(self, buf) -> CorpusWriter:
        """Create a writer object that can serialize documents in 
        a streaming fashion.

        Args:
            buf: str
                The buffer to write to.

        Examples:
            >>> import io
            >>> corpus = text_corpus()
            >>> doc = corpus.add_doc("This is a document.")
            >>> string = io.StringIO()
            >>> with corpus.writer(string) as writer:
            ...     for doc in corpus.docs:
            ...         writer.write(doc)
        """
        return CorpusWriter(buf, self.meta)

    def _repr_html_(self):
        """Return a HTML representation of the corpus."""
        s = f"<h1>Corpus with {len(self.doc_ids)} documents</h1>"
        s += f"<h2>Layers</h2>"
        s += f"<table>"
        s += "<tr><th>Name</th><th>Type</th><th>Base</th><th>Data</th><th>Link types</th><th>Target</th><th>Default</th></tr>"
        for key, value in self.meta.items():
            s += f"<tr><td>{key}</td><td>{value.layer_type}</td>"
            s += f"<td>{value.base}</td>"
            s += f"<td>{value.data}</td>"
            s += f"<td>{value.link_types}</td>"
            s += f"<td>{value.target}</td>"
            s += f"<td>{value.default}</td></tr>"
        s += "</table>"
        return s

    def __str__(self):
        """Return a string representation of the corpus."""
        return f"Corpus with {len(self.doc_ids)} documents and {len(self.meta)} layers."

class Corpus(ImmutableCorpus):
    """Corpus class for storing and processing text data.

    Examples:
        >>> corpus = Corpus()
        >>> corpus.add_layer_meta("text")
        >>> doc = corpus.add_doc("This is a document.")
    """
    def __init__(self, db=None, new=False, db_corpus=None):
        if db_corpus:
            self._pyo3 = db_corpus
            self.meta = self._pyo3.meta
        elif db:
            if not TEANGA_PYO3:
                teanga_db_fail()
            if new and os.path.exists(db):
                shutil.rmtree(db)
            self._pyo3 = teanga_pyo3.Corpus(db)
            self.meta = self._pyo3.meta
        else:
            self._pyo3 = None
            self.meta = {}
            self._docs = {}


    def add_meta_from_service(self, service : Service):
        """Add the meta data of a service to the corpus. This is normally
        required to call apply to a service

        Args:
            service: The service to add.

        Examples:
            >>> corpus = Corpus()
            >>> class ExampleService:
            ...     def requires(self):
            ...         return {"text": {"type": "characters"}}
            ...     def produces(self):
            ...         return {"first_char": {"type": "characters"}}
            >>> corpus.add_meta_from_service(ExampleService())

        Returns:
            A number representing the arithmetic sum of `a` and `b`.
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

        Args:
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
        if self._pyo3:
            self._pyo3.add_layer_meta(
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

        Args:

            If the corpus has only a single layer, the document can be added as a
            string. If the corpus has multiple layers, the document must be added
            by specifying the names of the layers and the data for each layer as
            keyword arguments.

        Examples:
            >>> corpus = text_corpus()
            >>> doc = corpus.add_doc("This is a document.")

            >>> corpus = parallel_corpus(["en", "nl"])
            >>> doc = corpus.add_doc(en="This is a document.", nl="Dit is een document.")
        """
        if len(args) == 1 and isinstance(args[0], Document):
            doc = args[0]
            if self._pyo3:
                self._pyo3.add_doc({layer_id: doc[layer_id].raw
                                     for layer_id in doc.layers})
            else:
                self._docs[doc.id] = doc
            return doc
        char_layers = [name for (name, layer) in self.meta.items()
                       if layer.layer_type == "characters"]
        if len(char_layers) == 0:
            raise Exception("No character layer found. " +
            "Please add at least one character layer.")
        elif len(char_layers) == 1:
            if len(args) == 1:
                doc_id = teanga_id_for_doc(self.doc_ids,
                        **{char_layers[0]: args[0]})
                doc = Document(self.meta, id=doc_id, corpus_ref=self, **{char_layers[0]: args[0]})
                if self._pyo3:
                    self._pyo3.add_doc({ char_layers[0]: args[0] })
                    doc._pyo3 = self._pyo3
                else:
                    self._docs[doc_id] = doc
                return doc
            elif len(kwargs) == 1 and list(kwargs.keys())[0] == char_layers[0]:
                doc_id = teanga_id_for_doc(self.doc_ids,
                                           **kwargs)
                doc = Document(self.meta, id=doc_id, corpus_ref=self, **kwargs)
                if self._pyo3:
                    self._pyo3.add_doc(**kwargs)
                    doc._pyo3 = self._pyo3
                else:
                    self._docs[doc_id] = doc
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
                doc = Document(self.meta, id=doc_id, corpus_ref=self, **kwargs)
                if self._pyo3:
                    self._pyo3.add_doc(kwargs)
                    doc._pyo3 = self._pyo3
                else:
                    self._docs[doc_id] = doc
                return doc
            else:
                raise Exception("Invalid arguments, please specify the text " +
                                "or use correct layer names.")
    def update_doc(self, old_id : str, doc: Document) -> str:
        """Replace a particular document indicated by an identifier
        with a new document object.

        Args:
            old_id: str
                The identifier of the document to replace.
            doc: Document
                The new document object.

        Returns:
            The identifier of the new document.
        """
        if self._pyo3:
            new_doc_id = self._pyo3.update_doc(old_id,
                             {name: layer.raw
                                    for (name, layer) in doc.layers.items()})
            return new_doc_id
        else:
            if old_id in self._docs:
                del self._docs[old_id]
            doc_id = teanga_id_for_doc(self.doc_ids,
                                       **doc.character_layers())
            self._docs[doc_id] = doc
            return doc_id

    @property
    def doc_ids(self) -> Iterable[str]:
        """Return the document ids of the corpus.

        Examples:
            >>> corpus = text_corpus()
            >>> doc = corpus.add_doc("This is a document.")
            >>> list(corpus.doc_ids)
            ['Kjco']

        """
        if self._pyo3:
            return self._pyo3.order
        else:
            return self._docs.keys()

    @property
    def docs(self) -> Iterator[Document]:
        """Get all the documents in the corpus

        Examples:
            >>> corpus = text_corpus()
            >>> doc = corpus.add_doc("This is a document.")
            >>> list(corpus.docs)
            [Document('Kjco', {'text': 'This is a document.'})]
        """
        if self._pyo3:
            for doc_id in self._pyo3.order:
                yield Document(self.meta, id=doc_id, _pyo3=self._pyo3,
                               corpus_ref=self,
                               **self._pyo3.get_doc_by_id(doc_id))
        else:
            for doc in self._docs.items():
                yield doc[1]

    def doc_by_id(self, doc_id:str) -> Document:
        """
        Get a document by its id.

        Args:
            doc_id: str
                The id of the document.

        Examples:
            >>> corpus = text_corpus()
            >>> doc = corpus.add_doc("This is a document.")
            >>> corpus.doc_by_id("Kjco")
            Document('Kjco', {'text': 'This is a document.'})

            >>> if TEANGA_PYO3:
            ...   corpus = Corpus("tmp",new=True)
            ...   corpus.add_layer_meta("text")
            ...   doc = corpus.add_doc("This is a document.")
        """
        if self._pyo3:
            return Document(self.meta, id=doc_id, _pyo3=self._pyo3,
                            corpus_ref=self,
                            **self._pyo3.get_doc_by_id(doc_id))
        else:
            if doc_id in self._docs:
                return self._docs[doc_id]
            else:
                raise Exception("Document with id " + doc_id + " not found.")

    @property
    def meta(self) -> dict[str, LayerDesc]:
        """Return the meta data of the corpus.

        Examples:
            >>> corpus = Corpus()
            >>> corpus.add_layer_meta("text")
            >>> corpus.meta
            {'text': LayerDesc(layer_type='characters', base=None, data=None, link_types=None, target=None, default=None, meta={})}
        """
        if self._pyo3:
            return {
                    key: LayerDesc(layer_type=layer.layer_type, base=layer.base,
                                  data=layer.data, link_types=layer.link_types,
                                  target=layer.target, default=layer.default,
                                  meta=layer.meta)
                    for key, layer in self._pyo3.meta.items() }
        else:
            return self._meta

    @meta.setter
    def meta(self, meta: dict[str, LayerDesc]):
        if self._pyo3:
            meta_mapped = {}
            for k, v in meta.items():
                if isinstance(v, LayerDesc):
                    meta_mapped[k] = teanga_pyo3.layerdesc_from_dict(v._asdict())
                elif type(v) is dict:
                    meta_mapped[k] = teanga_pyo3.layerdesc_from_dict(v)
                elif str(type(v)) == '<class \'builtins.PyLayerDesc\'>':
                    meta_mapped[k] = v
                else:
                    raise Exception("Invalid type for layer meta: " + str(type(v)))
            self._pyo3.meta = meta_mapped
        else:
            self._meta = meta


    def search(self, query=None, **kwargs) -> Iterator[str]:
        """Search for documents in the corpus.

        Args:
            kwargs, query:
                The search criteria. The keys are the layer names and the values
                can be either a string, a list of strings or a dictionary with values
                describing the search criteria.

                If the value is a string the search is interpreted as an exact
                match. If the layer has no data this is applied to the text
                otherwise it is applied to the data.

                If the value is a list of strings, the search is interpreted as a
                search for any of the strings in the list.

                For dictionaries, the following keys are supported:
                `$text`: The value on the base character layer equal this value.
                `$text_ne`: The value on the base character layer must not equal this value.
                `$eq`: The value must be equal to this value.
                `$ne`: The value must not be equal to this value.
                `$gt`: The value must be greater than this value.
                `$lt`: The value must be less than this value.
                `$gte`: The value must be greater than or equal to this value.
                `$lte`: The value must be less than or equal to this value.
                `$in`: The value must be in this list.
                `$nin`: The value must not be in this list.
                `$text_in`: The value on the base character layer must be in this list.
                `$text_nin`: The value on the base character layer must not be in this list.
                `$regex`: The value must match this regular expression.
                `$text_regex`: The value on the base character layer must match
                    this regular expression.
                `$and`: All the conditions in this list must be true.
                `$or`: At least one of the conditions in this list must be true.
                `$not`: The condition in this list must not be true.
                `$exists`: A particular layer must exist.

        Returns:
            An iterator over the document ids that match the search criteria.

        Examples:
            >>> corpus = Corpus()
            >>> corpus.add_layer_meta("text")
            >>> corpus.add_layer_meta("words", layer_type="span", base="text")
            >>> corpus.add_layer_meta("pos", layer_type="seq", base="words",
            ...                        data=["NOUN", "VERB", "ADJ"])
            >>> corpus.add_layer_meta("lemma", layer_type="seq", base="words",
            ...                        data="string")
            >>> doc = corpus.add_doc("Colorless green ideas sleep furiously.")
            >>> doc.words = [(0, 9), (10, 15), (16, 21), (22, 27), (28, 37)]
            >>> doc.pos = ["ADJ", "ADJ", "NOUN", "VERB", "ADV"]
            >>> doc.lemma = ["colorless", "green", "idea", "sleep", "furiously"]
            >>> list(corpus.search(pos="NOUN"))
            ['9wpe']
            >>> list(corpus.search(pos=["NOUN", "VERB"]))
            ['9wpe']
            >>> list(corpus.search(pos={"$in": ["NOUN", "VERB"]}))
            ['9wpe']
            >>> list(corpus.search(pos={"$regex": "N.*"}))
            ['9wpe']
            >>> list(corpus.search(pos="VERB", lemma="sleep"))
            ['9wpe']
            >>> list(corpus.search(pos="VERB", words="idea"))
            []
            >>> list(corpus.search(pos="VERB", words="ideas"))
            ['9wpe']
            >>> list(corpus.search({"pos": "VERB", "lemma": "sleep"}))
            ['9wpe']
            >>> list(corpus.search({"$and": {"pos": "VERB", "lemma": "sleep"}}))
            ['9wpe']
        """
        if kwargs and query:
            raise Exception("Cannot specify both query and kwargs.")
        if self._pyo3:
            if kwargs:
                query = self.normalise_query(kwargs)
            else:
                query = self.normalise_query(query)
            for result in self._pyo3.search(query):
                yield result
        else:
            for result in super().search(query, **kwargs):
                yield result
                
    def to_yaml(self, path_or_buf : str):
        """Write the corpus to a yaml file.

        Args:
            path_or_buf: str
                The path to the yaml file or a buffer.

        """
        if self._pyo3:
            if isinstance(path_or_buf, str):
                teanga_pyo3.write_corpus_to_yaml(self._pyo3, path_or_buf)
            else:
                yaml_str = teanga_pyo3.write_corpus_to_yaml_string(self._pyo3)
                path_or_buf.write(yaml_str)
        else:
            super().to_yaml(path_or_buf)

    def to_yaml_str(self) -> str:
        """
        Write the corpus to a yaml string.

        Examples:
            >>> corpus = Corpus()
            >>> corpus.add_layer_meta("text")
            >>> doc = corpus.add_doc("This is a document.")
            >>> corpus.to_yaml_str()
            '_meta:\\n    text:\\n        type: characters\\n\
Kjco:\\n    text: This is a document.\\n'
        """
        if self._pyo3:
            return teanga_pyo3.write_corpus_to_yaml_string(self._pyo3)
        else:
            return super().to_yaml_str()

    def to_json(self, path_or_buf):
        """Write the corpus to a JSON file.

        Args:
            path_or_buf: str
                The path to the json file or a buffer.

        """
        if self._pyo3:
            if isinstance(path_or_buf, str):
                teanga_pyo3.write_corpus_to_json(self._pyo3, path_or_buf)
            else:
                json_str = teanga_pyo3.write_corpus_to_json_string(self._pyo3)
                path_or_buf.write(json_str)
        else:
            super().to_json(path_or_buf)

    def to_json_str(self) -> str:
        """
        Write the corpus to a JSON string.

        Examples:
            >>> corpus = Corpus()
            >>> corpus.add_layer_meta("text")
            >>> doc = corpus.add_doc("This is a document.")
            >>> corpus.to_json_str()
            '{"_meta": {"text": {"type": "characters"}}, "_order": ["Kjco"], "Kjco": {"text": "This is a document."}}'
         """
        if self._pyo3:
            return teanga_pyo3.write_corpus_to_json_string(self._pyo3)
        else:
            return super().to_json_str()

    def to_cuac(self, path:str):
        """Write the corpus to a Cuac file.

        Args:
            path: str
                The path to the Cuac file.
        """
        if self._pyo3:
            teanga_pyo3.write_corpus_to_cuac(self._pyo3, path)
        else:
            return super().to_cuac(path)

    def apply(self, service : Service):
        """Apply a service to each document in the corpus.

        Args:
            service: The service to apply.

        Examples:
            >>> corpus = Corpus()
            >>> corpus.add_layer_meta("text")
            >>> corpus.add_layer_meta("first_char", layer_type="element", base="text")
            >>> doc = corpus.add_doc(text="This is a document.")
            >>> from teanga.service import Service
            >>> class FirstCharService(Service):
            ...     def requires(self):
            ...         return {"text": { "type": "characters"}}
            ...     def produces(self):
            ...         return {"first_char": {"type": "element", "base": "text"}}
            ...     def execute(self, input):
            ...         input["first_char"] = [0]
            ...         return input
            >>> corpus.apply(FirstCharService())
        """
        self.add_meta_from_service(service)
        for doc in self.docs:
            service.execute(doc)

    def __eq__(self, other):
        """
        Compare two Teanga Corpora for equality
        """
        if not isinstance(other, Corpus):
            return False
        if self.doc_ids != other.doc_ids:
            return False
        return all(self.doc_by_id(doc_id) == other.doc_by_id(doc_id)
                   for doc_id in self.doc_ids)

def _yaml_str(s):
    """
    """
    s = yaml.safe_dump(str(s))
    if s.endswith("\n...\n"):
        s = s[:-4]
    if not s.startswith("'"):
        s = s.replace("\n", "\n    ")
        if s.endswith("\n    "):
            s = s[:-4]
    return s

def _corpus_hook(dct : dict) -> Corpus:
    """
    """
    c = Corpus()
    if "_meta" not in dct:
        return dct
    c.meta = {key: _layer_desc_from_kwargs(value)
              for key, value in dct["_meta"].items()
              if not key.startswith("_")}
    if "_order" in dct:
        for doc_id in dct["_order"]:
            c._docs[doc_id] = Document(c.meta, id=doc_id, corpus_ref=c, **dct[doc_id])
    else:
        for doc_id, value in dct.items():
            if isinstance(doc_id, int):
                raise Exception(f"Document IDs must be escaped if they can be interpreted as integers."
                + f"Found: {doc_id}, may occur in document as Ox{doc_id:02x} or Oo{doc_id:02o} or +{doc_id:03}")
            if not doc_id.startswith("_"):
                doc = Document(c.meta, id=doc_id, corpus_ref=c, **value)
                text_fields = {
                        field: value for field, value in value.items()
                        if isinstance(value, str) and not field.startswith("_")
                }
                if not text_fields:
                    raise Exception("No text field found in document " + doc_id)
                tid = teanga_id_for_doc(c.doc_ids, **text_fields)
                if tid != doc_id:
                    raise Exception("Invalid document id: " + doc_id +
                                    " should be " + tid)
                c._docs[doc_id] = doc
    return c

def read_json_str(json_str:str, db_file:str=None) -> Corpus:
    """Read a corpus from a json string.

    Args:
        json_str: str
            The json string.
        db_file: str
            The path to the database file, if the corpus should be stored in a
            database.

    Examples:
        >>> corpus = read_json_str('{"_meta": {"text": {"type": \
    "characters"}},"Kjco": {"text": "This is a document."}}')
    """
    if db_file:
        if not TEANGA_PYO3:
            teanga_db_fail()
        return Corpus(db_corpus=teanga_pyo3.read_corpus_from_json_string(
            json_str, db_file))
    else:
        return json.loads(json_str, object_hook=_corpus_hook)

def read_json(path_or_buf, db_file:str=None) -> Corpus:
    """Read a corpus from a json file.

    Args:
        path_or_buf: str
            The path to the json file or a buffer.
        db_file: str
            The path to the database file, if the corpus should be stored in a
            database.
    """
    if db_file:
        if not TEANGA_PYO3:
            teanga_db_fail()
        return Corpus(db_corpus=teanga_pyo3.read_corpus_from_json_file(
            path_or_buf, db_file))
    else:
        return json.load(path_or_buf, object_hook=_corpus_hook)

def read_yaml(path_or_buf, db_file:str=None) -> Corpus:
    """Read a corpus from a yaml file.

    Args:
        path_or_buf: str
            The path to the yaml file or a buffer.
        db_file: str
            The path to the database file, if the corpus should be stored in a
            database.
    """
    if db_file:
        if not TEANGA_PYO3:
            teanga_db_fail()
        return Corpus(db_corpus=teanga_pyo3.read_corpus_from_yaml_file(
            path_or_buf, db_file))

    else:
        with open(path_or_buf) as f:
            return _corpus_hook(yaml.load(f, Loader=YamlLoader))

def read_yaml_str(yaml_str, db_file:str=None) -> Corpus:
    """Read a corpus from a yaml string.

    Args:
        yaml_str: str
            The yaml string.
        db_file: str
            The path to the database file, if the corpus should be stored in a
            database.

    Examples:
        >>> yaml_str = '''_meta:
        ...   text:
        ...     type: characters
        ... Kjco:
        ...   text: This is a document.'''
        >>> corpus = read_yaml_str(yaml_str)
    """
    if db_file:
        if not TEANGA_PYO3:
            teanga_db_fail()
        return Corpus(db_corpus=teanga_pyo3.read_corpus_from_yaml_string(
            yaml_str, db_file))
    else:
        return _corpus_hook(yaml.load(yaml_str, Loader=YamlLoader))
    
def parse(path_or_buf:str) -> CorpusStream:
    """Parse a corpus incrementally from a file or buffer. Note that you will need
    to load this into a Corpus object directly

    Args:
        path_or_buf: str
            The path to the file or a buffer.

    Examples:
        >>> import io
        >>> yaml_str = '''_meta:
        ...   text:
        ...     type: characters
        ... Kjco:
        ...   text: This is a document.'''
        >>> stream = parse(io.StringIO(yaml_str))
        >>> corpus = Corpus()
        >>> corpus._meta = stream.meta
        >>> for doc in stream:
        ...     _ = corpus.add_doc(doc)
    """
    return CorpusStream(path_or_buf)

def from_url(url:str, db_file:str=None) -> Corpus:
    """Read a corpus from a URL.

    Args:
        url: str
            The URL to read the corpus from.
        db_file: str
            The path to the database file, if the corpus should be stored in a
            database.
    """
    if db_file:
        if not TEANGA_PYO3:
            teanga_db_fail()
        return Corpus(db_corpus=teanga_pyo3.read_corpus_from_yaml_url(
            url, db_file))
    else:
        if url.endswith(".gz"):
            with gzip.open(urlopen(url), "rt") as f:
                return _corpus_hook(yaml.load(f, Loader=YamlLoader))
        else:
            with urlopen(url) as f:
                return _corpus_hook(yaml.load(f, Loader=YamlLoader))

DOWNLOAD_URLS = [
        "https://teanga.io/corpora/",
        ]

def download(name:str, db_file:str=None) -> Corpus:
    """Load a corpus by name from a remote server.

    Args:
        name: str
            The name of the corpus to download.
        db_file: str
            The path to the database file, if the corpus should be stored in a
            database.
    """
    for url in DOWNLOAD_URLS:
        try:
            corpus = from_url(url + name + ".yaml.gz", db_file)
            if corpus:
                return corpus
        except:
            pass
    raise Exception(f"Corpus {name} not found in {DOWNLOAD_URLS}")

def text_corpus(db_file:str = None) -> Corpus:
    """
    Create a corpus with a `text` and `tokens` layer

    Args:
        db_file: str
            The path to the database file, if the corpus should be stored in a
            database.
    
    Returns:
        A corpus with a `text` and `tokens` layer
    """
    corpus = Corpus(db=db_file)
    corpus.add_layer_meta("text")
    corpus.add_layer_meta("tokens", layer_type="span", base="text")
    return corpus

def parallel_corpus(languages : list[str], db_file:str = None,
                    alignments : Optional[List[Tuple[str, str]]] = None) -> Corpus:
    """
    Create a corpus with a character layer and token layer for each language

    Args:
        languages: list[str]
            The languages to create the corpus for
        db_file: str
            The path to the database file, if the corpus should be stored in a
            database.
        alignments:
            A list of pairs of language to add an alignment field for.

    Returns:
        A corpus with a character layer and token layer for each language

    Examples:
        >>> corpus = parallel_corpus(["en","de","nl"], 
        ...   alignments=[("en","de"),("en","nl")])
        >>> doc = corpus.add_doc(en="hello, world", de="Hallo, Welt!")
        >>> doc.en_tokens = [(0,5), (7,12)]
        >>> doc.de_tokens = [(0,5), (7,11)]
        >>> doc.en_de_alignments = [(0,0),(1,1)]
    """
    corpus = Corpus(db=db_file)
    for lang in languages:
        corpus.add_layer_meta(lang, layer_type="characters")
        corpus.add_layer_meta(lang + "_tokens", layer_type="span", base=lang)
    if alignments:
        for src, trg in alignments:
            corpus.add_layer_meta(src + "_" + trg + "_alignments",
                                  layer_type="element", base=src + "_tokens",
                                  target=trg + "_tokens",
                                  data="link")
    return corpus

def read_cuac(file:str, db_file:str=None) -> Corpus:
    """Read a corpus from a Cuac file. Requires teanga_pyo3 module.

    Args:
        file: str
            The path to the Cuac file.
        db_file: str
            The path to the database file, if the corpus should be stored in a
            database.
    """
    if not TEANGA_PYO3:
        teanga_db_fail()
    if not db_file:
        db_file = tempfile.mkdtemp()
    return Corpus(db_corpus=teanga_pyo3.read_corpus_from_cuac_file(file, db_file))

def teanga_db_fail():
    """
    """
    raise Exception("Teanga database not available. Please install the Teanga "
                    + "Rust package from https://github.com/teangaNLP/teanga.rs")
