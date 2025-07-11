import teanga

def test_indexes1():
    example = """_meta:
  text:
    type: characters
  words:
    type: span
    base: text
  ner:
    type: span
    base: words
    data: ["LOC", "PER", "ORG"]
54kk:
  text: "John Doe lives in New York."
  words: [[0, 4], [5, 8], [9, 14], [15, 17], [18, 22], [23, 26]]
  ner: [[0, 2, "PER"], [4, 6, LOC]]"""
    corpus = teanga.read_yaml_str(example)
    for doc in corpus.docs:
        print(doc.words.indexes("text"))
        print(doc.ner.indexes("text"))
        assert doc.ner.text == ["John Doe", "New York"]

def test_add_metadata():
    corpus = teanga.text_corpus()
    doc = corpus.add_doc("test")
    doc._author = "me"
    print(doc._author)

def test_update_character_layer():
    corpus = teanga.text_corpus()
    doc = corpus.add_doc(text="This is a document.")
    assert doc.id == "Kjco"
    doc.text = "New text"
    assert doc.id == "/C+4"

def test_str_character_layer_duality():
    corpus = teanga.text_corpus()
    doc = corpus.add_doc(text="This is a document.")
    # Character layers are equal to strings
    assert doc.text == "This is a document."
    # Can be set as strings
    doc.text = "Changed text"
    # Have length as strings
    assert len(doc.text) == 12
    # Can be indexed like strings
    assert doc.text[0] == "C"
    # Can be sliced like strings
    assert doc.text[0:5] == "Chang"
    # But are not strings
    assert type(doc.text) == teanga.document.CharacterLayer

def test_list_other_layer_duality():
    corpus = teanga.text_corpus()
    doc = corpus.add_doc(text="This is a document.")
    # Other layers can be set as lists
    doc.tokens = [[0, 4], [5, 7], [8, 9], [10, 19]]
    # Are equal to lists
    assert doc.tokens == [[0, 4], [5, 7], [8, 9], [10, 19]]
    # Can be indexed like lists
    assert doc.tokens[0] == [0, 4]
    # Have length like lists
    assert len(doc.tokens) == 4
    # But are not lists
    assert type(doc.tokens) == teanga.document.SpanLayer
    
