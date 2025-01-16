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

# this file creates several documents using bad or no types because
# these are still supported and should be kept functional in spite
# of not having appropriate type hints. For that reason the comment
# below disables many mypy checks that fails as a result of this.
# mypy: disable-error-code="assignment, index, arg-type, call-arg, operator, comparison-overlap, attr-defined"

import codecs
import ipaddress
import pickle
import sys
from datetime import datetime
from hashlib import md5
from typing import Any, ClassVar, Dict, List, Optional

import pytest
from pytest import raises

from elasticsearch.dsl import (
    Document,
    Index,
    InnerDoc,
    M,
    Mapping,
    MetaField,
    Range,
    analyzer,
    field,
    mapped_field,
    utils,
)
from elasticsearch.dsl.document_base import InstrumentedField
from elasticsearch.dsl.exceptions import IllegalOperation, ValidationException


class MyInner(InnerDoc):
    old_field = field.Text()


class MyDoc(Document):
    title = field.Keyword()
    name = field.Text()
    created_at = field.Date()
    inner = field.Object(MyInner)


class MySubDoc(MyDoc):
    name = field.Keyword()

    class Index:
        name = "default-index"


class MyDoc2(Document):
    extra = field.Long()


class MyMultiSubDoc(MyDoc2, MySubDoc):
    pass


class Comment(InnerDoc):
    title = field.Text()
    tags = field.Keyword(multi=True)


class DocWithNested(Document):
    comments = field.Nested(Comment)

    class Index:
        name = "test-doc-with-nested"


class SimpleCommit(Document):
    files = field.Text(multi=True)

    class Index:
        name = "test-git"


class Secret(str):
    pass


class SecretField(field.CustomField):
    builtin_type = "text"

    def _serialize(self, data: Any) -> Any:
        return codecs.encode(data, "rot_13")

    def _deserialize(self, data: Any) -> Any:
        if isinstance(data, Secret):
            return data
        return Secret(codecs.decode(data, "rot_13"))


class SecretDoc(Document):
    title = SecretField(index="no")

    class Index:
        name = "test-secret-doc"


class NestedSecret(Document):
    secrets = field.Nested(SecretDoc)

    class Index:
        name = "test-nested-secret"


class OptionalObjectWithRequiredField(Document):
    comments = field.Nested(properties={"title": field.Keyword(required=True)})

    class Index:
        name = "test-required"


class Host(Document):
    ip = field.Ip()

    class Index:
        name = "test-host"


def test_range_serializes_properly() -> None:
    class D(Document):
        lr: Range[int] = field.LongRange()

    d = D(lr=Range(lt=42))
    assert 40 in d.lr
    assert 47 not in d.lr
    assert {"lr": {"lt": 42}} == d.to_dict()

    d = D(lr={"lt": 42})
    assert {"lr": {"lt": 42}} == d.to_dict()


def test_range_deserializes_properly() -> None:
    class D(InnerDoc):
        lr = field.LongRange()

    d = D.from_es({"lr": {"lt": 42}}, True)
    assert isinstance(d.lr, Range)
    assert 40 in d.lr
    assert 47 not in d.lr


def test_resolve_nested() -> None:
    nested, field = NestedSecret._index.resolve_nested("secrets.title")
    assert nested == ["secrets"]
    assert field is NestedSecret._doc_type.mapping["secrets"]["title"]


def test_conflicting_mapping_raises_error_in_index_to_dict() -> None:
    class A(Document):
        name = field.Text()

    class B(Document):
        name = field.Keyword()

    i = Index("i")
    i.document(A)
    i.document(B)

    with raises(ValueError):
        i.to_dict()


def test_ip_address_serializes_properly() -> None:
    host = Host(ip=ipaddress.IPv4Address("10.0.0.1"))

    assert {"ip": "10.0.0.1"} == host.to_dict()


def test_matches_uses_index() -> None:
    assert SimpleCommit._matches({"_index": "test-git"})
    assert not SimpleCommit._matches({"_index": "not-test-git"})


def test_matches_with_no_name_always_matches() -> None:
    class D(Document):
        pass

    assert D._matches({})
    assert D._matches({"_index": "whatever"})


def test_matches_accepts_wildcards() -> None:
    class MyDoc(Document):
        class Index:
            name = "my-*"

    assert MyDoc._matches({"_index": "my-index"})
    assert not MyDoc._matches({"_index": "not-my-index"})


def test_assigning_attrlist_to_field() -> None:
    sc = SimpleCommit()
    l = ["README", "README.rst"]
    sc.files = utils.AttrList(l)

    assert sc.to_dict()["files"] is l


def test_optional_inner_objects_are_not_validated_if_missing() -> None:
    d = OptionalObjectWithRequiredField()

    d.full_clean()


def test_custom_field() -> None:
    s = SecretDoc(title=Secret("Hello"))

    assert {"title": "Uryyb"} == s.to_dict()
    assert s.title == "Hello"

    s = SecretDoc.from_es({"_source": {"title": "Uryyb"}})
    assert s.title == "Hello"
    assert isinstance(s.title, Secret)


def test_custom_field_mapping() -> None:
    assert {
        "properties": {"title": {"index": "no", "type": "text"}}
    } == SecretDoc._doc_type.mapping.to_dict()


def test_custom_field_in_nested() -> None:
    s = NestedSecret()
    s.secrets.append(SecretDoc(title=Secret("Hello")))

    assert {"secrets": [{"title": "Uryyb"}]} == s.to_dict()
    assert s.secrets[0].title == "Hello"


def test_multi_works_after_doc_has_been_saved() -> None:
    c = SimpleCommit()
    c.full_clean()
    c.files.append("setup.py")

    assert c.to_dict() == {"files": ["setup.py"]}


def test_multi_works_in_nested_after_doc_has_been_serialized() -> None:
    # Issue #359
    c = DocWithNested(comments=[Comment(title="First!")])

    assert [] == c.comments[0].tags
    assert {"comments": [{"title": "First!"}]} == c.to_dict()
    assert [] == c.comments[0].tags


def test_null_value_for_object() -> None:
    d = MyDoc(inner=None)

    assert d.inner is None


def test_inherited_doc_types_can_override_index() -> None:
    class MyDocDifferentIndex(MySubDoc):
        class Index:
            name = "not-default-index"
            settings = {"number_of_replicas": 0}
            aliases: Dict[str, Any] = {"a": {}}
            analyzers = [analyzer("my_analizer", tokenizer="keyword")]

    assert MyDocDifferentIndex._index._name == "not-default-index"
    assert MyDocDifferentIndex()._get_index() == "not-default-index"
    assert MyDocDifferentIndex._index.to_dict() == {
        "aliases": {"a": {}},
        "mappings": {
            "properties": {
                "created_at": {"type": "date"},
                "inner": {
                    "type": "object",
                    "properties": {"old_field": {"type": "text"}},
                },
                "name": {"type": "keyword"},
                "title": {"type": "keyword"},
            }
        },
        "settings": {
            "analysis": {
                "analyzer": {"my_analizer": {"tokenizer": "keyword", "type": "custom"}}
            },
            "number_of_replicas": 0,
        },
    }


def test_to_dict_with_meta() -> None:
    d = MySubDoc(title="hello")
    d.meta.routing = "some-parent"

    assert {
        "_index": "default-index",
        "_routing": "some-parent",
        "_source": {"title": "hello"},
    } == d.to_dict(True)


def test_to_dict_with_meta_includes_custom_index() -> None:
    d = MySubDoc(title="hello")
    d.meta.index = "other-index"

    assert {"_index": "other-index", "_source": {"title": "hello"}} == d.to_dict(True)


def test_to_dict_without_skip_empty_will_include_empty_fields() -> None:
    d = MySubDoc(tags=[], title=None, inner={})

    assert {} == d.to_dict()
    assert {"tags": [], "title": None, "inner": {}} == d.to_dict(skip_empty=False)


def test_attribute_can_be_removed() -> None:
    d = MyDoc(title="hello")

    del d.title
    assert "title" not in d._d_


def test_doc_type_can_be_correctly_pickled() -> None:
    d = DocWithNested(
        title="Hello World!", comments=[Comment(title="hellp")], meta={"id": 42}
    )
    s = pickle.dumps(d)

    d2 = pickle.loads(s)

    assert d2 == d
    assert 42 == d2.meta.id
    assert "Hello World!" == d2.title
    assert [{"title": "hellp"}] == d2.comments
    assert isinstance(d2.comments[0], Comment)


def test_meta_is_accessible_even_on_empty_doc() -> None:
    d = MyDoc()
    d.meta

    d = MyDoc(title="aaa")
    d.meta


def test_meta_field_mapping() -> None:
    class User(Document):
        username = field.Text()

        class Meta:
            all = MetaField(enabled=False)
            _index = MetaField(enabled=True)
            dynamic = MetaField("strict")
            dynamic_templates = MetaField([42])

    assert {
        "properties": {"username": {"type": "text"}},
        "_all": {"enabled": False},
        "_index": {"enabled": True},
        "dynamic": "strict",
        "dynamic_templates": [42],
    } == User._doc_type.mapping.to_dict()


def test_multi_value_fields() -> None:
    class Blog(Document):
        tags = field.Keyword(multi=True)

    b = Blog()
    assert [] == b.tags
    b.tags.append("search")
    b.tags.append("python")
    assert ["search", "python"] == b.tags


def test_docs_with_properties() -> None:
    class User(Document):
        pwd_hash: str = field.Text()

        def check_password(self, pwd: bytes) -> bool:
            return md5(pwd).hexdigest() == self.pwd_hash

        @property
        def password(self) -> None:
            raise AttributeError("readonly")

        @password.setter
        def password(self, pwd: bytes) -> None:
            self.pwd_hash = md5(pwd).hexdigest()

    u = User(pwd_hash=md5(b"secret").hexdigest())
    assert u.check_password(b"secret")
    assert not u.check_password(b"not-secret")

    u.password = b"not-secret"
    assert "password" not in u._d_
    assert not u.check_password(b"secret")
    assert u.check_password(b"not-secret")

    with raises(AttributeError):
        u.password


def test_nested_can_be_assigned_to() -> None:
    d1 = DocWithNested(comments=[Comment(title="First!")])
    d2 = DocWithNested()

    d2.comments = d1.comments
    assert isinstance(d1.comments[0], Comment)
    assert d2.comments == [{"title": "First!"}]
    assert {"comments": [{"title": "First!"}]} == d2.to_dict()
    assert isinstance(d2.comments[0], Comment)


def test_nested_can_be_none() -> None:
    d = DocWithNested(comments=None, title="Hello World!")

    assert {"title": "Hello World!"} == d.to_dict()


def test_nested_defaults_to_list_and_can_be_updated() -> None:
    md = DocWithNested()

    assert [] == md.comments

    md.comments.append({"title": "hello World!"})
    assert {"comments": [{"title": "hello World!"}]} == md.to_dict()


def test_to_dict_is_recursive_and_can_cope_with_multi_values() -> None:
    md = MyDoc(name=["a", "b", "c"])
    md.inner = [MyInner(old_field="of1"), MyInner(old_field="of2")]

    assert isinstance(md.inner[0], MyInner)

    assert {
        "name": ["a", "b", "c"],
        "inner": [{"old_field": "of1"}, {"old_field": "of2"}],
    } == md.to_dict()


def test_to_dict_ignores_empty_collections() -> None:
    md = MySubDoc(name="", address={}, count=0, valid=False, tags=[])

    assert {"name": "", "count": 0, "valid": False} == md.to_dict()


def test_declarative_mapping_definition() -> None:
    assert issubclass(MyDoc, Document)
    assert hasattr(MyDoc, "_doc_type")
    assert {
        "properties": {
            "created_at": {"type": "date"},
            "name": {"type": "text"},
            "title": {"type": "keyword"},
            "inner": {"type": "object", "properties": {"old_field": {"type": "text"}}},
        }
    } == MyDoc._doc_type.mapping.to_dict()


def test_you_can_supply_own_mapping_instance() -> None:
    class MyD(Document):
        title = field.Text()

        class Meta:
            mapping = Mapping()
            mapping.meta("_all", enabled=False)

    assert {
        "_all": {"enabled": False},
        "properties": {"title": {"type": "text"}},
    } == MyD._doc_type.mapping.to_dict()


def test_document_can_be_created_dynamically() -> None:
    n = datetime.now()
    md = MyDoc(title="hello")
    md.name = "My Fancy Document!"
    md.created_at = n

    inner = md.inner
    # consistent returns
    assert inner is md.inner
    inner.old_field = "Already defined."

    md.inner.new_field = ["undefined", "field"]

    assert {
        "title": "hello",
        "name": "My Fancy Document!",
        "created_at": n,
        "inner": {"old_field": "Already defined.", "new_field": ["undefined", "field"]},
    } == md.to_dict()


def test_invalid_date_will_raise_exception() -> None:
    md = MyDoc()
    md.created_at = "not-a-date"
    with raises(ValidationException):
        md.full_clean()


def test_document_inheritance() -> None:
    assert issubclass(MySubDoc, MyDoc)
    assert issubclass(MySubDoc, Document)
    assert hasattr(MySubDoc, "_doc_type")
    assert {
        "properties": {
            "created_at": {"type": "date"},
            "name": {"type": "keyword"},
            "title": {"type": "keyword"},
            "inner": {"type": "object", "properties": {"old_field": {"type": "text"}}},
        }
    } == MySubDoc._doc_type.mapping.to_dict()


def test_child_class_can_override_parent() -> None:
    class A(Document):
        o = field.Object(dynamic=False, properties={"a": field.Text()})

    class B(A):
        o = field.Object(dynamic="strict", properties={"b": field.Text()})

    assert {
        "properties": {
            "o": {
                "dynamic": "strict",
                "properties": {"a": {"type": "text"}, "b": {"type": "text"}},
                "type": "object",
            }
        }
    } == B._doc_type.mapping.to_dict()


def test_meta_fields_are_stored_in_meta_and_ignored_by_to_dict() -> None:
    md = MySubDoc(meta={"id": 42}, name="My First doc!")

    md.meta.index = "my-index"
    assert md.meta.index == "my-index"
    assert md.meta.id == 42
    assert {"name": "My First doc!"} == md.to_dict()
    assert {"id": 42, "index": "my-index"} == md.meta.to_dict()


def test_index_inheritance() -> None:
    assert issubclass(MyMultiSubDoc, MySubDoc)
    assert issubclass(MyMultiSubDoc, MyDoc2)
    assert issubclass(MyMultiSubDoc, Document)
    assert hasattr(MyMultiSubDoc, "_doc_type")
    assert hasattr(MyMultiSubDoc, "_index")
    assert {
        "properties": {
            "created_at": {"type": "date"},
            "name": {"type": "keyword"},
            "title": {"type": "keyword"},
            "inner": {"type": "object", "properties": {"old_field": {"type": "text"}}},
            "extra": {"type": "long"},
        }
    } == MyMultiSubDoc._doc_type.mapping.to_dict()


def test_meta_fields_can_be_set_directly_in_init() -> None:
    p = object()
    md = MyDoc(_id=p, title="Hello World!")

    assert md.meta.id is p


@pytest.mark.sync
def test_save_no_index(mock_client: Any) -> None:
    md = MyDoc()
    with raises(ValidationException):
        md.save(using="mock")


@pytest.mark.sync
def test_delete_no_index(mock_client: Any) -> None:
    md = MyDoc()
    with raises(ValidationException):
        md.delete(using="mock")


@pytest.mark.sync
def test_update_no_fields() -> None:
    md = MyDoc()
    with raises(IllegalOperation):
        md.update()


def test_search_with_custom_alias_and_index() -> None:
    search_object = MyDoc.search(
        using="staging", index=["custom_index1", "custom_index2"]
    )

    assert search_object._using == "staging"
    assert search_object._index == ["custom_index1", "custom_index2"]


def test_from_es_respects_underscored_non_meta_fields() -> None:
    doc = {
        "_index": "test-index",
        "_id": "elasticsearch",
        "_score": 12.0,
        "fields": {"hello": "world", "_routing": "es", "_tags": ["search"]},
        "_source": {
            "city": "Amsterdam",
            "name": "Elasticsearch",
            "_tagline": "You know, for search",
        },
    }

    class Company(Document):
        class Index:
            name = "test-company"

    c = Company.from_es(doc)

    assert c.meta.fields._tags == ["search"]
    assert c.meta.fields._routing == "es"
    assert c._tagline == "You know, for search"


def test_nested_and_object_inner_doc() -> None:
    class MySubDocWithNested(MyDoc):
        nested_inner = field.Nested(MyInner)

    props = MySubDocWithNested._doc_type.mapping.to_dict()["properties"]
    assert props == {
        "created_at": {"type": "date"},
        "inner": {"properties": {"old_field": {"type": "text"}}, "type": "object"},
        "name": {"type": "text"},
        "nested_inner": {
            "properties": {"old_field": {"type": "text"}},
            "type": "nested",
        },
        "title": {"type": "keyword"},
    }


def test_doc_with_type_hints() -> None:
    class TypedInnerDoc(InnerDoc):
        st: M[str]
        dt: M[Optional[datetime]]
        li: M[List[int]]

    class TypedDoc(Document):
        st: str
        dt: Optional[datetime]
        li: List[int]
        ob: TypedInnerDoc
        ns: List[TypedInnerDoc]
        ip: Optional[str] = field.Ip()
        k1: str = field.Keyword(required=True)
        k2: M[str] = field.Keyword()
        k3: str = mapped_field(field.Keyword(), default="foo")
        k4: M[Optional[str]] = mapped_field(field.Keyword())  # type: ignore[misc]
        s1: Secret = SecretField()
        s2: M[Secret] = SecretField()
        s3: Secret = mapped_field(SecretField())  # type: ignore[misc]
        s4: M[Optional[Secret]] = mapped_field(
            SecretField(), default_factory=lambda: "foo"
        )
        i1: ClassVar
        i2: ClassVar[int]

    props = TypedDoc._doc_type.mapping.to_dict()["properties"]
    assert props == {
        "st": {"type": "text"},
        "dt": {"type": "date"},
        "li": {"type": "integer"},
        "ob": {
            "type": "object",
            "properties": {
                "st": {"type": "text"},
                "dt": {"type": "date"},
                "li": {"type": "integer"},
            },
        },
        "ns": {
            "type": "nested",
            "properties": {
                "st": {"type": "text"},
                "dt": {"type": "date"},
                "li": {"type": "integer"},
            },
        },
        "ip": {"type": "ip"},
        "k1": {"type": "keyword"},
        "k2": {"type": "keyword"},
        "k3": {"type": "keyword"},
        "k4": {"type": "keyword"},
        "s1": {"type": "text"},
        "s2": {"type": "text"},
        "s3": {"type": "text"},
        "s4": {"type": "text"},
    }

    TypedDoc.i1 = "foo"
    TypedDoc.i2 = 123

    doc = TypedDoc()
    assert doc.k3 == "foo"
    assert doc.s4 == "foo"
    with raises(ValidationException) as exc_info:
        doc.full_clean()
    assert set(exc_info.value.args[0].keys()) == {
        "st",
        "k1",
        "k2",
        "ob",
        "s1",
        "s2",
        "s3",
    }

    assert TypedDoc.i1 == "foo"
    assert TypedDoc.i2 == 123

    doc.st = "s"
    doc.li = [1, 2, 3]
    doc.k1 = "k1"
    doc.k2 = "k2"
    doc.ob.st = "s"
    doc.ob.li = [1]
    doc.s1 = "s1"
    doc.s2 = "s2"
    doc.s3 = "s3"
    doc.full_clean()

    doc.ob = TypedInnerDoc(li=[1])
    with raises(ValidationException) as exc_info:
        doc.full_clean()
    assert set(exc_info.value.args[0].keys()) == {"ob"}
    assert set(exc_info.value.args[0]["ob"][0].args[0].keys()) == {"st"}

    doc.ob.st = "s"
    doc.ns.append(TypedInnerDoc(li=[1, 2]))
    with raises(ValidationException) as exc_info:
        doc.full_clean()

    doc.ns[0].st = "s"
    doc.full_clean()

    doc.ip = "1.2.3.4"
    n = datetime.now()
    doc.dt = n
    assert doc.to_dict() == {
        "st": "s",
        "li": [1, 2, 3],
        "dt": n,
        "ob": {
            "st": "s",
            "li": [1],
        },
        "ns": [
            {
                "st": "s",
                "li": [1, 2],
            }
        ],
        "ip": "1.2.3.4",
        "k1": "k1",
        "k2": "k2",
        "k3": "foo",
        "s1": "s1",
        "s2": "s2",
        "s3": "s3",
        "s4": "foo",
    }

    s = TypedDoc.search().sort(TypedDoc.st, -TypedDoc.dt, +TypedDoc.ob.st)
    s.aggs.bucket("terms_agg", "terms", field=TypedDoc.k1)
    assert s.to_dict() == {
        "aggs": {"terms_agg": {"terms": {"field": "k1"}}},
        "sort": ["st", {"dt": {"order": "desc"}}, "ob.st"],
    }


@pytest.mark.skipif(sys.version_info < (3, 10), reason="requires Python 3.10")
def test_doc_with_pipe_type_hints() -> None:
    with pytest.raises(TypeError):

        class BadlyTypedDoc(Document):
            s: str
            f: str | int | None  # type: ignore[syntax]

    class TypedDoc(Document):
        s: str
        f1: str | None  # type: ignore[syntax]
        f2: M[int | None]  # type: ignore[syntax]
        f3: M[datetime | None]  # type: ignore[syntax]

    props = TypedDoc._doc_type.mapping.to_dict()["properties"]
    assert props == {
        "s": {"type": "text"},
        "f1": {"type": "text"},
        "f2": {"type": "integer"},
        "f3": {"type": "date"},
    }

    doc = TypedDoc()
    with raises(ValidationException) as exc_info:
        doc.full_clean()
    assert set(exc_info.value.args[0].keys()) == {"s"}
    doc.s = "s"
    doc.full_clean()


def test_instrumented_field() -> None:
    class Child(InnerDoc):
        st: M[str]

    class Doc(Document):
        st: str
        ob: Child
        ns: List[Child]

    doc = Doc(
        st="foo",
        ob=Child(st="bar"),
        ns=[
            Child(st="baz"),
            Child(st="qux"),
        ],
    )

    assert type(doc.st) is str
    assert doc.st == "foo"

    assert type(doc.ob) is Child
    assert doc.ob.st == "bar"

    assert type(doc.ns) is utils.AttrList
    assert doc.ns[0].st == "baz"
    assert doc.ns[1].st == "qux"
    assert type(doc.ns[0]) is Child
    assert type(doc.ns[1]) is Child

    assert type(Doc.st) is InstrumentedField
    assert str(Doc.st) == "st"
    assert +Doc.st == "st"
    assert -Doc.st == "-st"
    assert Doc.st.to_dict() == {"type": "text"}
    with raises(AttributeError):
        Doc.st.something

    assert type(Doc.ob) is InstrumentedField
    assert str(Doc.ob) == "ob"
    assert str(Doc.ob.st) == "ob.st"
    assert +Doc.ob.st == "ob.st"
    assert -Doc.ob.st == "-ob.st"
    assert Doc.ob.st.to_dict() == {"type": "text"}
    with raises(AttributeError):
        Doc.ob.something
    with raises(AttributeError):
        Doc.ob.st.something

    assert type(Doc.ns) is InstrumentedField
    assert str(Doc.ns) == "ns"
    assert str(Doc.ns.st) == "ns.st"
    assert +Doc.ns.st == "ns.st"
    assert -Doc.ns.st == "-ns.st"
    assert Doc.ns.st.to_dict() == {"type": "text"}
    with raises(AttributeError):
        Doc.ns.something
    with raises(AttributeError):
        Doc.ns.st.something
