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

from pytest import raises

from elasticsearch.dsl import function, query, utils


def test_empty_Q_is_match_all() -> None:
    q = query.Q()

    assert isinstance(q, query.MatchAll)
    assert query.MatchAll() == q


def test_combined_fields_to_dict() -> None:
    assert {
        "combined_fields": {
            "query": "this is a test",
            "fields": ["name", "body", "description"],
            "operator": "and",
        },
    } == query.CombinedFields(
        query="this is a test",
        fields=["name", "body", "description"],
        operator="and",
    ).to_dict()


def test_combined_fields_to_dict_extra() -> None:
    assert {
        "combined_fields": {
            "query": "this is a test",
            "fields": ["name", "body^2"],
            "operator": "or",
        },
    } == query.CombinedFields(
        query="this is a test",
        fields=["name", "body^2"],
        operator="or",
    ).to_dict()


def test_match_to_dict() -> None:
    assert {"match": {"f": "value"}} == query.Match(f="value").to_dict()


def test_match_to_dict_extra() -> None:
    assert {"match": {"f": "value", "boost": 2}} == query.Match(
        f="value", boost=2
    ).to_dict()


def test_fuzzy_to_dict() -> None:
    assert {"fuzzy": {"f": "value"}} == query.Fuzzy(f="value").to_dict()


def test_prefix_to_dict() -> None:
    assert {"prefix": {"f": "value"}} == query.Prefix(f="value").to_dict()


def test_term_to_dict() -> None:
    assert {"term": {"_type": "article"}} == query.Term(_type="article").to_dict()


def test_terms_to_dict() -> None:
    assert {"terms": {"_type": ["article", "section"]}} == query.Terms(
        _type=["article", "section"]
    ).to_dict()
    assert {"terms": {"_type": ["article", "section"], "boost": 1.1}} == query.Terms(
        _type=("article", "section"), boost=1.1
    ).to_dict()
    assert {"terms": {"_type": "article", "boost": 1.1}} == query.Terms(
        _type="article", boost=1.1
    ).to_dict()
    assert {
        "terms": {"_id": {"index": "my-other-index", "id": "my-id"}, "boost": 1.1}
    } == query.Terms(
        _id={"index": "my-other-index", "id": "my-id"}, boost=1.1
    ).to_dict()


def test_bool_to_dict() -> None:
    bool = query.Bool(must=[query.Match(f="value")], should=[])

    assert {"bool": {"must": [{"match": {"f": "value"}}]}} == bool.to_dict()


def test_dismax_to_dict() -> None:
    assert {"dis_max": {"queries": [{"term": {"_type": "article"}}]}} == query.DisMax(
        queries=[query.Term(_type="article")]
    ).to_dict()


def test_bool_from_dict_issue_318() -> None:
    d = {"bool": {"must_not": {"match": {"field": "value"}}}}
    q = query.Q(d)

    assert q == ~query.Match(field="value")


def test_repr() -> None:
    bool = query.Bool(must=[query.Match(f="value")], should=[])

    assert "Bool(must=[Match(f='value')])" == repr(bool)


def test_query_clone() -> None:
    bool = query.Bool(
        must=[query.Match(x=42)],
        should=[query.Match(g="v2")],
        must_not=[query.Match(title="value")],
    )
    bool_clone = bool._clone()

    assert bool == bool_clone
    assert bool is not bool_clone


def test_bool_converts_its_init_args_to_queries() -> None:
    q = query.Bool(must=[{"match": {"f": "value"}}])  # type: ignore

    assert len(q.must) == 1
    assert q.must[0] == query.Match(f="value")


def test_two_queries_make_a_bool() -> None:
    q1 = query.Match(f="value1")
    q2 = query.Match(message={"query": "this is a test", "opeartor": "and"})
    q = q1 & q2

    assert isinstance(q, query.Bool)
    assert [q1, q2] == q.must


def test_other_and_bool_appends_other_to_must() -> None:
    q1 = query.Match(f="value1")
    qb = query.Bool()

    q = q1 & qb
    assert q is not qb
    assert q.must[0] == q1


def test_bool_and_other_appends_other_to_must() -> None:
    q1 = query.Match(f="value1")
    qb = query.Bool()

    q = qb & q1
    assert q is not qb
    assert q.must[0] == q1


def test_bool_and_other_sets_min_should_match_if_needed() -> None:
    q1 = query.Q("term", category=1)
    q2 = query.Q(
        "bool", should=[query.Q("term", name="aaa"), query.Q("term", name="bbb")]
    )

    q = q1 & q2
    assert q == query.Bool(
        must=[q1],
        should=[query.Q("term", name="aaa"), query.Q("term", name="bbb")],
        minimum_should_match=1,
    )


def test_bool_with_different_minimum_should_match_should_not_be_combined() -> None:
    q1 = query.Q(
        "bool",
        minimum_should_match=2,
        should=[
            query.Q("term", field="aa1"),
            query.Q("term", field="aa2"),
            query.Q("term", field="aa3"),
            query.Q("term", field="aa4"),
        ],
    )
    q2 = query.Q(
        "bool",
        minimum_should_match=3,
        should=[
            query.Q("term", field="bb1"),
            query.Q("term", field="bb2"),
            query.Q("term", field="bb3"),
            query.Q("term", field="bb4"),
        ],
    )
    q3 = query.Q(
        "bool",
        minimum_should_match=4,
        should=[
            query.Q("term", field="cc1"),
            query.Q("term", field="cc2"),
            query.Q("term", field="cc3"),
            query.Q("term", field="cc4"),
        ],
    )

    q4 = q1 | q2
    assert q4 == query.Bool(should=[q1, q2])

    q5 = q1 | q2 | q3
    assert q5 == query.Bool(should=[q1, q2, q3])


def test_empty_bool_has_min_should_match_0() -> None:
    assert 0 == query.Bool()._min_should_match


def test_query_and_query_creates_bool() -> None:
    q1 = query.Match(f=42)
    q2 = query.Match(g=47)

    q = q1 & q2
    assert isinstance(q, query.Bool)
    assert q.must == [q1, q2]


def test_match_all_and_query_equals_other() -> None:
    q1 = query.Match(f=42)
    q2 = query.MatchAll()

    q = q1 & q2
    assert q1 == q


def test_not_match_all_is_match_none() -> None:
    q = query.MatchAll()

    assert ~q == query.MatchNone()


def test_not_match_none_is_match_all() -> None:
    q = query.MatchNone()

    assert ~q == query.MatchAll()


def test_invert_empty_bool_is_match_none() -> None:
    q = query.Bool()

    assert ~q == query.MatchNone()


def test_match_none_or_query_equals_query() -> None:
    q1 = query.Match(f=42)
    q2 = query.MatchNone()

    assert q1 | q2 == query.Match(f=42)


def test_match_none_and_query_equals_match_none() -> None:
    q1 = query.Match(f=42)
    q2 = query.MatchNone()

    assert q1 & q2 == query.MatchNone()


def test_bool_and_bool() -> None:
    qt1, qt2, qt3 = query.Match(f=1), query.Match(f=2), query.Match(f=3)

    q1 = query.Bool(must=[qt1], should=[qt2])
    q2 = query.Bool(must_not=[qt3])
    assert q1 & q2 == query.Bool(
        must=[qt1], must_not=[qt3], should=[qt2], minimum_should_match=0
    )

    q1 = query.Bool(must=[qt1], should=[qt1, qt2])
    q2 = query.Bool(should=[qt3])
    assert q1 & q2 == query.Bool(
        must=[qt1, qt3], should=[qt1, qt2], minimum_should_match=0
    )


def test_bool_and_bool_with_min_should_match() -> None:
    qt1, qt2 = query.Match(f=1), query.Match(f=2)
    q1 = query.Q("bool", minimum_should_match=1, should=[qt1])
    q2 = query.Q("bool", minimum_should_match=1, should=[qt2])

    assert query.Q("bool", must=[qt1, qt2]) == q1 & q2


def test_negative_min_should_match() -> None:
    qt1, qt2 = query.Match(f=1), query.Match(f=2)
    q1 = query.Q("bool", minimum_should_match=-2, should=[qt1])
    q2 = query.Q("bool", minimum_should_match=1, should=[qt2])

    with raises(ValueError):
        q1 & q2
    with raises(ValueError):
        q2 & q1


def test_percentage_min_should_match() -> None:
    qt1, qt2 = query.Match(f=1), query.Match(f=2)
    q1 = query.Q("bool", minimum_should_match="50%", should=[qt1])
    q2 = query.Q("bool", minimum_should_match=1, should=[qt2])

    with raises(ValueError):
        q1 & q2
    with raises(ValueError):
        q2 & q1


def test_inverted_query_becomes_bool_with_must_not() -> None:
    q = query.Match(f=42)

    assert ~q == query.Bool(must_not=[query.Match(f=42)])


def test_inverted_query_with_must_not_become_should() -> None:
    q = query.Q("bool", must_not=[query.Q("match", f=1), query.Q("match", f=2)])

    assert ~q == query.Q("bool", should=[query.Q("match", f=1), query.Q("match", f=2)])


def test_inverted_query_with_must_and_must_not() -> None:
    q = query.Q(
        "bool",
        must=[query.Q("match", f=3), query.Q("match", f=4)],
        must_not=[query.Q("match", f=1), query.Q("match", f=2)],
    )
    print((~q).to_dict())
    assert ~q == query.Q(
        "bool",
        should=[
            # negation of must
            query.Q("bool", must_not=[query.Q("match", f=3)]),
            query.Q("bool", must_not=[query.Q("match", f=4)]),
            # negation of must_not
            query.Q("match", f=1),
            query.Q("match", f=2),
        ],
    )


def test_double_invert_returns_original_query() -> None:
    q = query.Match(f=42)

    assert q == ~~q


def test_bool_query_gets_inverted_internally() -> None:
    q = query.Bool(must_not=[query.Match(f=42)], must=[query.Match(g="v")])

    assert ~q == query.Bool(
        should=[
            # negating must
            query.Bool(must_not=[query.Match(g="v")]),
            # negating must_not
            query.Match(f=42),
        ]
    )


def test_match_all_or_something_is_match_all() -> None:
    q1 = query.MatchAll()
    q2 = query.Match(f=42)

    assert (q1 | q2) == query.MatchAll()
    assert (q2 | q1) == query.MatchAll()


def test_or_produces_bool_with_should() -> None:
    q1 = query.Match(f=42)
    q2 = query.Match(g="v")

    q = q1 | q2
    assert q == query.Bool(should=[q1, q2])


def test_or_bool_doesnt_loop_infinitely_issue_37() -> None:
    q = query.Match(f=42) | ~query.Match(f=47)

    assert q == query.Bool(
        should=[query.Bool(must_not=[query.Match(f=47)]), query.Match(f=42)]
    )


def test_or_bool_doesnt_loop_infinitely_issue_96() -> None:
    q = ~query.Match(f=42) | ~query.Match(f=47)

    assert q == query.Bool(
        should=[
            query.Bool(must_not=[query.Match(f=42)]),
            query.Bool(must_not=[query.Match(f=47)]),
        ]
    )


def test_bool_will_append_another_query_with_or() -> None:
    qb = query.Bool(should=[query.Match(f="v"), query.Match(f="v2")])
    q = query.Match(g=42)

    assert (q | qb) == query.Bool(should=[query.Match(f="v"), query.Match(f="v2"), q])


def test_bool_queries_with_only_should_get_concatenated() -> None:
    q1 = query.Bool(should=[query.Match(f=1), query.Match(f=2)])
    q2 = query.Bool(should=[query.Match(f=3), query.Match(f=4)])

    assert (q1 | q2) == query.Bool(
        should=[query.Match(f=1), query.Match(f=2), query.Match(f=3), query.Match(f=4)]
    )


def test_two_bool_queries_append_one_to_should_if_possible() -> None:
    q1 = query.Bool(should=[query.Match(f="v")])
    q2 = query.Bool(must=[query.Match(f="v")])

    assert (q1 | q2) == query.Bool(
        should=[query.Match(f="v"), query.Bool(must=[query.Match(f="v")])]
    )
    assert (q2 | q1) == query.Bool(
        should=[query.Match(f="v"), query.Bool(must=[query.Match(f="v")])]
    )


def test_queries_are_registered() -> None:
    assert "match" in query.Query._classes
    assert query.Query._classes["match"] is query.Match


def test_defining_query_registers_it() -> None:
    class MyQuery(query.Query):
        name = "my_query"

    assert "my_query" in query.Query._classes
    assert query.Query._classes["my_query"] is MyQuery


def test_Q_passes_query_through() -> None:
    q = query.Match(f="value1")

    assert query.Q(q) is q


def test_Q_constructs_query_by_name() -> None:
    q = query.Q("match", f="value")

    assert isinstance(q, query.Match)
    assert {"f": "value"} == q._params


def test_Q_translates_double_underscore_to_dots_in_param_names() -> None:
    q = query.Q("match", comment__author="honza")

    assert {"comment.author": "honza"} == q._params


def test_Q_doesn_translate_double_underscore_to_dots_in_param_names() -> None:
    q = query.Q("match", comment__author="honza", _expand__to_dot=False)

    assert {"comment__author": "honza"} == q._params


def test_Q_constructs_simple_query_from_dict() -> None:
    q = query.Q({"match": {"f": "value"}})

    assert isinstance(q, query.Match)
    assert {"f": "value"} == q._params


def test_Q_constructs_compound_query_from_dict() -> None:
    q = query.Q({"bool": {"must": [{"match": {"f": "value"}}]}})

    assert q == query.Bool(must=[query.Match(f="value")])


def test_Q_raises_error_when_passed_in_dict_and_params() -> None:
    with raises(Exception):
        # Ignore types as it's not a valid call
        query.Q({"match": {"f": "value"}}, f="value")  # type: ignore[call-overload]


def test_Q_raises_error_when_passed_in_query_and_params() -> None:
    q = query.Match(f="value1")

    with raises(Exception):
        # Ignore types as it's not a valid call signature
        query.Q(q, f="value")  # type: ignore[call-overload]


def test_Q_raises_error_on_unknown_query() -> None:
    with raises(Exception):
        query.Q("not a query", f="value")


def test_match_all_and_anything_is_anything() -> None:
    q = query.MatchAll()

    s = query.Match(f=42)
    assert q & s == s
    assert s & q == s


def test_function_score_with_functions() -> None:
    q = query.Q(
        "function_score",
        functions=[query.SF("script_score", script="doc['comment_count'] * _score")],
    )

    assert {
        "function_score": {
            "functions": [{"script_score": {"script": "doc['comment_count'] * _score"}}]
        }
    } == q.to_dict()


def test_function_score_with_no_function_is_boost_factor() -> None:
    q = query.Q(
        "function_score",
        functions=[query.SF({"weight": 20, "filter": query.Q("term", f=42)})],
    )

    assert {
        "function_score": {"functions": [{"filter": {"term": {"f": 42}}, "weight": 20}]}
    } == q.to_dict()


def test_function_score_to_dict() -> None:
    q = query.Q(
        "function_score",
        query=query.Q("match", title="python"),
        functions=[
            query.SF("random_score"),
            query.SF(
                "field_value_factor",
                field="comment_count",
                filter=query.Q("term", tags="python"),
            ),
        ],
    )

    d = {
        "function_score": {
            "query": {"match": {"title": "python"}},
            "functions": [
                {"random_score": {}},
                {
                    "filter": {"term": {"tags": "python"}},
                    "field_value_factor": {"field": "comment_count"},
                },
            ],
        }
    }
    assert d == q.to_dict()


def test_function_score_class_based_to_dict() -> None:
    q = query.FunctionScore(
        query=query.Match(title="python"),
        functions=[
            function.RandomScore(),
            function.FieldValueFactor(
                field="comment_count",
                filter=query.Term(tags="python"),
            ),
        ],
    )

    d = {
        "function_score": {
            "query": {"match": {"title": "python"}},
            "functions": [
                {"random_score": {}},
                {
                    "filter": {"term": {"tags": "python"}},
                    "field_value_factor": {"field": "comment_count"},
                },
            ],
        }
    }
    assert d == q.to_dict()


def test_function_score_with_single_function() -> None:
    d = {
        "function_score": {
            "filter": {"term": {"tags": "python"}},
            "script_score": {"script": "doc['comment_count'] * _score"},
        }
    }

    q = query.Q(d)
    assert isinstance(q, query.FunctionScore)
    assert isinstance(q.filter, query.Term)
    assert len(q.functions) == 1

    sf = q.functions[0]
    assert isinstance(sf, function.ScriptScore)
    assert "doc['comment_count'] * _score" == sf.script


def test_function_score_from_dict() -> None:
    d = {
        "function_score": {
            "filter": {"term": {"tags": "python"}},
            "functions": [
                {
                    "filter": {"terms": {"tags": "python"}},
                    "script_score": {"script": "doc['comment_count'] * _score"},
                },
                {"boost_factor": 6},
            ],
        }
    }

    q = query.Q(d)
    assert isinstance(q, query.FunctionScore)
    assert isinstance(q.filter, query.Term)
    assert len(q.functions) == 2

    sf = q.functions[0]
    assert isinstance(sf, function.ScriptScore)
    assert isinstance(sf.filter, query.Terms)

    sf = q.functions[1]
    assert isinstance(sf, function.BoostFactor)
    assert 6 == sf.value
    assert {"boost_factor": 6} == sf.to_dict()


def test_script_score() -> None:
    d = {
        "script_score": {
            "query": {"match_all": {}},
            "script": {"source": "...", "params": {}},
        }
    }
    q = query.Q(d)

    assert isinstance(q, query.ScriptScore)
    assert isinstance(q.query, query.MatchAll)
    assert q.script == {"source": "...", "params": {}}
    assert q.to_dict() == d


def test_expand_double_underscore_to_dot_setting() -> None:
    q = query.Term(comment__count=2)
    assert q.to_dict() == {"term": {"comment.count": 2}}
    utils.EXPAND__TO_DOT = False
    q = query.Term(comment__count=2)
    assert q.to_dict() == {"term": {"comment__count": 2}}
    utils.EXPAND__TO_DOT = True


def test_knn_query() -> None:
    q = query.Knn(field="image-vector", query_vector=[-5, 9, -12], num_candidates=10)
    assert q.to_dict() == {
        "knn": {
            "field": "image-vector",
            "query_vector": [-5, 9, -12],
            "num_candidates": 10,
        }
    }
