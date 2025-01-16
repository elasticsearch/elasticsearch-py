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
from typing import Any, AsyncIterator, Dict, Mapping, Sequence, cast

from elasticsearch.dsl import Agg, AsyncSearch, Response, aggs, async_connections
from elasticsearch.dsl.types import CompositeAggregate
from elasticsearch.helpers import async_bulk
from test_elasticsearch.test_dsl.test_integration.test_data import DATA, GIT_INDEX


async def scan_aggs(
    search: AsyncSearch,
    source_aggs: Sequence[Mapping[str, Agg]],
    inner_aggs: Dict[str, Agg] = {},
    size: int = 10,
) -> AsyncIterator[CompositeAggregate]:
    """
    Helper function used to iterate over all possible bucket combinations of
    ``source_aggs``, returning results of ``inner_aggs`` for each. Uses the
    ``composite`` aggregation under the hood to perform this.
    """

    async def run_search(**kwargs: Any) -> Response:
        s = search[:0]
        bucket = s.aggs.bucket(
            "comp",
            aggs.Composite(
                sources=source_aggs,
                size=size,
                **kwargs,
            ),
        )
        for agg_name, agg in inner_aggs.items():
            bucket[agg_name] = agg
        return await s.execute()

    response = await run_search()
    while response.aggregations["comp"].buckets:
        for b in response.aggregations["comp"].buckets:
            yield cast(CompositeAggregate, b)
        if "after_key" in response.aggregations["comp"]:
            after = response.aggregations["comp"].after_key
        else:
            after = response.aggregations["comp"].buckets[-1].key
        response = await run_search(after=after)


async def main() -> None:
    # initiate the default connection to elasticsearch
    client = async_connections.create_connection(
        hosts=[os.environ["ELASTICSEARCH_URL"]]
    )

    # create the index and populate it with some data
    # note that the dataset is imported from the library's test suite
    await client.indices.delete(index="git", ignore_unavailable=True)
    await client.indices.create(index="git", **GIT_INDEX)
    await async_bulk(client, DATA, raise_on_error=True, refresh=True)

    # run some aggregations on the data
    async for b in scan_aggs(
        AsyncSearch(index="git"),
        [{"files": aggs.Terms(field="files")}],
        {"first_seen": aggs.Min(field="committed_date")},
    ):
        print(
            "File %s has been modified %d times, first seen at %s."
            % (b.key.files, b.doc_count, b.first_seen.value_as_string)
        )

    # close the connection
    await async_connections.get_connection().close()


if __name__ == "__main__":
    asyncio.run(main())
