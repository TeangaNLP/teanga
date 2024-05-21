from collections import namedtuple

LayerDesc = namedtuple("LayerDesc",
                       ["layer_type", "base", "data", 
                        "link_types", "target", "default", "meta"],
                       defaults=[None, None, None, None, None, None, {}])

def _layer_desc_from_kwargs(kwargs):
    kwargs["meta"] = {}
    if "type" in kwargs:
        kwargs["layer_type"] = kwargs["type"]
        del kwargs["type"]
    kwargs2 = kwargs.copy()
    for key in kwargs:
        if key.startswith("_"):
            kwargs2["meta"][key[1:]] = kwargs[key]
            del kwargs2[key]
        elif key not in ["layer_type", "base", "data", "link_types", 
                         "target", "default", "meta"]:
            raise Exception("Invalid key in Teanga meta description: " + key)
    return LayerDesc(**kwargs2)

def _from_layer_desc(layer_desc):
    d = { 
         name: data for name,data in layer_desc._asdict().items()
         if data is not None and name != "meta"
    }
    for key, value in layer_desc.meta.items():
        d["_" + key] = value
    d["type"] = d["layer_type"]
    del d["layer_type"]
    return d
            

