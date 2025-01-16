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

from datetime import datetime

import pytest
import pytest_asyncio

from elasticsearch import AsyncElasticsearch
from elasticsearch.dsl import Q

from ..async_examples.parent_child import Answer, Comment, Question, User, setup

honza = User(
    id=42,
    signed_up=datetime(2013, 4, 3),
    username="honzakral",
    email="honza@elastic.co",
    location="Prague",
)

nick = User(
    id=47,
    signed_up=datetime(2017, 4, 3),
    username="fxdgear",
    email="nick.lang@elastic.co",
    location="Colorado",
)


@pytest_asyncio.fixture
async def question(async_write_client: AsyncElasticsearch) -> Question:
    await setup()
    assert await async_write_client.indices.exists_index_template(name="base")

    # create a question object
    q = Question(
        _id=1,
        author=nick,
        tags=["elasticsearch", "python"],
        title="How do I use elasticsearch from Python?",
        body="""
        I want to use elasticsearch, how do I do it from Python?
        """,
        created=None,
        question_answer=None,
        comments=[],
    )
    await q.save()
    return q


@pytest.mark.asyncio
async def test_comment(
    async_write_client: AsyncElasticsearch, question: Question
) -> None:
    await question.add_comment(nick, "Just use elasticsearch-py")

    q = await Question.get(1)  # type: ignore[arg-type]
    assert isinstance(q, Question)
    assert 1 == len(q.comments)

    c = q.comments[0]
    assert isinstance(c, Comment)
    assert c.author.username == "fxdgear"


@pytest.mark.asyncio
async def test_question_answer(
    async_write_client: AsyncElasticsearch, question: Question
) -> None:
    a = await question.add_answer(honza, "Just use `elasticsearch-py`!")

    assert isinstance(a, Answer)

    # refresh the index so we can search right away
    await Question._index.refresh()

    # we can now fetch answers from elasticsearch
    answers = await question.get_answers()
    assert 1 == len(answers)
    assert isinstance(answers[0], Answer)

    search = Question.search().query(
        "has_child",
        type="answer",
        inner_hits={},
        query=Q("term", author__username__keyword="honzakral"),
    )
    response = await search.execute()

    assert 1 == len(response.hits)

    q = response.hits[0]
    assert isinstance(q, Question)
    assert 1 == len(q.meta.inner_hits.answer.hits)
    assert q.meta.inner_hits.answer.hits is await q.get_answers()

    a = q.meta.inner_hits.answer.hits[0]
    assert isinstance(a, Answer)
    assert isinstance(await a.get_question(), Question)
    assert (await a.get_question()).meta.id == "1"
