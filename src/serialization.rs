// Serialization support for Teanga DB
// -----------------------------------------------------------------------------
use serde::de::Visitor;
use crate::{Corpus, LayerDesc, PyLayer};
use std::collections::HashMap;
use serde::Deserializer;
use std::cmp::min;

struct TeangaVisitor(String);

impl<'de> Visitor<'de> for TeangaVisitor {
    type Value = Corpus;

    fn expecting(&self, formatter: &mut std::fmt::Formatter) -> std::fmt::Result {
        formatter.write_str("a string representing a corpus")
    }

    fn visit_map<A>(self, mut map: A) -> Result<Self::Value, A::Error>
        where A: serde::de::MapAccess<'de>
    {
        let mut corpus = Corpus::new(self.0).map_err(serde::de::Error::custom)?;
        while let Some(ref key) = map.next_key::<String>()? {
            if key == "_meta" {
                eprintln!("Reading meta");
                let data = map.next_value::<HashMap<String, LayerDesc>>()?;
                corpus.meta = data;
                eprintln!("Meta: {:?}", corpus.meta);
            } else if key == "_order" {
                eprintln!("Reading order");
                let data = map.next_value::<Vec<String>>()?;
                corpus.order = data;
            } else {
                eprintln!("Reading doc {}", key);
                let doc = map.next_value::<HashMap<String, PyLayer>>()?;
                let id = corpus.add_doc(doc).map_err(serde::de::Error::custom)?;
                if id[..min(id.len(), key.len())] != key[..min(id.len(), key.len())] {
                    return Err(serde::de::Error::custom(format!("Document fails hash check: {} != {}", id, key)))
                }
            }
        }
        Ok(corpus)
    }
}

fn read_corpus_from_json_string(s: &str, path : String) -> Result<Corpus, serde_json::Error> {
    let mut deserializer = serde_json::Deserializer::from_str(s);
    deserializer.deserialize_any(TeangaVisitor(path))
}

fn read_corpus_from_yaml_string(s: &str, path : String) -> Result<Corpus, serde_yaml::Error> {
    let deserializer = serde_yaml::Deserializer::from_str(s);
    deserializer.deserialize_any(TeangaVisitor(path))
}


#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_deserialize_yaml() {
        let doc = "_meta:
    text:
        type: characters
    tokens:
        type: span
        on: text
_order: [\"ecWc\"]
ecWc:
    text: This is an example
    tokens: [[0, 4], [5, 7], [8, 10], [11, 18]]
";
        read_corpus_from_yaml_string(doc, "tmp".to_string()).unwrap();
    }
}

