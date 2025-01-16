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

import collections.abc
from copy import deepcopy
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Dict,
    Generic,
    Iterable,
    Literal,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Union,
    cast,
)

from elastic_transport.client_utils import DEFAULT

from .query import Query
from .response.aggs import AggResponse, BucketData, FieldBucketData, TopHitsData
from .utils import _R, AttrDict, DslBase

if TYPE_CHECKING:
    from elastic_transport.client_utils import DefaultType
    from . import types
    from .document_base import InstrumentedField
    from .search_base import SearchBase


def A(
    name_or_agg: Union[MutableMapping[str, Any], "Agg[_R]", str],
    filter: Optional[Union[str, "Query"]] = None,
    **params: Any,
) -> "Agg[_R]":
    if filter is not None:
        if name_or_agg != "filter":
            raise ValueError(
                "Aggregation %r doesn't accept positional argument 'filter'."
                % name_or_agg
            )
        params["filter"] = filter

    # {"terms": {"field": "tags"}, "aggs": {...}}
    if isinstance(name_or_agg, collections.abc.MutableMapping):
        if params:
            raise ValueError("A() cannot accept parameters when passing in a dict.")
        # copy to avoid modifying in-place
        agg = deepcopy(name_or_agg)
        # pop out nested aggs
        aggs = agg.pop("aggs", None)
        # pop out meta data
        meta = agg.pop("meta", None)
        # should be {"terms": {"field": "tags"}}
        if len(agg) != 1:
            raise ValueError(
                'A() can only accept dict with an aggregation ({"terms": {...}}). '
                "Instead it got (%r)" % name_or_agg
            )
        agg_type, params = agg.popitem()
        if aggs:
            params = params.copy()
            params["aggs"] = aggs
        if meta:
            params = params.copy()
            params["meta"] = meta
        return Agg[_R].get_dsl_class(agg_type)(_expand__to_dot=False, **params)

    # Terms(...) just return the nested agg
    elif isinstance(name_or_agg, Agg):
        if params:
            raise ValueError(
                "A() cannot accept parameters when passing in an Agg object."
            )
        return name_or_agg

    # "terms", field="tags"
    return Agg[_R].get_dsl_class(name_or_agg)(**params)


class Agg(DslBase, Generic[_R]):
    _type_name = "agg"
    _type_shortcut = staticmethod(A)
    name = ""

    def __contains__(self, key: str) -> bool:
        return False

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        if isinstance(d[self.name], dict):
            n = cast(Dict[str, Any], d[self.name])
            if "meta" in n:
                d["meta"] = n.pop("meta")
        return d

    def result(self, search: "SearchBase[_R]", data: Dict[str, Any]) -> AttrDict[Any]:
        return AggResponse[_R](self, search, data)


class AggBase(Generic[_R]):
    aggs: Dict[str, Agg[_R]]
    _base: Agg[_R]
    _params: Dict[str, Any]
    _param_defs: ClassVar[Dict[str, Any]] = {
        "aggs": {"type": "agg", "hash": True},
    }

    def __contains__(self, key: str) -> bool:
        return key in self._params.get("aggs", {})

    def __getitem__(self, agg_name: str) -> Agg[_R]:
        agg = cast(
            Agg[_R], self._params.setdefault("aggs", {})[agg_name]
        )  # propagate KeyError

        # make sure we're not mutating a shared state - whenever accessing a
        # bucket, return a shallow copy of it to be safe
        if isinstance(agg, Bucket):
            agg = A(agg.name, **agg._params)
            # be sure to store the copy so any modifications to it will affect us
            self._params["aggs"][agg_name] = agg

        return agg

    def __setitem__(self, agg_name: str, agg: Agg[_R]) -> None:
        self.aggs[agg_name] = A(agg)

    def __iter__(self) -> Iterable[str]:
        return iter(self.aggs)

    def _agg(
        self,
        bucket: bool,
        name: str,
        agg_type: Union[Dict[str, Any], Agg[_R], str],
        *args: Any,
        **params: Any,
    ) -> Agg[_R]:
        agg = self[name] = A(agg_type, *args, **params)

        # For chaining - when creating new buckets return them...
        if bucket:
            return agg
        # otherwise return self._base so we can keep chaining
        else:
            return self._base

    def metric(
        self,
        name: str,
        agg_type: Union[Dict[str, Any], Agg[_R], str],
        *args: Any,
        **params: Any,
    ) -> Agg[_R]:
        return self._agg(False, name, agg_type, *args, **params)

    def bucket(
        self,
        name: str,
        agg_type: Union[Dict[str, Any], Agg[_R], str],
        *args: Any,
        **params: Any,
    ) -> "Bucket[_R]":
        return cast("Bucket[_R]", self._agg(True, name, agg_type, *args, **params))

    def pipeline(
        self,
        name: str,
        agg_type: Union[Dict[str, Any], Agg[_R], str],
        *args: Any,
        **params: Any,
    ) -> "Pipeline[_R]":
        return cast("Pipeline[_R]", self._agg(False, name, agg_type, *args, **params))

    def result(self, search: "SearchBase[_R]", data: Any) -> AttrDict[Any]:
        return BucketData(self, search, data)  # type: ignore


class Bucket(AggBase[_R], Agg[_R]):
    def __init__(self, **params: Any):
        super().__init__(**params)
        # remember self for chaining
        self._base = self

    def to_dict(self) -> Dict[str, Any]:
        d = super(AggBase, self).to_dict()
        if isinstance(d[self.name], dict):
            n = cast(AttrDict[Any], d[self.name])
            if "aggs" in n:
                d["aggs"] = n.pop("aggs")
        return d


class Pipeline(Agg[_R]):
    pass


{% for k in classes %}
class {{ k.name }}({{ k.parent if k.parent else parent }}[_R]):
    """
    {% for line in k.docstring %}
    {{ line }}
    {% endfor %}
    {% if k.args %}
        {% if k.docstring %}

        {% endif %}
        {% for kwarg in k.args %}
            {% for line in kwarg.doc %}
    {{ line }}
            {% endfor %}
        {% endfor %}
    {% endif %}
    """
    {% if k.property_name %}
    name = "{{ k.property_name }}"
    {% endif %}
    {% if k.params %}
    _param_defs = {
    {% for param in k.params %}
        "{{ param.name }}": {{ param.param }},
    {% endfor %}
    {% if k.name == "Filter" or k.name == "Filters" or k.name == "Composite" %}
        {# Some #}
        "aggs": {"type": "agg", "hash": True},
    {% endif %}
    }
    {% endif %}

    def __init__(
        self,
        {% if k.args | length != 1 %}
            {% for arg in k.args %}
                {% if arg.positional %}
        {{ arg.name }}: {{ arg.type }} = DEFAULT,
                {% endif %}
        {% endfor %}
            {% if k.args and not k.args[-1].positional %}
        *,
            {% endif %}
            {% for arg in k.args %}
                {% if not arg.positional %}
        {{ arg.name }}: {{ arg.type }} = DEFAULT,
                {% endif %}
            {% endfor %}
        {% else %}
            {# when we have just one argument, we allow it as positional or keyword #}
            {% for arg in k.args %}
        {{ arg.name }}: {{ arg.type }} = DEFAULT,
            {% endfor %}
        {% endif %}
        **kwargs: Any
    ):
        {% if k.name == "FunctionScore" %}
            {# continuation of the FunctionScore shortcut property support from above #}
        if functions is DEFAULT:
            functions = []
            for name in ScoreFunction._classes:
                if name in kwargs:
                    functions.append({name: kwargs.pop(name)})  # type: ignore
        {% elif k.is_single_field %}
        if _field is not DEFAULT:
            kwargs[str(_field)] = _value
        {% elif k.is_multi_field %}
        if _fields is not DEFAULT:
            for field, value in _fields.items():
                kwargs[str(field)] = value
        {% endif %}
        super().__init__(
            {% for arg in k.args %}
                {% if not arg.positional %}
            {{ arg.name }}={{ arg.name }},
                {% endif %}
            {% endfor %}
            **kwargs
        )

    {# what follows is a set of Pythonic enhancements to some of the query classes
       which are outside the scope of the code generator #}
    {% if k.name == "Filter" %}
    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        if isinstance(d[self.name], dict):
            n = cast(AttrDict[Any], d[self.name])
            n.update(n.pop("filter", {}))
        return d

    {% elif k.name == "Histogram" or k.name == "DateHistogram" or k.name == "AutoDateHistogram" or k.name == "VariableWidthHistogram" %}
    def result(self, search: "SearchBase[_R]", data: Any) -> AttrDict[Any]:
        return FieldBucketData(self, search, data)

    {% elif k.name == "Terms" %}
    def result(self, search: "SearchBase[_R]", data: Any) -> AttrDict[Any]:
        return FieldBucketData(self, search, data)

    {% elif k.name == "TopHits" %}
    def result(self, search: "SearchBase[_R]", data: Any) -> AttrDict[Any]:
        return TopHitsData(self, search, data)

    {% endif %}
{% endfor %}
