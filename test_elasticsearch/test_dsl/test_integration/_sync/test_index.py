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

import pytest

from elasticsearch import Elasticsearch
from elasticsearch.dsl import (
    ComposableIndexTemplate,
    Date,
    Document,
    Index,
    IndexTemplate,
    Text,
    analysis,
)


class Post(Document):
    title = Text(analyzer=analysis.analyzer("my_analyzer", tokenizer="keyword"))
    published_from = Date()


@pytest.mark.sync
def test_index_template_works(write_client: Elasticsearch) -> None:
    it = IndexTemplate("test-template", "test-legacy-*")
    it.document(Post)
    it.settings(number_of_replicas=0, number_of_shards=1)
    it.save()

    i = Index("test-legacy-blog")
    i.create()

    assert {
        "test-legacy-blog": {
            "mappings": {
                "properties": {
                    "title": {"type": "text", "analyzer": "my_analyzer"},
                    "published_from": {"type": "date"},
                }
            }
        }
    } == write_client.indices.get_mapping(index="test-legacy-blog")


@pytest.mark.sync
def test_composable_index_template_works(
    write_client: Elasticsearch,
) -> None:
    it = ComposableIndexTemplate("test-template", "test-*")
    it.document(Post)
    it.settings(number_of_replicas=0, number_of_shards=1)
    it.save()

    i = Index("test-blog")
    i.create()

    assert {
        "test-blog": {
            "mappings": {
                "properties": {
                    "title": {"type": "text", "analyzer": "my_analyzer"},
                    "published_from": {"type": "date"},
                }
            }
        }
    } == write_client.indices.get_mapping(index="test-blog")


@pytest.mark.sync
def test_index_can_be_saved_even_with_settings(
    write_client: Elasticsearch,
) -> None:
    i = Index("test-blog", using=write_client)
    i.settings(number_of_shards=3, number_of_replicas=0)
    i.save()
    i.settings(number_of_replicas=1)
    i.save()

    assert (
        "1"
        == (i.get_settings())["test-blog"]["settings"]["index"]["number_of_replicas"]
    )


@pytest.mark.sync
def test_index_exists(data_client: Elasticsearch) -> None:
    assert Index("git").exists()
    assert not Index("not-there").exists()


@pytest.mark.sync
def test_index_can_be_created_with_settings_and_mappings(
    write_client: Elasticsearch,
) -> None:
    i = Index("test-blog", using=write_client)
    i.document(Post)
    i.settings(number_of_replicas=0, number_of_shards=1)
    i.create()

    assert {
        "test-blog": {
            "mappings": {
                "properties": {
                    "title": {"type": "text", "analyzer": "my_analyzer"},
                    "published_from": {"type": "date"},
                }
            }
        }
    } == write_client.indices.get_mapping(index="test-blog")

    settings = write_client.indices.get_settings(index="test-blog")
    assert settings["test-blog"]["settings"]["index"]["number_of_replicas"] == "0"
    assert settings["test-blog"]["settings"]["index"]["number_of_shards"] == "1"
    assert settings["test-blog"]["settings"]["index"]["analysis"] == {
        "analyzer": {"my_analyzer": {"type": "custom", "tokenizer": "keyword"}}
    }


@pytest.mark.sync
def test_delete(write_client: Elasticsearch) -> None:
    write_client.indices.create(
        index="test-index",
        body={"settings": {"number_of_replicas": 0, "number_of_shards": 1}},
    )

    i = Index("test-index", using=write_client)
    i.delete()
    assert not write_client.indices.exists(index="test-index")


@pytest.mark.sync
def test_multiple_indices_with_same_doc_type_work(
    write_client: Elasticsearch,
) -> None:
    i1 = Index("test-index-1", using=write_client)
    i2 = Index("test-index-2", using=write_client)

    for i in (i1, i2):
        i.document(Post)
        i.create()

    for j in ("test-index-1", "test-index-2"):
        settings = write_client.indices.get_settings(index=j)
        assert settings[j]["settings"]["index"]["analysis"] == {
            "analyzer": {"my_analyzer": {"type": "custom", "tokenizer": "keyword"}}
        }
