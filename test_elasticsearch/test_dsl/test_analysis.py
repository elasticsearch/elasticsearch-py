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

from elasticsearch.dsl import analysis


def test_analyzer_serializes_as_name() -> None:
    a = analysis.analyzer("my_analyzer")

    assert "my_analyzer" == a.to_dict()  # type: ignore


def test_analyzer_has_definition() -> None:
    a = analysis.CustomAnalyzer(
        "my_analyzer", tokenizer="keyword", filter=["lowercase"]
    )

    assert {
        "type": "custom",
        "tokenizer": "keyword",
        "filter": ["lowercase"],
    } == a.get_definition()


def test_simple_multiplexer_filter() -> None:
    a = analysis.analyzer(
        "my_analyzer",
        tokenizer="keyword",
        filter=[
            analysis.token_filter(
                "my_multi", "multiplexer", filters=["lowercase", "lowercase, stop"]
            )
        ],
    )

    assert {
        "analyzer": {
            "my_analyzer": {
                "filter": ["my_multi"],
                "tokenizer": "keyword",
                "type": "custom",
            }
        },
        "filter": {
            "my_multi": {
                "filters": ["lowercase", "lowercase, stop"],
                "type": "multiplexer",
            }
        },
    } == a.get_analysis_definition()


def test_multiplexer_with_custom_filter() -> None:
    a = analysis.analyzer(
        "my_analyzer",
        tokenizer="keyword",
        filter=[
            analysis.token_filter(
                "my_multi",
                "multiplexer",
                filters=[
                    [analysis.token_filter("en", "snowball", language="English")],
                    "lowercase, stop",
                ],
            )
        ],
    )

    assert {
        "analyzer": {
            "my_analyzer": {
                "filter": ["my_multi"],
                "tokenizer": "keyword",
                "type": "custom",
            }
        },
        "filter": {
            "en": {"type": "snowball", "language": "English"},
            "my_multi": {"filters": ["en", "lowercase, stop"], "type": "multiplexer"},
        },
    } == a.get_analysis_definition()


def test_conditional_token_filter() -> None:
    a = analysis.analyzer(
        "my_cond",
        tokenizer=analysis.tokenizer("keyword"),
        filter=[
            analysis.token_filter(
                "testing",
                "condition",
                script={"source": "return true"},
                filter=[
                    "lowercase",
                    analysis.token_filter("en", "snowball", language="English"),
                ],
            ),
            "stop",
        ],
    )

    assert {
        "analyzer": {
            "my_cond": {
                "filter": ["testing", "stop"],
                "tokenizer": "keyword",
                "type": "custom",
            }
        },
        "filter": {
            "en": {"language": "English", "type": "snowball"},
            "testing": {
                "script": {"source": "return true"},
                "filter": ["lowercase", "en"],
                "type": "condition",
            },
        },
    } == a.get_analysis_definition()


def test_conflicting_nested_filters_cause_error() -> None:
    a = analysis.analyzer(
        "my_cond",
        tokenizer=analysis.tokenizer("keyword"),
        filter=[
            analysis.token_filter("en", "stemmer", language="english"),
            analysis.token_filter(
                "testing",
                "condition",
                script={"source": "return true"},
                filter=[
                    "lowercase",
                    analysis.token_filter("en", "snowball", language="English"),
                ],
            ),
        ],
    )

    with raises(ValueError):
        a.get_analysis_definition()


def test_normalizer_serializes_as_name() -> None:
    n = analysis.normalizer("my_normalizer")

    assert "my_normalizer" == n.to_dict()  # type: ignore


def test_normalizer_has_definition() -> None:
    n = analysis.CustomNormalizer(
        "my_normalizer", filter=["lowercase", "asciifolding"], char_filter=["quote"]
    )

    assert {
        "type": "custom",
        "filter": ["lowercase", "asciifolding"],
        "char_filter": ["quote"],
    } == n.get_definition()


def test_tokenizer() -> None:
    t = analysis.tokenizer("trigram", "nGram", min_gram=3, max_gram=3)

    assert t.to_dict() == "trigram"  # type: ignore
    assert {"type": "nGram", "min_gram": 3, "max_gram": 3} == t.get_definition()


def test_custom_analyzer_can_collect_custom_items() -> None:
    trigram = analysis.tokenizer("trigram", "nGram", min_gram=3, max_gram=3)
    my_stop = analysis.token_filter("my_stop", "stop", stopwords=["a", "b"])
    umlauts = analysis.char_filter("umlauts", "pattern_replace", mappings=["ü=>ue"])
    a = analysis.analyzer(
        "my_analyzer",
        tokenizer=trigram,
        filter=["lowercase", my_stop],
        char_filter=["html_strip", umlauts],
    )

    assert a.to_dict() == "my_analyzer"  # type: ignore
    assert {
        "analyzer": {
            "my_analyzer": {
                "type": "custom",
                "tokenizer": "trigram",
                "filter": ["lowercase", "my_stop"],
                "char_filter": ["html_strip", "umlauts"],
            }
        },
        "tokenizer": {"trigram": trigram.get_definition()},
        "filter": {"my_stop": my_stop.get_definition()},
        "char_filter": {"umlauts": umlauts.get_definition()},
    } == a.get_analysis_definition()


def test_stemmer_analyzer_can_pass_name() -> None:
    t = analysis.token_filter(
        "my_english_filter", name="minimal_english", type="stemmer"
    )
    assert t.to_dict() == "my_english_filter"  # type: ignore
    assert {"type": "stemmer", "name": "minimal_english"} == t.get_definition()
