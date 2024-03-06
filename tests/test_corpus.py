def test_yaml_conv_1():
    import teanga
    c = teanga.Corpus()
    c.add_layer_meta("en", layer_type="characters")
    c.add_layer_meta("de", layer_type="characters")
    c.add_layer_meta("en_tokens", layer_type="span", on="en")
    c.add_layer_meta("de_tokens", layer_type="span", on="de")
    c.add_layer_meta("align", layer_type="element", on="en_tokens", 
                     target="de_tokens", data="link")
    doc = c.add_doc(en="Hello", de="Guten Tag")
    doc.add_layer("en_tokens", [[0,5]])
    doc.add_layer("de_tokens", [[0,5],[6,9]])
    doc.add_layer("align", [[0,0],[0,1]])

    yaml ="""_meta:
    align:
        type: element
        on: en_tokens
        data: link
        target: de_tokens
    de:
        type: characters
    de_tokens:
        type: span
        on: de
    en:
        type: characters
    en_tokens:
        type: span
        on: en
cBbB:
    en: Hello
    de: Guten Tag
    en_tokens: [[0, 5]]
    de_tokens: [[0, 5], [6, 9]]
    align: [[0, 0], [0, 1]]
"""
    assert c.to_yaml_str() == yaml
