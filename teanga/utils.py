from base64 import b64encode
from hashlib import sha256


def teanga_id_for_doc(ids, *args, **kwargs):
    """Return the Teanga ID for a document.

    Parameters:
        ids: str
            The IDs already generated and not to be repeated

        This works as the add_doc method, but returns the Teanga ID for the document.
        It is not necessary to call this method directly but instead you can use it
        via the Corpus class.

    Examples:
        >>> teanga_id_for_doc(set(), text="This is a document.")
        'Kjco'
        >>> teanga_id_for_doc(set(), en="This is a document.", nl="Dit is een document.")
        'Nnrd'
    """
    text = ""
    if len(kwargs) == 0:
        raise Exception("No arguments given.")
    for key in sorted(kwargs.keys()):
        text += key
        text += "\x00"
        text += kwargs[key]
        text += "\x00"
    code = b64encode(sha256(text.encode("utf-8")).digest()).decode("utf-8")
    n = 4
    while code[:n] in ids and n < len(code):
        n += 1
    return code[:n]


