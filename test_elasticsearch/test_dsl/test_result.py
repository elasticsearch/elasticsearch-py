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

import pickle
from datetime import date
from typing import Any, Dict

from pytest import fixture, raises

from elasticsearch.dsl import Date, Document, Object, Search, response
from elasticsearch.dsl.aggs import Terms
from elasticsearch.dsl.response.aggs import AggResponse, Bucket, BucketData
from elasticsearch.dsl.utils import AttrDict


@fixture
def agg_response(aggs_search: Search, aggs_data: Dict[str, Any]) -> response.Response:
    return response.Response(aggs_search, aggs_data)


def test_agg_response_is_pickleable(agg_response: response.Response) -> None:
    agg_response.hits
    r = pickle.loads(pickle.dumps(agg_response))

    assert r == agg_response
    assert r._search == agg_response._search
    assert r.hits == agg_response.hits


def test_response_is_pickleable(dummy_response: Dict[str, Any]) -> None:
    res = response.Response(Search(), dummy_response.body)  # type: ignore[attr-defined]
    res.hits
    r = pickle.loads(pickle.dumps(res))

    assert r == res
    assert r._search == res._search
    assert r.hits == res.hits


def test_hit_is_pickleable(dummy_response: Dict[str, Any]) -> None:
    res = response.Response(Search(), dummy_response)
    hits = pickle.loads(pickle.dumps(res.hits))

    assert hits == res.hits
    assert hits[0].meta == res.hits[0].meta


def test_response_stores_search(dummy_response: Dict[str, Any]) -> None:
    s = Search()
    r = response.Response(s, dummy_response)

    assert r._search is s


def test_attribute_error_in_hits_is_not_hidden(dummy_response: Dict[str, Any]) -> None:
    def f(hit: AttrDict[Any]) -> Any:
        raise AttributeError()

    s = Search().doc_type(employee=f)
    r = response.Response(s, dummy_response)
    with raises(TypeError):
        r.hits


def test_interactive_helpers(dummy_response: Dict[str, Any]) -> None:
    res = response.Response(Search(), dummy_response)
    hits = res.hits
    h = hits[0]

    rhits = (
        "[<Hit(test-index/elasticsearch): {}>, <Hit(test-index/42): {}...}}>, "
        "<Hit(test-index/47): {}...}}>, <Hit(test-index/53): {{}}>]"
    ).format(
        repr(dummy_response["hits"]["hits"][0]["_source"]),
        repr(dummy_response["hits"]["hits"][1]["_source"])[:60],
        repr(dummy_response["hits"]["hits"][2]["_source"])[:60],
    )

    assert res
    assert f"<Response: {rhits}>" == repr(res)
    assert rhits == repr(hits)
    assert {"meta", "city", "name"} == set(dir(h))
    assert "<Hit(test-index/elasticsearch): %r>" % dummy_response["hits"]["hits"][0][
        "_source"
    ] == repr(h)


def test_empty_response_is_false(dummy_response: Dict[str, Any]) -> None:
    dummy_response["hits"]["hits"] = []
    res = response.Response(Search(), dummy_response)

    assert not res


def test_len_response(dummy_response: Dict[str, Any]) -> None:
    res = response.Response(Search(), dummy_response)
    assert len(res) == 4


def test_iterating_over_response_gives_you_hits(dummy_response: Dict[str, Any]) -> None:
    res = response.Response(Search(), dummy_response)
    hits = list(h for h in res)

    assert res.success()
    assert 123 == res.took
    assert 4 == len(hits)
    assert all(isinstance(h, response.Hit) for h in hits)
    h = hits[0]

    assert "test-index" == h.meta.index
    assert "company" == h.meta.doc_type
    assert "elasticsearch" == h.meta.id
    assert 12 == h.meta.score

    assert hits[1].meta.routing == "elasticsearch"


def test_hits_get_wrapped_to_contain_additional_attrs(
    dummy_response: Dict[str, Any]
) -> None:
    res = response.Response(Search(), dummy_response)
    hits = res.hits

    assert 123 == hits.total  # type: ignore[attr-defined]
    assert 12.0 == hits.max_score  # type: ignore[attr-defined]


def test_hits_provide_dot_and_bracket_access_to_attrs(
    dummy_response: Dict[str, Any]
) -> None:
    res = response.Response(Search(), dummy_response)
    h = res.hits[0]

    assert "Elasticsearch" == h.name
    assert "Elasticsearch" == h["name"]

    assert "Honza" == res.hits[2].name.first

    with raises(KeyError):
        h["not_there"]

    with raises(AttributeError):
        h.not_there


def test_slicing_on_response_slices_on_hits(dummy_response: Dict[str, Any]) -> None:
    res = response.Response(Search(), dummy_response)

    assert res[0] is res.hits[0]
    assert res[::-1] == res.hits[::-1]


def test_aggregation_base(agg_response: response.Response) -> None:
    assert agg_response.aggs is agg_response.aggregations
    assert isinstance(agg_response.aggs, response.AggResponse)


def test_metric_agg_works(agg_response: response.Response) -> None:
    assert 25052.0 == agg_response.aggs.sum_lines.value


def test_aggregations_can_be_iterated_over(agg_response: response.Response) -> None:
    aggs = [a for a in agg_response.aggs]

    assert len(aggs) == 3
    assert all(map(lambda a: isinstance(a, AggResponse), aggs))


def test_aggregations_can_be_retrieved_by_name(
    agg_response: response.Response, aggs_search: Search
) -> None:
    a = agg_response.aggs["popular_files"]

    assert isinstance(a, BucketData)
    assert isinstance(a._meta["aggs"], Terms)
    assert a._meta["aggs"] is aggs_search.aggs.aggs["popular_files"]


def test_bucket_response_can_be_iterated_over(agg_response: response.Response) -> None:
    popular_files = agg_response.aggregations.popular_files

    buckets = [b for b in popular_files]
    assert all(isinstance(b, Bucket) for b in buckets)
    assert buckets == popular_files.buckets


def test_bucket_keys_get_deserialized(
    aggs_data: Dict[str, Any], aggs_search: Search
) -> None:
    class Commit(Document):
        info = Object(properties={"committed_date": Date()})

        class Index:
            name = "test-commit"

    aggs_search = aggs_search.doc_type(Commit)
    agg_response = response.Response(aggs_search, aggs_data)

    per_month = agg_response.aggregations.per_month
    for b in per_month:
        assert isinstance(b.key, date)
