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
from itertools import chain
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Dict,
    List,
    Literal,
    Mapping,
    MutableMapping,
    Optional,
    Protocol,
    Sequence,
    TypeVar,
    Union,
    cast,
    overload,
)

from elastic_transport.client_utils import DEFAULT

# 'SF' looks unused but the test suite assumes it's available
# from this module so others are liable to do so as well.
from .function import SF  # noqa: F401
from .function import ScoreFunction
from .utils import DslBase

if TYPE_CHECKING:
    from elastic_transport.client_utils import DefaultType
    from . import types, wrappers
    from .document_base import InstrumentedField

_T = TypeVar("_T")
_M = TypeVar("_M", bound=Mapping[str, Any])


class QProxiedProtocol(Protocol[_T]):
    _proxied: _T


@overload
def Q(name_or_query: MutableMapping[str, _M]) -> "Query": ...


@overload
def Q(name_or_query: "Query") -> "Query": ...


@overload
def Q(name_or_query: QProxiedProtocol[_T]) -> _T: ...


@overload
def Q(name_or_query: str = "match_all", **params: Any) -> "Query": ...


def Q(
    name_or_query: Union[
        str,
        "Query",
        QProxiedProtocol[_T],
        MutableMapping[str, _M],
    ] = "match_all",
    **params: Any,
) -> Union["Query", _T]:
    # {"match": {"title": "python"}}
    if isinstance(name_or_query, collections.abc.MutableMapping):
        if params:
            raise ValueError("Q() cannot accept parameters when passing in a dict.")
        if len(name_or_query) != 1:
            raise ValueError(
                'Q() can only accept dict with a single query ({"match": {...}}). '
                "Instead it got (%r)" % name_or_query
            )
        name, q_params = deepcopy(name_or_query).popitem()
        return Query.get_dsl_class(name)(_expand__to_dot=False, **q_params)

    # MatchAll()
    if isinstance(name_or_query, Query):
        if params:
            raise ValueError(
                "Q() cannot accept parameters when passing in a Query object."
            )
        return name_or_query

    # s.query = Q('filtered', query=s.query)
    if hasattr(name_or_query, "_proxied"):
        return cast(QProxiedProtocol[_T], name_or_query)._proxied

    # "match", title="python"
    return Query.get_dsl_class(name_or_query)(**params)


class Query(DslBase):
    _type_name = "query"
    _type_shortcut = staticmethod(Q)
    name: ClassVar[Optional[str]] = None

    # Add type annotations for methods not defined in every subclass
    __ror__: ClassVar[Callable[["Query", "Query"], "Query"]]
    __radd__: ClassVar[Callable[["Query", "Query"], "Query"]]
    __rand__: ClassVar[Callable[["Query", "Query"], "Query"]]

    def __add__(self, other: "Query") -> "Query":
        # make sure we give queries that know how to combine themselves
        # preference
        if hasattr(other, "__radd__"):
            return other.__radd__(self)
        return Bool(must=[self, other])

    def __invert__(self) -> "Query":
        return Bool(must_not=[self])

    def __or__(self, other: "Query") -> "Query":
        # make sure we give queries that know how to combine themselves
        # preference
        if hasattr(other, "__ror__"):
            return other.__ror__(self)
        return Bool(should=[self, other])

    def __and__(self, other: "Query") -> "Query":
        # make sure we give queries that know how to combine themselves
        # preference
        if hasattr(other, "__rand__"):
            return other.__rand__(self)
        return Bool(must=[self, other])


{% for k in classes %}
class {{ k.name }}({{ parent }}):
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
    name = "{{ k.property_name }}"
    {% if k.params %}
    _param_defs = {
    {% for param in k.params %}
        "{{ param.name }}": {{ param.param }},
    {% endfor %}
    {% if k.name == "FunctionScore" %}
        {# The FunctionScore class implements a custom solution for the `functions`
           shortcut property. Until the code generator can support shortcut
           properties directly that solution is added here #}
        "filter": {"type": "query"},
    {% endif %}
    }
    {% endif %}

    def __init__(
        self,
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
    {% if k.name == "MatchAll" %}
    def __add__(self, other: "Query") -> "Query":
        return other._clone()

    __and__ = __rand__ = __radd__ = __add__

    def __or__(self, other: "Query") -> "MatchAll":
        return self

    __ror__ = __or__

    def __invert__(self) -> "MatchNone":
        return MatchNone()


EMPTY_QUERY = MatchAll()

    {% elif k.name == "MatchNone" %}
    def __add__(self, other: "Query") -> "MatchNone":
        return self

    __and__ = __rand__ = __radd__ = __add__

    def __or__(self, other: "Query") -> "Query":
        return other._clone()

    __ror__ = __or__

    def __invert__(self) -> MatchAll:
        return MatchAll()

    {% elif k.name == "Bool" %}
    def __add__(self, other: Query) -> "Bool":
        q = self._clone()
        if isinstance(other, Bool):
            q.must += other.must
            q.should += other.should
            q.must_not += other.must_not
            q.filter += other.filter
        else:
            q.must.append(other)
        return q

    __radd__ = __add__

    def __or__(self, other: Query) -> Query:
        for q in (self, other):
            if isinstance(q, Bool) and not any(
                (q.must, q.must_not, q.filter, getattr(q, "minimum_should_match", None))
            ):
                other = self if q is other else other
                q = q._clone()
                if isinstance(other, Bool) and not any(
                    (
                        other.must,
                        other.must_not,
                        other.filter,
                        getattr(other, "minimum_should_match", None),
                    )
                ):
                    q.should.extend(other.should)
                else:
                    q.should.append(other)
                return q

        return Bool(should=[self, other])

    __ror__ = __or__

    @property
    def _min_should_match(self) -> int:
        return getattr(
            self,
            "minimum_should_match",
            0 if not self.should or (self.must or self.filter) else 1,
        )

    def __invert__(self) -> Query:
        # Because an empty Bool query is treated like
        # MatchAll the inverse should be MatchNone
        if not any(chain(self.must, self.filter, self.should, self.must_not)):
            return MatchNone()

        negations: List[Query] = []
        for q in chain(self.must, self.filter):
            negations.append(~q)

        for q in self.must_not:
            negations.append(q)

        if self.should and self._min_should_match:
            negations.append(Bool(must_not=self.should[:]))

        if len(negations) == 1:
            return negations[0]
        return Bool(should=negations)

    def __and__(self, other: Query) -> Query:
        q = self._clone()
        if isinstance(other, Bool):
            q.must += other.must
            q.must_not += other.must_not
            q.filter += other.filter
            q.should = []

            # reset minimum_should_match as it will get calculated below
            if "minimum_should_match" in q._params:
                del q._params["minimum_should_match"]

            for qx in (self, other):
                min_should_match = qx._min_should_match
                # TODO: percentages or negative numbers will fail here
                # for now we report an error
                if not isinstance(min_should_match, int) or min_should_match < 0:
                    raise ValueError(
                        "Can only combine queries with positive integer values for minimum_should_match"
                    )
                # all subqueries are required
                if len(qx.should) <= min_should_match:
                    q.must.extend(qx.should)
                # not all of them are required, use it and remember min_should_match
                elif not q.should:
                    q.minimum_should_match = min_should_match
                    q.should = qx.should
                # all queries are optional, just extend should
                elif q._min_should_match == 0 and min_should_match == 0:
                    q.should.extend(qx.should)
                # not all are required, add a should list to the must with proper min_should_match
                else:
                    q.must.append(
                        Bool(should=qx.should, minimum_should_match=min_should_match)
                    )
        else:
            if not (q.must or q.filter) and q.should:
                q._params.setdefault("minimum_should_match", 1)
            q.must.append(other)
        return q

    __rand__ = __and__

    {% elif k.name == "Terms" %}
    def _setattr(self, name: str, value: Any) -> None:
        # here we convert any iterables that are not strings to lists
        if hasattr(value, "__iter__") and not isinstance(value, (str, list, dict)):
            value = list(value)
        super()._setattr(name, value)

    {% endif %}

{% endfor %}
