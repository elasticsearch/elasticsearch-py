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
Example ``Document`` with completion suggester.

In the ``Person`` class we index the person's name to allow auto completing in
any order ("first last", "middle last first", ...). For the weight we use a
value from the ``popularity`` field which is a long.

To make the suggestions work in different languages we added a custom analyzer
that does ascii folding.
"""

import asyncio
import os
from itertools import permutations
from typing import TYPE_CHECKING, Any, Dict, Optional

from elasticsearch.dsl import (
    AsyncDocument,
    Completion,
    Keyword,
    Long,
    Text,
    analyzer,
    async_connections,
    mapped_field,
    token_filter,
)

# custom analyzer for names
ascii_fold = analyzer(
    "ascii_fold",
    # we don't want to split O'Brian or Toulouse-Lautrec
    tokenizer="whitespace",
    filter=["lowercase", token_filter("ascii_fold", "asciifolding")],
)


class Person(AsyncDocument):
    if TYPE_CHECKING:
        # definitions here help type checkers understand additional arguments
        # that are allowed in the constructor
        _id: Optional[int] = mapped_field(default=None)

    name: str = mapped_field(Text(fields={"keyword": Keyword()}), default="")
    popularity: int = mapped_field(Long(), default=0)

    # completion field with a custom analyzer
    suggest: Dict[str, Any] = mapped_field(Completion(analyzer=ascii_fold), init=False)

    def clean(self) -> None:
        """
        Automatically construct the suggestion input and weight by taking all
        possible permutations of Person's name as ``input`` and taking their
        popularity as ``weight``.
        """
        self.suggest = {
            "input": [" ".join(p) for p in permutations(self.name.split())],
            "weight": self.popularity,
        }

    class Index:
        name = "test-suggest"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}


async def main() -> None:
    # initiate the default connection to elasticsearch
    async_connections.create_connection(hosts=[os.environ["ELASTICSEARCH_URL"]])

    # create the empty index
    await Person.init()

    # index some sample data
    for id, (name, popularity) in enumerate(
        [("Henri de Toulouse-Lautrec", 42), ("Jára Cimrman", 124)]
    ):
        await Person(_id=id, name=name, popularity=popularity).save()

    # refresh index manually to make changes live
    await Person._index.refresh()

    # run some suggestions
    for text in ("já", "Jara Cimr", "tou", "de hen"):
        s = Person.search()
        s = s.suggest("auto_complete", text, completion={"field": "suggest"})
        response = await s.execute()

        # print out all the options we got
        for option in response.suggest["auto_complete"][0].options:
            print("%10s: %25s (%d)" % (text, option._source.name, option._score))

    # close the connection
    await async_connections.get_connection().close()


if __name__ == "__main__":
    asyncio.run(main())
