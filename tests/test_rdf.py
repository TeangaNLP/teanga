import rdflib
import teanga.rdf as rdf
import teanga

def test_teanga_corpus_to_rdf():
    corpus = teanga.Corpus()
    corpus.add_layer_meta("text", layer_type="characters")
    corpus.add_doc(text="Hello")
    graph = rdflib.Graph()
    rdf.teanga_corpus_to_rdf(graph, corpus, "http://example.org/corpus")
    assert len(graph) == 4
