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

from elasticsearch import Elasticsearch
from elasticsearch.dsl import analyzer, token_filter, tokenizer


@pytest.mark.sync
def test_simulate_with_just__builtin_tokenizer(
    client: Elasticsearch,
) -> None:
    a = analyzer("my-analyzer", tokenizer="keyword")
    tokens = (a.simulate("Hello World!", using=client)).tokens

    assert len(tokens) == 1
    assert tokens[0].token == "Hello World!"


@pytest.mark.sync
def test_simulate_complex(client: Elasticsearch) -> None:
    a = analyzer(
        "my-analyzer",
        tokenizer=tokenizer("split_words", "simple_pattern_split", pattern=":"),
        filter=["lowercase", token_filter("no-ifs", "stop", stopwords=["if"])],
    )

    tokens = (a.simulate("if:this:works", using=client)).tokens

    assert len(tokens) == 2
    assert ["this", "works"] == [t.token for t in tokens]


@pytest.mark.sync
def test_simulate_builtin(client: Elasticsearch) -> None:
    a = analyzer("my-analyzer", "english")
    tokens = (a.simulate("fixes running")).tokens

    assert ["fix", "run"] == [t.token for t in tokens]
