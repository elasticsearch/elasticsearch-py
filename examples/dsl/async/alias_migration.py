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

"""
Simple example with a single Document demonstrating how schema can be managed,
including upgrading with reindexing.

Key concepts:

    * setup() function to first initialize the schema (as index template) in
      elasticsearch. Can be called any time (recommended with every deploy of
      your app).

    * migrate() function to be called any time when the schema changes - it
      will create a new index (by incrementing the version) and update the alias.
      By default it will also (before flipping the alias) move the data from the
      previous index to the new one.

    * BlogPost._matches() class method is required for this code to work since
      otherwise BlogPost will not be used to deserialize the documents as those
      will have index set to the concrete index whereas the class refers to the
      alias.
"""
import asyncio
import os
from datetime import datetime
from fnmatch import fnmatch
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from elasticsearch.dsl import AsyncDocument, Keyword, async_connections, mapped_field

ALIAS = "test-blog"
PATTERN = ALIAS + "-*"
PRIORITY = 100


class BlogPost(AsyncDocument):
    if TYPE_CHECKING:
        # definitions here help type checkers understand additional arguments
        # that are allowed in the constructor
        _id: int

    title: str
    tags: List[str] = mapped_field(Keyword())
    content: str
    published: Optional[datetime] = mapped_field(default=None)

    def is_published(self) -> bool:
        return bool(self.published and datetime.now() > self.published)

    @classmethod
    def _matches(cls, hit: Dict[str, Any]) -> bool:
        # override _matches to match indices in a pattern instead of just ALIAS
        # hit is the raw dict as returned by elasticsearch
        return fnmatch(hit["_index"], PATTERN)

    class Index:
        # we will use an alias instead of the index
        name = ALIAS
        # set settings and possibly other attributes of the index like
        # analyzers
        settings = {"number_of_shards": 1, "number_of_replicas": 0}


async def setup() -> None:
    """
    Create the index template in elasticsearch specifying the mappings and any
    settings to be used. This can be run at any time, ideally at every new code
    deploy.
    """
    # create an index template
    index_template = BlogPost._index.as_composable_template(
        ALIAS, PATTERN, priority=PRIORITY
    )
    # upload the template into elasticsearch
    # potentially overriding the one already there
    await index_template.save()

    # create the first index if it doesn't exist
    if not await BlogPost._index.exists():
        await migrate(move_data=False)


async def migrate(move_data: bool = True, update_alias: bool = True) -> None:
    """
    Upgrade function that creates a new index for the data. Optionally it also can
    (and by default will) reindex previous copy of the data into the new index
    (specify ``move_data=False`` to skip this step) and update the alias to
    point to the latest index (set ``update_alias=False`` to skip).

    Note that while this function is running the application can still perform
    any and all searches without any loss of functionality. It should, however,
    not perform any writes at this time as those might be lost.
    """
    # construct a new index name by appending current timestamp
    next_index = PATTERN.replace("*", datetime.now().strftime("%Y%m%d%H%M%S%f"))

    # get the low level connection
    es = async_connections.get_connection()

    # create new index, it will use the settings from the template
    await es.indices.create(index=next_index)

    if move_data:
        # move data from current alias to the new index
        await es.options(request_timeout=3600).reindex(
            body={"source": {"index": ALIAS}, "dest": {"index": next_index}}
        )
        # refresh the index to make the changes visible
        await es.indices.refresh(index=next_index)

    if update_alias:
        # repoint the alias to point to the newly created index
        await es.indices.update_aliases(
            body={
                "actions": [
                    {"remove": {"alias": ALIAS, "index": PATTERN}},
                    {"add": {"alias": ALIAS, "index": next_index}},
                ]
            }
        )


async def main() -> None:
    # initiate the default connection to elasticsearch
    async_connections.create_connection(hosts=[os.environ["ELASTICSEARCH_URL"]])

    # create the empty index
    await setup()

    # create a new document
    bp = BlogPost(
        _id=0,
        title="Hello World!",
        tags=["testing", "dummy"],
        content=open(__file__).read(),
    )
    await bp.save(refresh=True)

    # create new index
    await migrate()

    # close the connection
    await async_connections.get_connection().close()


if __name__ == "__main__":
    asyncio.run(main())
