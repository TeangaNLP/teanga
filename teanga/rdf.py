import rdflib
from rdflib import RDF

TEANGA_BUILT_INS = set(["text", "words", "sentences", "paragraphs"])

def teanga_corpus_to_rdf(graph, corpus, url: str):
    """
    Convert a Teanga Corpus to RDF using the Teanga Namespace. The corpus
    is added to the current graph

    Parameters
    ----------

    graph : rdflib.Graph
    url : str
        The URL of the Teanga Corpus
    """
    teanga = rdflib.Namespace("http://teanga.io/teanga#")
    graph.add((rdflib.URIRef(url), RDF.type, teanga.Corpus))
    for document in corpus.get_docs():
        doc_url = url + "#" + document.id
        graph.add((rdflib.URIRef(doc_url), RDF.type, teanga.Document))
        graph.add((rdflib.URIRef(url), teanga.document, rdflib.URIRef(doc_url)))
        for layer in document.layers:
            layer_desc = corpus.get_meta()[layer]
            if "uri" in layer_desc.meta:
                layer_url = rdflib.URIRef(layer_desc.meta["uri"])
            elif layer in TEANGA_BUILT_INS:
                layer_url = teanga[layer]
            else:
                layer_url = url + "#" + layer
            if layer_desc.layer_type == "characters":
                graph.add((rdflib.URIRef(doc_url), 
                           layer_url,
                           rdflib.Literal(document.get_layer(layer).text(document))))
            elif layer_desc.layer_type == "span":
                for idx, data in enumerate(document.get_layer(layer).raw()):
                    node_url = (url + "#" + document.id + "&layer=" 
                                + layer + "&idx=" + str(idx))
                    node = rdflib.URIRef(node_url)
                    graph.add((rdflib.URIRef(doc_url), layer_url, node))
                    graph.add((node, teanga.idx, rdflib.Literal(idx)))
                    write_teanga_data(graph, node, data, teanga, 
                                      layer_desc.data, layer_desc.values)

    return graph
    
def write_teanga_data(graph, node, data, teanga, layer_desc):
    data_type = layer_desc.layer_type
    if data_type is None:
        return
    elif data_type == "string":
        graph.add((node, teanga.data, rdflib.Literal(data)))
    elif data_type == "link":
        # TODO:
        return
        
    

    
