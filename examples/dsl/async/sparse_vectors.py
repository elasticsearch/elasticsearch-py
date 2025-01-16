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
# Sparse vector database example

Requirements:

$ pip install nltk tqdm elasticsearch[async]

Before running this example, the ELSER v2 model must be downloaded and deployed
to the Elasticsearch cluster, and an ingest pipeline must be defined. This can
be done manually from Kibana, or with the following three curl commands from a
terminal, adjusting the endpoint as needed:

curl -X PUT \
  "http://localhost:9200/_ml/trained_models/.elser_model_2?wait_for_completion" \
  -H "Content-Type: application/json" \
  -d '{"input":{"field_names":["text_field"]}}'
curl -X POST \
  "http://localhost:9200/_ml/trained_models/.elser_model_2/deployment/_start?wait_for=fully_allocated"
curl -X PUT \
  "http://localhost:9200/_ingest/pipeline/elser_ingest_pipeline" \
  -H "Content-Type: application/json" \
  -d '{"processors":[{"foreach":{"field":"passages","processor":{"inference":{"model_id":".elser_model_2","input_output":[{"input_field":"_ingest._value.content","output_field":"_ingest._value.embedding"}]}}}}]}'

To run the example:

$ python sparse_vectors.py "text to search"

The index will be created automatically if it does not exist. Add
`--recreate-index` to regenerate it.

The example dataset includes a selection of workplace documents. The
following are good example queries to try out with this dataset:

$ python sparse_vectors.py "work from home"
$ python sparse_vectors.py "vacation time"
$ python sparse_vectors.py "can I bring a bird to work?"

When the index is created, the documents are split into short passages, and for
each passage a sparse embedding is generated using Elastic's ELSER v2 model.
The documents that are returned as search results are those that have the
highest scored passages. Add `--show-inner-hits` to the command to see
individual passage results as well.
"""

import argparse
import asyncio
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.request import urlopen

import nltk
from tqdm import tqdm

from elasticsearch.dsl import (
    AsyncDocument,
    AsyncSearch,
    InnerDoc,
    Keyword,
    Q,
    SparseVector,
    async_connections,
    mapped_field,
)

DATASET_URL = "https://raw.githubusercontent.com/elastic/elasticsearch-labs/main/datasets/workplace-documents.json"

# initialize sentence tokenizer
nltk.download("punkt_tab", quiet=True)


class Passage(InnerDoc):
    content: Optional[str]
    embedding: Dict[str, float] = mapped_field(SparseVector(), init=False)


class WorkplaceDoc(AsyncDocument):
    class Index:
        name = "workplace_documents_sparse"
        settings = {"default_pipeline": "elser_ingest_pipeline"}

    name: str
    summary: str
    content: str
    created: datetime
    updated: Optional[datetime]
    url: str = mapped_field(Keyword())
    category: str = mapped_field(Keyword())
    passages: List[Passage] = mapped_field(default=[])

    _model: Any = None

    def clean(self) -> None:
        # split the content into sentences
        passages = nltk.sent_tokenize(self.content)

        # generate an embedding for each passage and save it as a nested document
        for passage in passages:
            self.passages.append(Passage(content=passage))


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


async def search(query: str) -> AsyncSearch[WorkplaceDoc]:
    return WorkplaceDoc.search()[:5].query(
        "nested",
        path="passages",
        query=Q(
            "text_expansion",
            passages__content={
                "model_id": ".elser_model_2",
                "model_text": query,
            },
        ),
        inner_hits={"size": 2},
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Vector database with Elasticsearch")
    parser.add_argument(
        "--recreate-index", action="store_true", help="Recreate and populate the index"
    )
    parser.add_argument(
        "--show-inner-hits",
        action="store_true",
        help="Show results for individual passages",
    )
    parser.add_argument("query", action="store", help="The search query")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    # initiate the default connection to elasticsearch
    async_connections.create_connection(hosts=[os.environ["ELASTICSEARCH_URL"]])

    if args.recreate_index or not await WorkplaceDoc._index.exists():
        await create()

    results = await search(args.query)

    async for hit in results:
        print(
            f"Document: {hit.name} [Category: {hit.category}] [Score: {hit.meta.score}]"
        )
        print(f"Summary: {hit.summary}")
        if args.show_inner_hits:
            for passage in hit.meta.inner_hits["passages"]:
                print(f"  - [Score: {passage.meta.score}] {passage.content!r}")
        print("")

    # close the connection
    await async_connections.get_connection().close()


if __name__ == "__main__":
    asyncio.run(main())
