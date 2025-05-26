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
