// Purpose: Rust implementation of the TeangaDB Python module.
// Author: John P. McCrae
// License: Apache 2.0
use pyo3::prelude::*;
use std::collections::HashMap;

#[pyclass]
#[derive(Debug,Clone)]
/// A corpus object
struct Corpus {
    #[pyo3(get)]
    meta: HashMap<String, LayerDesc>,
    #[pyo3(get)]
    order: Vec<String>,
    path: String
}

#[pyclass]
#[derive(Debug,Clone)]
/// A layer description
struct LayerDesc {
    #[pyo3(get)]
    name: String,
    #[pyo3(get)]
    type_: LayerType,
    #[pyo3(get)]
    on: String,
    #[pyo3(get)]
    data: Option<String>,
    #[pyo3(get)]
    link_types: Option<Vec<String>>,
    #[pyo3(get)]
    target: Option<String>,
    #[pyo3(get)]
    default: Option<Vec<String>>
}

#[pymethods]
impl Corpus {
    #[new]
    /// Create a new corpus
    fn new(path : String) -> Corpus {
        Corpus {
            meta: HashMap::new(),
            order: Vec::new(),
            path
        }
    }

    /// Add a layer to the corpus
    /// # Arguments
    /// * `name` - The name of the layer
    /// * `type_` - The type of the layer
    /// * `on` - The layer that this layer is on
    /// * `data` - The data file for this layer
    /// * `link_types` - The link types for this layer
    /// * `target` - The target layer for this layer
    /// * `default` - The default values for this layer
    fn add_layer_meta(&mut self, name: String, type_: LayerType, 
        on: String, data: Option<String>, link_types: Option<Vec<String>>, 
        target: Option<String>, default: Option<Vec<String>>) -> PyResult<()> {
        if self.meta.contains_key(&name) {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                format!("Layer {} already exists", name)))
        }
        self.meta.insert(name.clone(), LayerDesc {
            name,
            type_,
            on,
            data,
            link_types,
            target,
            default
        });
        Ok(())
    }
}

#[allow(non_camel_case_types)]
#[derive(Debug,Clone)]
enum LayerType {
    characters,
    seq,
    div,
    element,
    span
}

impl FromPyObject<'_> for LayerType {
    fn extract(ob: &PyAny) -> PyResult<Self> {
        match ob.extract::<String>()?.as_str() {
            "characters" => Ok(LayerType::characters),
            "seq" => Ok(LayerType::seq),
            "div" => Ok(LayerType::div),
            "element" => Ok(LayerType::element),
            "span" => Ok(LayerType::span),
            _ => Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                format!("Unknown layer type {}", ob.extract::<String>()?)))
        }
    }
}

impl IntoPy<PyObject> for LayerType {
    fn into_py(self, py: Python) -> PyObject {
        match self {
            LayerType::characters => "characters".into_py(py),
            LayerType::seq => "seq".into_py(py),
            LayerType::div => "div".into_py(py),
            LayerType::element => "element".into_py(py),
            LayerType::span => "span".into_py(py)
        }
    }
}

/// A Python module implemented in Rust.
#[pymodule]
#[pyo3(name="teangadb")]
fn teangadb(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<Corpus>()?;
    Ok(())
}
