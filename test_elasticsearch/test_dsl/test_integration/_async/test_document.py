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

# this file creates several documents using bad or no types because
# these are still supported and should be kept functional in spite
# of not having appropriate type hints. For that reason the comment
# below disables many mypy checks that fails as a result of this.
# mypy: disable-error-code="assignment, index, arg-type, call-arg, operator, comparison-overlap, attr-defined"

from datetime import datetime
from ipaddress import ip_address
from typing import TYPE_CHECKING, Any, AsyncIterator, Dict, List, Tuple, Union

import pytest
from pytest import raises
from pytz import timezone

from elasticsearch import AsyncElasticsearch, ConflictError, NotFoundError
from elasticsearch.dsl import (
    AsyncDocument,
    AsyncSearch,
    Binary,
    Boolean,
    Date,
    DenseVector,
    Double,
    InnerDoc,
    Ip,
    Keyword,
    Long,
    Mapping,
    MetaField,
    Nested,
    Object,
    Q,
    RankFeatures,
    Text,
    analyzer,
    mapped_field,
)
from elasticsearch.dsl.utils import AttrList
from elasticsearch.helpers.errors import BulkIndexError

snowball = analyzer("my_snow", tokenizer="standard", filter=["lowercase", "snowball"])


class User(InnerDoc):
    name = Text(fields={"raw": Keyword()})


class Wiki(AsyncDocument):
    owner = Object(User)
    views = Long()
    ranked = RankFeatures()

    class Index:
        name = "test-wiki"


class Repository(AsyncDocument):
    owner = Object(User)
    created_at = Date()
    description = Text(analyzer=snowball)
    tags = Keyword()

    @classmethod
    def search(cls) -> AsyncSearch["Repository"]:  # type: ignore[override]
        return super().search().filter("term", commit_repo="repo")

    class Index:
        name = "git"


class Commit(AsyncDocument):
    committed_date = Date()
    authored_date = Date()
    description = Text(analyzer=snowball)

    class Index:
        name = "flat-git"

    class Meta:
        mapping = Mapping()


class History(InnerDoc):
    timestamp = Date()
    diff = Text()


class Comment(InnerDoc):
    content = Text()
    created_at = Date()
    author = Object(User)
    history = Nested(History)

    class Meta:
        dynamic = MetaField(False)


class PullRequest(AsyncDocument):
    comments = Nested(Comment)
    created_at = Date()

    class Index:
        name = "test-prs"


class SerializationDoc(AsyncDocument):
    i = Long()
    b = Boolean()
    d = Double()
    bin = Binary()
    ip = Ip()

    class Index:
        name = "test-serialization"


class Tags(AsyncDocument):
    tags = Keyword(multi=True)

    class Index:
        name = "tags"


@pytest.mark.asyncio
async def test_serialization(async_write_client: AsyncElasticsearch) -> None:
    await SerializationDoc.init()
    await async_write_client.index(
        index="test-serialization",
        id=42,
        body={
            "i": [1, 2, "3", None],
            "b": [True, False, "true", "false", None],
            "d": [0.1, "-0.1", None],
            "bin": ["SGVsbG8gV29ybGQ=", None],
            "ip": ["::1", "127.0.0.1", None],
        },
    )
    sd = await SerializationDoc.get(id=42)
    assert sd is not None

    assert sd.i == [1, 2, 3, None]
    assert sd.b == [True, False, True, False, None]
    assert sd.d == [0.1, -0.1, None]
    assert sd.bin == [b"Hello World", None]
    assert sd.ip == [ip_address("::1"), ip_address("127.0.0.1"), None]

    assert sd.to_dict() == {
        "b": [True, False, True, False, None],
        "bin": ["SGVsbG8gV29ybGQ=", None],
        "d": [0.1, -0.1, None],
        "i": [1, 2, 3, None],
        "ip": ["::1", "127.0.0.1", None],
    }


@pytest.mark.asyncio
async def test_nested_inner_hits_are_wrapped_properly(async_pull_request: Any) -> None:
    history_query = Q(
        "nested",
        path="comments.history",
        inner_hits={},
        query=Q("match", comments__history__diff="ahoj"),
    )
    s = PullRequest.search().query(
        "nested", inner_hits={}, path="comments", query=history_query
    )

    response = await s.execute()
    pr = response.hits[0]
    assert isinstance(pr, PullRequest)
    assert isinstance(pr.comments[0], Comment)
    assert isinstance(pr.comments[0].history[0], History)

    comment = pr.meta.inner_hits.comments.hits[0]
    assert isinstance(comment, Comment)
    assert comment.author.name == "honzakral"
    assert isinstance(comment.history[0], History)

    history = comment.meta.inner_hits["comments.history"].hits[0]
    assert isinstance(history, History)
    assert history.timestamp == datetime(2012, 1, 1)
    assert "score" in history.meta


@pytest.mark.asyncio
async def test_nested_inner_hits_are_deserialized_properly(
    async_pull_request: Any,
) -> None:
    s = PullRequest.search().query(
        "nested",
        inner_hits={},
        path="comments",
        query=Q("match", comments__content="hello"),
    )

    response = await s.execute()
    pr = response.hits[0]
    assert isinstance(pr.created_at, datetime)
    assert isinstance(pr.comments[0], Comment)
    assert isinstance(pr.comments[0].created_at, datetime)


@pytest.mark.asyncio
async def test_nested_top_hits_are_wrapped_properly(async_pull_request: Any) -> None:
    s = PullRequest.search()
    s.aggs.bucket("comments", "nested", path="comments").metric(
        "hits", "top_hits", size=1
    )

    r = await s.execute()

    print(r._d_)
    assert isinstance(r.aggregations.comments.hits.hits[0], Comment)


@pytest.mark.asyncio
async def test_update_object_field(async_write_client: AsyncElasticsearch) -> None:
    await Wiki.init()
    w = Wiki(
        owner=User(name="Honza Kral"),
        _id="elasticsearch-py",
        ranked={"test1": 0.1, "topic2": 0.2},
    )
    await w.save()

    assert "updated" == await w.update(owner=[{"name": "Honza"}, User(name="Nick")])
    assert w.owner[0].name == "Honza"
    assert w.owner[1].name == "Nick"

    w = await Wiki.get(id="elasticsearch-py")
    assert w.owner[0].name == "Honza"
    assert w.owner[1].name == "Nick"

    assert w.ranked == {"test1": 0.1, "topic2": 0.2}


@pytest.mark.asyncio
async def test_update_script(async_write_client: AsyncElasticsearch) -> None:
    await Wiki.init()
    w = Wiki(owner=User(name="Honza Kral"), _id="elasticsearch-py", views=42)
    await w.save()

    await w.update(script="ctx._source.views += params.inc", inc=5)
    w = await Wiki.get(id="elasticsearch-py")
    assert w.views == 47


@pytest.mark.asyncio
async def test_update_script_with_dict(async_write_client: AsyncElasticsearch) -> None:
    await Wiki.init()
    w = Wiki(owner=User(name="Honza Kral"), _id="elasticsearch-py", views=42)
    await w.save()

    await w.update(
        script={
            "source": "ctx._source.views += params.inc1 + params.inc2",
            "params": {"inc1": 2},
            "lang": "painless",
        },
        inc2=3,
    )
    w = await Wiki.get(id="elasticsearch-py")
    assert w.views == 47


@pytest.mark.asyncio
async def test_update_retry_on_conflict(async_write_client: AsyncElasticsearch) -> None:
    await Wiki.init()
    w = Wiki(owner=User(name="Honza Kral"), _id="elasticsearch-py", views=42)
    await w.save()

    w1 = await Wiki.get(id="elasticsearch-py")
    w2 = await Wiki.get(id="elasticsearch-py")
    assert w1 is not None
    assert w2 is not None

    await w1.update(
        script="ctx._source.views += params.inc", inc=5, retry_on_conflict=1
    )
    await w2.update(
        script="ctx._source.views += params.inc", inc=5, retry_on_conflict=1
    )

    w = await Wiki.get(id="elasticsearch-py")
    assert w.views == 52


@pytest.mark.asyncio
@pytest.mark.parametrize("retry_on_conflict", [None, 0])
async def test_update_conflicting_version(
    async_write_client: AsyncElasticsearch, retry_on_conflict: bool
) -> None:
    await Wiki.init()
    w = Wiki(owner=User(name="Honza Kral"), _id="elasticsearch-py", views=42)
    await w.save()

    w1 = await Wiki.get(id="elasticsearch-py")
    w2 = await Wiki.get(id="elasticsearch-py")
    assert w1 is not None
    assert w2 is not None

    await w1.update(script="ctx._source.views += params.inc", inc=5)

    with raises(ConflictError):
        await w2.update(
            script="ctx._source.views += params.inc",
            inc=5,
            retry_on_conflict=retry_on_conflict,
        )


@pytest.mark.asyncio
async def test_save_and_update_return_doc_meta(
    async_write_client: AsyncElasticsearch,
) -> None:
    await Wiki.init()
    w = Wiki(owner=User(name="Honza Kral"), _id="elasticsearch-py", views=42)
    resp = await w.save(return_doc_meta=True)
    assert resp["_index"] == "test-wiki"
    assert resp["result"] == "created"
    assert set(resp.keys()) == {
        "_id",
        "_index",
        "_primary_term",
        "_seq_no",
        "_shards",
        "_version",
        "result",
    }

    resp = await w.update(
        script="ctx._source.views += params.inc", inc=5, return_doc_meta=True
    )
    assert resp["_index"] == "test-wiki"
    assert resp["result"] == "updated"
    assert set(resp.keys()) == {
        "_id",
        "_index",
        "_primary_term",
        "_seq_no",
        "_shards",
        "_version",
        "result",
    }


@pytest.mark.asyncio
async def test_init(async_write_client: AsyncElasticsearch) -> None:
    await Repository.init(index="test-git")

    assert await async_write_client.indices.exists(index="test-git")


@pytest.mark.asyncio
async def test_get_raises_404_on_index_missing(
    async_data_client: AsyncElasticsearch,
) -> None:
    with raises(NotFoundError):
        await Repository.get("elasticsearch-dsl-php", index="not-there")


@pytest.mark.asyncio
async def test_get_raises_404_on_non_existent_id(
    async_data_client: AsyncElasticsearch,
) -> None:
    with raises(NotFoundError):
        await Repository.get("elasticsearch-dsl-php")


@pytest.mark.asyncio
async def test_get_returns_none_if_404_ignored(
    async_data_client: AsyncElasticsearch,
) -> None:
    assert None is await Repository.get(
        "elasticsearch-dsl-php", using=async_data_client.options(ignore_status=404)
    )


@pytest.mark.asyncio
async def test_get_returns_none_if_404_ignored_and_index_doesnt_exist(
    async_data_client: AsyncElasticsearch,
) -> None:
    assert None is await Repository.get(
        "42", index="not-there", using=async_data_client.options(ignore_status=404)
    )


@pytest.mark.asyncio
async def test_get(async_data_client: AsyncElasticsearch) -> None:
    elasticsearch_repo = await Repository.get("elasticsearch-dsl-py")

    assert isinstance(elasticsearch_repo, Repository)
    assert elasticsearch_repo.owner.name == "elasticsearch"
    assert datetime(2014, 3, 3) == elasticsearch_repo.created_at


@pytest.mark.asyncio
async def test_exists_return_true(async_data_client: AsyncElasticsearch) -> None:
    assert await Repository.exists("elasticsearch-dsl-py")


@pytest.mark.asyncio
async def test_exists_false(async_data_client: AsyncElasticsearch) -> None:
    assert not await Repository.exists("elasticsearch-dsl-php")


@pytest.mark.asyncio
async def test_get_with_tz_date(async_data_client: AsyncElasticsearch) -> None:
    first_commit = await Commit.get(
        id="3ca6e1e73a071a705b4babd2f581c91a2a3e5037", routing="elasticsearch-dsl-py"
    )
    assert first_commit is not None

    tzinfo = timezone("Europe/Prague")
    assert (
        tzinfo.localize(datetime(2014, 5, 2, 13, 47, 19, 123000))
        == first_commit.authored_date
    )


@pytest.mark.asyncio
async def test_save_with_tz_date(async_data_client: AsyncElasticsearch) -> None:
    tzinfo = timezone("Europe/Prague")
    first_commit = await Commit.get(
        id="3ca6e1e73a071a705b4babd2f581c91a2a3e5037", routing="elasticsearch-dsl-py"
    )
    assert first_commit is not None

    first_commit.committed_date = tzinfo.localize(
        datetime(2014, 5, 2, 13, 47, 19, 123456)
    )
    await first_commit.save()

    first_commit = await Commit.get(
        id="3ca6e1e73a071a705b4babd2f581c91a2a3e5037", routing="elasticsearch-dsl-py"
    )
    assert first_commit is not None

    assert (
        tzinfo.localize(datetime(2014, 5, 2, 13, 47, 19, 123456))
        == first_commit.committed_date
    )


COMMIT_DOCS_WITH_MISSING = [
    {"_id": "0"},  # Missing
    {"_id": "3ca6e1e73a071a705b4babd2f581c91a2a3e5037"},  # Existing
    {"_id": "f"},  # Missing
    {"_id": "eb3e543323f189fd7b698e66295427204fff5755"},  # Existing
]


@pytest.mark.asyncio
async def test_mget(async_data_client: AsyncElasticsearch) -> None:
    commits = await Commit.mget(COMMIT_DOCS_WITH_MISSING)
    assert commits[0] is None
    assert commits[1] is not None
    assert commits[1].meta.id == "3ca6e1e73a071a705b4babd2f581c91a2a3e5037"
    assert commits[2] is None
    assert commits[3] is not None
    assert commits[3].meta.id == "eb3e543323f189fd7b698e66295427204fff5755"


@pytest.mark.asyncio
async def test_mget_raises_exception_when_missing_param_is_invalid(
    async_data_client: AsyncElasticsearch,
) -> None:
    with raises(ValueError):
        await Commit.mget(COMMIT_DOCS_WITH_MISSING, missing="raj")


@pytest.mark.asyncio
async def test_mget_raises_404_when_missing_param_is_raise(
    async_data_client: AsyncElasticsearch,
) -> None:
    with raises(NotFoundError):
        await Commit.mget(COMMIT_DOCS_WITH_MISSING, missing="raise")


@pytest.mark.asyncio
async def test_mget_ignores_missing_docs_when_missing_param_is_skip(
    async_data_client: AsyncElasticsearch,
) -> None:
    commits = await Commit.mget(COMMIT_DOCS_WITH_MISSING, missing="skip")
    assert commits[0] is not None
    assert commits[0].meta.id == "3ca6e1e73a071a705b4babd2f581c91a2a3e5037"
    assert commits[1] is not None
    assert commits[1].meta.id == "eb3e543323f189fd7b698e66295427204fff5755"


@pytest.mark.asyncio
async def test_update_works_from_search_response(
    async_data_client: AsyncElasticsearch,
) -> None:
    elasticsearch_repo = (await Repository.search().execute())[0]

    await elasticsearch_repo.update(owner={"other_name": "elastic"})
    assert "elastic" == elasticsearch_repo.owner.other_name

    new_version = await Repository.get("elasticsearch-dsl-py")
    assert new_version is not None
    assert "elastic" == new_version.owner.other_name
    assert "elasticsearch" == new_version.owner.name


@pytest.mark.asyncio
async def test_update(async_data_client: AsyncElasticsearch) -> None:
    elasticsearch_repo = await Repository.get("elasticsearch-dsl-py")
    assert elasticsearch_repo is not None
    v = elasticsearch_repo.meta.version

    old_seq_no = elasticsearch_repo.meta.seq_no
    await elasticsearch_repo.update(
        owner={"new_name": "elastic"}, new_field="testing-update"
    )

    assert "elastic" == elasticsearch_repo.owner.new_name
    assert "testing-update" == elasticsearch_repo.new_field

    # assert version has been updated
    assert elasticsearch_repo.meta.version == v + 1

    new_version = await Repository.get("elasticsearch-dsl-py")
    assert new_version is not None
    assert "testing-update" == new_version.new_field
    assert "elastic" == new_version.owner.new_name
    assert "elasticsearch" == new_version.owner.name
    assert "seq_no" in new_version.meta
    assert new_version.meta.seq_no != old_seq_no
    assert "primary_term" in new_version.meta


@pytest.mark.asyncio
async def test_save_updates_existing_doc(async_data_client: AsyncElasticsearch) -> None:
    elasticsearch_repo = await Repository.get("elasticsearch-dsl-py")
    assert elasticsearch_repo is not None

    elasticsearch_repo.new_field = "testing-save"
    old_seq_no = elasticsearch_repo.meta.seq_no
    assert "updated" == await elasticsearch_repo.save()

    new_repo = await async_data_client.get(index="git", id="elasticsearch-dsl-py")
    assert "testing-save" == new_repo["_source"]["new_field"]
    assert new_repo["_seq_no"] != old_seq_no
    assert new_repo["_seq_no"] == elasticsearch_repo.meta.seq_no


@pytest.mark.asyncio
async def test_update_empty_field(async_client: AsyncElasticsearch) -> None:
    await Tags._index.delete(ignore_unavailable=True)
    await Tags.init()
    d = Tags(id="123", tags=["a", "b"])
    await d.save(refresh=True)
    await d.update(tags=[], refresh=True)
    assert d.tags == []

    r = await Tags.search().execute()
    assert r.hits[0].tags == []


@pytest.mark.asyncio
async def test_save_automatically_uses_seq_no_and_primary_term(
    async_data_client: AsyncElasticsearch,
) -> None:
    elasticsearch_repo = await Repository.get("elasticsearch-dsl-py")
    assert elasticsearch_repo is not None
    elasticsearch_repo.meta.seq_no += 1

    with raises(ConflictError):
        await elasticsearch_repo.save()


@pytest.mark.asyncio
async def test_delete_automatically_uses_seq_no_and_primary_term(
    async_data_client: AsyncElasticsearch,
) -> None:
    elasticsearch_repo = await Repository.get("elasticsearch-dsl-py")
    assert elasticsearch_repo is not None
    elasticsearch_repo.meta.seq_no += 1

    with raises(ConflictError):
        await elasticsearch_repo.delete()


def assert_doc_equals(expected: Any, actual: Any) -> None:
    for f in expected:
        assert f in actual
        assert actual[f] == expected[f]


@pytest.mark.asyncio
async def test_can_save_to_different_index(
    async_write_client: AsyncElasticsearch,
) -> None:
    test_repo = Repository(description="testing", meta={"id": 42})
    assert await test_repo.save(index="test-document")

    assert_doc_equals(
        {
            "found": True,
            "_index": "test-document",
            "_id": "42",
            "_source": {"description": "testing"},
        },
        await async_write_client.get(index="test-document", id=42),
    )


@pytest.mark.asyncio
async def test_save_without_skip_empty_will_include_empty_fields(
    async_write_client: AsyncElasticsearch,
) -> None:
    test_repo = Repository(field_1=[], field_2=None, field_3={}, meta={"id": 42})
    assert await test_repo.save(index="test-document", skip_empty=False)

    assert_doc_equals(
        {
            "found": True,
            "_index": "test-document",
            "_id": "42",
            "_source": {"field_1": [], "field_2": None, "field_3": {}},
        },
        await async_write_client.get(index="test-document", id=42),
    )


@pytest.mark.asyncio
async def test_delete(async_write_client: AsyncElasticsearch) -> None:
    await async_write_client.create(
        index="test-document",
        id="elasticsearch-dsl-py",
        body={
            "organization": "elasticsearch",
            "created_at": "2014-03-03",
            "owner": {"name": "elasticsearch"},
        },
    )

    test_repo = Repository(meta={"id": "elasticsearch-dsl-py"})
    test_repo.meta.index = "test-document"
    await test_repo.delete()

    assert not await async_write_client.exists(
        index="test-document",
        id="elasticsearch-dsl-py",
    )


@pytest.mark.asyncio
async def test_search(async_data_client: AsyncElasticsearch) -> None:
    assert await Repository.search().count() == 1


@pytest.mark.asyncio
async def test_search_returns_proper_doc_classes(
    async_data_client: AsyncElasticsearch,
) -> None:
    result = await Repository.search().execute()

    elasticsearch_repo = result.hits[0]

    assert isinstance(elasticsearch_repo, Repository)
    assert elasticsearch_repo.owner.name == "elasticsearch"


@pytest.mark.asyncio
async def test_refresh_mapping(async_data_client: AsyncElasticsearch) -> None:
    class Commit(AsyncDocument):
        class Index:
            name = "git"

    await Commit._index.load_mappings()

    assert "stats" in Commit._index._mapping
    assert "committer" in Commit._index._mapping
    assert "description" in Commit._index._mapping
    assert "committed_date" in Commit._index._mapping
    assert isinstance(Commit._index._mapping["committed_date"], Date)


@pytest.mark.asyncio
async def test_highlight_in_meta(async_data_client: AsyncElasticsearch) -> None:
    commit = (
        await Commit.search()
        .query("match", description="inverting")
        .highlight("description")
        .execute()
    )[0]

    assert isinstance(commit, Commit)
    assert "description" in commit.meta.highlight
    assert isinstance(commit.meta.highlight["description"], AttrList)
    assert len(commit.meta.highlight["description"]) > 0


@pytest.mark.asyncio
async def test_bulk(async_data_client: AsyncElasticsearch) -> None:
    class Address(InnerDoc):
        street: str
        active: bool

    class Doc(AsyncDocument):
        if TYPE_CHECKING:
            _id: int
        name: str
        age: int
        languages: List[str] = mapped_field(Keyword())
        addresses: List[Address]

        class Index:
            name = "bulk-index"

    await Doc._index.delete(ignore_unavailable=True)
    await Doc.init()

    async def gen1() -> AsyncIterator[Union[Doc, Dict[str, Any]]]:
        yield Doc(
            name="Joe",
            age=33,
            languages=["en", "fr"],
            addresses=[
                Address(street="123 Main St", active=True),
                Address(street="321 Park Dr.", active=False),
            ],
        )
        yield Doc(name="Susan", age=20, languages=["en"])
        yield {"_op_type": "create", "_id": "45", "_source": Doc(name="Sarah", age=45)}

    await Doc.bulk(gen1(), refresh=True)
    docs = list(await Doc.search().execute())
    assert len(docs) == 3
    assert docs[0].to_dict() == {
        "name": "Joe",
        "age": 33,
        "languages": [
            "en",
            "fr",
        ],
        "addresses": [
            {
                "active": True,
                "street": "123 Main St",
            },
            {
                "active": False,
                "street": "321 Park Dr.",
            },
        ],
    }
    assert docs[1].to_dict() == {
        "name": "Susan",
        "age": 20,
        "languages": ["en"],
    }
    assert docs[2].to_dict() == {
        "name": "Sarah",
        "age": 45,
    }
    assert docs[2].meta.id == "45"

    async def gen2() -> AsyncIterator[Union[Doc, Dict[str, Any]]]:
        yield {"_op_type": "create", "_id": "45", "_source": Doc(name="Sarah", age=45)}

    # a "create" action with an existing id should fail
    with raises(BulkIndexError):
        await Doc.bulk(gen2(), refresh=True)

    async def gen3() -> AsyncIterator[Union[Doc, Dict[str, Any]]]:
        yield Doc(_id="45", name="Sarah", age=45, languages=["es"])
        yield {"_op_type": "delete", "_id": docs[1].meta.id}

    await Doc.bulk(gen3(), refresh=True)
    with raises(NotFoundError):
        await Doc.get(docs[1].meta.id)
    doc = await Doc.get("45")
    assert doc is not None
    assert (doc).to_dict() == {
        "name": "Sarah",
        "age": 45,
        "languages": ["es"],
    }


@pytest.mark.asyncio
async def test_legacy_dense_vector(
    async_client: AsyncElasticsearch, es_version: Tuple[int, ...]
) -> None:
    if es_version >= (8, 16):
        pytest.skip("this test is a legacy version for Elasticsearch 8.15 or older")

    class Doc(AsyncDocument):
        float_vector: List[float] = mapped_field(DenseVector(dims=3))

        class Index:
            name = "vectors"

    await Doc._index.delete(ignore_unavailable=True)
    await Doc.init()

    doc = Doc(float_vector=[1.0, 1.2, 2.3])
    await doc.save(refresh=True)

    docs = await Doc.search().execute()
    assert len(docs) == 1
    assert docs[0].float_vector == doc.float_vector


@pytest.mark.asyncio
async def test_dense_vector(
    async_client: AsyncElasticsearch, es_version: Tuple[int, ...]
) -> None:
    if es_version < (8, 16):
        pytest.skip("this test requires Elasticsearch 8.16 or newer")

    class Doc(AsyncDocument):
        float_vector: List[float] = mapped_field(DenseVector())
        byte_vector: List[int] = mapped_field(DenseVector(element_type="byte"))
        bit_vector: str = mapped_field(DenseVector(element_type="bit"))

        class Index:
            name = "vectors"

    await Doc._index.delete(ignore_unavailable=True)
    await Doc.init()

    doc = Doc(
        float_vector=[1.0, 1.2, 2.3], byte_vector=[12, 23, 34, 45], bit_vector="12abf0"
    )
    await doc.save(refresh=True)

    docs = await Doc.search().execute()
    assert len(docs) == 1
    assert docs[0].float_vector == doc.float_vector
    assert docs[0].byte_vector == doc.byte_vector
    assert docs[0].bit_vector == doc.bit_vector
