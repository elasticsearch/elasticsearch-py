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

import pickle
from typing import Any, Dict, Tuple

from pytest import raises

from elasticsearch.dsl import Q, serializer, utils


def test_attrdict_pickle() -> None:
    ad: utils.AttrDict[str] = utils.AttrDict({})

    pickled_ad = pickle.dumps(ad)
    assert ad == pickle.loads(pickled_ad)


def test_attrlist_pickle() -> None:
    al = utils.AttrList[Any]([])

    pickled_al = pickle.dumps(al)
    assert al == pickle.loads(pickled_al)


def test_attrlist_slice() -> None:
    class MyAttrDict(utils.AttrDict[str]):
        pass

    l = utils.AttrList[Any]([{}, {}], obj_wrapper=MyAttrDict)
    assert isinstance(l[:][0], MyAttrDict)


def test_attrlist_with_type_argument() -> None:
    a = utils.AttrList[str](["a", "b"])
    assert list(a) == ["a", "b"]


def test_attrdict_keys_items() -> None:
    a = utils.AttrDict({"a": {"b": 42, "c": 47}, "d": "e"})
    assert list(a.keys()) == ["a", "d"]
    assert list(a.items()) == [("a", {"b": 42, "c": 47}), ("d", "e")]


def test_attrdict_with_type_argument() -> None:
    a = utils.AttrDict[str]({"a": "b"})
    assert list(a.keys()) == ["a"]
    assert list(a.items()) == [("a", "b")]


def test_merge() -> None:
    a: utils.AttrDict[Any] = utils.AttrDict({"a": {"b": 42, "c": 47}})
    b = {"a": {"b": 123, "d": -12}, "e": [1, 2, 3]}

    utils.merge(a, b)

    assert a == {"a": {"b": 123, "c": 47, "d": -12}, "e": [1, 2, 3]}


def test_merge_conflict() -> None:
    data: Tuple[Dict[str, Any], ...] = (
        {"a": 42},
        {"a": {"b": 47}},
    )
    for d in data:
        utils.merge({"a": {"b": 42}}, d)
        with raises(ValueError):
            utils.merge({"a": {"b": 42}}, d, True)


def test_attrdict_bool() -> None:
    d: utils.AttrDict[str] = utils.AttrDict({})

    assert not d
    d.title = "Title"
    assert d


def test_attrlist_items_get_wrapped_during_iteration() -> None:
    al = utils.AttrList([1, object(), [1], {}])

    l = list(iter(al))

    assert isinstance(l[2], utils.AttrList)
    assert isinstance(l[3], utils.AttrDict)


def test_serializer_deals_with_Attr_versions() -> None:
    d = utils.AttrDict({"key": utils.AttrList([1, 2, 3])})

    assert serializer.serializer.dumps(d) == serializer.serializer.dumps(
        {"key": [1, 2, 3]}
    )


def test_serializer_deals_with_objects_with_to_dict() -> None:
    class MyClass:
        def to_dict(self) -> int:
            return 42

    assert serializer.serializer.dumps(MyClass()) == b"42"


def test_recursive_to_dict() -> None:
    assert utils.recursive_to_dict({"k": [1, (1.0, {"v": Q("match", key="val")})]}) == {
        "k": [1, (1.0, {"v": {"match": {"key": "val"}}})]
    }


def test_attrlist_to_list() -> None:
    l = utils.AttrList[Any]([{}, {}]).to_list()
    assert isinstance(l, list)
    assert l == [{}, {}]


def test_attrdict_with_reserved_keyword() -> None:
    d = utils.AttrDict({"from": 10, "size": 20})
    assert d.from_ == 10
    assert d.size == 20
    d = utils.AttrDict({})
    d.from_ = 10
    assert {"from": 10} == d.to_dict()
