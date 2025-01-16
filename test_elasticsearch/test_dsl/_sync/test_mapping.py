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

import json

from elasticsearch.dsl import Keyword, Mapping, Nested, Text, analysis


def test_mapping_can_has_fields() -> None:
    m = Mapping()
    m.field("name", "text").field("tags", "keyword")

    assert {
        "properties": {"name": {"type": "text"}, "tags": {"type": "keyword"}}
    } == m.to_dict()


def test_mapping_update_is_recursive() -> None:
    m1 = Mapping()
    m1.field("title", "text")
    m1.field("author", "object")
    m1.field("author", "object", properties={"name": {"type": "text"}})
    m1.meta("_all", enabled=False)
    m1.meta("dynamic", False)

    m2 = Mapping()
    m2.field("published_from", "date")
    m2.field("author", "object", properties={"email": {"type": "text"}})
    m2.field("title", "text")
    m2.field("lang", "keyword")
    m2.meta("_analyzer", path="lang")

    m1.update(m2, update_only=True)

    assert {
        "_all": {"enabled": False},
        "_analyzer": {"path": "lang"},
        "dynamic": False,
        "properties": {
            "published_from": {"type": "date"},
            "title": {"type": "text"},
            "lang": {"type": "keyword"},
            "author": {
                "type": "object",
                "properties": {"name": {"type": "text"}, "email": {"type": "text"}},
            },
        },
    } == m1.to_dict()


def test_properties_can_iterate_over_all_the_fields() -> None:
    m = Mapping()
    m.field("f1", "text", test_attr="f1", fields={"f2": Keyword(test_attr="f2")})
    m.field("f3", Nested(test_attr="f3", properties={"f4": Text(test_attr="f4")}))

    assert {"f1", "f2", "f3", "f4"} == {
        f.test_attr for f in m.properties._collect_fields()
    }


def test_mapping_can_collect_all_analyzers_and_normalizers() -> None:
    a1 = analysis.analyzer(
        "my_analyzer1",
        tokenizer="keyword",
        filter=[
            "lowercase",
            analysis.token_filter("my_filter1", "stop", stopwords=["a", "b"]),
        ],
    )
    a2 = analysis.analyzer("english")
    a3 = analysis.analyzer("unknown_custom")
    a4 = analysis.analyzer(
        "my_analyzer2",
        tokenizer=analysis.tokenizer("trigram", "nGram", min_gram=3, max_gram=3),
        filter=[analysis.token_filter("my_filter2", "stop", stopwords=["c", "d"])],
    )
    a5 = analysis.analyzer("my_analyzer3", tokenizer="keyword")
    n1 = analysis.normalizer("my_normalizer1", filter=["lowercase"])
    n2 = analysis.normalizer(
        "my_normalizer2",
        filter=[
            "my_filter1",
            "my_filter2",
            analysis.token_filter("my_filter3", "stop", stopwords=["e", "f"]),
        ],
    )
    n3 = analysis.normalizer("unknown_custom")

    m = Mapping()
    m.field(
        "title",
        "text",
        analyzer=a1,
        fields={"english": Text(analyzer=a2), "unknown": Keyword(search_analyzer=a3)},
    )
    m.field("comments", Nested(properties={"author": Text(analyzer=a4)}))
    m.field("normalized_title", "keyword", normalizer=n1)
    m.field("normalized_comment", "keyword", normalizer=n2)
    m.field("unknown", "keyword", normalizer=n3)
    m.meta("_all", analyzer=a5)

    assert {
        "analyzer": {
            "my_analyzer1": {
                "filter": ["lowercase", "my_filter1"],
                "tokenizer": "keyword",
                "type": "custom",
            },
            "my_analyzer2": {
                "filter": ["my_filter2"],
                "tokenizer": "trigram",
                "type": "custom",
            },
            "my_analyzer3": {"tokenizer": "keyword", "type": "custom"},
        },
        "normalizer": {
            "my_normalizer1": {"filter": ["lowercase"], "type": "custom"},
            "my_normalizer2": {
                "filter": ["my_filter1", "my_filter2", "my_filter3"],
                "type": "custom",
            },
        },
        "filter": {
            "my_filter1": {"stopwords": ["a", "b"], "type": "stop"},
            "my_filter2": {"stopwords": ["c", "d"], "type": "stop"},
            "my_filter3": {"stopwords": ["e", "f"], "type": "stop"},
        },
        "tokenizer": {"trigram": {"max_gram": 3, "min_gram": 3, "type": "nGram"}},
    } == m._collect_analysis()

    assert json.loads(json.dumps(m.to_dict())) == m.to_dict()


def test_mapping_can_collect_multiple_analyzers() -> None:
    a1 = analysis.analyzer(
        "my_analyzer1",
        tokenizer="keyword",
        filter=[
            "lowercase",
            analysis.token_filter("my_filter1", "stop", stopwords=["a", "b"]),
        ],
    )
    a2 = analysis.analyzer(
        "my_analyzer2",
        tokenizer=analysis.tokenizer("trigram", "nGram", min_gram=3, max_gram=3),
        filter=[analysis.token_filter("my_filter2", "stop", stopwords=["c", "d"])],
    )
    m = Mapping()
    m.field("title", "text", analyzer=a1, search_analyzer=a2)
    m.field(
        "text",
        "text",
        analyzer=a1,
        fields={
            "english": Text(analyzer=a1),
            "unknown": Keyword(analyzer=a1, search_analyzer=a2),
        },
    )
    assert {
        "analyzer": {
            "my_analyzer1": {
                "filter": ["lowercase", "my_filter1"],
                "tokenizer": "keyword",
                "type": "custom",
            },
            "my_analyzer2": {
                "filter": ["my_filter2"],
                "tokenizer": "trigram",
                "type": "custom",
            },
        },
        "filter": {
            "my_filter1": {"stopwords": ["a", "b"], "type": "stop"},
            "my_filter2": {"stopwords": ["c", "d"], "type": "stop"},
        },
        "tokenizer": {"trigram": {"max_gram": 3, "min_gram": 3, "type": "nGram"}},
    } == m._collect_analysis()


def test_even_non_custom_analyzers_can_have_params() -> None:
    a1 = analysis.analyzer("whitespace", type="pattern", pattern=r"\\s+")
    m = Mapping()
    m.field("title", "text", analyzer=a1)

    assert {
        "analyzer": {"whitespace": {"type": "pattern", "pattern": r"\\s+"}}
    } == m._collect_analysis()


def test_resolve_field_can_resolve_multifields() -> None:
    m = Mapping()
    m.field("title", "text", fields={"keyword": Keyword()})

    assert isinstance(m.resolve_field("title.keyword"), Keyword)


def test_resolve_nested() -> None:
    m = Mapping()
    m.field("n1", "nested", properties={"n2": Nested(properties={"k1": Keyword()})})
    m.field("k2", "keyword")

    nested, field = m.resolve_nested("n1.n2.k1")
    assert nested == ["n1", "n1.n2"]
    assert isinstance(field, Keyword)

    nested, field = m.resolve_nested("k2")
    assert nested == []
    assert isinstance(field, Keyword)
