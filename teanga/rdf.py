import rdflib
from rdflib import RDF
import teanga

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
            print(layer)
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
            else:
                for idx, data in enumerate(document.get_layer(layer).raw()):
                    base_layer = layer_desc.base
                    base_layer_desc = corpus.get_meta()[base_layer]
                    node_url = _node_url(url, document.id, layer,
                                         layer_desc.layer_type, idx)
                    node = rdflib.URIRef(node_url)
                    graph.add((rdflib.URIRef(doc_url), layer_url, node))
                    graph.add((node, teanga.idx, rdflib.Literal(idx)))
                    if layer_desc.layer_type == "elements":
                        target_url = _node_url(url, document.id, base_layer,
                                               base_layer_desc.layer_type, data[0])
                        data_value = data[1]
                    elif layer_desc.layer_type == "seq":
                        target_url = _node_url(url, document.id, base_layer,
                                               base_layer_desc.layer_type, idx)
                        data_value = data
                    elif layer_desc.layer_type == "span":
                        target_url = _node_url(url, document.id, base_layer,
                                               base_layer_desc.layer_type, data[0], 
                                               data[1])
                        data_value = data[2]
                    elif layer_desc.layer_type == "div":
                        target_url = _node_url(url, document.id, base_layer,
                                               base_layer_desc.layer_type, data[0])
                        data_value = data[1]
                    graph.add((node, teanga.ref, rdflib.URIRef(target_url)))
                    write_teanga_data(graph, node, data_value, teanga, 
                                      layer_desc.data, 
                                      layer_desc.values,
                                      url, document)

    return graph

def _node_url(url: str, doc_id : str, layer: str, 
              layer_type: str, idx: int, end_idx: int = None):
    if layer_type == "characters":
        if end_idx:
            return (url + "#" + doc_id + "&layer=" + layer + 
                    "&char=" + str(idx) + "," + str(end_idx))
        else:
            return url + "#" + doc_id + "&layer=" + layer + "&char=" + str(idx)
    else:
        return url + "#" + doc_id + "&layer=" + layer + "&idx=" + idx
    
def write_teanga_data(graph : rdflib.Graph, 
                      node : rdflib.URIRef, 
                      data, 
                      teanga : rdflib.Namespace, 
                      layer_desc : teanga.corpus.LayerDesc,
                      url : str,
                      document: teanga.Document) -> None:
    data_type = layer_desc.layer_type
    if data_type is None:
        return
    elif data_type == "string":
        graph.add((node, teanga.data, rdflib.Literal(data)))
    elif data_type == "link":
        target_url = _node_url(url, document.id, layer_desc.target,
                               document.get_meta()[layer_desc.target].layer_type,
                               data)

        graph.add((node, teanga.link, rdflib.URIRef(target_url)))
    elif isinstance(data_type, list):
        graph.add((node, teanga.data, rdflib.Literal(data)))
    else:
        raise ValueError("Unknown data type: " + data_type)
