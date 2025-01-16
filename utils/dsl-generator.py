#  Licensed to Elasticsearch B.V. under one or more contributor
#  license agreements. See the NOTICE file distributed with
#  this work for additional information regarding copyright
#  ownership. Elasticsearch B.V. licenses this file to you under
#  the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
# 	http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing,
#  software distributed under the License is distributed on an
#  "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
#  KIND, either express or implied.  See the License for the
#  specific language governing permissions and limitations
#  under the License.

import json
import re
import textwrap
from urllib.error import HTTPError
from urllib.request import urlopen

from jinja2 import Environment, PackageLoader, select_autoescape

from elasticsearch import VERSION

jinja_env = Environment(
    loader=PackageLoader("utils"),
    autoescape=select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True,
)
query_py = jinja_env.get_template("query.py.tpl")
aggs_py = jinja_env.get_template("aggs.py.tpl")
response_init_py = jinja_env.get_template("response.__init__.py.tpl")
types_py = jinja_env.get_template("types.py.tpl")

# map with name replacements for Elasticsearch attributes
PROP_REPLACEMENTS = {"from": "from_"}

# map with Elasticsearch type replacements
# keys and values are in given in "{namespace}:{name}" format
TYPE_REPLACEMENTS = {
    "_types.query_dsl:DistanceFeatureQuery": "_types.query_dsl:DistanceFeatureQueryBase",
}

# some aggregation types are complicated to determine from the schema, so they
# have their correct type here
AGG_TYPES = {
    "bucket_count_ks_test": "Pipeline",
    "bucket_correlation": "Pipeline",
    "bucket_sort": "Bucket",
    "categorize_text": "Bucket",
    "filter": "Bucket",
    "moving_avg": "Pipeline",
    "variable_width_histogram": "Bucket",
}


def property_to_class_name(name):
    return "".join([w.title() if w != "ip" else "IP" for w in name.split("_")])


def wrapped_doc(text, width=70, initial_indent="", subsequent_indent=""):
    """Formats a docstring as a list of lines of up to the request width."""
    return textwrap.wrap(
        text.replace("\n", " "),
        width=width,
        initial_indent=initial_indent,
        subsequent_indent=subsequent_indent,
    )


def add_dict_type(type_):
    """Add Dict[str, Any] to a Python type hint."""
    if type_.startswith("Union["):
        type_ = f"{type_[:-1]}, Dict[str, Any]]"
    else:
        type_ = f"Union[{type_}, Dict[str, Any]]"
    return type_


def add_seq_dict_type(type_):
    """Add Sequence[Dict[str, Any]] to a Python type hint."""
    if type_.startswith("Union["):
        type_ = f"{type_[:-1]}, Sequence[Dict[str, Any]]]"
    else:
        type_ = f"Union[{type_}, Sequence[Dict[str, Any]]]"
    return type_


def add_not_set(type_):
    """Add DefaultType to a Python type hint."""
    if type_.startswith("Union["):
        type_ = f'{type_[:-1]}, "DefaultType"]'
    else:
        type_ = f'Union[{type_}, "DefaultType"]'
    return type_


def type_for_types_py(type_):
    """Converts a type rendered in a generic way to the format needed in the
    types.py module.
    """
    type_ = type_.replace('"DefaultType"', "DefaultType")
    type_ = type_.replace('"InstrumentedField"', "InstrumentedField")
    type_ = re.sub(r'"(function\.[a-zA-Z0-9_]+)"', r"\1", type_)
    type_ = re.sub(r'"types\.([a-zA-Z0-9_]+)"', r'"\1"', type_)
    type_ = re.sub(r'"(wrappers\.[a-zA-Z0-9_]+)"', r"\1", type_)
    return type_


class ElasticsearchSchema:
    """Operations related to the Elasticsearch schema."""

    def __init__(self):
        response = None
        for branch in [f"{VERSION[0]}.{VERSION[1]}", "main"]:
            url = f"https://raw.githubusercontent.com/elastic/elasticsearch-specification/{branch}/output/schema/schema.json"
            try:
                response = urlopen(url)
                print(f"Initializing code generation with '{branch}' specification.")
                break
            except HTTPError:
                continue
        if not response:
            raise RuntimeError("Could not download Elasticsearch schema")
        self.schema = json.loads(response.read())

        # Interfaces collects interfaces that are seen while traversing the schema.
        # Any interfaces collected here are then rendered as Python in the
        # types.py module.
        self.interfaces = []
        self.response_interfaces = []

    def find_type(self, name, namespace=None):
        for t in self.schema["types"]:
            if t["name"]["name"] == name and (
                namespace is None or t["name"]["namespace"] == namespace
            ):
                return t

    def inherits_from(self, type_, name, namespace=None):
        while "inherits" in type_:
            type_ = self.find_type(
                type_["inherits"]["type"]["name"],
                type_["inherits"]["type"]["namespace"],
            )
            if type_["name"]["name"] == name and (
                namespace is None or type_["name"]["namespace"] == namespace
            ):
                return True
        return False

    def get_python_type(self, schema_type, for_response=False):
        """Obtain Python typing details for a given schema type

        This method returns a tuple. The first element is a string with the
        Python type hint. The second element is a dictionary with Python DSL
        specific typing details to be stored in the DslBase._param_defs
        attribute (or None if the type does not need to be in _param_defs).

        When `for_response` is `False`, any new interfaces that are discovered
        are registered to be generated in "request" style, with alternative
        Dict type hints and default values. If `for_response` is `True`,
        interfaces are generated just with their declared type, without
        Dict alternative and without defaults, to help type checkers be more
        effective at parsing response expressions.
        """
        if schema_type["kind"] == "instance_of":
            type_name = schema_type["type"]
            if type_name["namespace"] in ["_types", "internal", "_builtins"]:
                if type_name["name"] in ["integer", "uint", "long", "ulong"]:
                    return "int", None
                elif type_name["name"] in ["number", "float", "double"]:
                    return "float", None
                elif type_name["name"] == "string":
                    return "str", None
                elif type_name["name"] == "boolean":
                    return "bool", None
                elif type_name["name"] == "binary":
                    return "bytes", None
                elif type_name["name"] == "null":
                    return "None", None
                elif type_name["name"] == "Field":
                    if for_response:
                        return "str", None
                    else:
                        return 'Union[str, "InstrumentedField"]', None
                else:
                    # not an instance of a native type, so we get the type and try again
                    return self.get_python_type(
                        self.find_type(type_name["name"], type_name["namespace"]),
                        for_response=for_response,
                    )
            elif (
                type_name["namespace"] == "_types.query_dsl"
                and type_name["name"] == "QueryContainer"
            ):
                # QueryContainer maps to the DSL's Query class
                return "Query", {"type": "query"}
            elif (
                type_name["namespace"] == "_types.query_dsl"
                and type_name["name"] == "FunctionScoreContainer"
            ):
                # FunctionScoreContainer maps to the DSL's ScoreFunction class
                return "ScoreFunction", {"type": "score_function"}
            elif (
                type_name["namespace"] == "_types.aggregations"
                and type_name["name"] == "Buckets"
            ):
                if for_response:
                    return "Union[Sequence[Any], Dict[str, Any]]", None
                else:
                    return "Dict[str, Query]", {"type": "query", "hash": True}
            elif (
                type_name["namespace"] == "_types.aggregations"
                and type_name["name"] == "CompositeAggregationSource"
            ):
                # QueryContainer maps to the DSL's Query class
                return "Agg[_R]", None
            else:
                # for any other instances we get the type and recurse
                type_ = self.find_type(type_name["name"], type_name["namespace"])
                if type_:
                    return self.get_python_type(type_, for_response=for_response)

        elif schema_type["kind"] == "type_alias":
            # for an alias, we use the aliased type
            return self.get_python_type(schema_type["type"], for_response=for_response)

        elif schema_type["kind"] == "array_of":
            # for arrays we use Sequence[element_type]
            type_, param = self.get_python_type(
                schema_type["value"], for_response=for_response
            )
            return f"Sequence[{type_}]", {**param, "multi": True} if param else None

        elif schema_type["kind"] == "dictionary_of":
            # for dicts we use Mapping[key_type, value_type]
            key_type, key_param = self.get_python_type(
                schema_type["key"], for_response=for_response
            )
            value_type, value_param = self.get_python_type(
                schema_type["value"], for_response=for_response
            )
            return f"Mapping[{key_type}, {value_type}]", (
                {**value_param, "hash": True} if value_param else None
            )

        elif schema_type["kind"] == "union_of":
            if (
                len(schema_type["items"]) == 2
                and schema_type["items"][0]["kind"] == "instance_of"
                and schema_type["items"][1]["kind"] == "array_of"
                and schema_type["items"][0] == schema_type["items"][1]["value"]
            ):
                # special kind of unions in the form Union[type, Sequence[type]]
                type_, param = self.get_python_type(
                    schema_type["items"][0], for_response=for_response
                )
                if schema_type["items"][0]["type"]["name"] in [
                    "CompletionSuggestOption",
                    "PhraseSuggestOption",
                    "TermSuggestOption",
                ]:
                    # for suggest types we simplify this type and return just the array form
                    return (
                        f"Sequence[{type_}]",
                        ({"type": param["type"], "multi": True} if param else None),
                    )
                else:
                    # for every other types we produce an union with the two alternatives
                    return (
                        f"Union[{type_}, Sequence[{type_}]]",
                        ({"type": param["type"], "multi": True} if param else None),
                    )
            elif (
                len(schema_type["items"]) == 2
                and schema_type["items"][0]["kind"] == "instance_of"
                and schema_type["items"][1]["kind"] == "instance_of"
                and schema_type["items"][0]["type"]
                == {"name": "T", "namespace": "_spec_utils.PipeSeparatedFlags"}
                and schema_type["items"][1]["type"]
                == {"name": "string", "namespace": "_builtins"}
            ):
                # for now we treat PipeSeparatedFlags as a special case
                if "PipeSeparatedFlags" not in self.interfaces:
                    self.interfaces.append("PipeSeparatedFlags")
                return '"types.PipeSeparatedFlags"', None
            else:
                # generic union type
                types = list(
                    dict.fromkeys(  # eliminate duplicates
                        [
                            self.get_python_type(t, for_response=for_response)
                            for t in schema_type["items"]
                        ]
                    )
                )
                return "Union[" + ", ".join([type_ for type_, _ in types]) + "]", None

        elif schema_type["kind"] == "enum":
            # enums are mapped to Literal[member, ...]
            return (
                "Literal["
                + ", ".join(
                    [f"\"{member['name']}\"" for member in schema_type["members"]]
                )
                + "]",
                None,
            )

        elif schema_type["kind"] == "interface":
            if schema_type["name"]["namespace"] == "_types.query_dsl":
                # handle specific DSL classes explicitly to map to existing
                # Python DSL classes
                if schema_type["name"]["name"].endswith("RangeQuery"):
                    return '"wrappers.Range[Any]"', None
                elif schema_type["name"]["name"].endswith("ScoreFunction"):
                    # When dropping Python 3.8, use `removesuffix("Function")` instead
                    name = schema_type["name"]["name"][:-8]
                    return f'"function.{name}"', None
                elif schema_type["name"]["name"].endswith("DecayFunction"):
                    return '"function.DecayFunction"', None
                elif schema_type["name"]["name"].endswith("Function"):
                    return f"\"function.{schema_type['name']['name']}\"", None
            elif schema_type["name"]["namespace"] == "_types.analysis" and schema_type[
                "name"
            ]["name"].endswith("Analyzer"):
                # not expanding analyzers at this time, maybe in the future
                return "str, Dict[str, Any]", None

            # to handle other interfaces we generate a type of the same name
            # and add the interface to the interfaces.py module
            if schema_type["name"]["name"] not in self.interfaces:
                self.interfaces.append(schema_type["name"]["name"])
                if for_response:
                    self.response_interfaces.append(schema_type["name"]["name"])
            return f"\"types.{schema_type['name']['name']}\"", None
        elif schema_type["kind"] == "user_defined_value":
            # user_defined_value maps to Python's Any type
            return "Any", None

        raise RuntimeError(f"Cannot find Python type for {schema_type}")

    def add_attribute(self, k, arg, for_types_py=False, for_response=False):
        """Add an attribute to the internal representation of a class.

        This method adds the argument `arg` to the data structure for a class
        stored in `k`. In particular, the argument is added to the `k["args"]`
        list, making sure required arguments are first in the list. If the
        argument is of a type that needs Python DSL specific typing details to
        be stored in the DslBase._param_defs attribute, then this is added to
        `k["params"]`.

        When `for_types_py` is `True`, type hints are formatted in the most
        convenient way for the types.py file. When possible, double quotes are
        removed from types, and for types that are in the same file the quotes
        are kept to prevent forward references, but the "types." namespace is
        removed. When `for_types_py` is `False`, all non-native types use
        quotes and are namespaced.

        When `for_response` is `True`, type hints are not given the optional
        dictionary representation, nor the `DefaultType` used for omitted
        attributes.
        """
        try:
            type_, param = self.get_python_type(arg["type"], for_response=for_response)
        except RuntimeError:
            type_ = "Any"
            param = None
        if not for_response:
            if type_ != "Any":
                if 'Sequence["types.' in type_:
                    type_ = add_seq_dict_type(type_)  # interfaces can be given as dicts
                elif "types." in type_:
                    type_ = add_dict_type(type_)  # interfaces can be given as dicts
                type_ = add_not_set(type_)
        if for_types_py:
            type_ = type_for_types_py(type_)
        required = "(required) " if arg["required"] else ""
        server_default = (
            f" Defaults to `{arg['serverDefault']}` if omitted."
            if arg.get("serverDefault")
            else ""
        )
        doc = wrapped_doc(
            f":arg {arg['name']}: {required}{arg.get('description', '')}{server_default}",
            subsequent_indent="    ",
        )
        arg = {
            "name": PROP_REPLACEMENTS.get(arg["name"], arg["name"]),
            "type": type_,
            "doc": doc,
            "required": arg["required"],
        }
        if param is not None:
            param = {"name": arg["name"], "param": param}
        if arg["required"]:
            # insert in the right place so that all required arguments
            # appear at the top of the argument list
            i = 0
            for i in range(len(k["args"]) + 1):
                if i == len(k["args"]):
                    break
                if k["args"][i].get("positional"):
                    continue
                if k["args"][i]["required"] is False:
                    break
            k["args"].insert(i, arg)
        else:
            k["args"].append(arg)
        if param and "params" in k:
            k["params"].append(param)

    def add_behaviors(self, type_, k, for_types_py=False, for_response=False):
        """Add behaviors reported in the specification of the given type to the
        class representation.
        """
        if "behaviors" in type_:
            for behavior in type_["behaviors"]:
                if (
                    behavior["type"]["name"] != "AdditionalProperty"
                    or behavior["type"]["namespace"] != "_spec_utils"
                ):
                    # we do not support this behavior, so we ignore it
                    continue
                key_type, _ = self.get_python_type(
                    behavior["generics"][0], for_response=for_response
                )
                if "InstrumentedField" in key_type:
                    value_type, _ = self.get_python_type(
                        behavior["generics"][1], for_response=for_response
                    )
                    if for_types_py:
                        value_type = value_type.replace('"DefaultType"', "DefaultType")
                        value_type = value_type.replace(
                            '"InstrumentedField"', "InstrumentedField"
                        )
                        value_type = re.sub(
                            r'"(function\.[a-zA-Z0-9_]+)"', r"\1", value_type
                        )
                        value_type = re.sub(
                            r'"types\.([a-zA-Z0-9_]+)"', r'"\1"', value_type
                        )
                        value_type = re.sub(
                            r'"(wrappers\.[a-zA-Z0-9_]+)"', r"\1", value_type
                        )
                    k["args"].append(
                        {
                            "name": "_field",
                            "type": add_not_set(key_type),
                            "doc": [":arg _field: The field to use in this query."],
                            "required": False,
                            "positional": True,
                        }
                    )
                    k["args"].append(
                        {
                            "name": "_value",
                            "type": add_not_set(add_dict_type(value_type)),
                            "doc": [":arg _value: The query value for the field."],
                            "required": False,
                            "positional": True,
                        }
                    )
                    k["is_single_field"] = True
                else:
                    raise RuntimeError(
                        f"Non-field AdditionalProperty are not supported for interface {type_['name']['namespace']}:{type_['name']['name']}."
                    )

    def property_to_python_class(self, p):
        """Return a dictionary with template data necessary to render a schema
        property as a Python class.

        Used for "container" sub-classes such as `QueryContainer`, where each
        sub-class is represented by a Python DSL class.

        The format is as follows:

        ```python
        {
            "property_name": "the name of the property",
            "name": "the class name to use for the property",
            "docstring": "the formatted docstring as a list of strings",
            "args": [  # a Python description of each class attribute
                "name": "the name of the attribute",
                "type": "the Python type hint for the attribute",
                "doc": ["formatted lines of documentation to add to class docstring"],
                "required": bool,
                "positional": bool,
            ],
            "params": [
                "name": "the attribute name",
                "param": "the param dictionary to include in `_param_defs` for the class",
            ],  # a DSL-specific description of interesting attributes
            "is_single_field": bool  # True for single-key dicts with field key
            "is_multi_field": bool  # True for multi-key dicts with field keys
        }
        ```
        """
        k = {
            "property_name": p["name"],
            "name": property_to_class_name(p["name"]),
        }
        k["docstring"] = wrapped_doc(p.get("description") or "")
        other_classes = []
        kind = p["type"]["kind"]
        if kind == "instance_of":
            namespace = p["type"]["type"]["namespace"]
            name = p["type"]["type"]["name"]
            if f"{namespace}:{name}" in TYPE_REPLACEMENTS:
                namespace, name = TYPE_REPLACEMENTS[f"{namespace}:{name}"].split(":")
            if name == "QueryContainer" and namespace == "_types.query_dsl":
                type_ = {
                    "kind": "interface",
                    "properties": [p],
                }
            else:
                type_ = self.find_type(name, namespace)
            if p["name"] in AGG_TYPES:
                k["parent"] = AGG_TYPES[p["name"]]

            if type_["kind"] == "interface":
                # set the correct parent for bucket and pipeline aggregations
                if self.inherits_from(
                    type_, "PipelineAggregationBase", "_types.aggregations"
                ):
                    k["parent"] = "Pipeline"
                elif self.inherits_from(
                    type_, "BucketAggregationBase", "_types.aggregations"
                ):
                    k["parent"] = "Bucket"

                # generate class attributes
                k["args"] = []
                k["params"] = []
                self.add_behaviors(type_, k)
                while True:
                    for arg in type_["properties"]:
                        self.add_attribute(k, arg)
                    if "inherits" in type_ and "type" in type_["inherits"]:
                        type_ = self.find_type(
                            type_["inherits"]["type"]["name"],
                            type_["inherits"]["type"]["namespace"],
                        )
                    else:
                        break

            elif type_["kind"] == "type_alias":
                if type_["type"]["kind"] == "union_of":
                    # for unions we create sub-classes
                    for other in type_["type"]["items"]:
                        other_class = self.interface_to_python_class(
                            other["type"]["name"],
                            other["type"]["namespace"],
                            for_types_py=False,
                        )
                        other_class["parent"] = k["name"]
                        other_classes.append(other_class)
                else:
                    raise RuntimeError(
                        "Cannot generate code for instances of type_alias instances that are not unions."
                    )

            else:
                raise RuntimeError(
                    f"Cannot generate code for instances of kind '{type_['kind']}'"
                )

        elif kind == "dictionary_of":
            key_type, _ = self.get_python_type(p["type"]["key"])
            if "InstrumentedField" in key_type:
                value_type, _ = self.get_python_type(p["type"]["value"])
                if p["type"]["singleKey"]:
                    # special handling for single-key dicts with field key
                    k["args"] = [
                        {
                            "name": "_field",
                            "type": add_not_set(key_type),
                            "doc": [":arg _field: The field to use in this query."],
                            "required": False,
                            "positional": True,
                        },
                        {
                            "name": "_value",
                            "type": add_not_set(add_dict_type(value_type)),
                            "doc": [":arg _value: The query value for the field."],
                            "required": False,
                            "positional": True,
                        },
                    ]
                    k["is_single_field"] = True
                else:
                    # special handling for multi-key dicts with field keys
                    k["args"] = [
                        {
                            "name": "_fields",
                            "type": f"Optional[Mapping[{key_type}, {value_type}]]",
                            "doc": [
                                ":arg _fields: A dictionary of fields with their values."
                            ],
                            "required": False,
                            "positional": True,
                        },
                    ]
                    k["is_multi_field"] = True
            else:
                raise RuntimeError(f"Cannot generate code for type {p['type']}")

        else:
            raise RuntimeError(f"Cannot generate code for type {p['type']}")
        return [k] + other_classes

    def interface_to_python_class(
        self,
        interface,
        namespace=None,
        *,
        for_types_py=True,
        for_response=False,
    ):
        """Return a dictionary with template data necessary to render an
        interface a Python class.

        This is used to render interfaces that are referenced by container
        classes. The current list of rendered interfaces is passed as a second
        argument to allow this method to add more interfaces to it as they are
        discovered.

        The returned format is as follows:

        ```python
        {
            "name": "the class name to use for the interface class",
            "parent": "the parent class name",
            "args": [ # a Python description of each class attribute
                "name": "the name of the attribute",
                "type": "the Python type hint for the attribute",
                "doc": ["formatted lines of documentation to add to class docstring"],
                "required": bool,
                "positional": bool,
            ],
            "buckets_as_dict": "type" # optional, only present in aggregation response
                                      # classes that have buckets that can have a list
                                      # or dict representation
        }
        ```
        """
        type_ = self.find_type(interface, namespace)
        if type_["kind"] not in ["interface", "response"]:
            raise RuntimeError(f"Type {interface} is not an interface")
        if type_["kind"] == "response":
            # we consider responses as interfaces because they also have properties
            # but the location of the properties is different
            type_ = type_["body"]
        k = {"name": interface, "for_response": for_response, "args": []}
        k["docstring"] = wrapped_doc(type_.get("description") or "")
        self.add_behaviors(
            type_, k, for_types_py=for_types_py, for_response=for_response
        )
        generics = []
        while True:
            for arg in type_["properties"]:
                if interface == "ResponseBody" and arg["name"] == "hits":
                    k["args"].append(
                        {
                            "name": "hits",
                            "type": "Sequence[_R]",
                            "doc": [":arg hits: search results"],
                            "required": arg["required"],
                        }
                    )
                elif interface == "ResponseBody" and arg["name"] == "aggregations":
                    # Aggregations are tricky because the DSL client uses a
                    # flexible representation that is difficult to generate
                    # from the schema.
                    # To handle this we let the generator do its work by calling
                    # `add_attribute()`, but then we save the generated attribute
                    # apart and replace it with the DSL's `AggResponse` class.
                    # The generated type is then used in type hints in variables
                    # and methods of this class.
                    self.add_attribute(
                        k, arg, for_types_py=for_types_py, for_response=for_response
                    )
                    k["aggregate_type"] = (
                        k["args"][-1]["type"]
                        .split("Mapping[str, ")[1]
                        .rsplit("]", 1)[0]
                    )
                    k["args"][-1] = {
                        "name": "aggregations",
                        "type": '"AggResponse[_R]"',
                        "doc": [":arg aggregations: aggregation results"],
                        "required": arg["required"],
                    }
                elif (
                    "name" in type_
                    and type_["name"]["name"] == "MultiBucketAggregateBase"
                    and arg["name"] == "buckets"
                ):
                    # Also during aggregation response generation, the "buckets"
                    # attribute that many aggregation responses have is very
                    # complex, supporting over a dozen different aggregation
                    # types via generics, each in array or object configurations.
                    # Typing this attribute proved very difficult. A solution
                    # that worked with mypy and pyright is to type "buckets"
                    # for the list form, and create a `buckets_as_dict`
                    # property that is typed appropriately for accessing the
                    # buckets in dictionary form.
                    # The generic type is assumed to be the first in the list,
                    # which is a simplification that should be improved when a
                    # more complete implementation of generics is added.
                    if generics[0]["type"]["name"] == "Void":
                        generic_type = "Any"
                    else:
                        _g = self.find_type(
                            generics[0]["type"]["name"],
                            generics[0]["type"]["namespace"],
                        )
                        generic_type, _ = self.get_python_type(
                            _g, for_response=for_response
                        )
                        generic_type = type_for_types_py(generic_type)
                    k["args"].append(
                        {
                            "name": arg["name"],
                            # for the type we only include the array form, since
                            # this client does not request the dict form
                            "type": f"Sequence[{generic_type}]",
                            "doc": [
                                ":arg buckets: (required) the aggregation buckets as a list"
                            ],
                            "required": True,
                        }
                    )
                    k["buckets_as_dict"] = generic_type
                else:
                    if interface == "Hit" and arg["name"].startswith("_"):
                        # Python DSL removes the undersore prefix from all the
                        # properties of the hit, so we do the same
                        arg["name"] = arg["name"][1:]

                    self.add_attribute(
                        k, arg, for_types_py=for_types_py, for_response=for_response
                    )

            if "inherits" not in type_ or "type" not in type_["inherits"]:
                break

            if "generics" in type_["inherits"]:
                # Generics are only supported for certain specific cases at this
                # time. Here we just save them so that they can be recalled later
                # while traversing over to parent classes to find inherited
                # attributes.
                for generic_type in type_["inherits"]["generics"]:
                    generics.append(generic_type)

            type_ = self.find_type(
                type_["inherits"]["type"]["name"],
                type_["inherits"]["type"]["namespace"],
            )
        return k


def generate_query_py(schema, filename):
    """Generate query.py with all the properties of `QueryContainer` as Python
    classes.
    """
    classes = []
    query_container = schema.find_type("QueryContainer", "_types.query_dsl")
    for p in query_container["properties"]:
        classes += schema.property_to_python_class(p)

    with open(filename, "wt") as f:
        f.write(query_py.render(classes=classes, parent="Query"))
    print(f"Generated {filename}.")


def generate_aggs_py(schema, filename):
    """Generate aggs.py with all the properties of `AggregationContainer` as
    Python classes.
    """
    classes = []
    aggs_container = schema.find_type("AggregationContainer", "_types.aggregations")
    for p in aggs_container["properties"]:
        if "containerProperty" not in p or not p["containerProperty"]:
            classes += schema.property_to_python_class(p)

    with open(filename, "wt") as f:
        f.write(aggs_py.render(classes=classes, parent="Agg"))
    print(f"Generated {filename}.")


def generate_response_init_py(schema, filename):
    """Generate response/__init__.py with all the response properties
    documented and typed.
    """
    search_response = schema.interface_to_python_class(
        "ResponseBody",
        "_global.search",
        for_types_py=False,
        for_response=True,
    )
    ubq_response = schema.interface_to_python_class(
        "Response",
        "_global.update_by_query",
        for_types_py=False,
        for_response=True,
    )
    with open(filename, "wt") as f:
        f.write(
            response_init_py.render(response=search_response, ubq_response=ubq_response)
        )
    print(f"Generated {filename}.")


def generate_types_py(schema, filename):
    """Generate types.py"""
    classes = {}
    for interface in schema.interfaces:
        if interface == "PipeSeparatedFlags":
            continue  # handled as a special case
        for_response = interface in schema.response_interfaces
        k = schema.interface_to_python_class(
            interface, for_types_py=True, for_response=for_response
        )
        classes[k["name"]] = k

    # sort classes by being request/response and then by name
    sorted_classes = sorted(
        list(classes.keys()),
        key=lambda i: str(int(i in schema.response_interfaces)) + i,
    )
    classes_list = []
    for n in sorted_classes:
        k = classes[n]
        if k in classes_list:
            continue
        classes_list.append(k)

    with open(filename, "wt") as f:
        f.write(types_py.render(classes=classes_list))
    print(f"Generated {filename}.")


if __name__ == "__main__":
    schema = ElasticsearchSchema()
    generate_query_py(schema, "elasticsearch/dsl/query.py")
    generate_aggs_py(schema, "elasticsearch/dsl/aggs.py")
    generate_response_init_py(schema, "elasticsearch/dsl/response/__init__.py")
    generate_types_py(schema, "elasticsearch/dsl/types.py")
