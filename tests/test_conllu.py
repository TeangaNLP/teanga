from teanga import read_yaml_str
from teanga.conllu import read_conllu_str

CONLLU_1 = """
"""

TEANGA_1 = """_meta:
  text:
    type: characters
  tokens:
    base: text
    type: span
  comm:
    base: text
    type: characters
    data: string
  upos:
    data: ["ADJ", "ADP", "ADV", "AUX", "CCONJ", "DET", "INTJ", "NOUN", "NUM", "PART", "PRON", "PROPN", "PUNCT", "SCONJ", "VERB", "X" ]
    base: tokens
    type: seq
OvM2:
  text: _Bhojpuri text_
  tokens: [[0, 7], [8, 9], [10, 20], [21, 24], [25, 26]]
  comm: lokaraṁjana ā sāṁskrtika gīta -
  upos: ["NOUN", "CCONJ", "ADJ", "NOUN", "PUNCT" ]
cN0V:
  text: _Bhojpuri text_
  tokens: [[0, 3], [4, 5], [6, 13], [14, 17], [18, 19]]
  comm: āīṁ ā saparivāra āīṁ .
  upos: ["VERB", "CCONJ", "NOUN", "VERB", "PUNCT" ]"""

CONLLU_2 = """# newdoc id = n01001
# sent_id = n01001011
# text = “While much of the digital transition is unprecedented in 
2	While	while	SCONJ	IN	_	9	mark	9:mark	_
3	much	much	ADJ	JJ	Degree=Pos	9	nsubj	9:nsubj	_
4	of	of	ADP	IN	_	7	case	7:case	_
5	the	the	DET	DT	Definite=Def|PronType=Art	7	det	7:det	_
6	digital	digital	ADJ	JJ	Degree=Pos	7	amod	7:amod	_
7	transition	transition	NOUN	NN	Number=Sing	3	nmod	3:nmod:of	_
8	is	be	AUX	VBZ	Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin	9	cop	9:cop	_
9	unprecedented	unprecedented	ADJ	JJ	Degree=Pos	20	advcl	20:advcl:while	_
10	in	in	ADP	IN	_	13	case	13:case	_
"""

TEANGA_2 = """_meta:
  text:
    type: characters
  tokens:
    base: text
    type: span
  newdoc_id:
    type: string
  sent_id:
    type: characters
  lemma:
    base: tokens
    data: string
  upos:
    base: tokens
    data: ["ADJ", "ADP", "ADV", "AUX", "CCONJ", "DET", "INTJ", "NOUN", "NUM", "PART", "PRON", "PROPN", "PUNCT", "SCONJ", "VERB", "X" ]
  xpos:
    base: tokens
    data: string
  feats:
    base: tokens
    data: string
  head:
    base: tokens
    data: link
  deps:
    base: tokens
    data: string
  misc:
    base: tokens
    data: string
xxxx:
  newdoc_id: n01001
  sent_id: n01001011
  text: “While much of the digital transition is unprecedented in
  tokens: [[0,1], ... ]
  lemma: ["While", "much", "of", "the", "digital", "transition", "be", "unprecedented", "in"]
  upos: ["SCONJ", "ADJ", "ADP", "DET", "ADJ", "NOUN", "AUX", "ADJ", "ADP"]
  xpos: ["IN", "JJ", "IN", "DT", "JJ", "NN", "VBZ", "JJ", "IN"]
  feats: ["_", "Degree=Pos", "_", "Definite=Def|PronType=Art", "Degree=Pos", "Number=Sing", "Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin", "Degree=Pos", "_"]
  head: [9, 9, 7, 7, 7, 3, 9, 20, 13]
  deps: ["mark", "nsubj", "case", "det", "amod", "nmod", "cop", "advcl", "case"]
  misc: ["_", "_", "_", "_", "_", "_", "_", "_", "_"]"""


def test_conllu_1():
    teanga_corpus = read_yaml_str(TEANGA_1)
    conllu_corpus = read_conllu_str(CONLLU_1)
    assert teanga_corpus == conllu_corpus


def test_conllu_2():
    teanga_corpus = read_yaml_str(TEANGA_2)
    conllu_corpus = read_conllu_str(CONLLU_2)
    assert teanga_corpus == conllu_corpus
