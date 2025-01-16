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
from elasticsearch.dsl import A, Search

from ..examples.composite_agg import scan_aggs


@pytest.mark.sync
def test_scan_aggs_exhausts_all_files(
    data_client: Elasticsearch,
) -> None:
    s = Search(index="flat-git")
    key_aggs = [{"files": A("terms", field="files")}]
    file_list = [f for f in scan_aggs(s, key_aggs)]

    assert len(file_list) == 26


@pytest.mark.sync
def test_scan_aggs_with_multiple_aggs(
    data_client: Elasticsearch,
) -> None:
    s = Search(index="flat-git")
    key_aggs = [
        {"files": A("terms", field="files")},
        {
            "months": A(
                "date_histogram", field="committed_date", calendar_interval="month"
            )
        },
    ]
    file_list = [
        f
        for f in scan_aggs(
            s, key_aggs, {"first_seen": A("min", field="committed_date")}
        )
    ]

    assert len(file_list) == 47
