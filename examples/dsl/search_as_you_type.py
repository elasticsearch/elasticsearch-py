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
Example ``Document`` with search_as_you_type field datatype and how to search it.

When creating a field with search_as_you_type datatype ElasticSearch creates additional
subfields to enable efficient as-you-type completion, matching terms at any position
within the input.

To custom analyzer with ascii folding allow search to work in different languages.
"""

import os
from typing import TYPE_CHECKING, Optional

from elasticsearch.dsl import Document, SearchAsYouType, connections, mapped_field
from elasticsearch.dsl.query import MultiMatch


class Person(Document):
    if TYPE_CHECKING:
        # definitions here help type checkers understand additional arguments
        # that are allowed in the constructor
        _id: Optional[int] = mapped_field(default=None)

    name: str = mapped_field(SearchAsYouType(max_shingle_size=3), default="")

    class Index:
        name = "test-search-as-you-type"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}


def main() -> None:
    # initiate the default connection to elasticsearch
    connections.create_connection(hosts=[os.environ["ELASTICSEARCH_URL"]])

    # create the empty index
    Person.init()

    import pprint

    pprint.pprint(Person().to_dict(), indent=2)

    # index some sample data
    names = [
        "Andy Warhol",
        "Alphonse Mucha",
        "Henri de Toulouse-Lautrec",
        "Jára Cimrman",
    ]
    for id, name in enumerate(names):
        Person(_id=id, name=name).save()

    # refresh index manually to make changes live
    Person._index.refresh()

    # run some suggestions
    for text in ("já", "Cimr", "toulouse", "Henri Tou", "a"):
        s = Person.search()

        s.query = MultiMatch(  # type: ignore[assignment]
            query=text,
            type="bool_prefix",
            fields=["name", "name._2gram", "name._3gram"],
        )

        response = s.execute()

        # print out all the options we got
        for h in response:
            print("%15s: %25s" % (text, h.name))

    # close the connection
    connections.get_connection().close()


if __name__ == "__main__":
    main()
