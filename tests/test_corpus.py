import teanga
import yaml

def test_yaml_conv_1():
    c = teanga.Corpus()
    c.add_layer_meta("en", layer_type="characters")
    c.add_layer_meta("de", layer_type="characters")
    c.add_layer_meta("en_tokens", layer_type="span", base="en")
    c.add_layer_meta("de_tokens", layer_type="span", base="de")
    c.add_layer_meta("align", layer_type="element", base="en_tokens", 
                     target="de_tokens", data="link")
    doc = c.add_doc(en="Hello", de="Guten Tag")
    doc["en_tokens"] = [[0,5]]
    doc["de_tokens"] = [[0,5],[6,9]]
    doc["align"] = [[0,0],[0,1]]

    yaml ="""_meta:
    align:
        type: element
        base: en_tokens
        data: link
        target: de_tokens
    de:
        type: characters
    de_tokens:
        type: span
        base: de
    en:
        type: characters
    en_tokens:
        type: span
        base: en
cBbB:
    en: Hello
    de: Guten Tag
    en_tokens: [[0, 5]]
    de_tokens: [[0, 5], [6, 9]]
    align: [[0, 0], [0, 1]]
"""
    assert c.to_yaml_str() == yaml


def test_readme_example_1():
    example = """_meta:
    text:
        type: characters
    tokens:
        type: span
        base: text
    upos:
        type: seq
        base: tokens
        data: ["ADJ", ... "X"]
    document:
        type: div
        base: text
        default: [[0]]
    author:
        type: element
        base: document
        data: string
VC90:
    text: "Teanga2 data model"
    tokens: [[0,7], [8,12], [13,18]]
    upos: ["PROPN", "NOUN", "NOUN"]
    author: [[0, "John P. McCrae"], [0, "Somebody Else"]]"""
    teanga.read_yaml_str(example)
 
def test_readme_example_2():
    example = """_meta:
  text:
    type: characters
  words:
    type: span
    base: text
  upos:
    type: seq
    base: words
    data: ["DET","NOUN","VERB"]
  dep:
    type: seq
    base: words
    data: link
    link_types: ["root","nsubj","dobj"]
    target: dep
k0Jl:
  text: "this is an example"
  words: [[0,4], [5,7], [8,10], [11,17]]
  upos: ["DET", "VERB", "DET", "NOUN"]
  dep: [[1, "nsubj"], [1, "root"], [2, "det"], [1, "dobj"]]"""
    teanga.read_yaml_str(example)

def test_readme_example_3():
    example = """_meta:
    _uri: https://jmccrae.github.io/teanga2/meta/basic.yaml
    author:
        base: document
        data: string
        _uri: https://jmccrae.github.io/teanga2/props/author.html
jjVi:
    _uri: corpus/doc1.yaml"""
    teanga.read_yaml_str(example)


def test_ud():
    example = """_meta:
  text:
    type: characters
  words:
    type: span
    base: text
  rel:
    type: seq
    base: words
    data: link
    link_types: ["root","nsubj","dobj"]
k0Jl:
    text: "this is an example"
    words: [[0,4], [5,7], [8,10], [11,17]]
    rel: [[1, "nsubj"], [1, "root"], [2, "det"], [1, "dobj"]]"""
    corpus = teanga.read_yaml_str(example)
    for id, doc in corpus.docs:
        for layer in doc.layers:
            print(doc[layer].data)

def test_open_url():
    corpus = teanga.from_url("https://teanga.io/examples/ex1.yaml")
    assert len(corpus.docs) == 1
    assert corpus.docs[0][1].text.text[0] == "Teanga2 data model"

    def test_default_layers():
    corpus = teanga.Corpus()
    corpus.add_layer_meta("text", layer_type="characters")
    corpus.add_layer_meta("document", layer_type="div", base="text", default=[0])
    doc = corpus.add_doc(text="Hello world")
    yaml_str = corpus.to_yaml_str()
    obj = yaml.load(yaml_str, Loader=yaml.FullLoader)
    assert obj["_meta"]["document"]["default"] == [0]
    print(obj.keys())
    assert "docuemnt" not in obj["bAiu"]