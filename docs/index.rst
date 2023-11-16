Teanga2 - A Natural Language Processing Toolkit
===============================================
Teanga2 is a data model and framework for the development of natural language
processing tools. The core of the framework is a data model that is used to
represent linguistic data. The data model is based on a model of layers of
stand-off annotation, where each layer is a set of annotations that refer to
other layers or directly to the text. The data model is implemented in Python
and is used to represent linguistic data in memory. The framework provides
functionality for reading and writing data in the data model from and to
different formats, including YAML and JSON. The framework also provides
a database backend for storing and querying data in the data model. This
is implemented in Rust, with the help of the `sled` library.

.. _sled: https://sled.rs/

Example usage
-------------

This is an example of creating and using a corpus in Teanga2:

.. code-block:: python
    
    from teanga import Corpus
    corpus = Corpus()
    corpus.add_document("This is a document")


Modules
=======

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
