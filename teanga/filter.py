from .corpus import Corpus, ImmutableCorpus
from typing import Iterator, Callable, Union, List
from .layer_desc import LayerDesc
from .document import Document

class SubsetCorpus(ImmutableCorpus):
    """A corpus that only contains certain documents 
       according to a filter function.
    """
    def __init__(self, corpus : 'ImmutableCorpus', subset : list[str]):
        """Create a new SubsetCorpus.

        Args:
            corpus: The corpus to filter.
            subset: A list of document IDs to include in the subset.
        """
        self._corpus = corpus
        self._subset = subset

    @property
    def doc_ids(self) -> Iterator[str]:
        """Return an iterator over the document IDs in the subset."""
        return iter(self._subset)

    def doc_by_id(self, doc_id: str) -> 'Document':
        """Return a document by its ID from the subset."""
        if doc_id not in self._subset:
            raise KeyError(f"Document ID {doc_id} not found in subset.")
        return self._corpus.doc_by_id(doc_id)

    @property
    def meta(self) -> dict[str, LayerDesc]:
        """Return the metadata of the corpus."""
        return self._corpus.meta


class FilterCorpus(ImmutableCorpus):
    """A corpus that views a subset of document by lazily filtering"""
    def __init__(self, corpus: 'ImmutableCorpus', filter_func: Callable[Document, bool]):
        """Create a new FilterCorpus.

        Args:
            corpus: The corpus to filter.
            filter_func: A function that takes a document ID and returns True if the
                         document should be included in the filtered corpus.
        """
        self._corpus = corpus
        self._filter_func = filter_func
        self._subset = None

    @property
    def doc_ids(self) -> Iterator[str]:
        """Return an iterator over the document IDs that match the filter."""
        if self._subset is None:
            self._subset = [doc_id for doc_id in self._corpus.doc_ids if self._filter_func(self._corpus.doc_by_id(doc_id))]
        return iter(self._subset)   

    def doc_by_id(self, doc_id: str) -> 'Document':
        """Return a document by its ID if it matches the filter."""
        if ((self._subset is None and not self._filter_func(self._corpus.doc_by_id(doc_id))) or
            doc_id not in self._doc_ids):
            raise KeyError(f"Document ID {doc_id} does not match the filter.")
        return self._corpus.doc_by_id(doc_id)
    
    @property
    def meta(self) -> dict[str, LayerDesc]:
        """Return the metadata of the corpus."""
        return self._corpus.meta



