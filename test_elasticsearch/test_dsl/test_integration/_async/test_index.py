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

from elasticsearch import AsyncElasticsearch
from elasticsearch.dsl import (
    AsyncComposableIndexTemplate,
    AsyncDocument,
    AsyncIndex,
    AsyncIndexTemplate,
    Date,
    Text,
    analysis,
)


class Post(AsyncDocument):
    title = Text(analyzer=analysis.analyzer("my_analyzer", tokenizer="keyword"))
    published_from = Date()


@pytest.mark.asyncio
async def test_index_template_works(async_write_client: AsyncElasticsearch) -> None:
    it = AsyncIndexTemplate("test-template", "test-legacy-*")
    it.document(Post)
    it.settings(number_of_replicas=0, number_of_shards=1)
    await it.save()

    i = AsyncIndex("test-legacy-blog")
    await i.create()

    assert {
        "test-legacy-blog": {
            "mappings": {
                "properties": {
                    "title": {"type": "text", "analyzer": "my_analyzer"},
                    "published_from": {"type": "date"},
                }
            }
        }
    } == await async_write_client.indices.get_mapping(index="test-legacy-blog")


@pytest.mark.asyncio
async def test_composable_index_template_works(
    async_write_client: AsyncElasticsearch,
) -> None:
    it = AsyncComposableIndexTemplate("test-template", "test-*")
    it.document(Post)
    it.settings(number_of_replicas=0, number_of_shards=1)
    await it.save()

    i = AsyncIndex("test-blog")
    await i.create()

    assert {
        "test-blog": {
            "mappings": {
                "properties": {
                    "title": {"type": "text", "analyzer": "my_analyzer"},
                    "published_from": {"type": "date"},
                }
            }
        }
    } == await async_write_client.indices.get_mapping(index="test-blog")


@pytest.mark.asyncio
async def test_index_can_be_saved_even_with_settings(
    async_write_client: AsyncElasticsearch,
) -> None:
    i = AsyncIndex("test-blog", using=async_write_client)
    i.settings(number_of_shards=3, number_of_replicas=0)
    await i.save()
    i.settings(number_of_replicas=1)
    await i.save()

    assert (
        "1"
        == (await i.get_settings())["test-blog"]["settings"]["index"][
            "number_of_replicas"
        ]
    )


@pytest.mark.asyncio
async def test_index_exists(async_data_client: AsyncElasticsearch) -> None:
    assert await AsyncIndex("git").exists()
    assert not await AsyncIndex("not-there").exists()


@pytest.mark.asyncio
async def test_index_can_be_created_with_settings_and_mappings(
    async_write_client: AsyncElasticsearch,
) -> None:
    i = AsyncIndex("test-blog", using=async_write_client)
    i.document(Post)
    i.settings(number_of_replicas=0, number_of_shards=1)
    await i.create()

    assert {
        "test-blog": {
            "mappings": {
                "properties": {
                    "title": {"type": "text", "analyzer": "my_analyzer"},
                    "published_from": {"type": "date"},
                }
            }
        }
    } == await async_write_client.indices.get_mapping(index="test-blog")

    settings = await async_write_client.indices.get_settings(index="test-blog")
    assert settings["test-blog"]["settings"]["index"]["number_of_replicas"] == "0"
    assert settings["test-blog"]["settings"]["index"]["number_of_shards"] == "1"
    assert settings["test-blog"]["settings"]["index"]["analysis"] == {
        "analyzer": {"my_analyzer": {"type": "custom", "tokenizer": "keyword"}}
    }


@pytest.mark.asyncio
async def test_delete(async_write_client: AsyncElasticsearch) -> None:
    await async_write_client.indices.create(
        index="test-index",
        body={"settings": {"number_of_replicas": 0, "number_of_shards": 1}},
    )

    i = AsyncIndex("test-index", using=async_write_client)
    await i.delete()
    assert not await async_write_client.indices.exists(index="test-index")


@pytest.mark.asyncio
async def test_multiple_indices_with_same_doc_type_work(
    async_write_client: AsyncElasticsearch,
) -> None:
    i1 = AsyncIndex("test-index-1", using=async_write_client)
    i2 = AsyncIndex("test-index-2", using=async_write_client)

    for i in (i1, i2):
        i.document(Post)
        await i.create()

    for j in ("test-index-1", "test-index-2"):
        settings = await async_write_client.indices.get_settings(index=j)
        assert settings[j]["settings"]["index"]["analysis"] == {
            "analyzer": {"my_analyzer": {"type": "custom", "tokenizer": "keyword"}}
        }
