import yaml
from typing import Any, Iterator, List, Tuple
from teanga.utils import teanga_id_for_doc
from teanga.layer_desc import _layer_desc_from_kwargs

class CorpusStream:
    """A stream of documents from a YAML file.

    Args:
        buf: A path to a YAML file or a buffer.

    Examples:
        >>> import io
        >>> yaml_str = '''_meta:
        ...   text:
        ...     type: characters
        ... Kjco:
        ...   text: This is a document.'''
        >>> stream = CorpusStream(io.StringIO(yaml_str))
        >>> next(stream)
        Document('Kjco', {'text': CharacterLayer('This is a document.')})
    """
    def __init__(self, buf):
        self.stream = read_obj(yaml.parse(buf))
        key, value = next(self.stream)
        if key != "_meta":
            raise ValueError(f"Expected _meta, got {key}")
        self.meta = {key: _layer_desc_from_kwargs(v)
              for key, v in value.items()
              if not key.startswith("_")}
        self.doc_ids = []
    
    def __next__(self):
        from teanga import Document
        key, value = next(self.stream)
        while key.startswith("_"):
            if key == "_order":
                self.doc_ids = value
            key, value = next(self.stream)
        doc = Document(self.meta, id=key, **value)
        text_fields = {
                field: value for field, value in value.items()
                if isinstance(value, str)
        }
        tid = teanga_id_for_doc(self.doc_ids, **text_fields)
        self.doc_ids.append(key)
        if tid != key:
            raise Exception("Invalid document id: " + key +
                            " should be " + tid)
        return doc

    def __iter__(self):
        return self

def read_obj(stream) -> Iterator[Tuple[str, Any]]:
    """Read an object from a YAML stream.

    Args:
        stream: A YAML stream.

    Examples:
        >>> stream = yaml.parse("a: 1\\nb: 2")
        >>> list(read_obj(stream))
        [('a', 1), ('b', 2)]
    """
    event = next(stream)
    while isinstance(event, yaml.StreamStartEvent) or isinstance(event, yaml.DocumentStartEvent):
        event = next(stream)
    if isinstance(event, yaml.MappingStartEvent):
        while True:
            event = next(stream)
            if isinstance(event, yaml.MappingEndEvent) or event is None:
                break
            else:
                key = yaml.safe_load(event.value)
                value = read_any(stream)
                yield key, value
        else:
            raise ValueError(f"Expected mapping, got {event}")

def read_any(stream) -> Any:
    """Read any value from a YAML stream.

    Args:
        stream: A YAML stream.

    Examples:
        >>> stream = yaml.parse("a: 1")
        >>> read_any(stream)
        {'a': 1}
    """
    event = next(stream)
    while isinstance(event, yaml.StreamStartEvent) or isinstance(event, yaml.DocumentStartEvent):
        event = next(stream)
    if isinstance(event, yaml.ScalarEvent):
        return yaml.safe_load(event.value)
    elif isinstance(event, yaml.SequenceStartEvent):
        return read_seq(stream)
    elif isinstance(event, yaml.MappingStartEvent):
        return dict(read_obj2(stream))
    else:
        raise ValueError(f"Expected scalar, sequence, or mapping, got {event}")

def read_seq(stream) -> List[Any]:
    """Read a sequence of values from a YAML stream. Assumes the `SequenceStartEvent` has already been read.

    Args:
        stream: A YAML stream.

    Examples:
        >>> stream = yaml.parse("- 1\\n- 2")
        >>> next(stream)
        StreamStartEvent()
        >>> next(stream)
        DocumentStartEvent()
        >>> next(stream)
        SequenceStartEvent(anchor=None, tag=None, implicit=True)
        >>> read_seq(stream)
        [1, 2]
    """
    event = next(stream)
    elems = []
    while not isinstance(event, yaml.SequenceEndEvent):
        if isinstance(event, yaml.MappingStartEvent):
            elems.append(dict(read_obj2(stream)))
        elif isinstance(event, yaml.ScalarEvent):
            elems.append(yaml.safe_load(event.value))
        elif isinstance(event, yaml.SequenceStartEvent):
            elems.append(read_seq(stream))
        else:
            raise ValueError(f"Expected mapping, scalar, or sequence, got {event}")
        event = next(stream)
    return elems


def read_obj2(stream) -> Iterator[Tuple[str, Any]]:
    """Read an object from a YAML stream. The MappingStartEvent has already been read.

    Args:
        stream: A YAML stream.
    """
    for _ in range(100):
        event = next(stream)
        if isinstance(event, yaml.MappingEndEvent) or event is None:
            break
        else:
            key = yaml.safe_load(event.value)
            value = read_any(stream)
            yield key, value


