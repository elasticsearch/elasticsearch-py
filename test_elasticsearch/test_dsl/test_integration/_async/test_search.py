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
from pytest import raises

from elasticsearch import ApiError, AsyncElasticsearch
from elasticsearch.dsl import (
    AsyncDocument,
    AsyncMultiSearch,
    AsyncSearch,
    Date,
    Keyword,
    Q,
    Text,
)
from elasticsearch.dsl.response import aggs

from ..test_data import FLAT_DATA


class Repository(AsyncDocument):
    created_at = Date()
    description = Text(analyzer="snowball")
    tags = Keyword()

    @classmethod
    def search(cls) -> AsyncSearch["Repository"]:  # type: ignore[override]
        return super().search().filter("term", commit_repo="repo")

    class Index:
        name = "git"


class Commit(AsyncDocument):
    class Index:
        name = "flat-git"


@pytest.mark.asyncio
async def test_filters_aggregation_buckets_are_accessible(
    async_data_client: AsyncElasticsearch,
) -> None:
    has_tests_query = Q("term", files="test_elasticsearch_dsl")
    s = Commit.search()[0:0]
    s.aggs.bucket("top_authors", "terms", field="author.name.raw").bucket(
        "has_tests", "filters", filters={"yes": has_tests_query, "no": ~has_tests_query}
    ).metric("lines", "stats", field="stats.lines")

    response = await s.execute()

    assert isinstance(
        response.aggregations.top_authors.buckets[0].has_tests.buckets.yes, aggs.Bucket
    )
    assert (
        35
        == response.aggregations.top_authors.buckets[0].has_tests.buckets.yes.doc_count
    )
    assert (
        228
        == response.aggregations.top_authors.buckets[0].has_tests.buckets.yes.lines.max
    )


@pytest.mark.asyncio
async def test_top_hits_are_wrapped_in_response(
    async_data_client: AsyncElasticsearch,
) -> None:
    s = Commit.search()[0:0]
    s.aggs.bucket("top_authors", "terms", field="author.name.raw").metric(
        "top_commits", "top_hits", size=5
    )
    response = await s.execute()

    top_commits = response.aggregations.top_authors.buckets[0].top_commits
    assert isinstance(top_commits, aggs.TopHitsData)
    assert 5 == len(top_commits)

    hits = [h for h in top_commits]
    assert 5 == len(hits)
    assert isinstance(hits[0], Commit)


@pytest.mark.asyncio
async def test_inner_hits_are_wrapped_in_response(
    async_data_client: AsyncElasticsearch,
) -> None:
    s = AsyncSearch(index="git")[0:1].query(
        "has_parent", parent_type="repo", inner_hits={}, query=Q("match_all")
    )
    response = await s.execute()

    commit = response.hits[0]
    assert isinstance(commit.meta.inner_hits.repo, response.__class__)
    assert repr(commit.meta.inner_hits.repo[0]).startswith(
        "<Hit(git/elasticsearch-dsl-py): "
    )


@pytest.mark.asyncio
async def test_inner_hits_are_serialized_to_dict(
    async_data_client: AsyncElasticsearch,
) -> None:
    s = AsyncSearch(index="git")[0:1].query(
        "has_parent", parent_type="repo", inner_hits={}, query=Q("match_all")
    )
    response = await s.execute()
    d = response.to_dict(recursive=True)
    assert isinstance(d, dict)
    assert isinstance(d["hits"]["hits"][0]["inner_hits"]["repo"], dict)

    # iterating over the results changes the format of the internal AttrDict
    for hit in response:
        pass

    d = response.to_dict(recursive=True)
    assert isinstance(d, dict)
    assert isinstance(d["hits"]["hits"][0]["inner_hits"]["repo"], dict)


@pytest.mark.asyncio
async def test_scan_respects_doc_types(async_data_client: AsyncElasticsearch) -> None:
    repos = [repo async for repo in Repository.search().scan()]

    assert 1 == len(repos)
    assert isinstance(repos[0], Repository)
    assert repos[0].organization == "elasticsearch"


@pytest.mark.asyncio
async def test_scan_iterates_through_all_docs(
    async_data_client: AsyncElasticsearch,
) -> None:
    s = AsyncSearch(index="flat-git")

    commits = [commit async for commit in s.scan()]

    assert 52 == len(commits)
    assert {d["_id"] for d in FLAT_DATA} == {c.meta.id for c in commits}


@pytest.mark.asyncio
async def test_search_after(async_data_client: AsyncElasticsearch) -> None:
    page_size = 7
    s = AsyncSearch(index="flat-git")[:page_size].sort("authored_date")
    commits = []
    while True:
        r = await s.execute()
        commits += r.hits
        if len(r.hits) < page_size:
            break
        s = s.search_after()

    assert 52 == len(commits)
    assert {d["_id"] for d in FLAT_DATA} == {c.meta.id for c in commits}


@pytest.mark.asyncio
async def test_search_after_no_search(async_data_client: AsyncElasticsearch) -> None:
    s = AsyncSearch(index="flat-git")
    with raises(
        ValueError, match="A search must be executed before using search_after"
    ):
        s.search_after()
    await s.count()
    with raises(
        ValueError, match="A search must be executed before using search_after"
    ):
        s.search_after()


@pytest.mark.asyncio
async def test_search_after_no_sort(async_data_client: AsyncElasticsearch) -> None:
    s = AsyncSearch(index="flat-git")
    r = await s.execute()
    with raises(
        ValueError, match="Cannot use search_after when results are not sorted"
    ):
        r.search_after()


@pytest.mark.asyncio
async def test_search_after_no_results(async_data_client: AsyncElasticsearch) -> None:
    s = AsyncSearch(index="flat-git")[:100].sort("authored_date")
    r = await s.execute()
    assert 52 == len(r.hits)
    s = s.search_after()
    r = await s.execute()
    assert 0 == len(r.hits)
    with raises(
        ValueError, match="Cannot use search_after when there are no search results"
    ):
        r.search_after()


@pytest.mark.asyncio
async def test_point_in_time(async_data_client: AsyncElasticsearch) -> None:
    page_size = 7
    commits = []
    async with AsyncSearch(index="flat-git")[:page_size].point_in_time(
        keep_alive="30s"
    ) as s:
        pit_id = s._extra["pit"]["id"]
        while True:
            r = await s.execute()
            commits += r.hits
            if len(r.hits) < page_size:
                break
            s = s.search_after()
            assert pit_id == s._extra["pit"]["id"]
            assert "30s" == s._extra["pit"]["keep_alive"]

    assert 52 == len(commits)
    assert {d["_id"] for d in FLAT_DATA} == {c.meta.id for c in commits}


@pytest.mark.asyncio
async def test_iterate(async_data_client: AsyncElasticsearch) -> None:
    s = AsyncSearch(index="flat-git")

    commits = [commit async for commit in s.iterate()]

    assert 52 == len(commits)
    assert {d["_id"] for d in FLAT_DATA} == {c.meta.id for c in commits}


@pytest.mark.asyncio
async def test_response_is_cached(async_data_client: AsyncElasticsearch) -> None:
    s = Repository.search()
    repos = [repo async for repo in s]

    assert hasattr(s, "_response")
    assert s._response.hits == repos


@pytest.mark.asyncio
async def test_multi_search(async_data_client: AsyncElasticsearch) -> None:
    s1 = Repository.search()
    s2 = AsyncSearch[Repository](index="flat-git")

    ms = AsyncMultiSearch[Repository]()
    ms = ms.add(s1).add(s2)

    r1, r2 = await ms.execute()

    assert 1 == len(r1)
    assert isinstance(r1[0], Repository)
    assert r1._search is s1

    assert 52 == r2.hits.total.value  # type: ignore[attr-defined]
    assert r2._search is s2


@pytest.mark.asyncio
async def test_multi_missing(async_data_client: AsyncElasticsearch) -> None:
    s1 = Repository.search()
    s2 = AsyncSearch[Repository](index="flat-git")
    s3 = AsyncSearch[Repository](index="does_not_exist")

    ms = AsyncMultiSearch[Repository]()
    ms = ms.add(s1).add(s2).add(s3)

    with raises(ApiError):
        await ms.execute()

    r1, r2, r3 = await ms.execute(raise_on_error=False)

    assert 1 == len(r1)
    assert isinstance(r1[0], Repository)
    assert r1._search is s1

    assert 52 == r2.hits.total.value  # type: ignore[attr-defined]
    assert r2._search is s2

    assert r3 is None


@pytest.mark.asyncio
async def test_raw_subfield_can_be_used_in_aggs(
    async_data_client: AsyncElasticsearch,
) -> None:
    s = AsyncSearch(index="git")[0:0]
    s.aggs.bucket("authors", "terms", field="author.name.raw", size=1)

    r = await s.execute()

    authors = r.aggregations.authors
    assert 1 == len(authors)
    assert {"key": "Honza Král", "doc_count": 52} == authors[0]
