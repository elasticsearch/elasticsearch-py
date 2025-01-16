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
# Semantic Text example

Requirements:

$ pip install "elasticsearch[async]" tqdm

Before running this example, an ELSER inference endpoint must be created in the
Elasticsearch cluster. This can be done manually from Kibana, or with the
following curl command from a terminal:

curl -X PUT \
  "$ELASTICSEARCH_URL/_inference/sparse_embedding/my-elser-endpoint" \
  -H "Content-Type: application/json" \
  -d '{"service":"elser","service_settings":{"num_allocations":1,"num_threads":1}}'

To run the example:

$ python semantic_text.py "text to search"

The index will be created automatically if it does not exist. Add
`--recreate-index` to the command to regenerate it.

The example dataset includes a selection of workplace documents. The
following are good example queries to try out with this dataset:

$ python semantic_text.py "work from home"
$ python semantic_text.py "vacation time"
$ python semantic_text.py "can I bring a bird to work?"

When the index is created, the inference service will split the documents into
short passages, and for each passage a sparse embedding will be generated using
Elastic's ELSER v2 model.
"""

import argparse
import asyncio
import json
import os
from datetime import datetime
from typing import Any, Optional
from urllib.request import urlopen

from tqdm import tqdm

from elasticsearch import dsl

DATASET_URL = "https://raw.githubusercontent.com/elastic/elasticsearch-labs/main/datasets/workplace-documents.json"


class WorkplaceDoc(dsl.AsyncDocument):
    class Index:
        name = "workplace_documents_semantic"

    name: str
    summary: str
    content: Any = dsl.mapped_field(
        dsl.field.SemanticText(inference_id="my-elser-endpoint")
    )
    created: datetime
    updated: Optional[datetime]
    url: str = dsl.mapped_field(dsl.Keyword())
    category: str = dsl.mapped_field(dsl.Keyword())


async def create() -> None:

    # create the index
    await WorkplaceDoc._index.delete(ignore_unavailable=True)
    await WorkplaceDoc.init()

    # download the data
    dataset = json.loads(urlopen(DATASET_URL).read())

    # import the dataset
    for data in tqdm(dataset, desc="Indexing documents..."):
        doc = WorkplaceDoc(
            name=data["name"],
            summary=data["summary"],
            content=data["content"],
            created=data.get("created_on"),
            updated=data.get("updated_at"),
            url=data["url"],
            category=data["category"],
        )
        await doc.save()

    # refresh the index
    await WorkplaceDoc._index.refresh()


async def search(query: str) -> dsl.AsyncSearch[WorkplaceDoc]:
    search = WorkplaceDoc.search()
    search = search[:5]
    return search.query(dsl.query.Semantic(field=WorkplaceDoc.content, query=query))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Vector database with Elasticsearch")
    parser.add_argument(
        "--recreate-index", action="store_true", help="Recreate and populate the index"
    )
    parser.add_argument("query", action="store", help="The search query")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    # initiate the default connection to elasticsearch
    dsl.async_connections.create_connection(hosts=[os.environ["ELASTICSEARCH_URL"]])

    if args.recreate_index or not await WorkplaceDoc._index.exists():
        await create()

    results = await search(args.query)

    async for hit in results:
        print(
            f"Document: {hit.name} [Category: {hit.category}] [Score: {hit.meta.score}]"
        )
        print(f"Content: {hit.content.text}")
        print("--------------------\n")

    # close the connection
    await dsl.async_connections.get_connection().close()


if __name__ == "__main__":
    asyncio.run(main())
