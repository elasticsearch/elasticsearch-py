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

from typing import Any, Dict

from elasticsearch import Elasticsearch

user_mapping = {
    "properties": {"name": {"type": "text", "fields": {"raw": {"type": "keyword"}}}}
}

FLAT_GIT_INDEX: Dict[str, Any] = {
    "settings": {
        # custom analyzer for analyzing file paths
        "analysis": {
            "analyzer": {
                "file_path": {
                    "type": "custom",
                    "tokenizer": "path_hierarchy",
                    "filter": ["lowercase"],
                }
            }
        },
    },
    "mappings": {
        "properties": {
            "description": {"type": "text", "analyzer": "snowball"},
            "author": user_mapping,
            "authored_date": {"type": "date"},
            "committer": user_mapping,
            "committed_date": {"type": "date"},
            "parent_shas": {"type": "keyword"},
            "files": {
                "type": "text",
                "analyzer": "file_path",
                "fielddata": True,
            },
        }
    },
}

GIT_INDEX: Dict[str, Any] = {
    "settings": {
        # custom analyzer for analyzing file paths
        "analysis": {
            "analyzer": {
                "file_path": {
                    "type": "custom",
                    "tokenizer": "path_hierarchy",
                    "filter": ["lowercase"],
                }
            }
        },
    },
    "mappings": {
        "properties": {
            # common fields
            "description": {"type": "text", "analyzer": "snowball"},
            "commit_repo": {"type": "join", "relations": {"repo": "commit"}},
            # COMMIT mappings
            "author": user_mapping,
            "authored_date": {"type": "date"},
            "committer": user_mapping,
            "committed_date": {"type": "date"},
            "parent_shas": {"type": "keyword"},
            "files": {
                "type": "text",
                "analyzer": "file_path",
                "fielddata": True,
            },
            # REPO mappings
            "is_public": {"type": "boolean"},
            "owner": user_mapping,
            "created_at": {"type": "date"},
            "tags": {"type": "keyword"},
        }
    },
}


def create_flat_git_index(client: Elasticsearch, index: str) -> None:
    client.indices.create(index=index, body=FLAT_GIT_INDEX)


def create_git_index(client: Elasticsearch, index: str) -> None:
    client.indices.create(index=index, body=GIT_INDEX)


DATA = [
    # repository
    {
        "_id": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": "repo",
            "organization": "elasticsearch",
            "created_at": "2014-03-03",
            "owner": {"name": "elasticsearch"},
            "is_public": True,
        },
        "_index": "git",
    },
    # documents
    {
        "_id": "3ca6e1e73a071a705b4babd2f581c91a2a3e5037",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": [
                "elasticsearch_dsl/aggs.py",
                "elasticsearch_dsl/search.py",
                "test_elasticsearch_dsl/test_aggs.py",
                "test_elasticsearch_dsl/test_search.py",
            ],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 7, "insertions": 23, "lines": 30, "files": 4},
            "description": "Make sure buckets aren't modified in-place",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["eb3e543323f189fd7b698e66295427204fff5755"],
            "committed_date": "2014-05-02T13:47:19",
            "authored_date": "2014-05-02T13:47:19.123+02:00",
        },
        "_index": "git",
    },
    {
        "_id": "eb3e543323f189fd7b698e66295427204fff5755",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": ["elasticsearch_dsl/search.py"],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 0, "insertions": 18, "lines": 18, "files": 1},
            "description": "Add communication with ES server",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["dd15b6ba17dd9ba16363a51f85b31f66f1fb1157"],
            "committed_date": "2014-05-01T13:32:14",
            "authored_date": "2014-05-01T13:32:14",
        },
        "_index": "git",
    },
    {
        "_id": "dd15b6ba17dd9ba16363a51f85b31f66f1fb1157",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": [
                "elasticsearch_dsl/utils.py",
                "test_elasticsearch_dsl/test_result.py",
                "elasticsearch_dsl/result.py",
            ],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 18, "insertions": 44, "lines": 62, "files": 3},
            "description": "Minor cleanup and adding helpers for interactive python",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["ed19caf25abd25300e707fadf3f81b05c5673446"],
            "committed_date": "2014-05-01T13:30:44",
            "authored_date": "2014-05-01T13:30:44",
        },
        "_index": "git",
    },
    {
        "_id": "ed19caf25abd25300e707fadf3f81b05c5673446",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": [
                "elasticsearch_dsl/aggs.py",
                "elasticsearch_dsl/search.py",
                "test_elasticsearch_dsl/test_search.py",
            ],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 0, "insertions": 28, "lines": 28, "files": 3},
            "description": "Make sure aggs do copy-on-write",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["583e52c71e9a72c1b291ec5843683d8fa8f1ce2d"],
            "committed_date": "2014-04-27T16:28:09",
            "authored_date": "2014-04-27T16:28:09",
        },
        "_index": "git",
    },
    {
        "_id": "583e52c71e9a72c1b291ec5843683d8fa8f1ce2d",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": ["elasticsearch_dsl/aggs.py"],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 1, "insertions": 1, "lines": 2, "files": 1},
            "description": "Use __setitem__ from DslBase in AggsBase",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["1dd19210b5be92b960f7db6f66ae526288edccc3"],
            "committed_date": "2014-04-27T15:51:53",
            "authored_date": "2014-04-27T15:51:53",
        },
        "_index": "git",
    },
    {
        "_id": "1dd19210b5be92b960f7db6f66ae526288edccc3",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": [
                "elasticsearch_dsl/aggs.py",
                "elasticsearch_dsl/query.py",
                "test_elasticsearch_dsl/test_search.py",
                "elasticsearch_dsl/search.py",
                "elasticsearch_dsl/filter.py",
            ],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 21, "insertions": 98, "lines": 119, "files": 5},
            "description": "Have Search clone itself on any change besides aggs",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["b4c9e29376af2e42a4e6dc153f0f293b1a18bac3"],
            "committed_date": "2014-04-26T14:49:43",
            "authored_date": "2014-04-26T14:49:43",
        },
        "_index": "git",
    },
    {
        "_id": "b4c9e29376af2e42a4e6dc153f0f293b1a18bac3",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": ["test_elasticsearch_dsl/test_result.py"],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 0, "insertions": 5, "lines": 5, "files": 1},
            "description": "Add tests for [] on response",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["a64a54181b232bb5943bd16960be9416e402f5f5"],
            "committed_date": "2014-04-26T13:56:52",
            "authored_date": "2014-04-26T13:56:52",
        },
        "_index": "git",
    },
    {
        "_id": "a64a54181b232bb5943bd16960be9416e402f5f5",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": ["test_elasticsearch_dsl/test_result.py"],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 1, "insertions": 7, "lines": 8, "files": 1},
            "description": "Test access to missing fields raises appropriate exceptions",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["df3f778a3d37b170bde6979a4ef2d9e3e6400778"],
            "committed_date": "2014-04-25T16:01:07",
            "authored_date": "2014-04-25T16:01:07",
        },
        "_index": "git",
    },
    {
        "_id": "df3f778a3d37b170bde6979a4ef2d9e3e6400778",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": [
                "elasticsearch_dsl/utils.py",
                "test_elasticsearch_dsl/test_result.py",
                "elasticsearch_dsl/result.py",
            ],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 8, "insertions": 31, "lines": 39, "files": 3},
            "description": "Support attribute access even for inner/nested objects",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["7e599e116b5ff5d271ce3fe1ebc80e82ab3d5925"],
            "committed_date": "2014-04-25T15:59:02",
            "authored_date": "2014-04-25T15:59:02",
        },
        "_index": "git",
    },
    {
        "_id": "7e599e116b5ff5d271ce3fe1ebc80e82ab3d5925",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": [
                "test_elasticsearch_dsl/test_result.py",
                "elasticsearch_dsl/result.py",
            ],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 0, "insertions": 149, "lines": 149, "files": 2},
            "description": "Added a prototype of a Respose and Result classes",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["e2882d28cb8077eaa3e5d8ae76543482d4d90f7e"],
            "committed_date": "2014-04-25T15:12:15",
            "authored_date": "2014-04-25T15:12:15",
        },
        "_index": "git",
    },
    {
        "_id": "e2882d28cb8077eaa3e5d8ae76543482d4d90f7e",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": ["docs/index.rst"],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 0, "insertions": 6, "lines": 6, "files": 1},
            "description": "add warning to the docs",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["51f94d83d1c47d3b81207736ca97a1ec6302678f"],
            "committed_date": "2014-04-22T19:16:21",
            "authored_date": "2014-04-22T19:16:21",
        },
        "_index": "git",
    },
    {
        "_id": "51f94d83d1c47d3b81207736ca97a1ec6302678f",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": ["elasticsearch_dsl/utils.py"],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 3, "insertions": 29, "lines": 32, "files": 1},
            "description": "Add some comments to the code",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["0950f6c600b49e2bf012d03b02250fb71c848555"],
            "committed_date": "2014-04-22T19:12:06",
            "authored_date": "2014-04-22T19:12:06",
        },
        "_index": "git",
    },
    {
        "_id": "0950f6c600b49e2bf012d03b02250fb71c848555",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": ["README.rst"],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 0, "insertions": 6, "lines": 6, "files": 1},
            "description": "Added a WIP warning",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["54d058f5ac6be8225ef61d5529772aada42ec6c8"],
            "committed_date": "2014-04-20T00:19:25",
            "authored_date": "2014-04-20T00:19:25",
        },
        "_index": "git",
    },
    {
        "_id": "54d058f5ac6be8225ef61d5529772aada42ec6c8",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": [
                "elasticsearch_dsl/__init__.py",
                "elasticsearch_dsl/search.py",
                "test_elasticsearch_dsl/test_search.py",
            ],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 36, "insertions": 7, "lines": 43, "files": 3},
            "description": "Remove the operator kwarg from .query",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["4cb07845e45787abc1f850c0b561e487e0034424"],
            "committed_date": "2014-04-20T00:17:25",
            "authored_date": "2014-04-20T00:17:25",
        },
        "_index": "git",
    },
    {
        "_id": "4cb07845e45787abc1f850c0b561e487e0034424",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": [
                "elasticsearch_dsl/aggs.py",
                "test_elasticsearch_dsl/test_search.py",
            ],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 35, "insertions": 49, "lines": 84, "files": 2},
            "description": "Complex example",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["578abe80f76aafd7e81fe46a44403e601733a938"],
            "committed_date": "2014-03-24T20:48:45",
            "authored_date": "2014-03-24T20:48:45",
        },
        "_index": "git",
    },
    {
        "_id": "578abe80f76aafd7e81fe46a44403e601733a938",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": ["test_elasticsearch_dsl/test_search.py"],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 2, "insertions": 0, "lines": 2, "files": 1},
            "description": "removing extra whitespace",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["ecb84f03565940c7d294dbc80723420dcfbab340"],
            "committed_date": "2014-03-24T20:42:23",
            "authored_date": "2014-03-24T20:42:23",
        },
        "_index": "git",
    },
    {
        "_id": "ecb84f03565940c7d294dbc80723420dcfbab340",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": ["test_elasticsearch_dsl/test_search.py"],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 1, "insertions": 3, "lines": 4, "files": 1},
            "description": "Make sure attribute access works for .query on Search",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["9a247c876ab66e2bca56b25f392d054e613b1b2a"],
            "committed_date": "2014-03-24T20:35:02",
            "authored_date": "2014-03-24T20:34:46",
        },
        "_index": "git",
    },
    {
        "_id": "9a247c876ab66e2bca56b25f392d054e613b1b2a",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": ["elasticsearch_dsl/search.py"],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 0, "insertions": 2, "lines": 2, "files": 1},
            "description": "Make sure .index and .doc_type methods are chainable",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["cee5e46947d510a49edd3609ff91aab7b1f3ac89"],
            "committed_date": "2014-03-24T20:27:46",
            "authored_date": "2014-03-24T20:27:46",
        },
        "_index": "git",
    },
    {
        "_id": "cee5e46947d510a49edd3609ff91aab7b1f3ac89",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": [
                "elasticsearch_dsl/search.py",
                "test_elasticsearch_dsl/test_search.py",
                "elasticsearch_dsl/filter.py",
            ],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 13, "insertions": 128, "lines": 141, "files": 3},
            "description": "Added .filter and .post_filter to Search",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["1d6857182b09a556d58c6bc5bdcb243092812ba3"],
            "committed_date": "2014-03-24T20:26:57",
            "authored_date": "2014-03-24T20:26:57",
        },
        "_index": "git",
    },
    {
        "_id": "1d6857182b09a556d58c6bc5bdcb243092812ba3",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": ["elasticsearch_dsl/utils.py", "elasticsearch_dsl/query.py"],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 24, "insertions": 29, "lines": 53, "files": 2},
            "description": "Extracted combination logic into DslBase",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["4ad92f15a1955846c01642318303a821e8435b75"],
            "committed_date": "2014-03-24T20:03:51",
            "authored_date": "2014-03-24T20:03:51",
        },
        "_index": "git",
    },
    {
        "_id": "4ad92f15a1955846c01642318303a821e8435b75",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": ["elasticsearch_dsl/utils.py", "elasticsearch_dsl/query.py"],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 43, "insertions": 45, "lines": 88, "files": 2},
            "description": "Extracted bool-related logic to a mixin to be reused by filters",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["6eb39dc2825605543ac1ed0b45b9b6baeecc44c2"],
            "committed_date": "2014-03-24T19:16:16",
            "authored_date": "2014-03-24T19:16:16",
        },
        "_index": "git",
    },
    {
        "_id": "6eb39dc2825605543ac1ed0b45b9b6baeecc44c2",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": [
                "elasticsearch_dsl/search.py",
                "test_elasticsearch_dsl/test_search.py",
            ],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 1, "insertions": 32, "lines": 33, "files": 2},
            "description": "Enable otheroperators when querying on Search object",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["be094c7b307332cb6039bf9a7c984d2c7593ddff"],
            "committed_date": "2014-03-24T18:25:10",
            "authored_date": "2014-03-24T18:25:10",
        },
        "_index": "git",
    },
    {
        "_id": "be094c7b307332cb6039bf9a7c984d2c7593ddff",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": [
                "elasticsearch_dsl/utils.py",
                "elasticsearch_dsl/query.py",
                "test_elasticsearch_dsl/test_query.py",
            ],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 23, "insertions": 35, "lines": 58, "files": 3},
            "description": "make sure query operations always return copies",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["b2576e3b6437e2cb9d8971fee4ead60df91fd75b"],
            "committed_date": "2014-03-24T18:10:37",
            "authored_date": "2014-03-24T18:03:13",
        },
        "_index": "git",
    },
    {
        "_id": "b2576e3b6437e2cb9d8971fee4ead60df91fd75b",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": [
                "elasticsearch_dsl/query.py",
                "test_elasticsearch_dsl/test_query.py",
            ],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 1, "insertions": 53, "lines": 54, "files": 2},
            "description": "Adding or operator for queries",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["1be002170ac3cd59d2e97824b83b88bb3c9c60ed"],
            "committed_date": "2014-03-24T17:53:38",
            "authored_date": "2014-03-24T17:53:38",
        },
        "_index": "git",
    },
    {
        "_id": "1be002170ac3cd59d2e97824b83b88bb3c9c60ed",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": [
                "elasticsearch_dsl/query.py",
                "test_elasticsearch_dsl/test_query.py",
            ],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 0, "insertions": 35, "lines": 35, "files": 2},
            "description": "Added inverting of queries",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["24e1e38b2f704f65440d96c290b7c6cd54c2e00e"],
            "committed_date": "2014-03-23T17:44:36",
            "authored_date": "2014-03-23T17:44:36",
        },
        "_index": "git",
    },
    {
        "_id": "24e1e38b2f704f65440d96c290b7c6cd54c2e00e",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": ["elasticsearch_dsl/aggs.py", "elasticsearch_dsl/utils.py"],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 5, "insertions": 1, "lines": 6, "files": 2},
            "description": "Change equality checks to use .to_dict()",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["277cfaedbaf3705ed74ad6296227e1172c97a63f"],
            "committed_date": "2014-03-23T17:43:01",
            "authored_date": "2014-03-23T17:43:01",
        },
        "_index": "git",
    },
    {
        "_id": "277cfaedbaf3705ed74ad6296227e1172c97a63f",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": [
                "elasticsearch_dsl/query.py",
                "test_elasticsearch_dsl/test_query.py",
            ],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 1, "insertions": 11, "lines": 12, "files": 2},
            "description": "Test combining of bool queries",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["6aa3868a6a9f35f71553ce96f9d3d63c74d054fd"],
            "committed_date": "2014-03-21T15:15:06",
            "authored_date": "2014-03-21T15:15:06",
        },
        "_index": "git",
    },
    {
        "_id": "6aa3868a6a9f35f71553ce96f9d3d63c74d054fd",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": [
                "elasticsearch_dsl/query.py",
                "test_elasticsearch_dsl/test_query.py",
            ],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 1, "insertions": 23, "lines": 24, "files": 2},
            "description": "Adding & operator for queries",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["bb311eb35e7eb53fb5ae01e3f80336866c7e3e37"],
            "committed_date": "2014-03-21T15:10:08",
            "authored_date": "2014-03-21T15:10:08",
        },
        "_index": "git",
    },
    {
        "_id": "bb311eb35e7eb53fb5ae01e3f80336866c7e3e37",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": [
                "elasticsearch_dsl/utils.py",
                "test_elasticsearch_dsl/test_query.py",
            ],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 1, "insertions": 4, "lines": 5, "files": 2},
            "description": "Don't serialize empty typed fields into dict",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["aea8ea9e421bd53a5b058495e68c3fd57bb1dacc"],
            "committed_date": "2014-03-15T16:29:37",
            "authored_date": "2014-03-15T16:29:37",
        },
        "_index": "git",
    },
    {
        "_id": "aea8ea9e421bd53a5b058495e68c3fd57bb1dacc",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": [
                "elasticsearch_dsl/utils.py",
                "elasticsearch_dsl/query.py",
                "test_elasticsearch_dsl/test_query.py",
            ],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 3, "insertions": 37, "lines": 40, "files": 3},
            "description": "Bool queries, when combining just adds their params together",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["a8819a510b919be43ff3011b904f257798fb8916"],
            "committed_date": "2014-03-15T16:16:40",
            "authored_date": "2014-03-15T16:16:40",
        },
        "_index": "git",
    },
    {
        "_id": "a8819a510b919be43ff3011b904f257798fb8916",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": ["test_elasticsearch_dsl/run_tests.py"],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 6, "insertions": 2, "lines": 8, "files": 1},
            "description": "Simpler run_tests.py",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["e35792a725be2325fc54d3fcb95a7d38d8075a99"],
            "committed_date": "2014-03-15T16:02:21",
            "authored_date": "2014-03-15T16:02:21",
        },
        "_index": "git",
    },
    {
        "_id": "e35792a725be2325fc54d3fcb95a7d38d8075a99",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": ["elasticsearch_dsl/aggs.py", "elasticsearch_dsl/query.py"],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 2, "insertions": 2, "lines": 4, "files": 2},
            "description": "Maku we don't treat shortcuts as methods.",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["3179d778dc9e3f2883d5f7ffa63b9ae0399c16bc"],
            "committed_date": "2014-03-15T15:59:21",
            "authored_date": "2014-03-15T15:59:21",
        },
        "_index": "git",
    },
    {
        "_id": "3179d778dc9e3f2883d5f7ffa63b9ae0399c16bc",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": [
                "elasticsearch_dsl/aggs.py",
                "elasticsearch_dsl/query.py",
                "elasticsearch_dsl/utils.py",
            ],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 9, "insertions": 5, "lines": 14, "files": 3},
            "description": "Centralize == of Dsl objects",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["b5e7d0c4b284211df8f7b464fcece93a27a802fb"],
            "committed_date": "2014-03-10T21:37:24",
            "authored_date": "2014-03-10T21:37:24",
        },
        "_index": "git",
    },
    {
        "_id": "b5e7d0c4b284211df8f7b464fcece93a27a802fb",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": [
                "elasticsearch_dsl/aggs.py",
                "elasticsearch_dsl/search.py",
                "test_elasticsearch_dsl/test_search.py",
                "elasticsearch_dsl/utils.py",
                "elasticsearch_dsl/query.py",
                "test_elasticsearch_dsl/test_aggs.py",
            ],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 75, "insertions": 115, "lines": 190, "files": 6},
            "description": "Experimental draft with more declarative DSL",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["0fe741b43adee5ca1424584ddd3f35fa33f8733c"],
            "committed_date": "2014-03-10T21:34:39",
            "authored_date": "2014-03-10T21:34:39",
        },
        "_index": "git",
    },
    {
        "_id": "0fe741b43adee5ca1424584ddd3f35fa33f8733c",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": ["test_elasticsearch_dsl/test_search.py"],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 2, "insertions": 2, "lines": 4, "files": 1},
            "description": "Make sure .query is chainable",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["a22be5933d4b022cbacee867b1aece120208edf3"],
            "committed_date": "2014-03-07T17:41:59",
            "authored_date": "2014-03-07T17:41:59",
        },
        "_index": "git",
    },
    {
        "_id": "a22be5933d4b022cbacee867b1aece120208edf3",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": [
                "elasticsearch_dsl/aggs.py",
                "elasticsearch_dsl/search.py",
                "test_elasticsearch_dsl/test_search.py",
            ],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 14, "insertions": 44, "lines": 58, "files": 3},
            "description": "Search now does aggregations",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["e823686aacfc4bdcb34ffdab337a26fa09659a9a"],
            "committed_date": "2014-03-07T17:29:55",
            "authored_date": "2014-03-07T17:29:55",
        },
        "_index": "git",
    },
    {
        "_id": "e823686aacfc4bdcb34ffdab337a26fa09659a9a",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": [".gitignore"],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 0, "insertions": 1, "lines": 1, "files": 1},
            "description": "Ignore html coverage report",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["e0aedb3011c71d704deec03a8f32b2b360d6e364"],
            "committed_date": "2014-03-07T17:03:23",
            "authored_date": "2014-03-07T17:03:23",
        },
        "_index": "git",
    },
    {
        "_id": "e0aedb3011c71d704deec03a8f32b2b360d6e364",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": [
                "elasticsearch_dsl/aggs.py",
                "test_elasticsearch_dsl/test_aggs.py",
            ],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 0, "insertions": 228, "lines": 228, "files": 2},
            "description": "Added aggregation DSL objects",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["61cbc0aa62a0b776ae5e333406659dbb2f5cfbbd"],
            "committed_date": "2014-03-07T16:25:55",
            "authored_date": "2014-03-07T16:25:55",
        },
        "_index": "git",
    },
    {
        "_id": "61cbc0aa62a0b776ae5e333406659dbb2f5cfbbd",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": ["elasticsearch_dsl/utils.py", "elasticsearch_dsl/query.py"],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 12, "insertions": 7, "lines": 19, "files": 2},
            "description": "Only retrieve DslClass, leave the instantiation to the caller",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["647f1017a7b17a913e07af70a3b03202f6adbdfd"],
            "committed_date": "2014-03-07T15:27:43",
            "authored_date": "2014-03-07T15:27:43",
        },
        "_index": "git",
    },
    {
        "_id": "647f1017a7b17a913e07af70a3b03202f6adbdfd",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": [
                "test_elasticsearch_dsl/test_search.py",
                "elasticsearch_dsl/query.py",
                "test_elasticsearch_dsl/test_query.py",
            ],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 19, "insertions": 19, "lines": 38, "files": 3},
            "description": "No need to replicate Query suffix when in query namespace",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["7c4f94ecdb38f0e91c7ee52f579c0ea148afcc7d"],
            "committed_date": "2014-03-07T15:19:01",
            "authored_date": "2014-03-07T15:19:01",
        },
        "_index": "git",
    },
    {
        "_id": "7c4f94ecdb38f0e91c7ee52f579c0ea148afcc7d",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": ["elasticsearch_dsl/utils.py"],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 2, "insertions": 3, "lines": 5, "files": 1},
            "description": "Ask forgiveness, not permission",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["c10793c2ca43688195e415b25b674ff34d58eaff"],
            "committed_date": "2014-03-07T15:13:22",
            "authored_date": "2014-03-07T15:13:22",
        },
        "_index": "git",
    },
    {
        "_id": "c10793c2ca43688195e415b25b674ff34d58eaff",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": [
                "elasticsearch_dsl/utils.py",
                "elasticsearch_dsl/query.py",
                "test_elasticsearch_dsl/test_query.py",
            ],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 24, "insertions": 27, "lines": 51, "files": 3},
            "description": "Extract DSL object registration to DslMeta",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["d8867fdb17fcf4c696657740fa08d29c36adc6ec"],
            "committed_date": "2014-03-07T15:12:13",
            "authored_date": "2014-03-07T15:10:31",
        },
        "_index": "git",
    },
    {
        "_id": "d8867fdb17fcf4c696657740fa08d29c36adc6ec",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": [
                "elasticsearch_dsl/search.py",
                "test_elasticsearch_dsl/test_search.py",
            ],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 0, "insertions": 13, "lines": 13, "files": 2},
            "description": "Search.to_dict",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["2eb7cd980d917ed6f4a4dd8e246804f710ec5082"],
            "committed_date": "2014-03-07T02:58:33",
            "authored_date": "2014-03-07T02:58:33",
        },
        "_index": "git",
    },
    {
        "_id": "2eb7cd980d917ed6f4a4dd8e246804f710ec5082",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": [
                "elasticsearch_dsl/search.py",
                "test_elasticsearch_dsl/test_search.py",
            ],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 0, "insertions": 113, "lines": 113, "files": 2},
            "description": "Basic Search object",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["11708576f9118e0dbf27ae1f8a7b799cf281b511"],
            "committed_date": "2014-03-06T21:02:03",
            "authored_date": "2014-03-06T21:01:05",
        },
        "_index": "git",
    },
    {
        "_id": "11708576f9118e0dbf27ae1f8a7b799cf281b511",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": [
                "elasticsearch_dsl/query.py",
                "test_elasticsearch_dsl/test_query.py",
            ],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 0, "insertions": 13, "lines": 13, "files": 2},
            "description": "MatchAll query + anything is anything",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["1dc496e5c7c1b2caf290df477fca2db61ebe37e0"],
            "committed_date": "2014-03-06T20:40:39",
            "authored_date": "2014-03-06T20:39:52",
        },
        "_index": "git",
    },
    {
        "_id": "1dc496e5c7c1b2caf290df477fca2db61ebe37e0",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": [
                "elasticsearch_dsl/query.py",
                "test_elasticsearch_dsl/test_query.py",
            ],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 0, "insertions": 53, "lines": 53, "files": 2},
            "description": "From_dict, Q(dict) and bool query parses it's subqueries",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["d407f99d1959b7b862a541c066d9fd737ce913f3"],
            "committed_date": "2014-03-06T20:24:30",
            "authored_date": "2014-03-06T20:24:30",
        },
        "_index": "git",
    },
    {
        "_id": "d407f99d1959b7b862a541c066d9fd737ce913f3",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": ["CONTRIBUTING.md", "README.rst"],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 6, "insertions": 21, "lines": 27, "files": 2},
            "description": "Housekeeping - licence and updated generic CONTRIBUTING.md",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["277e8ecc7395754d1ba1f2411ec32337a3e9d73f"],
            "committed_date": "2014-03-05T16:21:44",
            "authored_date": "2014-03-05T16:21:44",
        },
        "_index": "git",
    },
    {
        "_id": "277e8ecc7395754d1ba1f2411ec32337a3e9d73f",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": [
                "elasticsearch_dsl/query.py",
                "setup.py",
                "test_elasticsearch_dsl/test_query.py",
            ],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 0, "insertions": 59, "lines": 59, "files": 3},
            "description": "Automatic query registration and Q function",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["8f1e34bd8f462fec50bcc10971df2d57e2986604"],
            "committed_date": "2014-03-05T16:18:52",
            "authored_date": "2014-03-05T16:18:52",
        },
        "_index": "git",
    },
    {
        "_id": "8f1e34bd8f462fec50bcc10971df2d57e2986604",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": [
                "elasticsearch_dsl/query.py",
                "test_elasticsearch_dsl/test_query.py",
            ],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 0, "insertions": 54, "lines": 54, "files": 2},
            "description": "Initial implementation of match and bool queries",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["fcff47ddcc6d08be5739d03dd30f504fb9db2608"],
            "committed_date": "2014-03-05T15:55:06",
            "authored_date": "2014-03-05T15:55:06",
        },
        "_index": "git",
    },
    {
        "_id": "fcff47ddcc6d08be5739d03dd30f504fb9db2608",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": [
                "docs/Makefile",
                "CONTRIBUTING.md",
                "docs/conf.py",
                "LICENSE",
                "Changelog.rst",
                "docs/index.rst",
                "docs/Changelog.rst",
            ],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 0, "insertions": 692, "lines": 692, "files": 7},
            "description": "Docs template",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["febe8127ae48fcc81778c0fb2d628f1bcc0a0350"],
            "committed_date": "2014-03-04T01:42:31",
            "authored_date": "2014-03-04T01:42:31",
        },
        "_index": "git",
    },
    {
        "_id": "febe8127ae48fcc81778c0fb2d628f1bcc0a0350",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": [
                "elasticsearch_dsl/__init__.py",
                "test_elasticsearch_dsl/run_tests.py",
                "setup.py",
                "README.rst",
                "test_elasticsearch_dsl/__init__.py",
            ],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 0, "insertions": 82, "lines": 82, "files": 5},
            "description": "Empty project structure",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": ["2a8f1ce89760bfc72808f3945b539eae650acac9"],
            "committed_date": "2014-03-04T01:37:49",
            "authored_date": "2014-03-03T18:23:55",
        },
        "_index": "git",
    },
    {
        "_id": "2a8f1ce89760bfc72808f3945b539eae650acac9",
        "routing": "elasticsearch-dsl-py",
        "_source": {
            "commit_repo": {"name": "commit", "parent": "elasticsearch-dsl-py"},
            "files": [".gitignore"],
            "committer": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "stats": {"deletions": 0, "insertions": 9, "lines": 9, "files": 1},
            "description": "Initial commit, .gitignore",
            "author": {"name": "Honza Kr\xe1l", "email": "honza.kral@gmail.com"},
            "parent_shas": [],
            "committed_date": "2014-03-03T18:15:05",
            "authored_date": "2014-03-03T18:15:05",
        },
        "_index": "git",
    },
]


def flatten_doc(d: Dict[str, Any]) -> Dict[str, Any]:
    src = d["_source"].copy()
    del src["commit_repo"]
    return {"_index": "flat-git", "_id": d["_id"], "_source": src}


FLAT_DATA = [flatten_doc(d) for d in DATA if "routing" in d]


def create_test_git_data(d: Dict[str, Any]) -> Dict[str, Any]:
    src = d["_source"].copy()
    return {
        "_index": "test-git",
        "routing": "elasticsearch-dsl-py",
        "_id": d["_id"],
        "_source": src,
    }


TEST_GIT_DATA = [create_test_git_data(d) for d in DATA]
