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

from typing import Any

from elasticsearch import Elasticsearch
from elasticsearch.dsl.search import Q, Search


def test_count_all(data_client: Elasticsearch) -> None:
    s = Search(using=data_client).index("git")
    assert 53 == s.count()


def test_count_prefetch(data_client: Elasticsearch, mocker: Any) -> None:
    mocker.spy(data_client, "count")

    search = Search(using=data_client).index("git")
    search.execute()
    assert search.count() == 53
    assert data_client.count.call_count == 0  # type: ignore[attr-defined]

    search._response.hits.total.relation = "gte"  # type: ignore[attr-defined]
    assert search.count() == 53
    assert data_client.count.call_count == 1  # type: ignore[attr-defined]


def test_count_filter(data_client: Elasticsearch) -> None:
    s = Search(using=data_client).index("git").filter(~Q("exists", field="parent_shas"))
    # initial commit + repo document
    assert 2 == s.count()
