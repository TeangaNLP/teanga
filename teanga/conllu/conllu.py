from conllu import parse_incr
from typing import TextIO
from io import StringIO
import teanga
from teanga.utils import find_spans

def conllu_corpus(db : str = None, include_form = False) -> teanga.Corpus:
    """Create a new empty Teanga Corpus object with metadata fields as
    specified in the CoNLL-U format.
    Args:
    db: str
        The DB location to use of the Teanga corpus
    include_form: bool
        Also include a form layer
    """
    corpus = teanga.Corpus(db=db)
    corpus.add_layer_meta('text', 'characters')
    corpus.add_layer_meta('tokens', 'span', base='text')
    if include_form:
        corpus.add_layer_meta('form', 'seq', base='tokens', data='string')
    corpus.add_layer_meta('lemma', 'seq', base='tokens', data='string')
    corpus.add_layer_meta('upos', 'seq', base='tokens', data=["ADJ", "ADP", "ADV", "AUX", "CCONJ", "DET", "INTJ", "NOUN", "NUM", "PART", "PRON", "PROPN", "PUNCT", "SCONJ", "VERB", "X" ])
    corpus.add_layer_meta('xpos', 'seq', base='tokens', data='string')
    corpus.add_layer_meta('feats', 'seq', base='tokens', data='string')
    corpus.add_layer_meta('dep', 'seq', base='tokens', data='link', link_types=["acl", "advcl", "advmod", "amod", "appos", "aux", "case", "cc", "ccomp", "compound", "conj", "cop", "csubj", "dep", "det", "discourse", "dislocated", "expl", "fixed", "flat", "goeswith", "iobj", "list", "mark", "nmod", "nsubj", "nummod", "obj", "obl", "orphan", "parataxis", "punct", "reparandum", "root", "vocative", "xcomp" ])
    corpus.add_layer_meta('misc', 'seq', base='tokens', data='string')

    return corpus

def read_conllu_str(s : str, db: str=None, include_form: bool=False) -> teanga.Corpus:
    """Read a CoNLL-U string and return a Teanga Corpus object.
    
    Args:

    s: str
        The CoNLL-U string to read.
    db: str
        The DB location to use of the Teanga corpus
    include_form: bool
        Also include a form layer
    """
    corpus = conllu_corpus(db, include_form)

    read_conllu(StringIO(s), corpus)

    return corpus


def read_conllu_file(file : str, db: str=None, include_form : bool=False) -> teanga.Corpus:
    """Read a CoNLL-U file and return a Teanga Corpus object.
    
    Args:

    file: str
        The CoNLL-U filename to read.
    db: str
        The DB location to use of the Teanga corpus
    include_form: bool
        Also include a form layer
    """
    corpus = conllu_corpus(db, include_form)

    read_conllu(open(file), corpus)

    return corpus

def read_conllu(obj : TextIO, corpus : teanga.Corpus):
    """Read a CoNLL-U object and return a Teanga Corpus object.
    
    Args:
    obj: TextIO
        The CoNLL-U object to read.
    corpus: teanga.Corpus
        The Teanga corpus to populate
    """
    for sentence in parse_incr(obj):
        if "text" in sentence.metadata:
            text = sentence.metadata["text"]
        else:
            text = " ".join(get_forms(sentence))
        doc = corpus.add_doc(text)
        for key, value in sentence.metadata.items():
            if key == "text":
                continue
            doc.metadata[key] = value
        try:
            doc.tokens = dupe_spans(find_spans(get_forms(sentence), text), sentence)
            if "form" in corpus.meta:
                doc.form = [token['form'] for token in sentence]
            doc.lemma = [token['lemma'] for token in sentence]
            if all(token['upos'] is not None for token in sentence):
                doc.upos = [token['upos'] for token in sentence]
            if all(token['xpos'] is not None for token in sentence):
                doc.xpos = [token['xpos'] for token in sentence]
            if any(token['feats'] is not None for token in sentence):
                doc.feats = [map_feats(token['feats']) for token in sentence]
            if (all(token['head'] is not None for token in sentence) and
                all(token['deprel'] is not None for token in sentence)):
                doc.dep = [[token['head'], token['deprel']] for token in sentence]
            if all(token['misc'] is not None for token in sentence):
                doc.misc = [map_feats(token['misc']) for token in sentence]
        except teanga.utils.TokenizationMismatch as e:
            print(f"Error: {e}")
            print(f"Skipping sentence.")
            continue

    return corpus

def get_forms(sentence : list) -> list:
    """Get the forms of all tokens in a sentence."""
    forms = []
    sent_iter = iter(sentence)
    while True:
        try:
            token = next(sent_iter)
        except StopIteration:
            break
        forms.append(token['form'])
        if isinstance(token["id"], tuple):
            start = int(token["id"][0])
            end = int(token["id"][2])
            diff = end - start
            for i in range(diff + 1):
                try:
                    token = next(sent_iter)
                except StopIteration:
                    break

    return forms

def dupe_spans(spans : list, sentence : list) -> list:
    """Duplicate the spans in a sentence, e.g., if the text is 'della' and
    there are three tokens with ids, `[1-2, 1, 2]`, then the span for token
    1 will be duplicated 3 times"""
    new_spans = []
    sent_iter = iter(sentence)
    span_iter = iter(spans)
    while True:
        try:
            token = next(sent_iter)
            span = next(span_iter)
        except StopIteration:
            break
        new_spans.append(span)
        if isinstance(token["id"], tuple):
            start = int(token["id"][0])
            end = int(token["id"][2])
            diff = end - start
            for i in range(diff + 1):
                try:
                    token = next(sent_iter)
                    new_spans.append(span)
                except StopIteration:
                    break
    return new_spans

def map_feats(d: dict):
    if isinstance(d, str):
        return d
    if d is None:
        return ""
    else:
        return "|".join(f"{k}={v}" for k, v in d.items())

