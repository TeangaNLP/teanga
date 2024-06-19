#!/usr/bin/env python3
#

"""
Generate common YAML metadata using the feature list, available from:

https://github.com/UniversalDependencies/docs-automation/blob/master/valrules/feats.json
"""

import sys
import typing
import json
import yaml

# The static metadata portion
YAML_META: dict = {
    'text': {
        'type': 'characters'
    },

    'tokens': {
        'type': 'span',
        'on': 'text'
    },

    'upos': {
        'type': 'seq',
        'on': 'tokens',
        'data': [
            'ADJ',
            'ADP',
            'ADV',
            'AUX',
            'CCONJ',
            'DET',
            'INTJ',
            'NOUN',
            'NUM',
            'PART',
            'PRON',
            'PROPN',
            'PUNCT',
            'SCONJ',
            'SYM',
            'VERB',
            'X'
        ]
    },

# Author/Document not currently used
#    'document': {
#        'type': 'div',
#        'on': 'text',
#        'value': [ [0] ]
#    },
#
#    'author': {
#        'type': 'element',
#        'on': 'document',
#        'data': 'str'
#    }
}


##
## !!! NOTE: The following must use same values as set in conllu2yaml.py
##

# Placeholder value when a feature doesn't apply to a specific token:
FEATURE_PLACEHOLDER_VALUE = None
#FEATURE_PLACEHOLDER_VALUE = ""

# The name prefix for feature keys in the metadata
FEATURE_NAME_PREFIX = 'feat.'


def generate(infile: typing.TextIO, outfile: typing.TextIO) -> None:
    """ Generate YAML metadata with features JSON input.
    Arguments:
        infile: The input "feats.json" file handle.
        outfile: The output ".yaml" file handle.
    """

    feats_tree = json.load(infile)

    # A dict of features by name with set() values list
    features = {}

    # Process each language
    for lang_code, lang_node in feats_tree['features'].items():
#        print(f'Processing language: {lang_code}')

        # Process each feature
        for feat_name, feature_node in lang_node.items():
#            print(f'  Processing feature: {feat_name}')

            # Skip contexted features (i.e Xxxxxx[xxx])
            if '[' in feat_name:
                continue

            # Find (or create) feature
            try:
                feat_values = features[feat_name]
            except KeyError:
                feat_values = set()
                features[feat_name] = feat_values

            # Add allowed values
            # XXX - Sometimes uvalues used, sometimes lvalues used
            feat_values.update(feature_node['uvalues'])
            feat_values.update(feature_node['lvalues'])

    # Build metadata
    docmeta = YAML_META.copy()

    # Add each feature
    for feat_name, feat_values in features.items():
        # Avoid duplicates by removing any values matching placeholder
        feat_values.discard(FEATURE_PLACEHOLDER_VALUE)

        # Insert metadata entry
        docmeta[FEATURE_NAME_PREFIX + feat_name] = {
            'type': 'seq',
            'on': 'tokens',
            'data': [ FEATURE_PLACEHOLDER_VALUE ] + sorted(feat_values)
        }

    outdoc = { '_meta': docmeta }

    yaml.dump(outdoc, outfile, encoding='utf-8')


def generate_file(inpath: str, outpath: str) -> None:
    """ Generate YAML metadata with features JSON input.
    Arguments:
        inpath: The input "feats.json" filename.
        outpath: The output ".yaml" filename.
    """

    with open(inpath, 'r', encoding="utf-8") as infile:
        with open(outpath, 'w', encoding="utf-8") as outfile:
            generate(infile, outfile)

#
#

def main() -> None:
    """ Run script from command line. """
    if len(sys.argv) < 2:
        print('Usage: ' + sys.argv[0] + ' <feats>.json <meta>.yaml', file=sys.stderr)
        sys.exit(1)

    generate_file(sys.argv[1], sys.argv[2])

if __name__ == '__main__':
    main()
