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

import asyncio
import os
from typing import TYPE_CHECKING, Any, List, Optional

from elasticsearch.dsl import (
    AsyncDocument,
    AsyncSearch,
    Keyword,
    Percolator,
    Q,
    Query,
    async_connections,
    mapped_field,
)


class BlogPost(AsyncDocument):
    """
    Blog posts that will be automatically tagged based on percolation queries.
    """

    if TYPE_CHECKING:
        # definitions here help type checkers understand additional arguments
        # that are allowed in the constructor
        _id: int

    content: Optional[str]
    tags: List[str] = mapped_field(Keyword(), default_factory=list)

    class Index:
        name = "test-blogpost"

    async def add_tags(self) -> None:
        # run a percolation to automatically tag the blog post.
        s = AsyncSearch(index="test-percolator")
        s = s.query(
            "percolate", field="query", index=self._get_index(), document=self.to_dict()
        )

        # collect all the tags from matched percolators
        async for percolator in s:
            self.tags.extend(percolator.tags)

        # make sure tags are unique
        self.tags = list(set(self.tags))

    async def save(self, **kwargs: Any) -> None:  # type: ignore[override]
        await self.add_tags()
        await super().save(**kwargs)


class PercolatorDoc(AsyncDocument):
    """
    Document class used for storing the percolation queries.
    """

    if TYPE_CHECKING:
        _id: str

    # relevant fields from BlogPost must be also present here for the queries
    # to be able to use them. Another option would be to use document
    # inheritance but save() would have to be reset to normal behavior.
    content: Optional[str]

    # the percolator query to be run against the doc
    query: Query = mapped_field(Percolator())
    # list of tags to append to a document
    tags: List[str] = mapped_field(Keyword(multi=True))

    class Index:
        name = "test-percolator"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}


async def setup() -> None:
    # create the percolator index if it doesn't exist
    if not await PercolatorDoc._index.exists():
        await PercolatorDoc.init()

    # register a percolation query looking for documents about python
    await PercolatorDoc(
        _id="python",
        tags=["programming", "development", "python"],
        content="",
        query=Q("match", content="python"),
    ).save(refresh=True)


async def main() -> None:
    # initiate the default connection to elasticsearch
    async_connections.create_connection(hosts=[os.environ["ELASTICSEARCH_URL"]])

    await setup()

    # close the connection
    await async_connections.get_connection().close()


if __name__ == "__main__":
    asyncio.run(main())
