import teanga

def read_conllu_str(s : str, db: str=None) -> teanga.Corpus:
    """Read a CoNLL-U string and return a Teanga Corpus object.
    
    Args:

    s: str
        The CoNLL-U string to read.
    db: str
        The DB location to use of the Teanga corpus
    """
    corpus = teanga.Corpus(db)

    ### Do all the CoNLL stuff

    return corpus

def read_conllu_file(file : str, db: str=None) -> teanga.Corpus:
    """Read a CoNLL-U file and return a Teanga Corpus object.
    
    Args:

    file: str
        The CoNLL-U file to read.
    db: str
        The DB location to use of the Teanga corpus
    """
    corpus = teanga.Corpus(db)

    ### Do all the CoNLL stuff

    return corpus
