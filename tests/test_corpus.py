import teanga
import yaml
import tempfile

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
    align: [[0, 0], [0, 1]]
    de: Guten Tag
    de_tokens: [[0, 5], [6, 9]]
    en: Hello
    en_tokens: [[0, 5]]
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

#def test_readme_example_3():
#    example = """_meta:
#    _uri: https://jmccrae.github.io/teanga2/meta/basic.yaml
#    author:
#        base: document
#        data: string
#        _uri: https://jmccrae.github.io/teanga2/props/author.html
#jjVi:
#    _uri: corpus/doc1.yaml"""
#    teanga.read_yaml_str(example)


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
    for doc in corpus.docs:
        for layer in doc.layers:
            print(doc[layer].data)

def test_open_url():
    corpus = teanga.from_url("https://teanga.io/examples/ex1.yaml")
    corpus_docs = list(corpus.docs)
    assert len(corpus_docs) == 1
    assert corpus_docs[0].text.text[0] == "Teanga2 data model"

def test_default_layers():
    corpus = teanga.Corpus()
    corpus.add_layer_meta("text", layer_type="characters")
    corpus.add_layer_meta("document", layer_type="div", base="text", default=[0])
    doc = corpus.add_doc(text="Hello world")
    yaml_str = corpus.to_yaml_str()
    obj = yaml.load(yaml_str, Loader=yaml.FullLoader)
    assert obj["_meta"]["document"]["default"] == [0]
    assert "docuemnt" not in obj["bAiu"]

def test_sentences():
    corpus = teanga.Corpus()
    corpus.add_layer_meta("text", layer_type="characters")
    corpus.add_layer_meta("words", layer_type="span", base="text")
    corpus.add_layer_meta("sentences", layer_type="div", base="words")
    doc = corpus.add_doc(text="Hello world. This is a test.")
    doc.words = [[0, 5], [6, 11], [11, 12], [13, 15], [16, 16], [17, 20]]
    doc.sentences = [0, 3]
    sentences = doc.sentences.text
    assert sentences[0] == "Hello world. "
    assert sentences[1] == "This is a test."

def test_issue_14():
    corpus = teanga.Corpus()
    corpus.add_layer_meta("text", layer_type="characters")
    corpus.add_layer_meta("words", layer_type="span", base="text")
    corpus.add_layer_meta("upos", layer_type="seq", base="words", data=["DET","NOUN","VERB"])
    doc = corpus.add_doc(text="This is an example")
    doc.words = [[0,4], [5,7], [8,10], [11,17]]
    doc.upos = [["DET"], ["VERB"], ["DET"], ["NOUN"]]
    assert(doc.upos.data == ["DET", "VERB", "DET", "NOUN"])

def test_long_text_yaml_serialize():
    corpus = teanga.Corpus()
    corpus.add_layer_meta("text", layer_type="characters")
    doc = corpus.add_doc(text="YAML see History and name) is a human-readable data serialization language. It is commonly used for configuration files and in applications where data is being stored or transmitted. YAML targets many of the same communications applications as Extensible Markup Language (XML) but has a minimal syntax that intentionally differs from Standard Generalized Markup Language (SGML). It uses Python-style indentation to indicate nesting and does not require quotes around most string values (it also supports JSON style and mixed in the same file).")
    yaml_str = corpus.to_yaml_str()
    print(yaml_str)
    corpus2 = teanga.read_yaml_str(yaml_str)
    
def test_write_meta():
    corpus = teanga.Corpus()
    corpus.add_layer_meta("text", layer_type="characters")
    doc = corpus.add_doc(text="Hello world")
    doc.metadata["author"] = "John P. McCrae"
    yaml_str = corpus.to_yaml_str()
    print(yaml_str)
    assert(yaml_str == """_meta:
    text:
        type: characters
bAiu:
    text: Hello world
    _author: John P. McCrae
""")

def test_cuac():
    try:
        import teangadb
    except ImportError:
        print("Skipping cuac test as teangadb not available")
        return
    corpus = teanga.Corpus()
    corpus.add_layer_meta("text")
    doc = corpus.add_doc("This is a document.")
    # create a temporary cuac file
    temp_file = tempfile.NamedTemporaryFile(delete=True)
    corpus.to_cuac(temp_file.name)
    corpus = teanga.read_cuac(temp_file.name)

def test_teanga_id_2():
    corpus = teanga.Corpus()
    corpus.add_layer_meta("text", layer_type="characters")
    corpus.add_layer_meta("fileid", layer_type="characters")
    doc = corpus.add_doc(text="This is a document.", fileid="doc1")
    assert doc.id == "fexV"

def test_subset():
    corpus = teanga.Corpus()
    corpus.add_layer_meta("text", layer_type="characters")
    doc1 = corpus.add_doc(text="This is a document.")
    doc2 = corpus.add_doc(text="This is another document.")
    subset = corpus.subset([doc1.id])
    assert len(list(subset.docs)) == 1
    assert subset[0].text.raw == "This is a document."
    assert subset[0].id == doc1.id
    subset = corpus.subset([0])
    assert len(list(subset.docs)) == 1
    assert subset[0].text.raw == "This is a document."
    subset = corpus.subset(range(1,2))
    assert len(list(subset.docs)) == 1
    assert subset[0].text.raw == "This is another document."

def test_int_ids():
    example = """_meta:
    annot_utt:
        type: characters
    locale:
        type: characters
    slots:
        type: seq
        base: tokens
        data: ["B-date", "B-audiobook_name", "B-change_amount", "B-business_type", "B-music_genre", "B-radio_name", "B-color_type", "B-alarm_type", "B-game_type", "B-transport_descriptor", "B-weather_descriptor", "B-artist_name", "
B-transport_name", "B-event_name", "B-media_type", "B-cooking_type", "B-order_type", "B-list_name", "B-podcast_name", "B-time_zone", "B-business_name", "B-currency_name", "B-device_type", "B-audiobook_author", "B-transport_type", "
B-drink_type", "B-podcast_descriptor", "B-music_album", "B-timeofday", "B-music_descriptor", "B-coffee_type", "B-email_folder", "B-person", "B-movie_name", "B-email_address", "B-definition_word", "B-app_name", "B-transport_agency",
 "B-relation", "B-news_topic", "B-song_name", "B-game_name", "B-joke_type", "B-playlist_name", "B-house_place", "B-time", "B-sport_type", "B-food_type", "B-general_frequency", "B-ingredient", "B-player_setting", "B-meal_type", "B-m
ovie_type", "B-personal_info", "B-place_name", "I-date", "I-audiobook_name", "I-change_amount", "I-business_type", "I-music_genre", "I-radio_name", "I-color_type", "I-alarm_type", "I-game_type", "I-transport_descriptor", "I-weather
_descriptor", "I-artist_name", "I-transport_name", "I-event_name", "I-media_type", "I-cooking_type", "I-order_type", "I-list_name", "I-podcast_name", "I-time_zone", "I-business_name", "I-currency_name", "I-device_type", "I-audioboo
k_author", "I-transport_type", "I-drink_type", "I-podcast_descriptor", "I-music_album", "I-timeofday", "I-music_descriptor", "I-coffee_type", "I-email_folder", "I-person", "I-movie_name", "I-email_address", "I-definition_word", "I-
app_name", "I-transport_agency", "I-relation", "I-news_topic", "I-song_name", "I-game_name", "I-joke_type", "I-playlist_name", "I-house_place", "I-time", "I-sport_type", "I-food_type", "I-general_frequency", "I-ingredient", "I-play
er_setting", "I-meal_type", "I-movie_type", "I-personal_info", "I-place_name", "O"]
    text:
        type: characters
    tokens:
        type: span
        base: text
"+011":
    annot_utt: "[music_genre : \u0B9F\u0BC6\u0B95\u0BCD\u0BA9\u0BCB] \u0B87\u0B9A\u0BC8\u0BAF\u0BC8 \u0BB5\u0BBE\u0B9A\u0BBF\u0B95\u0BCD\u0B95\u0BB5\u0BC1\u0BAE\u0BCD"
    locale: ta-IN
    slots: ["B-music_genre", "O", "O"]
    text: "\u0B9F\u0BC6\u0B95\u0BCD\u0BA9\u0BCB \u0B87\u0B9A\u0BC8\u0BAF\u0BC8 \u0BB5\u0BBE\u0B9A\u0BBF\u0B95\u0BCD\u0B95\u0BB5\u0BC1\u0BAE\u0BCD"
    tokens: [[0, 6], [7, 12], [13, 24]]
"0x8e":
    annot_utt: "\u062C\u0647\u0632 \u0627\u0644\u0642\u0627\u0626\u0645\u0629"
    locale: ar-SA
    slots: ["O", "O"]
    text: "\u062C\u0647\u0632 \u0627\u0644\u0642\u0627\u0626\u0645\u0629"
    tokens: [[0, 3], [4, 11]]"""
    corpus = teanga.read_yaml_str(example)
    string = corpus.to_yaml_str()
    print(string)
    corpus2 = teanga.read_yaml_str(string)

# Removed due to speed issues in downloading remote resource
#def test_download():
#    corpus = teanga.download("qc")
