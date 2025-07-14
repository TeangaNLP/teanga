from typing import Union, Callable, KeysView, ItemsView
from collections import Counter
from typing import TYPE_CHECKING
from teanga import Document
from .corpus import ImmutableCorpus

class GroupedCorpus:
    """A corpus that is grouped by some criterion."""

    def __init__(self, corpus, groups):
        """Create a new grouped corpus.

        Args:
            corpus: The corpus to group.
            groups: A dictionary where keys are group IDs and values are lists of
                    document IDs that belong to that group.
        """

        self.corpus = corpus
        self.groups = groups

    @property
    def docs(self) -> dict[str,ImmutableCorpus]:
        """Return the documents by group

        Returns:
            A dictionary with the documents grouped by the group criterion.

        Examples:
            >>> from teanga import Corpus
            >>> corpus = Corpus()
            >>> corpus.add_layer_meta("text")
            >>> corpus.add_layer_meta("words", layer_type="span", base="text")
            >>> corpus.add_layer_meta("document", layer_type="div", base="text",
            ... default=[0])
            >>> corpus.add_layer_meta("author", layer_type="seq", base="document",
            ... data="string")
            >>> doc1 = corpus.add_doc("This is a document.")
            >>> doc1.words = [(0, 4), (5, 7), (8, 9), (10, 18)]
            >>> doc1.author = ["John"]
            >>> doc2 = corpus.add_doc("This is another document.")
            >>> doc2.words = [(0, 4), (5, 7), (8, 15), (16, 25)]
            >>> doc2.author = ["Mary"]
            >>> group = corpus.by("author")
            >>> group.keys()
            dict_keys(['John', 'Mary'])
        """
        from .filter import SubsetCorpus
        return {group_id: SubsetCorpus(self.corpus, group)
                for group_id, group in self.groups.items()}

    def text_freq(self, layer:str,
                  condition : Union[str,
            Callable[[str], bool], list] = None) -> dict[str, int]:
        """Get the frequence of a text string in the corpus.

        Parameters:
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
            >>> from teanga import Corpus
            >>> corpus = Corpus()
            >>> corpus.add_layer_meta("text")
            >>> corpus.add_layer_meta("words", layer_type="span", base="text")
            >>> corpus.add_layer_meta("document", layer_type="div", base="text",
            ... default=[0])
            >>> corpus.add_layer_meta("author", layer_type="seq", base="document",
            ... data="string")
            >>> doc1 = corpus.add_doc("This is a document.")
            >>> doc1.words = [(0, 4), (5, 7), (8, 9), (10, 18)]
            >>> doc1.author = ["John"]
            >>> doc2 = corpus.add_doc("This is another document.")
            >>> doc2.words = [(0, 4), (5, 7), (8, 15), (16, 24)]
            >>> doc2.author = ["Mary"]
            >>> group = corpus.by("author")
            >>> group.text_freq("words")
            {'John': Counter({'This': 1, 'is': 1, 'a': 1, 'document': 1}), \
'Mary': Counter({'This': 1, 'is': 1, 'another': 1, 'document': 1})}
        """
        if condition is None:
            return {id: Counter(word
                for doc in group.docs
                for word in doc[layer].text)
                for id, group in self.items()}
        elif isinstance(condition, str):
            return {id: Counter(word
                for doc in group.docs
                           for word in doc[layer].text
                           if word == condition)
                for id, group in self.items()}
        elif callable(condition):
            return {id: Counter(word
                for doc in group.docs
                for word in doc[layer].text
                           if condition(word))
                for id, group in self.items()}
        else:
            return {id: Counter(word
                for doc in group.docs
                for word in doc[layer].text
                           if word in condition)
                for id, group in self.items()}

    def val_freq(self, layer:str,
                 condition = None) -> Counter:
        """Get the frequency of a value in a layer.

        Parameters:
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
            >>> from teanga import Corpus
            >>> corpus = Corpus()
            >>> corpus.add_layer_meta("text")
            >>> corpus.add_layer_meta("words", layer_type="span", base="text")
            >>> corpus.add_layer_meta("pos", layer_type="seq", base="words",
            ...                        data=["NOUN", "VERB", "ADJ", "ADV"])
            >>> doc1 = corpus.add_doc("Colorless green ideas sleep furiously.")
            >>> doc1.words = [(0, 9), (10, 15), (16, 21), (22, 28), (29, 37)]
            >>> doc1.pos = ["ADJ", "ADJ", "NOUN", "VERB", "ADV"]
            >>> doc2 = corpus.add_doc("Furiously sleep ideas green colorless.")
            >>> doc2.words = [(0, 9), (10, 15), (16, 21), (22, 28), (29, 37)]
            >>> doc2.pos = ["ADV", "VERB", "NOUN", "ADJ", "ADJ"]
            >>> group = corpus.by_doc()
            >>> group.val_freq("pos")
            {'9wpe': Counter({'ADJ': 2, 'NOUN': 1, 'VERB': 1, 'ADV': 1}), \
'9d3t': Counter({'ADJ': 2, 'ADV': 1, 'VERB': 1, 'NOUN': 1})}
        """
        if condition is None:
            return {id: Counter(val
                for doc in group.docs
                for val in doc[layer].data)
                for id, group in self.items()}
        elif isinstance(condition, str):
            return {id: Counter(val
                for doc in group.docs
                for val in doc[layer].data
                           if val == condition)
                for id, group in self.items()}
        elif callable(condition):
            return {id: Counter(val
                for doc in group.docs
                for val in doc[layer].data
                           if condition(val))
                for id, group in self.items()}
        else:
            return {id: Counter(val
                for doc in group.docs
                for val in doc[layer].data
                           if val in condition)
                for id, group in self.items()}

    def __getitem__(self, group_id: str) -> 'ImmutableCorpus':
        """Get the documents in a specific group by its ID.

        Args:
            group_id: The ID of the group to retrieve.

        Returns:
            A list of tuples containing document IDs and their corresponding Document objects.
        """
        if group_id not in self.groups:
            raise KeyError(f"Group ID {group_id} not found in grouped corpus.")
        from .filter import SubsetCorpus
        return SubsetCorpus(self.corpus, self.groups[group_id])

    def items(self) -> ItemsView[str, ImmutableCorpus]:
        """Return an iterator over the group IDs and their corresponding document subsets."""
        from .filter import SubsetCorpus
        return ({ group_id: SubsetCorpus(self.corpus, group)
                for group_id, group in self.groups.items() }).items()

    def keys(self) -> KeysView[str]:
        """Return a list of group IDs in the grouped corpus."""
        return self.groups.keys()

