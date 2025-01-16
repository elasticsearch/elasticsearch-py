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

from ..async_examples import alias_migration
from ..async_examples.alias_migration import ALIAS, PATTERN, BlogPost, migrate


@pytest.mark.asyncio
async def test_alias_migration(async_write_client: AsyncElasticsearch) -> None:
    # create the index
    await alias_migration.setup()

    # verify that template, index, and alias has been set up
    assert await async_write_client.indices.exists_index_template(name=ALIAS)
    assert await async_write_client.indices.exists(index=PATTERN)
    assert await async_write_client.indices.exists_alias(name=ALIAS)

    indices = await async_write_client.indices.get(index=PATTERN)
    assert len(indices) == 1
    index_name, _ = indices.popitem()

    # which means we can now save a document
    with open(__file__) as f:
        bp = BlogPost(
            _id=0,
            title="Hello World!",
            tags=["testing", "dummy"],
            content=f.read(),
            published=None,
        )
        await bp.save(refresh=True)

    assert await BlogPost.search().count() == 1

    # _matches work which means we get BlogPost instance
    bp = (await BlogPost.search().execute())[0]
    assert isinstance(bp, BlogPost)
    assert not bp.is_published()
    assert "0" == bp.meta.id

    # create new index
    await migrate()

    indices = await async_write_client.indices.get(index=PATTERN)
    assert 2 == len(indices)
    alias = await async_write_client.indices.get(index=ALIAS)
    assert 1 == len(alias)
    assert index_name not in alias

    # data has been moved properly
    assert await BlogPost.search().count() == 1

    # _matches work which means we get BlogPost instance
    bp = (await BlogPost.search().execute())[0]
    assert isinstance(bp, BlogPost)
    assert "0" == bp.meta.id
