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
from pytest import raises

from elasticsearch import Elasticsearch
from elasticsearch.dsl import Mapping, analysis, exceptions


@pytest.mark.sync
def test_mapping_saved_into_es(write_client: Elasticsearch) -> None:
    m = Mapping()
    m.field(
        "name", "text", analyzer=analysis.analyzer("my_analyzer", tokenizer="keyword")
    )
    m.field("tags", "keyword")
    m.save("test-mapping", using=write_client)

    assert {
        "test-mapping": {
            "mappings": {
                "properties": {
                    "name": {"type": "text", "analyzer": "my_analyzer"},
                    "tags": {"type": "keyword"},
                }
            }
        }
    } == write_client.indices.get_mapping(index="test-mapping")


@pytest.mark.sync
def test_mapping_saved_into_es_when_index_already_exists_closed(
    write_client: Elasticsearch,
) -> None:
    m = Mapping()
    m.field(
        "name", "text", analyzer=analysis.analyzer("my_analyzer", tokenizer="keyword")
    )
    write_client.indices.create(index="test-mapping")

    with raises(exceptions.IllegalOperation):
        m.save("test-mapping", using=write_client)

    write_client.cluster.health(index="test-mapping", wait_for_status="yellow")
    write_client.indices.close(index="test-mapping")
    m.save("test-mapping", using=write_client)

    assert {
        "test-mapping": {
            "mappings": {
                "properties": {"name": {"type": "text", "analyzer": "my_analyzer"}}
            }
        }
    } == write_client.indices.get_mapping(index="test-mapping")


@pytest.mark.sync
def test_mapping_saved_into_es_when_index_already_exists_with_analysis(
    write_client: Elasticsearch,
) -> None:
    m = Mapping()
    analyzer = analysis.analyzer("my_analyzer", tokenizer="keyword")
    m.field("name", "text", analyzer=analyzer)

    new_analysis = analyzer.get_analysis_definition()
    new_analysis["analyzer"]["other_analyzer"] = {
        "type": "custom",
        "tokenizer": "whitespace",
    }
    write_client.indices.create(
        index="test-mapping", body={"settings": {"analysis": new_analysis}}
    )

    m.field("title", "text", analyzer=analyzer)
    m.save("test-mapping", using=write_client)

    assert {
        "test-mapping": {
            "mappings": {
                "properties": {
                    "name": {"type": "text", "analyzer": "my_analyzer"},
                    "title": {"type": "text", "analyzer": "my_analyzer"},
                }
            }
        }
    } == write_client.indices.get_mapping(index="test-mapping")


@pytest.mark.sync
def test_mapping_gets_updated_from_es(
    write_client: Elasticsearch,
) -> None:
    write_client.indices.create(
        index="test-mapping",
        body={
            "settings": {"number_of_shards": 1, "number_of_replicas": 0},
            "mappings": {
                "date_detection": False,
                "properties": {
                    "title": {
                        "type": "text",
                        "analyzer": "snowball",
                        "fields": {"raw": {"type": "keyword"}},
                    },
                    "created_at": {"type": "date"},
                    "comments": {
                        "type": "nested",
                        "properties": {
                            "created": {"type": "date"},
                            "author": {
                                "type": "text",
                                "analyzer": "snowball",
                                "fields": {"raw": {"type": "keyword"}},
                            },
                        },
                    },
                },
            },
        },
    )

    m = Mapping.from_es("test-mapping", using=write_client)

    assert ["comments", "created_at", "title"] == list(
        sorted(m.properties.properties._d_.keys())  # type: ignore[attr-defined]
    )
    assert {
        "date_detection": False,
        "properties": {
            "comments": {
                "type": "nested",
                "properties": {
                    "created": {"type": "date"},
                    "author": {
                        "analyzer": "snowball",
                        "fields": {"raw": {"type": "keyword"}},
                        "type": "text",
                    },
                },
            },
            "created_at": {"type": "date"},
            "title": {
                "analyzer": "snowball",
                "fields": {"raw": {"type": "keyword"}},
                "type": "text",
            },
        },
    } == m.to_dict()

    # test same with alias
    write_client.indices.put_alias(index="test-mapping", name="test-alias")

    m2 = Mapping.from_es("test-alias", using=write_client)
    assert m2.to_dict() == m.to_dict()
