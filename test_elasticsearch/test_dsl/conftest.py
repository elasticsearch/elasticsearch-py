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
import re
import time
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, Generator, Tuple, cast
from unittest import SkipTest
from unittest.mock import AsyncMock, Mock

import pytest_asyncio
from elastic_transport import ObjectApiResponse
from pytest import fixture, skip

from elasticsearch import AsyncElasticsearch, Elasticsearch
from elasticsearch.dsl import Search
from elasticsearch.dsl.async_connections import add_connection as add_async_connection
from elasticsearch.dsl.async_connections import connections as async_connections
from elasticsearch.dsl.connections import add_connection, connections
from elasticsearch.exceptions import ConnectionError
from elasticsearch.helpers import bulk

from ..utils import CA_CERTS, wipe_cluster
from .test_integration._async import test_document as async_document
from .test_integration._sync import test_document as sync_document
from .test_integration.test_data import (
    DATA,
    FLAT_DATA,
    TEST_GIT_DATA,
    create_flat_git_index,
    create_git_index,
)


def get_test_client(
    elasticsearch_url, wait: bool = True, **kwargs: Any
) -> Elasticsearch:
    # construct kwargs from the environment
    kw: Dict[str, Any] = {"request_timeout": 30}

    if elasticsearch_url.startswith("https://"):
        kw["ca_certs"] = CA_CERTS

    if "PYTHON_CONNECTION_CLASS" in os.environ:
        kw["node_class"] = os.environ["PYTHON_CONNECTION_CLASS"]

    kw.update(kwargs)
    client = Elasticsearch(elasticsearch_url, **kw)

    # wait for yellow status
    for tries_left in range(100 if wait else 1, 0, -1):
        try:
            client.cluster.health(wait_for_status="yellow")
            return client
        except ConnectionError:
            if wait and tries_left == 1:
                raise
            time.sleep(0.1)

    raise SkipTest("Elasticsearch failed to start.")


async def get_async_test_client(
    elasticsearch_url, wait: bool = True, **kwargs: Any
) -> AsyncElasticsearch:
    # construct kwargs from the environment
    kw: Dict[str, Any] = {"request_timeout": 30}

    if elasticsearch_url.startswith("https://"):
        kw["ca_certs"] = CA_CERTS

    kw.update(kwargs)
    client = AsyncElasticsearch(elasticsearch_url, **kw)

    # wait for yellow status
    for tries_left in range(100 if wait else 1, 0, -1):
        try:
            await client.cluster.health(wait_for_status="yellow")
            return client
        except ConnectionError:
            if wait and tries_left == 1:
                raise
            await asyncio.sleep(0.1)

    await client.close()
    raise SkipTest("Elasticsearch failed to start.")


def _get_version(version_string: str) -> Tuple[int, ...]:
    if "." not in version_string:
        return ()
    version = version_string.strip().split(".")
    return tuple(int(v) if v.isdigit() else 999 for v in version)


@fixture
def client(elasticsearch_url) -> Elasticsearch:
    try:
        connection = get_test_client(
            elasticsearch_url, wait="WAIT_FOR_ES" in os.environ
        )
        add_connection("default", connection)
        yield connection
        wipe_cluster(connection)
        connection.close()
    except SkipTest:
        skip()


@pytest_asyncio.fixture
async def async_client(elasticsearch_url) -> AsyncGenerator[AsyncElasticsearch, None]:
    try:
        connection = await get_async_test_client(
            elasticsearch_url, wait="WAIT_FOR_ES" in os.environ
        )
        add_async_connection("default", connection)
        yield connection
        wipe_cluster(connection)
        await connection.close()
    except SkipTest:
        skip()


@fixture
def es_version(client: Elasticsearch) -> Generator[Tuple[int, ...], None, None]:
    info = client.info()
    yield tuple(
        int(x)
        for x in re.match(r"^([0-9.]+)", info["version"]["number"]).group(1).split(".")  # type: ignore
    )


@fixture
def write_client(client: Elasticsearch) -> Generator[Elasticsearch, None, None]:
    yield client
    for index_name in client.indices.get(index="test-*", expand_wildcards="all"):
        client.indices.delete(index=index_name)
    client.options(ignore_status=404).indices.delete_template(name="test-template")
    client.options(ignore_status=404).indices.delete_index_template(
        name="test-template"
    )


@pytest_asyncio.fixture
async def async_write_client(
    write_client: Elasticsearch, async_client: AsyncElasticsearch
) -> AsyncGenerator[AsyncElasticsearch, None]:
    yield async_client


@fixture
def mock_client(
    dummy_response: ObjectApiResponse[Any],
) -> Generator[Elasticsearch, None, None]:
    client = Mock()
    client.search.return_value = dummy_response
    client.update_by_query.return_value = dummy_response
    add_connection("mock", client)

    yield client
    connections._conns = {}
    connections._kwargs = {}


@fixture
def async_mock_client(
    dummy_response: ObjectApiResponse[Any],
) -> Generator[Elasticsearch, None, None]:
    client = Mock()
    client.search = AsyncMock(return_value=dummy_response)
    client.indices = AsyncMock()
    client.update_by_query = AsyncMock()
    client.delete_by_query = AsyncMock()
    add_async_connection("mock", client)

    yield client
    async_connections._conns = {}
    async_connections._kwargs = {}


@fixture
def data_client(client: Elasticsearch) -> Generator[Elasticsearch, None, None]:
    # create mappings
    create_git_index(client, "git")
    create_flat_git_index(client, "flat-git")
    # load data
    bulk(client, DATA, raise_on_error=True, refresh=True)
    bulk(client, FLAT_DATA, raise_on_error=True, refresh=True)
    yield client
    client.options(ignore_status=404).indices.delete(index="git")
    client.options(ignore_status=404).indices.delete(index="flat-git")


@pytest_asyncio.fixture
async def async_data_client(
    data_client: Elasticsearch, async_client: AsyncElasticsearch
) -> AsyncGenerator[AsyncElasticsearch, None]:
    yield async_client


@fixture
def dummy_response() -> ObjectApiResponse[Any]:
    return ObjectApiResponse(
        meta=None,
        body={
            "_shards": {"failed": 0, "successful": 10, "total": 10},
            "hits": {
                "hits": [
                    {
                        "_index": "test-index",
                        "_type": "company",
                        "_id": "elasticsearch",
                        "_score": 12.0,
                        "_source": {"city": "Amsterdam", "name": "Elasticsearch"},
                    },
                    {
                        "_index": "test-index",
                        "_type": "employee",
                        "_id": "42",
                        "_score": 11.123,
                        "_routing": "elasticsearch",
                        "_source": {
                            "name": {"first": "Shay", "last": "Bannon"},
                            "lang": "java",
                            "twitter": "kimchy",
                        },
                    },
                    {
                        "_index": "test-index",
                        "_type": "employee",
                        "_id": "47",
                        "_score": 1,
                        "_routing": "elasticsearch",
                        "_source": {
                            "name": {"first": "Honza", "last": "Král"},
                            "lang": "python",
                            "twitter": "honzakral",
                        },
                    },
                    {
                        "_index": "test-index",
                        "_type": "employee",
                        "_id": "53",
                        "_score": 16.0,
                        "_routing": "elasticsearch",
                    },
                ],
                "max_score": 12.0,
                "total": 123,
            },
            "timed_out": False,
            "took": 123,
        },
    )


@fixture
def aggs_search() -> Search:
    s = Search(index="flat-git")
    s.aggs.bucket("popular_files", "terms", field="files", size=2).metric(
        "line_stats", "stats", field="stats.lines"
    ).metric("top_commits", "top_hits", size=2, _source=["stats.*", "committed_date"])
    s.aggs.bucket(
        "per_month", "date_histogram", interval="month", field="info.committed_date"
    )
    s.aggs.metric("sum_lines", "sum", field="stats.lines")
    return s


@fixture
def aggs_data() -> Dict[str, Any]:
    return {
        "took": 4,
        "timed_out": False,
        "_shards": {"total": 1, "successful": 1, "failed": 0},
        "hits": {"total": 52, "hits": [], "max_score": 0.0},
        "aggregations": {
            "sum_lines": {"value": 25052.0},
            "per_month": {
                "buckets": [
                    {
                        "doc_count": 38,
                        "key": 1393632000000,
                        "key_as_string": "2014-03-01T00:00:00.000Z",
                    },
                    {
                        "doc_count": 11,
                        "key": 1396310400000,
                        "key_as_string": "2014-04-01T00:00:00.000Z",
                    },
                    {
                        "doc_count": 3,
                        "key": 1398902400000,
                        "key_as_string": "2014-05-01T00:00:00.000Z",
                    },
                ]
            },
            "popular_files": {
                "buckets": [
                    {
                        "key": "elasticsearch_dsl",
                        "line_stats": {
                            "count": 40,
                            "max": 228.0,
                            "min": 2.0,
                            "sum": 2151.0,
                            "avg": 53.775,
                        },
                        "doc_count": 40,
                        "top_commits": {
                            "hits": {
                                "total": 40,
                                "hits": [
                                    {
                                        "_id": "3ca6e1e73a071a705b4babd2f581c91a2a3e5037",
                                        "_type": "doc",
                                        "_source": {
                                            "stats": {
                                                "files": 4,
                                                "deletions": 7,
                                                "lines": 30,
                                                "insertions": 23,
                                            },
                                            "committed_date": "2014-05-02T13:47:19",
                                        },
                                        "_score": 1.0,
                                        "_index": "flat-git",
                                    },
                                    {
                                        "_id": "eb3e543323f189fd7b698e66295427204fff5755",
                                        "_type": "doc",
                                        "_source": {
                                            "stats": {
                                                "files": 1,
                                                "deletions": 0,
                                                "lines": 18,
                                                "insertions": 18,
                                            },
                                            "committed_date": "2014-05-01T13:32:14",
                                        },
                                        "_score": 1.0,
                                        "_index": "flat-git",
                                    },
                                ],
                                "max_score": 1.0,
                            }
                        },
                    },
                    {
                        "key": "test_elasticsearch_dsl",
                        "line_stats": {
                            "count": 35,
                            "max": 228.0,
                            "min": 2.0,
                            "sum": 1939.0,
                            "avg": 55.4,
                        },
                        "doc_count": 35,
                        "top_commits": {
                            "hits": {
                                "total": 35,
                                "hits": [
                                    {
                                        "_id": "3ca6e1e73a071a705b4babd2f581c91a2a3e5037",
                                        "_type": "doc",
                                        "_source": {
                                            "stats": {
                                                "files": 4,
                                                "deletions": 7,
                                                "lines": 30,
                                                "insertions": 23,
                                            },
                                            "committed_date": "2014-05-02T13:47:19",
                                        },
                                        "_score": 1.0,
                                        "_index": "flat-git",
                                    },
                                    {
                                        "_id": "dd15b6ba17dd9ba16363a51f85b31f66f1fb1157",
                                        "_type": "doc",
                                        "_source": {
                                            "stats": {
                                                "files": 3,
                                                "deletions": 18,
                                                "lines": 62,
                                                "insertions": 44,
                                            },
                                            "committed_date": "2014-05-01T13:30:44",
                                        },
                                        "_score": 1.0,
                                        "_index": "flat-git",
                                    },
                                ],
                                "max_score": 1.0,
                            }
                        },
                    },
                ],
                "doc_count_error_upper_bound": 0,
                "sum_other_doc_count": 120,
            },
        },
    }


def make_pr(pr_module: Any) -> Any:
    return pr_module.PullRequest(
        _id=42,
        comments=[
            pr_module.Comment(
                content="Hello World!",
                author=pr_module.User(name="honzakral"),
                created_at=datetime(2018, 1, 9, 10, 17, 3, 21184),
                history=[
                    pr_module.History(
                        timestamp=datetime(2012, 1, 1),
                        diff="-Ahoj Svete!\n+Hello World!",
                    )
                ],
            ),
        ],
        created_at=datetime(2018, 1, 9, 9, 17, 3, 21184),
    )


@fixture
def pull_request(write_client: Elasticsearch) -> sync_document.PullRequest:
    sync_document.PullRequest.init()
    pr = cast(sync_document.PullRequest, make_pr(sync_document))
    pr.save(refresh=True)
    return pr


@pytest_asyncio.fixture
async def async_pull_request(
    async_write_client: AsyncElasticsearch,
) -> async_document.PullRequest:
    await async_document.PullRequest.init()
    pr = cast(async_document.PullRequest, make_pr(async_document))
    await pr.save(refresh=True)
    return pr


@fixture
def setup_ubq_tests(client: Elasticsearch) -> str:
    index = "test-git"
    create_git_index(client, index)
    bulk(client, TEST_GIT_DATA, raise_on_error=True, refresh=True)
    return index
