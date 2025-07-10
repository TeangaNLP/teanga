import pytest
import teanga
import teanga.spacy

def test_multiline_spacy():
    spacy = pytest.importorskip("spacy")
    corpus = teanga.text_corpus()
    corpus.add_doc("This is a test.\n\nThis is a second sentence.")
    service = teanga.spacy.SpaCy("en_core_web_sm")
    service.setup()
    corpus.apply(service)

    print(corpus[0].tokens)
    assert corpus[0].tokens.raw == [[0, 4], [5, 7], [8, 9], [10, 14], [14,15], [17, 21], [22, 24], [25, 26], [27, 33], [34, 42], [42, 43]]

