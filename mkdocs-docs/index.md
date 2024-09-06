# <img src="assets/images/teanga-logo.svg"  style="height:50vh;display:block;margin-left:auto;margin-right:auto"/>

# Teanga2 Framework

> **High Performance** • **Easy to Learn** • **Fast to Code** • **Ready for Production**


Teanga2, A Pandas for NLP.  Teanga2 is a layer-based data processing tool designed for efficient handling of common NLP tasks. Think of it as an advanced, specialized version of Pandas specifically for natural language processing. Teanga2 streamlines workflows, facilitates data manipulation capabilities, and simplifies complex NLP operations.


---

## Installation

Follow our comprehensive [Getting Started Guide](tutorials/getting-started.md) to build your first project in minutes.

### from pypi
```bash
pip install teanga2
``` 

### pip from git
```bash
pip install git+https://github.com/teangaNLP/teanga2
```

### manually with pip/poetry
```bash
https://github.com/TeangaNLP/teanga2.git
cd teanga2
# poetry
poetry init
poetry install
# or pip 
pip install .
``` 

## Features:

- 🚀 **Blazing Fast**: Optimized for performance, designed for speed.
- 🧠 **Easy to Learn**: Intuitive, minimalistic syntax that reduces learning curve.
- ⏱️ **Rapid Development**: Write less code, achieve more.

---

## Why Choose Teanga2?

- **High Performance**: Achieve lightning-fast responses with built-in optimizations.
- **Fast to Code**: Focus on building features, not boilerplate.
- **Easy to Use**: Clean and simple API design makes learning a breeze.

---

## Key Information:

| **Feature**            | **Details**                              |
|------------------------|------------------------------------------|
| Test Coverage          | 99%                                      |
| Package Version        | v1.2.0                                   |
| Supported Python Versions | 3.7, 3.8, 3.9, 3.10                      |
| License                | MIT                                      |
| Documentation          | Fully documented with examples           |

---


## Project layout
    ├── docs
    │   ├── conf.py
    │   ├── html
    │   ├── img
    │   ├── index.rst
    │   ├── make.bat
    │   ├── Makefile
    │   ├── modules.rst
    │   └── teanga.rst
    ├── examples
    │   └── tokenizer_service.py
    ├── LICENSE
    ├── mkdocs-docs
    │   ├── assets
    │   ├── explanation.md
    │   ├── how-to-guides.md
    │   ├── index.md
    │   ├── reference
    │   ├── scripts
    │   └── tutorials
    ├── mkdocs.yml
    ├── poetry.lock
    ├── pyproject.toml
    ├── pytest.ini
    ├── README.md
    ├── teanga
    │   ├── corpus.py
    │   ├── document.py
    │   ├── groups.py
    │   ├── __init__.py
    │   ├── layer_desc.py
    │   ├── __pycache__
    │   ├── rdf.py
    │   ├── service.py
    │   ├── transforms.py
    │   └── utils.py
    └── tests
        ├── __init__.py
        ├── test_corpus.py
        └── test_rdf.py
