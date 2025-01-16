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

import logging
import re
from functools import partial
from typing import Any, List, Optional, Union

import pytest

from elasticsearch import Elasticsearch, NotFoundError
from elasticsearch.helpers import BulkIndexError
from elasticsearch.helpers.vectorstore import (
    BM25Strategy,
    DenseVectorScriptScoreStrategy,
    DenseVectorStrategy,
    DistanceMetric,
    SparseVectorStrategy,
    VectorStore,
)
from elasticsearch.helpers.vectorstore._sync._utils import model_is_deployed
from test_elasticsearch.utils import es_version

from . import ConsistentFakeEmbeddings, FakeEmbeddings

logging.basicConfig(level=logging.DEBUG)

"""
docker-compose up elasticsearch

By default runs against local docker instance of Elasticsearch.
To run against Elastic Cloud, set the following environment variables:
- ES_CLOUD_ID
- ES_API_KEY

Some of the tests require the following models to be deployed in the ML Node:
- elser (can be downloaded and deployed through Kibana and trained models UI)
- sentence-transformers__all-minilm-l6-v2 (can be deployed through the API,
  loaded via eland)

These tests that require the models to be deployed are skipped by default.
Enable them by adding the model name to the modelsDeployed list below.
"""

ELSER_MODEL_ID = ".elser_model_2"
TRANSFORMER_MODEL_ID = "sentence-transformers__all-minilm-l6-v2"


class TestVectorStore:
    def test_search_without_metadata(
        self, sync_client: Elasticsearch, index: str
    ) -> None:
        """Test end to end construction and search without metadata."""

        def assert_query(query_body: dict, query: Optional[str]) -> dict:
            assert query_body == {
                "knn": {
                    "field": "vector_field",
                    "filter": [],
                    "k": 1,
                    "num_candidates": 50,
                    "query_vector": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0],
                }
            }
            return query_body

        store = VectorStore(
            index=index,
            retrieval_strategy=DenseVectorStrategy(),
            embedding_service=ConsistentFakeEmbeddings(),
            client=sync_client,
        )

        texts = ["foo", "bar", "baz"]
        store.add_texts(texts)

        output = store.search(query="foo", k=1, custom_query=assert_query)
        assert [doc["_source"]["text_field"] for doc in output] == ["foo"]

    def test_search_without_metadata_async(
        self, sync_client: Elasticsearch, index: str
    ) -> None:
        """Test end to end construction and search without metadata."""
        store = VectorStore(
            index=index,
            retrieval_strategy=DenseVectorStrategy(),
            embedding_service=ConsistentFakeEmbeddings(),
            client=sync_client,
        )

        texts = ["foo", "bar", "baz"]
        store.add_texts(texts)

        output = store.search(query="foo", k=1)
        assert [doc["_source"]["text_field"] for doc in output] == ["foo"]

    def test_add_vectors(self, sync_client: Elasticsearch, index: str) -> None:
        """
        Test adding pre-built embeddings instead of using inference for the texts.
        This allows you to separate the embeddings text and the page_content
        for better proximity between user's question and embedded text.
        For example, your embedding text can be a question, whereas page_content
        is the answer.
        """
        embeddings = ConsistentFakeEmbeddings()
        texts = ["foo1", "foo2", "foo3"]
        metadatas = [{"page": i} for i in range(len(texts))]

        embedding_vectors = embeddings.embed_documents(texts)

        store = VectorStore(
            index=index,
            retrieval_strategy=DenseVectorStrategy(),
            embedding_service=embeddings,
            client=sync_client,
        )

        store.add_texts(texts=texts, vectors=embedding_vectors, metadatas=metadatas)
        output = store.search(query="foo1", k=1)
        assert [doc["_source"]["text_field"] for doc in output] == ["foo1"]
        assert [doc["_source"]["metadata"]["page"] for doc in output] == [0]

    def test_search_with_metadata(self, sync_client: Elasticsearch, index: str) -> None:
        """Test end to end construction and search with metadata."""
        store = VectorStore(
            index=index,
            retrieval_strategy=DenseVectorStrategy(),
            embedding_service=ConsistentFakeEmbeddings(),
            client=sync_client,
        )

        texts = ["foo", "bar", "baz"]
        metadatas = [{"page": i} for i in range(len(texts))]
        store.add_texts(texts=texts, metadatas=metadatas)

        output = store.search(query="foo", k=1)
        assert [doc["_source"]["text_field"] for doc in output] == ["foo"]
        assert [doc["_source"]["metadata"]["page"] for doc in output] == [0]

        output = store.search(query="bar", k=1)
        assert [doc["_source"]["text_field"] for doc in output] == ["bar"]
        assert [doc["_source"]["metadata"]["page"] for doc in output] == [1]

    def test_search_with_filter(self, sync_client: Elasticsearch, index: str) -> None:
        """Test end to end construction and search with metadata."""
        store = VectorStore(
            index=index,
            retrieval_strategy=DenseVectorStrategy(),
            embedding_service=FakeEmbeddings(),
            client=sync_client,
        )

        texts = ["foo", "foo", "foo"]
        metadatas = [{"page": i} for i in range(len(texts))]
        store.add_texts(texts=texts, metadatas=metadatas)

        def assert_query(query_body: dict, query: Optional[str]) -> dict:
            assert query_body == {
                "knn": {
                    "field": "vector_field",
                    "filter": [{"term": {"metadata.page": "1"}}],
                    "k": 3,
                    "num_candidates": 50,
                    "query_vector": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0],
                }
            }
            return query_body

        output = store.search(
            query="foo",
            k=3,
            filter=[{"term": {"metadata.page": "1"}}],
            custom_query=assert_query,
        )
        assert [doc["_source"]["text_field"] for doc in output] == ["foo"]
        assert [doc["_source"]["metadata"]["page"] for doc in output] == [1]

    def test_search_script_score(self, sync_client: Elasticsearch, index: str) -> None:
        """Test end to end construction and search with metadata."""
        store = VectorStore(
            index=index,
            retrieval_strategy=DenseVectorScriptScoreStrategy(),
            embedding_service=FakeEmbeddings(),
            client=sync_client,
        )

        texts = ["foo", "bar", "baz"]
        store.add_texts(texts)

        expected_query = {
            "query": {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'vector_field') + 1.0",  # noqa: E501
                        "params": {
                            "query_vector": [
                                1.0,
                                1.0,
                                1.0,
                                1.0,
                                1.0,
                                1.0,
                                1.0,
                                1.0,
                                1.0,
                                0.0,
                            ]
                        },
                    },
                }
            }
        }

        def assert_query(query_body: dict, query: Optional[str]) -> dict:
            assert query_body == expected_query
            return query_body

        output = store.search(query="foo", k=1, custom_query=assert_query)
        assert [doc["_source"]["text_field"] for doc in output] == ["foo"]

    def test_search_script_score_with_filter(
        self, sync_client: Elasticsearch, index: str
    ) -> None:
        """Test end to end construction and search with metadata."""
        store = VectorStore(
            index=index,
            retrieval_strategy=DenseVectorScriptScoreStrategy(),
            embedding_service=FakeEmbeddings(),
            client=sync_client,
        )

        texts = ["foo", "bar", "baz"]
        metadatas = [{"page": i} for i in range(len(texts))]
        store.add_texts(texts=texts, metadatas=metadatas)

        def assert_query(query_body: dict, query: Optional[str]) -> dict:
            expected_query = {
                "query": {
                    "script_score": {
                        "query": {"bool": {"filter": [{"term": {"metadata.page": 0}}]}},
                        "script": {
                            "source": "cosineSimilarity(params.query_vector, 'vector_field') + 1.0",  # noqa: E501
                            "params": {
                                "query_vector": [
                                    1.0,
                                    1.0,
                                    1.0,
                                    1.0,
                                    1.0,
                                    1.0,
                                    1.0,
                                    1.0,
                                    1.0,
                                    0.0,
                                ]
                            },
                        },
                    }
                }
            }
            assert query_body == expected_query
            return query_body

        output = store.search(
            query="foo",
            k=1,
            custom_query=assert_query,
            filter=[{"term": {"metadata.page": 0}}],
        )
        assert [doc["_source"]["text_field"] for doc in output] == ["foo"]
        assert [doc["_source"]["metadata"]["page"] for doc in output] == [0]

    def test_search_script_score_distance_dot_product(
        self, sync_client: Elasticsearch, index: str
    ) -> None:
        """Test end to end construction and search with metadata."""
        store = VectorStore(
            index=index,
            retrieval_strategy=DenseVectorScriptScoreStrategy(
                distance=DistanceMetric.DOT_PRODUCT,
            ),
            embedding_service=FakeEmbeddings(),
            client=sync_client,
        )

        texts = ["foo", "bar", "baz"]
        store.add_texts(texts)

        def assert_query(query_body: dict, query: Optional[str]) -> dict:
            assert query_body == {
                "query": {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": """
            double value = dotProduct(params.query_vector, 'vector_field');
            return sigmoid(1, Math.E, -value);
            """,
                            "params": {
                                "query_vector": [
                                    1.0,
                                    1.0,
                                    1.0,
                                    1.0,
                                    1.0,
                                    1.0,
                                    1.0,
                                    1.0,
                                    1.0,
                                    0.0,
                                ]
                            },
                        },
                    }
                }
            }
            return query_body

        output = store.search(query="foo", k=1, custom_query=assert_query)
        assert [doc["_source"]["text_field"] for doc in output] == ["foo"]

    def test_search_knn_with_hybrid_search(
        self, sync_client: Elasticsearch, index: str
    ) -> None:
        """Test end to end construction and search with metadata."""
        if es_version(sync_client) < (8, 14):
            pytest.skip("This test requires Elasticsearch 8.14 or newer")

        store = VectorStore(
            index=index,
            retrieval_strategy=DenseVectorStrategy(hybrid=True),
            embedding_service=FakeEmbeddings(),
            client=sync_client,
        )

        texts = ["foo", "bar", "baz"]
        store.add_texts(texts)

        def assert_query(query_body: dict, query: Optional[str]) -> dict:
            assert query_body == {
                "retriever": {
                    "rrf": {
                        "retrievers": [
                            {
                                "standard": {
                                    "query": {
                                        "bool": {
                                            "filter": [],
                                            "must": [
                                                {
                                                    "match": {
                                                        "text_field": {"query": "foo"}
                                                    }
                                                }
                                            ],
                                        }
                                    },
                                },
                            },
                            {
                                "knn": {
                                    "field": "vector_field",
                                    "filter": [],
                                    "k": 1,
                                    "num_candidates": 50,
                                    "query_vector": [
                                        1.0,
                                        1.0,
                                        1.0,
                                        1.0,
                                        1.0,
                                        1.0,
                                        1.0,
                                        1.0,
                                        1.0,
                                        0.0,
                                    ],
                                },
                            },
                        ],
                    }
                }
            }
            return query_body

        output = store.search(query="foo", k=1, custom_query=assert_query)
        assert [doc["_source"]["text_field"] for doc in output] == ["foo"]

    def test_search_knn_with_hybrid_search_rrf(
        self, sync_client: Elasticsearch, index: str
    ) -> None:
        """Test end to end construction and rrf hybrid search with metadata."""
        if es_version(sync_client) < (8, 14):
            pytest.skip("This test requires Elasticsearch 8.14 or newer")

        texts = ["foo", "bar", "baz"]

        def assert_query(
            query_body: dict,
            query: Optional[str],
            expected_rrf: Union[dict, bool],
        ) -> dict:
            standard_query = {
                "query": {
                    "bool": {
                        "filter": [],
                        "must": [{"match": {"text_field": {"query": "foo"}}}],
                    }
                }
            }
            knn_query = {
                "field": "vector_field",
                "filter": [],
                "k": 3,
                "num_candidates": 50,
                "query_vector": [
                    1.0,
                    1.0,
                    1.0,
                    1.0,
                    1.0,
                    1.0,
                    1.0,
                    1.0,
                    1.0,
                    0.0,
                ],
            }

            if expected_rrf is not False:
                cmp_query_body = {
                    "retriever": {
                        "rrf": {
                            "retrievers": [
                                {"standard": standard_query},
                                {"knn": knn_query},
                            ],
                        }
                    }
                }
                if isinstance(expected_rrf, dict):
                    cmp_query_body["retriever"]["rrf"].update(expected_rrf)
            else:
                cmp_query_body = {
                    "knn": knn_query,
                    **standard_query,
                }

            assert query_body == cmp_query_body

            return query_body

        # 1. check query_body is okay
        if es_version(sync_client) >= (8, 14):
            rrf_test_cases: List[Union[dict, bool]] = [
                True,
                False,
                {"rank_constant": 1, "rank_window_size": 5},
            ]
        else:
            # for 8.13.x and older there is no retriever query, so we can only
            # run hybrid searches with rrf=False
            rrf_test_cases: List[Union[dict, bool]] = [False]
        for rrf_test_case in rrf_test_cases:
            store = VectorStore(
                index=index,
                retrieval_strategy=DenseVectorStrategy(hybrid=True, rrf=rrf_test_case),
                embedding_service=FakeEmbeddings(),
                client=sync_client,
            )
            store.add_texts(texts)

            # without fetch_k parameter
            output = store.search(
                query="foo",
                k=3,
                custom_query=partial(assert_query, expected_rrf=rrf_test_case),
            )

        # 2. check query result is okay
        es_output = store.client.search(
            index=index,
            retriever={
                "rrf": {
                    "retrievers": [
                        {
                            "knn": {
                                "field": "vector_field",
                                "filter": [],
                                "k": 3,
                                "num_candidates": 50,
                                "query_vector": [
                                    1.0,
                                    1.0,
                                    1.0,
                                    1.0,
                                    1.0,
                                    1.0,
                                    1.0,
                                    1.0,
                                    1.0,
                                    0.0,
                                ],
                            },
                        },
                        {
                            "standard": {
                                "query": {
                                    "bool": {
                                        "filter": [],
                                        "must": [
                                            {"match": {"text_field": {"query": "foo"}}}
                                        ],
                                    }
                                },
                            },
                        },
                    ],
                    "rank_constant": 1,
                    "rank_window_size": 5,
                }
            },
            size=3,
        )

        assert [o["_source"]["text_field"] for o in output] == [
            e["_source"]["text_field"] for e in es_output["hits"]["hits"]
        ]

        # 3. check rrf default option is okay
        store = VectorStore(
            index=f"{index}_default",
            retrieval_strategy=DenseVectorStrategy(hybrid=True),
            embedding_service=FakeEmbeddings(),
            client=sync_client,
        )
        store.add_texts(texts)

        # with fetch_k parameter
        output = store.search(
            query="foo",
            k=3,
            num_candidates=50,
            custom_query=partial(assert_query, expected_rrf={}),
        )

    def test_search_knn_with_custom_query_fn(
        self, sync_client: Elasticsearch, index: str
    ) -> None:
        """test that custom query function is called
        with the query string and query body"""
        store = VectorStore(
            index=index,
            retrieval_strategy=DenseVectorStrategy(),
            embedding_service=FakeEmbeddings(),
            client=sync_client,
        )

        def my_custom_query(query_body: dict, query: Optional[str]) -> dict:
            assert query == "foo"
            assert query_body == {
                "knn": {
                    "field": "vector_field",
                    "filter": [],
                    "k": 1,
                    "num_candidates": 50,
                    "query_vector": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0],
                }
            }
            return {"query": {"match": {"text_field": {"query": "bar"}}}}

        """Test end to end construction and search with metadata."""
        texts = ["foo", "bar", "baz"]
        store.add_texts(texts)

        output = store.search(query="foo", k=1, custom_query=my_custom_query)
        assert [doc["_source"]["text_field"] for doc in output] == ["bar"]

    def test_search_with_knn_infer_instack(
        self, sync_client: Elasticsearch, index: str
    ) -> None:
        """test end to end with knn retrieval strategy and inference in-stack"""

        if not model_is_deployed(sync_client, TRANSFORMER_MODEL_ID):
            pytest.skip(
                f"{TRANSFORMER_MODEL_ID} model not deployed in ML Node skipping test"
            )

        text_field = "text_field"

        store = VectorStore(
            index=index,
            retrieval_strategy=DenseVectorStrategy(model_id=TRANSFORMER_MODEL_ID),
            client=sync_client,
        )

        # setting up the pipeline for inference
        store.client.ingest.put_pipeline(
            id="test_pipeline",
            processors=[
                {
                    "inference": {
                        "model_id": TRANSFORMER_MODEL_ID,
                        "field_map": {"query_field": text_field},
                        "target_field": "vector_query_field",
                    }
                }
            ],
        )

        # creating a new index with the pipeline,
        # not relying on langchain to create the index
        store.client.indices.create(
            index=index,
            mappings={
                "properties": {
                    text_field: {"type": "text_field"},
                    "vector_query_field": {
                        "properties": {
                            "predicted_value": {
                                "type": "dense_vector",
                                "dims": 384,
                                "index": True,
                                "similarity": "l2_norm",
                            }
                        }
                    },
                }
            },
            settings={"index": {"default_pipeline": "test_pipeline"}},
        )

        # adding documents to the index
        texts = ["foo", "bar", "baz"]

        for i, text in enumerate(texts):
            store.client.create(
                index=index,
                id=str(i),
                document={text_field: text, "metadata": {}},
            )

        store.client.indices.refresh(index=index)

        def assert_query(query_body: dict, query: Optional[str]) -> dict:
            assert query_body == {
                "knn": {
                    "filter": [],
                    "field": "vector_query_field.predicted_value",
                    "k": 1,
                    "num_candidates": 50,
                    "query_vector_builder": {
                        "text_embedding": {
                            "model_id": TRANSFORMER_MODEL_ID,
                            "model_text": "foo",
                        }
                    },
                }
            }
            return query_body

        output = store.search(query="foo", k=1, custom_query=assert_query)
        assert [doc["_source"]["text_field"] for doc in output] == ["foo"]

        output = store.search(query="bar", k=1)
        assert [doc["_source"]["text_field"] for doc in output] == ["bar"]

    def test_search_with_sparse_infer_instack(
        self, sync_client: Elasticsearch, index: str
    ) -> None:
        """test end to end with sparse retrieval strategy and inference in-stack"""

        if not model_is_deployed(sync_client, ELSER_MODEL_ID):
            reason = f"{ELSER_MODEL_ID} model not deployed in ML Node, skipping test"
            pytest.skip(reason)

        store = VectorStore(
            index=index,
            retrieval_strategy=SparseVectorStrategy(model_id=ELSER_MODEL_ID),
            client=sync_client,
        )

        texts = ["foo", "bar", "baz"]
        store.add_texts(texts)

        output = store.search(query="foo", k=1)
        assert [doc["_source"]["text_field"] for doc in output] == ["foo"]

    def test_deployed_model_check_fails_semantic(
        self, sync_client: Elasticsearch, index: str
    ) -> None:
        """test that exceptions are raised if a specified model is not deployed"""
        with pytest.raises(NotFoundError):
            store = VectorStore(
                index=index,
                retrieval_strategy=DenseVectorStrategy(
                    model_id="non-existing model ID"
                ),
                client=sync_client,
            )
            store.add_texts(["foo", "bar", "baz"])

    def test_search_bm25(self, sync_client: Elasticsearch, index: str) -> None:
        """Test end to end using the BM25Strategy retrieval strategy."""
        store = VectorStore(
            index=index,
            retrieval_strategy=BM25Strategy(),
            client=sync_client,
        )

        texts = ["foo", "bar", "baz"]
        store.add_texts(texts)

        def assert_query(query_body: dict, query: Optional[str]) -> dict:
            assert query_body == {
                "query": {
                    "bool": {
                        "must": [{"match": {"text_field": {"query": "foo"}}}],
                        "filter": [],
                    }
                }
            }
            return query_body

        output = store.search(query="foo", k=1, custom_query=assert_query)
        assert [doc["_source"]["text_field"] for doc in output] == ["foo"]

    def test_search_bm25_with_filter(
        self, sync_client: Elasticsearch, index: str
    ) -> None:
        """Test end to using the BM25Strategy retrieval strategy with metadata."""
        store = VectorStore(
            index=index,
            retrieval_strategy=BM25Strategy(),
            client=sync_client,
        )

        texts = ["foo", "foo", "foo"]
        metadatas = [{"page": i} for i in range(len(texts))]
        store.add_texts(texts=texts, metadatas=metadatas)

        def assert_query(query_body: dict, query: Optional[str]) -> dict:
            assert query_body == {
                "query": {
                    "bool": {
                        "must": [{"match": {"text_field": {"query": "foo"}}}],
                        "filter": [{"term": {"metadata.page": 1}}],
                    }
                }
            }
            return query_body

        output = store.search(
            query="foo",
            k=3,
            custom_query=assert_query,
            filter=[{"term": {"metadata.page": 1}}],
        )
        assert [doc["_source"]["text_field"] for doc in output] == ["foo"]
        assert [doc["_source"]["metadata"]["page"] for doc in output] == [1]

    def test_delete(self, sync_client: Elasticsearch, index: str) -> None:
        """Test delete methods from vector store."""
        store = VectorStore(
            index=index,
            retrieval_strategy=DenseVectorStrategy(),
            embedding_service=FakeEmbeddings(),
            client=sync_client,
        )

        texts = ["foo", "bar", "baz", "gni"]
        metadatas = [{"page": i} for i in range(len(texts))]
        ids = store.add_texts(texts=texts, metadatas=metadatas)

        output = store.search(query="foo", k=10)
        assert len(output) == 4

        store.delete(ids=ids[1:3])
        output = store.search(query="foo", k=10)
        assert len(output) == 2

        store.delete(ids=["not-existing"])
        output = store.search(query="foo", k=10)
        assert len(output) == 2

        store.delete(ids=[ids[0]])
        output = store.search(query="foo", k=10)
        assert len(output) == 1

        store.delete(ids=[ids[3]])
        output = store.search(query="gni", k=10)
        assert len(output) == 0

    def test_indexing_exception_error(
        self,
        sync_client: Elasticsearch,
        index: str,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test bulk exception logging is giving better hints."""
        store = VectorStore(
            index=index,
            retrieval_strategy=BM25Strategy(),
            client=sync_client,
        )

        store.client.indices.create(
            index=index,
            mappings={"properties": {}},
            settings={"index": {"default_pipeline": "not-existing-pipeline"}},
        )

        texts = ["foo"]

        with pytest.raises(BulkIndexError):
            store.add_texts(texts)

        error_reason = "pipeline with id [not-existing-pipeline] does not exist"
        log_message = f"First error reason: {error_reason}"

        assert log_message in caplog.text

    def test_user_agent_default(
        self, sync_client_request_saving: Elasticsearch, index: str
    ) -> None:
        """Test to make sure the user-agent is set correctly."""
        store = VectorStore(
            index=index,
            retrieval_strategy=BM25Strategy(),
            client=sync_client_request_saving,
        )
        expected_pattern = r"^elasticsearch-py-vs/\d+\.\d+\.\d+$"

        got_agent = store.client._headers["User-Agent"]
        assert (
            re.match(expected_pattern, got_agent) is not None
        ), f"The user agent '{got_agent}' does not match the expected pattern."

        texts = ["foo", "bob", "baz"]
        store.add_texts(texts)

        for request in store.client.transport.requests:  # type: ignore
            agent = request["headers"]["User-Agent"]
            assert (
                re.match(expected_pattern, agent) is not None
            ), f"The user agent '{agent}' does not match the expected pattern."

    def test_user_agent_custom(
        self, sync_client_request_saving: Elasticsearch, index: str
    ) -> None:
        """Test to make sure the user-agent is set correctly."""
        user_agent = "this is THE user_agent!"

        store = VectorStore(
            user_agent=user_agent,
            index=index,
            retrieval_strategy=BM25Strategy(),
            client=sync_client_request_saving,
        )

        assert store.client._headers["User-Agent"] == user_agent

        texts = ["foo", "bob", "baz"]
        store.add_texts(texts)

        for request in store.client.transport.requests:  # type: ignore
            assert request["headers"]["User-Agent"] == user_agent

    def test_bulk_args(self, sync_client_request_saving: Any, index: str) -> None:
        """Test to make sure the bulk arguments work as expected."""
        store = VectorStore(
            index=index,
            retrieval_strategy=BM25Strategy(),
            client=sync_client_request_saving,
        )

        texts = ["foo", "bob", "baz"]
        store.add_texts(texts, bulk_kwargs={"chunk_size": 1})

        # 1 for index exist, 1 for index create, 3 to index docs
        assert len(store.client.transport.requests) == 5  # type: ignore

    def test_max_marginal_relevance_search_errors(
        self, sync_client: Elasticsearch, index: str
    ) -> None:
        """Test max marginal relevance search error conditions."""
        texts = ["foo", "bar", "baz"]
        vector_field = "vector_field"
        embedding_service = ConsistentFakeEmbeddings()
        store = VectorStore(
            index=index,
            retrieval_strategy=DenseVectorScriptScoreStrategy(),
            embedding_service=embedding_service,
            client=sync_client,
        )
        store.add_texts(texts)

        # search without query embeddings vector or query
        with pytest.raises(
            ValueError, match="specify either query or query_embedding to search"
        ):
            store.max_marginal_relevance_search(
                vector_field=vector_field,
                k=3,
                num_candidates=3,
            )

        # search without service
        no_service_store = VectorStore(
            index=index,
            retrieval_strategy=DenseVectorScriptScoreStrategy(),
            client=sync_client,
        )
        with pytest.raises(
            ValueError, match="specify embedding_service to search with query"
        ):
            no_service_store.max_marginal_relevance_search(
                query=texts[0],
                vector_field=vector_field,
                k=3,
                num_candidates=3,
            )

    def test_max_marginal_relevance_search(
        self, sync_client: Elasticsearch, index: str
    ) -> None:
        """Test max marginal relevance search."""
        texts = ["foo", "bar", "baz"]
        vector_field = "vector_field"
        text_field = "text_field"
        query_embedding = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0]
        embedding_service = ConsistentFakeEmbeddings()
        store = VectorStore(
            index=index,
            retrieval_strategy=DenseVectorScriptScoreStrategy(),
            embedding_service=embedding_service,
            vector_field=vector_field,
            text_field=text_field,
            client=sync_client,
        )
        store.add_texts(texts)

        # search with query
        mmr_output = store.max_marginal_relevance_search(
            query=texts[0],
            vector_field=vector_field,
            k=3,
            num_candidates=3,
        )
        sim_output = store.search(query=texts[0], k=3)
        assert mmr_output == sim_output

        # search with query embeddings
        mmr_output = store.max_marginal_relevance_search(
            query_embedding=query_embedding,
            vector_field=vector_field,
            k=3,
            num_candidates=3,
        )
        sim_output = store.search(query_vector=query_embedding, k=3)
        assert mmr_output == sim_output

        mmr_output = store.max_marginal_relevance_search(
            query=texts[0],
            vector_field=vector_field,
            k=2,
            num_candidates=3,
        )
        assert len(mmr_output) == 2
        assert mmr_output[0]["_source"][text_field] == texts[0]
        assert mmr_output[1]["_source"][text_field] == texts[1]

        mmr_output = store.max_marginal_relevance_search(
            query=texts[0],
            vector_field=vector_field,
            k=2,
            num_candidates=3,
            lambda_mult=0.1,  # more diversity
        )
        assert len(mmr_output) == 2
        assert mmr_output[0]["_source"][text_field] == texts[0]
        assert mmr_output[1]["_source"][text_field] == texts[2]

        # if fetch_k < k, then the output will be less than k
        mmr_output = store.max_marginal_relevance_search(
            query=texts[0],
            vector_field=vector_field,
            k=3,
            num_candidates=2,
        )
        assert len(mmr_output) == 2

    def test_metadata_mapping(self, sync_client: Elasticsearch, index: str) -> None:
        """Test that the metadata mapping is applied."""
        test_mappings = {
            "my_field": {"type": "keyword"},
            "another_field": {"type": "text"},
        }
        store = VectorStore(
            index=index,
            retrieval_strategy=DenseVectorStrategy(distance=DistanceMetric.COSINE),
            embedding_service=FakeEmbeddings(),
            num_dimensions=10,
            client=sync_client,
            metadata_mappings=test_mappings,
        )

        texts = ["foo", "foo", "foo"]
        metadatas = [{"my_field": str(i)} for i in range(len(texts))]
        store.add_texts(texts=texts, metadatas=metadatas)

        mapping_response = sync_client.indices.get_mapping(index=index)
        mapping_properties = mapping_response[index]["mappings"]["properties"]
        assert mapping_properties["vector_field"] == {
            "type": "dense_vector",
            "dims": 10,
            "index": True,
            "index_options": {
                "ef_construction": 100,
                "m": 16,
                "type": "int8_hnsw",
            },
            "similarity": "cosine",
        }

        assert "metadata" in mapping_properties
        for key, val in test_mappings.items():
            assert mapping_properties["metadata"]["properties"][key] == val

    def test_custom_index_settings(
        self, sync_client: Elasticsearch, index: str
    ) -> None:
        """Test that the custom index settings are applied."""
        test_settings = {
            "analysis": {
                "tokenizer": {
                    "custom_tokenizer": {"type": "pattern", "pattern": "[,;\\s]+"}
                },
                "analyzer": {
                    "custom_analyzer": {
                        "type": "custom",
                        "tokenizer": "custom_tokenizer",
                    }
                },
            }
        }

        test_mappings = {
            "my_field": {"type": "keyword"},
            "another_field": {"type": "text", "analyzer": "custom_analyzer"},
        }

        store = VectorStore(
            index=index,
            retrieval_strategy=DenseVectorStrategy(distance=DistanceMetric.COSINE),
            embedding_service=FakeEmbeddings(),
            num_dimensions=10,
            client=sync_client,
            metadata_mappings=test_mappings,
            custom_index_settings=test_settings,
        )

        sample_texts = [
            "Sample text one, with some keywords.",
            "Another; sample, text with; different keywords.",
            "Third example text, with more keywords.",
        ]
        store.add_texts(texts=sample_texts)

        # Fetch the actual index settings from Elasticsearch
        actual_settings = sync_client.indices.get_settings(index=index)

        # Assert that the custom settings were applied correctly
        custom_settings_applied = actual_settings[index]["settings"]["index"][
            "analysis"
        ]
        assert (
            custom_settings_applied == test_settings["analysis"]
        ), f"Expected custom index settings {test_settings} but got {custom_settings_applied}"

    def test_custom_index_settings_with_collision(
        self, sync_client: Elasticsearch, index: str
    ) -> None:
        """Test that custom index settings that collide cause an error."""
        test_settings = {
            "default_pipeline": "my_pipeline",
            "analysis": {
                "tokenizer": {
                    "custom_tokenizer": {"type": "pattern", "pattern": "[,;\\s]+"}
                },
                "analyzer": {
                    "custom_analyzer": {
                        "type": "custom",
                        "tokenizer": "custom_tokenizer",
                    }
                },
            },
        }

        test_mappings = {
            "my_field": {"type": "keyword"},
            "another_field": {"type": "text", "analyzer": "custom_analyzer"},
        }

        store = VectorStore(
            index=index,
            retrieval_strategy=SparseVectorStrategy(),
            client=sync_client,
            metadata_mappings=test_mappings,
            custom_index_settings=test_settings,
        )
        with pytest.raises(ValueError, match="Conflicting settings"):
            store.add_texts(texts=["some text"])
