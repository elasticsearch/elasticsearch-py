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

import os
import subprocess
import sys
from glob import glob
from pathlib import Path

import unasync


def main(check=False):
    # the list of directories that need to be processed with unasync
    # each entry has two paths:
    #   - the source path with the async sources
    #   - the destination path where the sync sources should be written
    source_dirs = [
        (
            "elasticsearch/dsl/_async/",
            "elasticsearch/dsl/_sync/",
        ),
        ("test_elasticsearch/test_dsl/_async/", "test_elasticsearch/test_dsl/_sync/"),
        (
            "test_elasticsearch/test_dsl/test_integration/_async/",
            "test_elasticsearch/test_dsl/test_integration/_sync/",
        ),
        (
            "test_elasticsearch/test_dsl/test_integration/test_examples/_async/",
            "test_elasticsearch/test_dsl/test_integration/test_examples/_sync/",
        ),
        ("examples/dsl/async/", "examples/dsl/"),
    ]

    # Unasync all the generated async code
    additional_replacements = {
        "_async": "_sync",
        "AsyncElasticsearch": "Elasticsearch",
        "AsyncSearch": "Search",
        "AsyncMultiSearch": "MultiSearch",
        "AsyncEmptySearch": "EmptySearch",
        "AsyncDocument": "Document",
        "AsyncIndexMeta": "IndexMeta",
        "AsyncIndexTemplate": "IndexTemplate",
        "AsyncIndex": "Index",
        "AsyncComposableIndexTemplate": "ComposableIndexTemplate",
        "AsyncUpdateByQuery": "UpdateByQuery",
        "AsyncMapping": "Mapping",
        "AsyncFacetedSearch": "FacetedSearch",
        "AsyncUsingType": "UsingType",
        "async_connections": "connections",
        "async_scan": "scan",
        "async_simulate": "simulate",
        "async_bulk": "bulk",
        "async_mock_client": "mock_client",
        "async_client": "client",
        "async_data_client": "data_client",
        "async_write_client": "write_client",
        "async_pull_request": "pull_request",
        "async_examples": "examples",
        "async_sleep": "sleep",
        "assert_awaited_once_with": "assert_called_once_with",
        "pytest_asyncio": "pytest",
        "asynccontextmanager": "contextmanager",
    }
    rules = [
        unasync.Rule(
            fromdir=dir[0],
            todir=f"{dir[0]}_sync_check/" if check else dir[1],
            additional_replacements=additional_replacements,
        )
        for dir in source_dirs
    ]

    filepaths = []
    for root, _, filenames in os.walk(Path(__file__).absolute().parent.parent):
        if "/site-packages" in root or "/." in root or "__pycache__" in root:
            continue
        for filename in filenames:
            if filename.rpartition(".")[-1] in (
                "py",
                "pyi",
            ) and not filename.startswith("utils.py"):
                filepaths.append(os.path.join(root, filename))

    unasync.unasync_files(filepaths, rules)
    for dir in source_dirs:
        output_dir = f"{dir[0]}_sync_check/" if check else dir[1]
        subprocess.check_call(["black", "--target-version=py38", output_dir])
        subprocess.check_call(["isort", output_dir])
        for file in glob("*.py", root_dir=dir[0]):
            # remove asyncio from sync files
            subprocess.check_call(
                ["sed", "-i.bak", "/^import asyncio$/d", f"{output_dir}{file}"]
            )
            subprocess.check_call(
                [
                    "sed",
                    "-i.bak",
                    "s/asyncio\\.run(main())/main()/",
                    f"{output_dir}{file}",
                ]
            )
            subprocess.check_call(
                [
                    "sed",
                    "-i.bak",
                    "s/elasticsearch\\[async\\]/elasticsearch/",
                    f"{output_dir}{file}",
                ]
            )
            subprocess.check_call(
                [
                    "sed",
                    "-i.bak",
                    "s/pytest.mark.asyncio/pytest.mark.sync/",
                    f"{output_dir}{file}",
                ]
            )
            subprocess.check_call(["rm", f"{output_dir}{file}.bak"])

            if check:
                # make sure there are no differences between _sync and _sync_check
                subprocess.check_call(
                    [
                        "diff",
                        f"{dir[1]}{file}",
                        f"{output_dir}{file}",
                    ]
                )

        if check:
            subprocess.check_call(["rm", "-rf", output_dir])


if __name__ == "__main__":
    main(check="--check" in sys.argv)
