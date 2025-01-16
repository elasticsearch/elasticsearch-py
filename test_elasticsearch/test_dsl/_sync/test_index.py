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

import string
from random import choice
from typing import Any, Dict

import pytest
from pytest import raises

from elasticsearch.dsl import Date, Document, Index, IndexTemplate, Text, analyzer


class Post(Document):
    title = Text()
    published_from = Date()


def test_multiple_doc_types_will_combine_mappings() -> None:
    class User(Document):
        username = Text()

    i = Index("i")
    i.document(Post)
    i.document(User)
    assert {
        "mappings": {
            "properties": {
                "title": {"type": "text"},
                "username": {"type": "text"},
                "published_from": {"type": "date"},
            }
        }
    } == i.to_dict()


def test_search_is_limited_to_index_name() -> None:
    i = Index("my-index")
    s = i.search()

    assert s._index == ["my-index"]


def test_cloned_index_has_copied_settings_and_using() -> None:
    client = object()
    i = Index("my-index", using=client)  # type: ignore[arg-type]
    i.settings(number_of_shards=1)

    i2 = i.clone("my-other-index")

    assert "my-other-index" == i2._name
    assert client is i2._using
    assert i._settings == i2._settings
    assert i._settings is not i2._settings


def test_cloned_index_has_analysis_attribute() -> None:
    """
    Regression test for Issue #582 in which `AsyncIndex.clone()` was not copying
    over the `_analysis` attribute.
    """
    client = object()
    i = Index("my-index", using=client)  # type: ignore[arg-type]

    random_analyzer_name = "".join(choice(string.ascii_letters) for _ in range(100))
    random_analyzer = analyzer(
        random_analyzer_name, tokenizer="standard", filter="standard"
    )

    i.analyzer(random_analyzer)

    i2 = i.clone("my-clone-index")

    assert i.to_dict()["settings"]["analysis"] == i2.to_dict()["settings"]["analysis"]


def test_settings_are_saved() -> None:
    i = Index("i")
    i.settings(number_of_replicas=0)
    i.settings(number_of_shards=1)

    assert {"settings": {"number_of_shards": 1, "number_of_replicas": 0}} == i.to_dict()


def test_registered_doc_type_included_in_to_dict() -> None:
    i = Index("i", using="alias")
    i.document(Post)

    assert {
        "mappings": {
            "properties": {
                "title": {"type": "text"},
                "published_from": {"type": "date"},
            }
        }
    } == i.to_dict()


def test_registered_doc_type_included_in_search() -> None:
    i = Index("i", using="alias")
    i.document(Post)

    s = i.search()

    assert s._doc_type == [Post]


def test_aliases_add_to_object() -> None:
    random_alias = "".join(choice(string.ascii_letters) for _ in range(100))
    alias_dict: Dict[str, Any] = {random_alias: {}}

    index = Index("i", using="alias")
    index.aliases(**alias_dict)

    assert index._aliases == alias_dict


def test_aliases_returned_from_to_dict() -> None:
    random_alias = "".join(choice(string.ascii_letters) for _ in range(100))
    alias_dict: Dict[str, Any] = {random_alias: {}}

    index = Index("i", using="alias")
    index.aliases(**alias_dict)

    assert index._aliases == index.to_dict()["aliases"] == alias_dict


def test_analyzers_added_to_object() -> None:
    random_analyzer_name = "".join(choice(string.ascii_letters) for _ in range(100))
    random_analyzer = analyzer(
        random_analyzer_name, tokenizer="standard", filter="standard"
    )

    index = Index("i", using="alias")
    index.analyzer(random_analyzer)

    assert index._analysis["analyzer"][random_analyzer_name] == {
        "filter": ["standard"],
        "type": "custom",
        "tokenizer": "standard",
    }


def test_analyzers_returned_from_to_dict() -> None:
    random_analyzer_name = "".join(choice(string.ascii_letters) for _ in range(100))
    random_analyzer = analyzer(
        random_analyzer_name, tokenizer="standard", filter="standard"
    )
    index = Index("i", using="alias")
    index.analyzer(random_analyzer)

    assert index.to_dict()["settings"]["analysis"]["analyzer"][
        random_analyzer_name
    ] == {"filter": ["standard"], "type": "custom", "tokenizer": "standard"}


def test_conflicting_analyzer_raises_error() -> None:
    i = Index("i")
    i.analyzer("my_analyzer", tokenizer="whitespace", filter=["lowercase", "stop"])

    with raises(ValueError):
        i.analyzer("my_analyzer", tokenizer="keyword", filter=["lowercase", "stop"])


def test_index_template_can_have_order() -> None:
    i = Index("i-*")
    it = i.as_template("i", order=2)

    assert {"index_patterns": ["i-*"], "order": 2} == it.to_dict()


@pytest.mark.sync
def test_index_template_save_result(mock_client: Any) -> None:
    it = IndexTemplate("test-template", "test-*")

    assert it.save(using="mock") == mock_client.indices.put_template()
