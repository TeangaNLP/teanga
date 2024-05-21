import rdflib
import teanga.rdf as rdf
import teanga

def test_teanga_corpus_to_rdf_1():
    corpus = teanga.Corpus()
    corpus.add_layer_meta("text", layer_type="characters")
    corpus.add_doc(text="Hello")
    graph = rdflib.Graph()
    rdf.teanga_corpus_to_rdf(graph, corpus, "http://example.org/corpus")
    assert len(graph) == 4

def test_teanga_corpus_to_rdf_2():
    corpus = teanga.Corpus()
    corpus.add_layer_meta("text", layer_type="characters")
    corpus.add_layer_meta("words", layer_type="span", base="text")
    doc = corpus.add_doc("Hello there! Goodbye!")
    doc.words = [(0, 5), (6, 12), (14, 22)]
    print(doc.layers)
    graph = rdflib.Graph()
    rdf.teanga_corpus_to_rdf(graph, corpus, "http://example.org/corpus")
    for s, p, o in graph:
        print(s, p, o)
    assert ((rdflib.URIRef("http://example.org/corpus#xQAb"), 
             rdflib.URIRef("http://teanga.io/teanga#text"), 
             rdflib.Literal("Hello there! Goodbye!")) in graph)
    assert ((rdflib.URIRef("http://example.org/corpus#xQAb"),
             rdflib.URIRef("http://teanga.io/teanga#words"),
             rdflib.URIRef("http://example.org/corpus#xQAb&layer=words&idx=0")) in graph)
    assert ((rdflib.URIRef("http://example.org/corpus#xQAb&layer=words&idx=0"),
             rdflib.URIRef("http://teanga.io/teanga#idx"),
             rdflib.Literal(0)) in graph)
    assert ((rdflib.URIRef("http://example.org/corpus#xQAb&layer=words&idx=0"),
             rdflib.URIRef("http://teanga.io/teanga#ref"),
             rdflib.URIRef("http://example.org/corpus#xQAb&layer=text&chars=0,5")) in graph)
    
