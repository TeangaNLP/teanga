#!/usr/bin/env python3
#

""" Convert CoNLL-U file(s) to YAML. """

import sys
import typing
import logging

import conllu
import yaml

# The name prefix for record keys in the output document
OUTPUT_RECORD_NAME_PREFIX = 'sent.'

# Placeholder value when a feature doesn't apply to a specific token:
FEATURE_PLACEHOLDER_VALUE = None
#FEATURE_PLACEHOLDER_VALUE = ""

# The name prefix for feature keys in the output document
FEATURE_NAME_PREFIX = 'feat.'

# Token delimiters to skip (i.e. whitespaces)
TOKEN_DELIMS = set(
    [ ' ', '\t', '\u00A0', '\u1680', '\u2005', '\u202F', '\u3000', '\uFEFF' ])


logger = logging.getLogger(__name__)
#logging.basicConfig(encoding='utf-8', level=logging.DEBUG)
logging.basicConfig(encoding='utf-8', level=logging.WARNING)


def next_span(start_offset: int, sentence: str, token: str) \
        -> typing.Tuple[typing.List[int], int]:
    """ Create the next token span
    Arguments:
        start_offset: The current sentence offset.
        sentence: The sentence text.
        token: The current token.
    Returns:
        (tuple) The span for this token,
        (int) The next starting offset.
    """

    end_offset = start_offset + len(token)
    # Note: This must be a list, not a tuple, for YAML output
    span = [ start_offset, end_offset ]

    found = sentence[start_offset:end_offset]

    logger.debug('start_offset: %s', start_offset)
    logger.debug('token: %s', token)
    logger.debug('span: %s', span)
    logger.debug('sentence[span]: %s', found)

    # Integrity assertion - Should never happen
    if found != token:
        raise ValueError(f'Token mismatch creating span for [{token}] in: {sentence}')

    # Skip over spaces
    sentence_len = len(sentence)

    while end_offset < sentence_len and sentence[end_offset] in TOKEN_DELIMS:
        logger.debug('skipping space at: i%s', end_offset)
        end_offset += 1

    if end_offset < sentence_len:
        logger.debug('next character: %s  [0x%s]',
            sentence[end_offset], sentence[end_offset].encode("utf-8").hex())

    return (span, end_offset)


def get_token_ids(token) -> typing.Optional[typing.List[int]]:
    """ Extract the id or id range from a token
    Arguments:
        sentence: A token.
    Returns:
        A list of ids.
    """

    tid = token['id']

    # Normal token?
    if isinstance(tid, int):
        return [ tid ]

    # Verify tuple:  (int, '-' | '.', int)
    if len(tid) != 3:
        return None

    if not isinstance(tid[0], int) or not isinstance(tid[2], int):
        return None

    if tid[1] == '-':
        # Multitoken (-)
        return list(range(tid[0], tid[2] + 1))

    if tid[1] == '.':
        # empty (.)
        return [ tid[0] ]

    return None


def process_features(token_idx: int, feats: typing.Dict[str, str],
        token_count: int, feat_lists: typing.Dict[str, typing.List[str]]) \
        -> None:
    """ Process features and save them in token position.
    Arguments:
        token_idx: The array index of this token.
        feats: The input features.
        token_count: The total number of tokens.
        feat_lists: A dictionary of output features.
    """

    for feat_name, feat_value in feats.items():
        # Get (or create) list for named feature
        try:
            feat = feat_lists[feat_name]
        except KeyError:
            feat = [ FEATURE_PLACEHOLDER_VALUE ] * token_count
            feat_lists[feat_name] = feat

        feat[token_idx] = feat_value


def convert_sentence(sentence: typing.Sequence) -> typing.Tuple[str, dict]:
    """ Convert a CoNLL-U parsed sentence to a YAML node.
    Arguments:
        sentence: A sequence of tokens.
    Returns:
        (str) The YAML node key.
        (dict) The YAML node value.
    """

    logger.debug('sentence: %s', sentence)

    token_meta = sentence.metadata

    key = OUTPUT_RECORD_NAME_PREFIX + token_meta['sent_id']
    text = token_meta['text']

    token_count = len(sentence)

    span_list = [ None ] * token_count
    upos_list = [ None ] * token_count
    feat_lists = {}

    id_spans = {}

    span_offset = 0

    for token_idx, token in enumerate(sentence):
        logger.debug('token_idx: %s', token_idx)
        logger.debug('token.items: %s', token.items())

        ids = get_token_ids(token)

        if not ids:
            raise ValueError(f'Unexpect token type: {token}  [{token["id"]}]')

        logger.debug('ids: %s', ids)

        if ids[0] == 0:
            # Root token - use entire span
            span = [ 0, len(text) ]
        elif len(ids) == 1:
            # Normal or empty token - look for existing span
            span = id_spans.get(ids[0], None)
        else:
            span = None

        logger.debug('existing span: %s', span)

        if span:
            # Duplicate to avoid YAML refs
            span = list(span)
        else:
            # If span not already known then get the next
            (span, span_offset) = next_span(span_offset, text, token['form'])

        # Saves span for overlayed tokens
        for tid in ids:
            id_spans[tid] = span

        span_list[token_idx] = span
        upos_list[token_idx] = token['upos']

        # Process optional features
        feats = token['feats']

        if feats:
            process_features(token_idx, feats, token_count, feat_lists)

    # Build output record
    outrec = {
        'text': text,
        'tokens': span_list,
        'upos': upos_list
    }

    # Add values for each feature found in this sentence
    for feat_name, feat_values in feat_lists.items():
        outrec[FEATURE_NAME_PREFIX + feat_name] = feat_values

    return (key, outrec)


def convert(infile: typing.TextIO, outfile: typing.TextIO) -> None:
    """ Convert a CoNLL-U file to YAML
    Arguments:
        infile: The input ".conllu" file handle.
        outfile: The output ".yaml" file handle.
    """

    sentences = conllu.parse_incr(infile)

    outdoc = {}

    for sentence in sentences:
        (key, rec) = convert_sentence(sentence)
        outdoc[key] = rec

    yaml.dump(outdoc, outfile, encoding='utf-8')


def convert_file(inpath: str, outpath: str) -> None:
    """ Convert a CoNLL-U file to YAML
    Arguments:
        inpath: The input ".conllu" filename.
        outpath: The output ".yaml" filename.
    """

    with open(inpath, 'r', encoding="utf-8") as infile:
        with open(outpath, 'w', encoding="utf-8") as outfile:
            convert(infile, outfile)


def convert_all_files(files: typing.List[str]) -> None:
    """ Convert a list of CoNLL-U file(s) to YAML
    Arguments:
        files: The input ".conllu" filenames.
    """

    for inpath in files:
        outpath = inpath

        if outpath[-7:] in ( '.conllu', '.CONLLU' ):
            outpath = outpath[:-7]

        outpath += '.yaml'

        convert_file(inpath, outpath)

#
#

def main():
    """ Run script from command line. """

    if len(sys.argv) < 2:
        print('Usage: ' + sys.argv[0] + ' <conllu-file(s)>', file=sys.stderr)
        sys.exit(1)

    convert_all_files(sys.argv[1:])

if __name__ == '__main__':
    main()
