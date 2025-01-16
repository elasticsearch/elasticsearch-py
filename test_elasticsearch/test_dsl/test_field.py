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

import base64
import ipaddress
from datetime import date, datetime, time
from typing import cast

import pytest
from dateutil import tz

from elasticsearch.dsl import InnerDoc, Range, ValidationException, field


def test_date_range_deserialization() -> None:
    data = {"lt": "2018-01-01T00:30:10"}

    r = field.DateRange().deserialize(data)

    assert isinstance(r, Range)
    assert r.lt == datetime(2018, 1, 1, 0, 30, 10)


def test_boolean_deserialization() -> None:
    bf = field.Boolean()

    assert not bf.deserialize("false")
    assert not bf.deserialize(False)
    assert not bf.deserialize("")
    assert not bf.deserialize(0)

    assert bf.deserialize(True)
    assert bf.deserialize("true")
    assert bf.deserialize(1)


def test_datetime_deserialization() -> None:
    f = field.Date()
    dt = datetime.now()
    assert dt == f._deserialize(dt.isoformat())

    d = date.today()
    assert datetime.combine(d, time()) == f._deserialize(d.isoformat())


def test_date_deserialization() -> None:
    f = field.Date(format="yyyy-MM-dd")
    d = date.today()
    assert d == f._deserialize(d.isoformat())

    dt = datetime.now()
    assert dt.date() == f._deserialize(dt.isoformat())


def test_date_field_can_have_default_tz() -> None:
    f = field.Date(default_timezone="UTC")
    now = datetime.now()

    now_with_tz = cast(datetime, f._deserialize(now))

    assert now_with_tz.tzinfo == tz.gettz("UTC")
    assert now.isoformat() + "+00:00" == now_with_tz.isoformat()

    now_with_tz = cast(datetime, f._deserialize(now.isoformat()))

    assert now_with_tz.tzinfo == tz.gettz("UTC")
    assert now.isoformat() + "+00:00" == now_with_tz.isoformat()


def test_custom_field_car_wrap_other_field() -> None:
    class MyField(field.CustomField):
        @property
        def builtin_type(self) -> field.Text:
            return field.Text(**self._params)

    assert {"type": "text", "index": "not_analyzed"} == MyField(
        index="not_analyzed"
    ).to_dict()


def test_field_from_dict() -> None:
    f = field.construct_field({"type": "text", "index": "not_analyzed"})

    assert isinstance(f, field.Text)
    assert {"type": "text", "index": "not_analyzed"} == f.to_dict()


def test_multi_fields_are_accepted_and_parsed() -> None:
    f = field.construct_field(
        "text",
        fields={"raw": {"type": "keyword"}, "eng": field.Text(analyzer="english")},
    )

    assert isinstance(f, field.Text)
    assert {
        "type": "text",
        "fields": {
            "raw": {"type": "keyword"},
            "eng": {"type": "text", "analyzer": "english"},
        },
    } == f.to_dict()


def test_nested_provides_direct_access_to_its_fields() -> None:
    f = field.Nested(properties={"name": {"type": "text", "index": "not_analyzed"}})

    assert "name" in f
    assert f["name"] == field.Text(index="not_analyzed")


def test_field_supports_multiple_analyzers() -> None:
    f = field.Text(analyzer="snowball", search_analyzer="keyword")
    assert {
        "analyzer": "snowball",
        "search_analyzer": "keyword",
        "type": "text",
    } == f.to_dict()


def test_multifield_supports_multiple_analyzers() -> None:
    f = field.Text(
        fields={
            "f1": field.Text(search_analyzer="keyword", analyzer="snowball"),
            "f2": field.Text(analyzer="keyword"),
        }
    )
    assert {
        "fields": {
            "f1": {
                "analyzer": "snowball",
                "search_analyzer": "keyword",
                "type": "text",
            },
            "f2": {"analyzer": "keyword", "type": "text"},
        },
        "type": "text",
    } == f.to_dict()


def test_scaled_float() -> None:
    with pytest.raises(TypeError):
        field.ScaledFloat()  # type: ignore
    f = field.ScaledFloat(123)
    assert f.to_dict() == {"scaling_factor": 123, "type": "scaled_float"}


def test_ipaddress() -> None:
    f = field.Ip()
    assert f.deserialize("127.0.0.1") == ipaddress.ip_address("127.0.0.1")
    assert f.deserialize("::1") == ipaddress.ip_address("::1")
    assert f.serialize(f.deserialize("::1")) == "::1"
    assert f.deserialize(None) is None
    with pytest.raises(ValueError):
        assert f.deserialize("not_an_ipaddress")


def test_float() -> None:
    f = field.Float()
    assert f.deserialize("42") == 42.0
    assert f.deserialize(None) is None
    with pytest.raises(ValueError):
        assert f.deserialize("not_a_float")


def test_integer() -> None:
    f = field.Integer()
    assert f.deserialize("42") == 42
    assert f.deserialize(None) is None
    with pytest.raises(ValueError):
        assert f.deserialize("not_an_integer")


def test_binary() -> None:
    f = field.Binary()
    assert f.deserialize(base64.b64encode(b"42")) == b"42"
    assert f.deserialize(f.serialize(b"42")) == b"42"
    assert f.deserialize(None) is None


def test_constant_keyword() -> None:
    f = field.ConstantKeyword()
    assert f.to_dict() == {"type": "constant_keyword"}


def test_rank_features() -> None:
    f = field.RankFeatures()
    assert f.to_dict() == {"type": "rank_features"}


def test_object_dynamic_values() -> None:
    f = field.Object(dynamic=True)
    assert f.to_dict()["dynamic"] is True
    f = field.Object(dynamic=False)
    assert f.to_dict()["dynamic"] is False
    f = field.Object(dynamic="strict")
    assert f.to_dict()["dynamic"] == "strict"


def test_object_disabled() -> None:
    f = field.Object(enabled=False)
    assert f.to_dict() == {"type": "object", "enabled": False}


def test_object_constructor() -> None:
    expected = {"type": "object", "properties": {"inner_int": {"type": "integer"}}}

    class Inner(InnerDoc):
        inner_int = field.Integer()

    obj_from_doc = field.Object(doc_class=Inner)
    assert obj_from_doc.to_dict() == expected

    obj_from_props = field.Object(properties={"inner_int": field.Integer()})
    assert obj_from_props.to_dict() == expected

    with pytest.raises(ValidationException):
        field.Object(doc_class=Inner, properties={"inner_int": field.Integer()})

    with pytest.raises(ValidationException):
        field.Object(doc_class=Inner, dynamic=False)
