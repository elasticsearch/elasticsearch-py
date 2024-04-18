from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union, cast

from elasticsearch import Elasticsearch

from elasticsearch.vectorstore._sync._utils import model_must_be_deployed
from elasticsearch.vectorstore._sync.embedding_service import EmbeddingService


class DistanceMetric(str, Enum):
    """Enumerator of all Elasticsearch dense vector distance metrics."""

    COSINE = "COSINE"
    DOT_PRODUCT = "DOT_PRODUCT"
    EUCLIDEAN_DISTANCE = "EUCLIDEAN_DISTANCE"
    MAX_INNER_PRODUCT = "MAX_INNER_PRODUCT"


class RetrievalStrategy(ABC):
    @abstractmethod
    def es_query(
        self,
        query: Optional[str],
        k: int,
        num_candidates: int,
        filter: List[dict] = [],
        query_vector: Optional[List[float]] = None,
    ) -> Dict:
        """
        Returns the Elasticsearch query body for the given parameters.
        The store will execute the query.

        Args:
            query: The text query. Can be None if query_vector is given.
            k: The total number of results to retrieve.
            num_candidates: The number of results to fetch initially in knn search.
            filter: List of filter clauses to apply to the query.
            query_vector: The query vector. Can be None if a query string is given.

        Returns:
            Dict: The Elasticsearch query body.
        """

    @abstractmethod
    def create_index(
        self,
        client: Elasticsearch,
        index_name: str,
        metadata_mapping: Optional[dict[str, str]],
    ) -> None:
        """
        Create the required index and do necessary preliminary work, like
        creating inference pipelines or checking if a required model was deployed.

        Args:
            client: Elasticsearch client connection.
            index_name: The name of the Elasticsearch index to create.
            metadata_mapping: Flat dictionary with field and field type pairs that
                describe the schema of the metadata.
        """

    def embed_for_indexing(self, text: str) -> Dict[str, Any]:
        """
        If this strategy creates vector embeddings in Python (not in Elasticsearch),
        this method is used to apply the inference.
        The output is a dictionary with the vector field and the vector embedding.
        It is merged in the ElasticserachStore with the rest of the document (text data,
        metadata) before indexing.

        Args:
            text: Text input that can be used as input for inference.

        Returns:
            Dict: field and value pairs that extend the document to be indexed.
        """
        return {}


# TODO test when repsective image is released
class Semantic(RetrievalStrategy):
    """Dense or sparse retrieval with in-stack inference using semantic_text fields."""

    def __init__(
        self,
        model_id: str,
        text_field: str = "text_field",
        inference_field: str = "text_semantic",
    ):
        self.model_id = model_id
        self.text_field = text_field
        self.inference_field = inference_field

    def es_query(
        self,
        query: Optional[str],
        k: int,
        num_candidates: int,
        filter: List[dict] = [],
        query_vector: Optional[List[float]] = None,
    ) -> Dict:
        if query_vector:
            raise ValueError(
                "Cannot do sparse retrieval with a query_vector. "
                "Inference is currently always applied in-stack."
            )

        return {
            "query": {
                "semantic": {
                    self.text_field: query,
                },
            },
            "filter": filter,
        }

    def create_index(
        self,
        client: Elasticsearch,
        index_name: str,
        metadata_mapping: Optional[dict[str, str]],
    ) -> None:
        if self.model_id:
            model_must_be_deployed(client, self.model_id)

        mappings: dict[str, Any] = {
            "properties": {
                self.inference_field: {
                    "type": "semantic_text",
                    "model_id": self.model_id,
                }
            }
        }
        if metadata_mapping:
            mappings["properties"]["metadata"] = {"properties": metadata_mapping}

        client.indices.create(index=index_name, mappings=mappings)


class SparseVector(RetrievalStrategy):
    """Sparse retrieval strategy using the `text_expansion` processor."""

    def __init__(
        self,
        model_id: str = ".elser_model_2",
        text_field: str = "text_field",
        vector_field: str = "vector_field",
    ):
        self.model_id = model_id
        self.text_field = text_field
        self.vector_field = vector_field
        self._tokens_field = "tokens"

    def es_query(
        self,
        query: Optional[str],
        k: int,
        num_candidates: int,
        filter: List[dict] = [],
        query_vector: Optional[List[float]] = None,
    ) -> Dict:
        if query_vector:
            raise ValueError(
                "Cannot do sparse retrieval with a query_vector. "
                "Inference is currently always applied in Elasticsearch."
            )
        if query is None:
            raise ValueError("please specify a query string")

        return {
            "query": {
                "bool": {
                    "must": [
                        {
                            "text_expansion": {
                                f"{self.vector_field}.{self._tokens_field}": {
                                    "model_id": self.model_id,
                                    "model_text": query,
                                }
                            }
                        }
                    ],
                    "filter": filter,
                }
            },
            "size": k,
        }

    def create_index(
        self,
        client: Elasticsearch,
        index_name: str,
        metadata_mapping: Optional[dict[str, str]],
    ) -> None:
        pipeline_name = f"{self.model_id}_sparse_embedding"

        if self.model_id:
            model_must_be_deployed(client, self.model_id)

            # Create a pipeline for the model
            client.ingest.put_pipeline(
                id=pipeline_name,
                description="Embedding pipeline for Python VectorStore",
                processors=[
                    {
                        "inference": {
                            "model_id": self.model_id,
                            "target_field": self.vector_field,
                            "field_map": {self.text_field: "text_field"},
                            "inference_config": {
                                "text_expansion": {"results_field": self._tokens_field}
                            },
                        }
                    }
                ],
            )

        mappings = {
            "properties": {
                self.vector_field: {
                    "properties": {self._tokens_field: {"type": "rank_features"}}
                }
            }
        }
        if metadata_mapping:
            mappings["properties"]["metadata"] = {"properties": metadata_mapping}
        settings = {"default_pipeline": pipeline_name}

        client.indices.create(
            index=index_name, mappings=mappings, settings=settings
        )

        return None


class DenseVector(RetrievalStrategy):
    """K-nearest-neighbors retrieval."""

    def __init__(
        self,
        knn_type: Literal["hnsw", "int8_hnsw", "flat", "int8_flat"] = "hnsw",
        vector_field: str = "vector_field",
        distance: DistanceMetric = DistanceMetric.COSINE,
        embedding_service: Optional[EmbeddingService] = None,
        model_id: Optional[str] = None,
        num_dimensions: Optional[int] = None,
        hybrid: bool = False,
        rrf: Union[bool, dict] = True,
        text_field: Optional[str] = "text_field",
    ):
        if embedding_service and model_id:
            raise ValueError("either specify embedding_service or model_id, not both")
        if model_id and not num_dimensions:
            raise ValueError(
                "if model_id is specified, num_dimensions must also be specified"
            )
        if hybrid and not text_field:
            raise ValueError(
                "to enable hybrid you have to specify a text_field (for BM25 matching)"
            )

        self.knn_type = knn_type
        self.vector_field = vector_field
        self.distance = distance
        self.embedding_service = embedding_service
        self.model_id = model_id
        self.num_dimensions = num_dimensions
        self.hybrid = hybrid
        self.rrf = rrf
        self.text_field = text_field

    def es_query(
        self,
        query: Optional[str],
        k: int,
        num_candidates: int,
        filter: List[dict] = [],
        query_vector: Optional[List[float]] = None,
    ) -> Dict:
        knn = {
            "filter": filter,
            "field": self.vector_field,
            "k": k,
            "num_candidates": num_candidates,
        }

        if query_vector:
            knn["query_vector"] = query_vector
        elif self.embedding_service:
            knn["query_vector"] = self.embedding_service.embed_query(
                cast(str, query)
            )
        else:
            # Inference in Elasticsearch. When initializing we make sure to always have
            # a model_id if don't have an embedding_service.
            knn["query_vector_builder"] = {
                "text_embedding": {
                    "model_id": self.model_id,
                    "model_text": query,
                }
            }

        if self.hybrid:
            return self._hybrid(query=cast(str, query), knn=knn, filter=filter)

        return {"knn": knn}

    def create_index(
        self,
        client: Elasticsearch,
        index_name: str,
        metadata_mapping: Optional[dict[str, str]],
    ) -> None:
        if self.embedding_service and not self.num_dimensions:
            self.num_dimensions = len(
                self.embedding_service.embed_query("get number of dimensions")
            )

        if self.model_id:
            model_must_be_deployed(client, self.model_id)

        if self.distance is DistanceMetric.COSINE:
            similarityAlgo = "cosine"
        elif self.distance is DistanceMetric.EUCLIDEAN_DISTANCE:
            similarityAlgo = "l2_norm"
        elif self.distance is DistanceMetric.DOT_PRODUCT:
            similarityAlgo = "dot_product"
        elif self.distance is DistanceMetric.MAX_INNER_PRODUCT:
            similarityAlgo = "max_inner_product"
        else:
            raise ValueError(f"Similarity {self.distance} not supported.")

        mappings: Dict[str, Any] = {
            "properties": {
                self.vector_field: {
                    "type": "dense_vector",
                    "dims": self.num_dimensions,
                    "index": True,
                    "similarity": similarityAlgo,
                },
            }
        }
        if metadata_mapping:
            mappings["properties"]["metadata"] = {"properties": metadata_mapping}

        r = client.indices.create(index=index_name, mappings=mappings)
        print(r)

    def embed_for_indexing(self, text: str) -> Dict[str, Any]:
        if self.embedding_service:
            vector = self.embedding_service.embed_query(text)
            return {self.vector_field: vector}
        return {}

    def _hybrid(self, query: str, knn: dict, filter: list):
        # Add a query to the knn query.
        # RRF is used to even the score from the knn query and text query
        # RRF has two optional parameters: {'rank_constant':int, 'window_size':int}
        # https://www.elastic.co/guide/en/elasticsearch/reference/current/rrf.html
        query_body = {
            "knn": knn,
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                self.text_field: {
                                    "query": query,
                                }
                            }
                        }
                    ],
                    "filter": filter,
                }
            },
        }

        if isinstance(self.rrf, dict):
            query_body["rank"] = {"rrf": self.rrf}
        elif isinstance(self.rrf, bool) and self.rrf is True:
            query_body["rank"] = {"rrf": {}}

        return query_body


class DenseVectorScriptScore(RetrievalStrategy):
    """Exact nearest neighbors retrieval using the `script_score` query."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_field: str = "vector_field",
        distance: DistanceMetric = DistanceMetric.COSINE,
        num_dimensions: Optional[int] = None,
    ) -> None:
        self.vector_field = vector_field
        self.distance = distance
        self.embedding_service = embedding_service
        self.num_dimensions = num_dimensions

    def es_query(
        self,
        query: Optional[str],
        k: int,
        num_candidates: int,
        filter: List[dict] = [],
        query_vector: Optional[List[float]] = None,
    ) -> Dict:
        if self.distance is DistanceMetric.COSINE:
            similarityAlgo = (
                f"cosineSimilarity(params.query_vector, '{self.vector_field}') + 1.0"
            )
        elif self.distance is DistanceMetric.EUCLIDEAN_DISTANCE:
            similarityAlgo = (
                f"1 / (1 + l2norm(params.query_vector, '{self.vector_field}'))"
            )
        elif self.distance is DistanceMetric.DOT_PRODUCT:
            similarityAlgo = f"""
            double value = dotProduct(params.query_vector, '{self.vector_field}');
            return sigmoid(1, Math.E, -value);
            """
        elif self.distance is DistanceMetric.MAX_INNER_PRODUCT:
            similarityAlgo = f"""
            double value = dotProduct(params.query_vector, '{self.vector_field}');
            if (dotProduct < 0) {{
                return 1 / (1 + -1 * dotProduct);
            }}
            return dotProduct + 1;
            """
        else:
            raise ValueError(f"Similarity {self.distance} not supported.")

        queryBool: Dict = {"match_all": {}}
        if filter:
            queryBool = {"bool": {"filter": filter}}

        if not query_vector:
            if not self.embedding_service:
                raise ValueError(
                    "if not embedding_service is given, you need to "
                    "procive a query_vector"
                )
            if not query:
                raise ValueError("either specify a query string or a query_vector")
            query_vector = self.embedding_service.embed_query(query)

        return {
            "query": {
                "script_score": {
                    "query": queryBool,
                    "script": {
                        "source": similarityAlgo,
                        "params": {"query_vector": query_vector},
                    },
                },
            }
        }

    def create_index(
        self,
        client: Elasticsearch,
        index_name: str,
        metadata_mapping: Optional[dict[str, str]],
    ) -> None:
        if not self.num_dimensions:
            self.num_dimensions = len(
                self.embedding_service.embed_query("get number of dimensions")
            )

        mappings = {
            "properties": {
                self.vector_field: {
                    "type": "dense_vector",
                    "dims": self.num_dimensions,
                    "index": False,
                }
            }
        }
        if metadata_mapping:
            mappings["properties"]["metadata"] = {"properties": metadata_mapping}

        client.indices.create(index=index_name, mappings=mappings)

        return None

    def embed_for_indexing(self, text: str) -> Dict[str, Any]:
        return {self.vector_field: self.embedding_service.embed_query(text)}


class BM25(RetrievalStrategy):
    def __init__(
        self,
        text_field: str = "text_field",
        k1: Optional[float] = None,
        b: Optional[float] = None,
    ):
        self.text_field = text_field
        self.k1 = k1
        self.b = b

    def es_query(
        self,
        query: Optional[str],
        k: int,
        num_candidates: int,
        filter: List[dict] = [],
        query_vector: Optional[List[float]] = None,
    ) -> Dict:
        return {
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                self.text_field: {
                                    "query": query,
                                }
                            },
                        },
                    ],
                    "filter": filter,
                },
            },
        }

    def create_index(
        self,
        client: Elasticsearch,
        index_name: str,
        metadata_mapping: Optional[dict[str, str]],
    ) -> None:
        similarity_name = "custom_bm25"

        mappings: Dict = {
            "properties": {
                self.text_field: {
                    "type": "text",
                    "similarity": similarity_name,
                },
            },
        }
        if metadata_mapping:
            mappings["properties"]["metadata"] = {"properties": metadata_mapping}

        bm25: Dict = {
            "type": "BM25",
        }
        if self.k1 is not None:
            bm25["k1"] = self.k1
        if self.b is not None:
            bm25["b"] = self.b
        settings = {
            "similarity": {
                similarity_name: bm25,
            }
        }

        client.indices.create(
            index=index_name, mappings=mappings, settings=settings
        )
