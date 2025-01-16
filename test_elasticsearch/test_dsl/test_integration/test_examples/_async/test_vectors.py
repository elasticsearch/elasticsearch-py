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

from hashlib import md5
from typing import Any, List, Tuple
from unittest import SkipTest

import pytest

from elasticsearch import AsyncElasticsearch
from test_elasticsearch.test_dsl.async_sleep import sleep

from ..async_examples import vectors


@pytest.mark.asyncio
async def test_vector_search(
    async_write_client: AsyncElasticsearch, es_version: Tuple[int, ...], mocker: Any
) -> None:
    # this test only runs on Elasticsearch >= 8.11 because the example uses
    # a dense vector without specifying an explicit size
    if es_version < (8, 11):
        raise SkipTest("This test requires Elasticsearch 8.11 or newer")

    class MockModel:
        def __init__(self, model: Any):
            pass

        def encode(self, text: str) -> List[float]:
            vector = [int(ch) for ch in md5(text.encode()).digest()]
            total = sum(vector)
            return [float(v) / total for v in vector]

    mocker.patch.object(vectors, "SentenceTransformer", new=MockModel)

    await vectors.create()
    for i in range(10):
        results = await (await vectors.search("Welcome to our team!")).execute()
        if len(results.hits) > 0:
            break
        await sleep(0.1)
    assert results[0].name == "New Employee Onboarding Guide"
