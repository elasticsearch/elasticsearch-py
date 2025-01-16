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

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Mapping, Optional, Sequence

if TYPE_CHECKING:
    from _operator import _SupportsComparison

import pytest

from elasticsearch.dsl import Range


@pytest.mark.parametrize(
    "kwargs, item",
    [
        ({}, 1),
        ({}, -1),
        ({"gte": -1}, -1),
        ({"lte": 4}, 4),
        ({"lte": 4, "gte": 2}, 4),
        ({"lte": 4, "gte": 2}, 2),
        ({"gt": datetime.now() - timedelta(seconds=10)}, datetime.now()),
    ],
)
def test_range_contains(
    kwargs: Mapping[str, "_SupportsComparison"], item: "_SupportsComparison"
) -> None:
    assert item in Range(**kwargs)


@pytest.mark.parametrize(
    "kwargs, item",
    [
        ({"gt": -1}, -1),
        ({"lt": 4}, 4),
        ({"lt": 4}, 42),
        ({"lte": 4, "gte": 2}, 1),
        ({"lte": datetime.now() - timedelta(seconds=10)}, datetime.now()),
    ],
)
def test_range_not_contains(
    kwargs: Mapping[str, "_SupportsComparison"], item: "_SupportsComparison"
) -> None:
    assert item not in Range(**kwargs)


@pytest.mark.parametrize(
    "args,kwargs",
    [
        (({},), {"lt": 42}),
        ((), {"not_lt": 42}),
        ((object(),), {}),
        ((), {"lt": 1, "lte": 1}),
        ((), {"gt": 1, "gte": 1}),
    ],
)
def test_range_raises_value_error_on_wrong_params(
    args: Sequence[Any], kwargs: Mapping[str, "_SupportsComparison"]
) -> None:
    with pytest.raises(ValueError):
        Range(*args, **kwargs)


@pytest.mark.parametrize(
    "range,lower,inclusive",
    [
        (Range(gt=1), 1, False),
        (Range(gte=1), 1, True),
        (Range(), None, False),
        (Range(lt=42), None, False),
    ],
)
def test_range_lower(
    range: Range["_SupportsComparison"],
    lower: Optional["_SupportsComparison"],
    inclusive: bool,
) -> None:
    assert (lower, inclusive) == range.lower


@pytest.mark.parametrize(
    "range,upper,inclusive",
    [
        (Range(lt=1), 1, False),
        (Range(lte=1), 1, True),
        (Range(), None, False),
        (Range(gt=42), None, False),
    ],
)
def test_range_upper(
    range: Range["_SupportsComparison"],
    upper: Optional["_SupportsComparison"],
    inclusive: bool,
) -> None:
    assert (upper, inclusive) == range.upper
