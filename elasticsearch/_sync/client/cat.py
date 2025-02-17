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

import typing as t

from elastic_transport import ObjectApiResponse, TextApiResponse

from ._base import NamespacedClient
from .utils import (
    SKIP_IN_PATH,
    Stability,
    _quote,
    _rewrite_parameters,
    _stability_warning,
)


class CatClient(NamespacedClient):

    @_rewrite_parameters()
    def aliases(
        self,
        *,
        name: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        error_trace: t.Optional[bool] = None,
        expand_wildcards: t.Optional[
            t.Union[
                t.Sequence[
                    t.Union[str, t.Literal["all", "closed", "hidden", "none", "open"]]
                ],
                t.Union[str, t.Literal["all", "closed", "hidden", "none", "open"]],
            ]
        ] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        format: t.Optional[str] = None,
        h: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        help: t.Optional[bool] = None,
        human: t.Optional[bool] = None,
        local: t.Optional[bool] = None,
        master_timeout: t.Optional[t.Union[str, t.Literal[-1], t.Literal[0]]] = None,
        pretty: t.Optional[bool] = None,
        s: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        v: t.Optional[bool] = None,
    ) -> t.Union[ObjectApiResponse[t.Any], TextApiResponse]:
        """
        .. raw:: html

          <p>Get aliases.</p>
          <p>Get the cluster's index aliases, including filter and routing information.
          This API does not return data stream aliases.</p>
          <p>IMPORTANT: CAT APIs are only intended for human consumption using the command line or the Kibana console. They are not intended for use by applications. For application consumption, use the aliases API.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/cat-alias.html>`_

        :param name: A comma-separated list of aliases to retrieve. Supports wildcards
            (`*`). To retrieve all aliases, omit this parameter or use `*` or `_all`.
        :param expand_wildcards: The type of index that wildcard patterns can match.
            If the request can target data streams, this argument determines whether
            wildcard expressions match hidden data streams. It supports comma-separated
            values, such as `open,hidden`.
        :param format: Specifies the format to return the columnar data in, can be set
            to `text`, `json`, `cbor`, `yaml`, or `smile`.
        :param h: List of columns to appear in the response. Supports simple wildcards.
        :param help: When set to `true` will output available columns. This option can't
            be combined with any other query string option.
        :param local: If `true`, the request computes the list of selected nodes from
            the local cluster state. If `false` the list of selected nodes are computed
            from the cluster state of the master node. In both cases the coordinating
            node will send requests for further information to each selected node.
        :param master_timeout: The period to wait for a connection to the master node.
            If the master node is not available before the timeout expires, the request
            fails and returns an error. To indicated that the request should never timeout,
            you can set it to `-1`.
        :param s: List of columns that determine how the table should be sorted. Sorting
            defaults to ascending and can be changed by setting `:asc` or `:desc` as
            a suffix to the column name.
        :param v: When set to `true` will enable verbose output.
        """
        __path_parts: t.Dict[str, str]
        if name not in SKIP_IN_PATH:
            __path_parts = {"name": _quote(name)}
            __path = f'/_cat/aliases/{__path_parts["name"]}'
        else:
            __path_parts = {}
            __path = "/_cat/aliases"
        __query: t.Dict[str, t.Any] = {}
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if expand_wildcards is not None:
            __query["expand_wildcards"] = expand_wildcards
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if format is not None:
            __query["format"] = format
        if h is not None:
            __query["h"] = h
        if help is not None:
            __query["help"] = help
        if human is not None:
            __query["human"] = human
        if local is not None:
            __query["local"] = local
        if master_timeout is not None:
            __query["master_timeout"] = master_timeout
        if pretty is not None:
            __query["pretty"] = pretty
        if s is not None:
            __query["s"] = s
        if v is not None:
            __query["v"] = v
        __headers = {"accept": "text/plain,application/json"}
        return self.perform_request(  # type: ignore[return-value]
            "GET",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="cat.aliases",
            path_parts=__path_parts,
        )

    @_rewrite_parameters()
    def allocation(
        self,
        *,
        node_id: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        bytes: t.Optional[
            t.Union[str, t.Literal["b", "gb", "kb", "mb", "pb", "tb"]]
        ] = None,
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        format: t.Optional[str] = None,
        h: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        help: t.Optional[bool] = None,
        human: t.Optional[bool] = None,
        local: t.Optional[bool] = None,
        master_timeout: t.Optional[t.Union[str, t.Literal[-1], t.Literal[0]]] = None,
        pretty: t.Optional[bool] = None,
        s: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        v: t.Optional[bool] = None,
    ) -> t.Union[ObjectApiResponse[t.Any], TextApiResponse]:
        """
        .. raw:: html

          <p>Get shard allocation information.</p>
          <p>Get a snapshot of the number of shards allocated to each data node and their disk space.</p>
          <p>IMPORTANT: CAT APIs are only intended for human consumption using the command line or Kibana console. They are not intended for use by applications.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/cat-allocation.html>`_

        :param node_id: A comma-separated list of node identifiers or names used to limit
            the returned information.
        :param bytes: The unit used to display byte values.
        :param format: Specifies the format to return the columnar data in, can be set
            to `text`, `json`, `cbor`, `yaml`, or `smile`.
        :param h: List of columns to appear in the response. Supports simple wildcards.
        :param help: When set to `true` will output available columns. This option can't
            be combined with any other query string option.
        :param local: If `true`, the request computes the list of selected nodes from
            the local cluster state. If `false` the list of selected nodes are computed
            from the cluster state of the master node. In both cases the coordinating
            node will send requests for further information to each selected node.
        :param master_timeout: Period to wait for a connection to the master node.
        :param s: List of columns that determine how the table should be sorted. Sorting
            defaults to ascending and can be changed by setting `:asc` or `:desc` as
            a suffix to the column name.
        :param v: When set to `true` will enable verbose output.
        """
        __path_parts: t.Dict[str, str]
        if node_id not in SKIP_IN_PATH:
            __path_parts = {"node_id": _quote(node_id)}
            __path = f'/_cat/allocation/{__path_parts["node_id"]}'
        else:
            __path_parts = {}
            __path = "/_cat/allocation"
        __query: t.Dict[str, t.Any] = {}
        if bytes is not None:
            __query["bytes"] = bytes
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if format is not None:
            __query["format"] = format
        if h is not None:
            __query["h"] = h
        if help is not None:
            __query["help"] = help
        if human is not None:
            __query["human"] = human
        if local is not None:
            __query["local"] = local
        if master_timeout is not None:
            __query["master_timeout"] = master_timeout
        if pretty is not None:
            __query["pretty"] = pretty
        if s is not None:
            __query["s"] = s
        if v is not None:
            __query["v"] = v
        __headers = {"accept": "text/plain,application/json"}
        return self.perform_request(  # type: ignore[return-value]
            "GET",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="cat.allocation",
            path_parts=__path_parts,
        )

    @_rewrite_parameters()
    def component_templates(
        self,
        *,
        name: t.Optional[str] = None,
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        format: t.Optional[str] = None,
        h: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        help: t.Optional[bool] = None,
        human: t.Optional[bool] = None,
        local: t.Optional[bool] = None,
        master_timeout: t.Optional[t.Union[str, t.Literal[-1], t.Literal[0]]] = None,
        pretty: t.Optional[bool] = None,
        s: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        v: t.Optional[bool] = None,
    ) -> t.Union[ObjectApiResponse[t.Any], TextApiResponse]:
        """
        .. raw:: html

          <p>Get component templates.</p>
          <p>Get information about component templates in a cluster.
          Component templates are building blocks for constructing index templates that specify index mappings, settings, and aliases.</p>
          <p>IMPORTANT: CAT APIs are only intended for human consumption using the command line or Kibana console.
          They are not intended for use by applications. For application consumption, use the get component template API.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/cat-component-templates.html>`_

        :param name: The name of the component template. It accepts wildcard expressions.
            If it is omitted, all component templates are returned.
        :param format: Specifies the format to return the columnar data in, can be set
            to `text`, `json`, `cbor`, `yaml`, or `smile`.
        :param h: List of columns to appear in the response. Supports simple wildcards.
        :param help: When set to `true` will output available columns. This option can't
            be combined with any other query string option.
        :param local: If `true`, the request computes the list of selected nodes from
            the local cluster state. If `false` the list of selected nodes are computed
            from the cluster state of the master node. In both cases the coordinating
            node will send requests for further information to each selected node.
        :param master_timeout: The period to wait for a connection to the master node.
        :param s: List of columns that determine how the table should be sorted. Sorting
            defaults to ascending and can be changed by setting `:asc` or `:desc` as
            a suffix to the column name.
        :param v: When set to `true` will enable verbose output.
        """
        __path_parts: t.Dict[str, str]
        if name not in SKIP_IN_PATH:
            __path_parts = {"name": _quote(name)}
            __path = f'/_cat/component_templates/{__path_parts["name"]}'
        else:
            __path_parts = {}
            __path = "/_cat/component_templates"
        __query: t.Dict[str, t.Any] = {}
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if format is not None:
            __query["format"] = format
        if h is not None:
            __query["h"] = h
        if help is not None:
            __query["help"] = help
        if human is not None:
            __query["human"] = human
        if local is not None:
            __query["local"] = local
        if master_timeout is not None:
            __query["master_timeout"] = master_timeout
        if pretty is not None:
            __query["pretty"] = pretty
        if s is not None:
            __query["s"] = s
        if v is not None:
            __query["v"] = v
        __headers = {"accept": "text/plain,application/json"}
        return self.perform_request(  # type: ignore[return-value]
            "GET",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="cat.component_templates",
            path_parts=__path_parts,
        )

    @_rewrite_parameters()
    def count(
        self,
        *,
        index: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        format: t.Optional[str] = None,
        h: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        help: t.Optional[bool] = None,
        human: t.Optional[bool] = None,
        pretty: t.Optional[bool] = None,
        s: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        v: t.Optional[bool] = None,
    ) -> t.Union[ObjectApiResponse[t.Any], TextApiResponse]:
        """
        .. raw:: html

          <p>Get a document count.</p>
          <p>Get quick access to a document count for a data stream, an index, or an entire cluster.
          The document count only includes live documents, not deleted documents which have not yet been removed by the merge process.</p>
          <p>IMPORTANT: CAT APIs are only intended for human consumption using the command line or Kibana console.
          They are not intended for use by applications. For application consumption, use the count API.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/cat-count.html>`_

        :param index: A comma-separated list of data streams, indices, and aliases used
            to limit the request. It supports wildcards (`*`). To target all data streams
            and indices, omit this parameter or use `*` or `_all`.
        :param format: Specifies the format to return the columnar data in, can be set
            to `text`, `json`, `cbor`, `yaml`, or `smile`.
        :param h: List of columns to appear in the response. Supports simple wildcards.
        :param help: When set to `true` will output available columns. This option can't
            be combined with any other query string option.
        :param s: List of columns that determine how the table should be sorted. Sorting
            defaults to ascending and can be changed by setting `:asc` or `:desc` as
            a suffix to the column name.
        :param v: When set to `true` will enable verbose output.
        """
        __path_parts: t.Dict[str, str]
        if index not in SKIP_IN_PATH:
            __path_parts = {"index": _quote(index)}
            __path = f'/_cat/count/{__path_parts["index"]}'
        else:
            __path_parts = {}
            __path = "/_cat/count"
        __query: t.Dict[str, t.Any] = {}
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if format is not None:
            __query["format"] = format
        if h is not None:
            __query["h"] = h
        if help is not None:
            __query["help"] = help
        if human is not None:
            __query["human"] = human
        if pretty is not None:
            __query["pretty"] = pretty
        if s is not None:
            __query["s"] = s
        if v is not None:
            __query["v"] = v
        __headers = {"accept": "text/plain,application/json"}
        return self.perform_request(  # type: ignore[return-value]
            "GET",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="cat.count",
            path_parts=__path_parts,
        )

    @_rewrite_parameters()
    def fielddata(
        self,
        *,
        fields: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        bytes: t.Optional[
            t.Union[str, t.Literal["b", "gb", "kb", "mb", "pb", "tb"]]
        ] = None,
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        format: t.Optional[str] = None,
        h: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        help: t.Optional[bool] = None,
        human: t.Optional[bool] = None,
        pretty: t.Optional[bool] = None,
        s: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        v: t.Optional[bool] = None,
    ) -> t.Union[ObjectApiResponse[t.Any], TextApiResponse]:
        """
        .. raw:: html

          <p>Get field data cache information.</p>
          <p>Get the amount of heap memory currently used by the field data cache on every data node in the cluster.</p>
          <p>IMPORTANT: cat APIs are only intended for human consumption using the command line or Kibana console.
          They are not intended for use by applications. For application consumption, use the nodes stats API.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/cat-fielddata.html>`_

        :param fields: Comma-separated list of fields used to limit returned information.
            To retrieve all fields, omit this parameter.
        :param bytes: The unit used to display byte values.
        :param format: Specifies the format to return the columnar data in, can be set
            to `text`, `json`, `cbor`, `yaml`, or `smile`.
        :param h: List of columns to appear in the response. Supports simple wildcards.
        :param help: When set to `true` will output available columns. This option can't
            be combined with any other query string option.
        :param s: List of columns that determine how the table should be sorted. Sorting
            defaults to ascending and can be changed by setting `:asc` or `:desc` as
            a suffix to the column name.
        :param v: When set to `true` will enable verbose output.
        """
        __path_parts: t.Dict[str, str]
        if fields not in SKIP_IN_PATH:
            __path_parts = {"fields": _quote(fields)}
            __path = f'/_cat/fielddata/{__path_parts["fields"]}'
        else:
            __path_parts = {}
            __path = "/_cat/fielddata"
        __query: t.Dict[str, t.Any] = {}
        if bytes is not None:
            __query["bytes"] = bytes
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if format is not None:
            __query["format"] = format
        if h is not None:
            __query["h"] = h
        if help is not None:
            __query["help"] = help
        if human is not None:
            __query["human"] = human
        if pretty is not None:
            __query["pretty"] = pretty
        if s is not None:
            __query["s"] = s
        if v is not None:
            __query["v"] = v
        __headers = {"accept": "text/plain,application/json"}
        return self.perform_request(  # type: ignore[return-value]
            "GET",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="cat.fielddata",
            path_parts=__path_parts,
        )

    @_rewrite_parameters()
    def health(
        self,
        *,
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        format: t.Optional[str] = None,
        h: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        help: t.Optional[bool] = None,
        human: t.Optional[bool] = None,
        pretty: t.Optional[bool] = None,
        s: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        time: t.Optional[
            t.Union[str, t.Literal["d", "h", "m", "micros", "ms", "nanos", "s"]]
        ] = None,
        ts: t.Optional[bool] = None,
        v: t.Optional[bool] = None,
    ) -> t.Union[ObjectApiResponse[t.Any], TextApiResponse]:
        """
        .. raw:: html

          <p>Get the cluster health status.</p>
          <p>IMPORTANT: CAT APIs are only intended for human consumption using the command line or Kibana console.
          They are not intended for use by applications. For application consumption, use the cluster health API.
          This API is often used to check malfunctioning clusters.
          To help you track cluster health alongside log files and alerting systems, the API returns timestamps in two formats:
          <code>HH:MM:SS</code>, which is human-readable but includes no date information;
          <code>Unix epoch time</code>, which is machine-sortable and includes date information.
          The latter format is useful for cluster recoveries that take multiple days.
          You can use the cat health API to verify cluster health across multiple nodes.
          You also can use the API to track the recovery of a large cluster over a longer period of time.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/cat-health.html>`_

        :param format: Specifies the format to return the columnar data in, can be set
            to `text`, `json`, `cbor`, `yaml`, or `smile`.
        :param h: List of columns to appear in the response. Supports simple wildcards.
        :param help: When set to `true` will output available columns. This option can't
            be combined with any other query string option.
        :param s: List of columns that determine how the table should be sorted. Sorting
            defaults to ascending and can be changed by setting `:asc` or `:desc` as
            a suffix to the column name.
        :param time: The unit used to display time values.
        :param ts: If true, returns `HH:MM:SS` and Unix epoch timestamps.
        :param v: When set to `true` will enable verbose output.
        """
        __path_parts: t.Dict[str, str] = {}
        __path = "/_cat/health"
        __query: t.Dict[str, t.Any] = {}
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if format is not None:
            __query["format"] = format
        if h is not None:
            __query["h"] = h
        if help is not None:
            __query["help"] = help
        if human is not None:
            __query["human"] = human
        if pretty is not None:
            __query["pretty"] = pretty
        if s is not None:
            __query["s"] = s
        if time is not None:
            __query["time"] = time
        if ts is not None:
            __query["ts"] = ts
        if v is not None:
            __query["v"] = v
        __headers = {"accept": "text/plain,application/json"}
        return self.perform_request(  # type: ignore[return-value]
            "GET",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="cat.health",
            path_parts=__path_parts,
        )

    @_rewrite_parameters()
    def help(self) -> TextApiResponse:
        """
        .. raw:: html

          <p>Get CAT help.</p>
          <p>Get help for the CAT APIs.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/cat.html>`_
        """
        __path_parts: t.Dict[str, str] = {}
        __path = "/_cat"
        __query: t.Dict[str, t.Any] = {}
        __headers = {"accept": "text/plain"}
        return self.perform_request(  # type: ignore[return-value]
            "GET",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="cat.help",
            path_parts=__path_parts,
        )

    @_rewrite_parameters()
    def indices(
        self,
        *,
        index: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        bytes: t.Optional[
            t.Union[str, t.Literal["b", "gb", "kb", "mb", "pb", "tb"]]
        ] = None,
        error_trace: t.Optional[bool] = None,
        expand_wildcards: t.Optional[
            t.Union[
                t.Sequence[
                    t.Union[str, t.Literal["all", "closed", "hidden", "none", "open"]]
                ],
                t.Union[str, t.Literal["all", "closed", "hidden", "none", "open"]],
            ]
        ] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        format: t.Optional[str] = None,
        h: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        health: t.Optional[t.Union[str, t.Literal["green", "red", "yellow"]]] = None,
        help: t.Optional[bool] = None,
        human: t.Optional[bool] = None,
        include_unloaded_segments: t.Optional[bool] = None,
        master_timeout: t.Optional[t.Union[str, t.Literal[-1], t.Literal[0]]] = None,
        pretty: t.Optional[bool] = None,
        pri: t.Optional[bool] = None,
        s: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        time: t.Optional[
            t.Union[str, t.Literal["d", "h", "m", "micros", "ms", "nanos", "s"]]
        ] = None,
        v: t.Optional[bool] = None,
    ) -> t.Union[ObjectApiResponse[t.Any], TextApiResponse]:
        """
        .. raw:: html

          <p>Get index information.</p>
          <p>Get high-level information about indices in a cluster, including backing indices for data streams.</p>
          <p>Use this request to get the following information for each index in a cluster:</p>
          <ul>
          <li>shard count</li>
          <li>document count</li>
          <li>deleted document count</li>
          <li>primary store size</li>
          <li>total store size of all shards, including shard replicas</li>
          </ul>
          <p>These metrics are retrieved directly from Lucene, which Elasticsearch uses internally to power indexing and search. As a result, all document counts include hidden nested documents.
          To get an accurate count of Elasticsearch documents, use the cat count or count APIs.</p>
          <p>CAT APIs are only intended for human consumption using the command line or Kibana console.
          They are not intended for use by applications. For application consumption, use an index endpoint.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/cat-indices.html>`_

        :param index: Comma-separated list of data streams, indices, and aliases used
            to limit the request. Supports wildcards (`*`). To target all data streams
            and indices, omit this parameter or use `*` or `_all`.
        :param bytes: The unit used to display byte values.
        :param expand_wildcards: The type of index that wildcard patterns can match.
        :param format: Specifies the format to return the columnar data in, can be set
            to `text`, `json`, `cbor`, `yaml`, or `smile`.
        :param h: List of columns to appear in the response. Supports simple wildcards.
        :param health: The health status used to limit returned indices. By default,
            the response includes indices of any health status.
        :param help: When set to `true` will output available columns. This option can't
            be combined with any other query string option.
        :param include_unloaded_segments: If true, the response includes information
            from segments that are not loaded into memory.
        :param master_timeout: Period to wait for a connection to the master node.
        :param pri: If true, the response only includes information from primary shards.
        :param s: List of columns that determine how the table should be sorted. Sorting
            defaults to ascending and can be changed by setting `:asc` or `:desc` as
            a suffix to the column name.
        :param time: The unit used to display time values.
        :param v: When set to `true` will enable verbose output.
        """
        __path_parts: t.Dict[str, str]
        if index not in SKIP_IN_PATH:
            __path_parts = {"index": _quote(index)}
            __path = f'/_cat/indices/{__path_parts["index"]}'
        else:
            __path_parts = {}
            __path = "/_cat/indices"
        __query: t.Dict[str, t.Any] = {}
        if bytes is not None:
            __query["bytes"] = bytes
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if expand_wildcards is not None:
            __query["expand_wildcards"] = expand_wildcards
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if format is not None:
            __query["format"] = format
        if h is not None:
            __query["h"] = h
        if health is not None:
            __query["health"] = health
        if help is not None:
            __query["help"] = help
        if human is not None:
            __query["human"] = human
        if include_unloaded_segments is not None:
            __query["include_unloaded_segments"] = include_unloaded_segments
        if master_timeout is not None:
            __query["master_timeout"] = master_timeout
        if pretty is not None:
            __query["pretty"] = pretty
        if pri is not None:
            __query["pri"] = pri
        if s is not None:
            __query["s"] = s
        if time is not None:
            __query["time"] = time
        if v is not None:
            __query["v"] = v
        __headers = {"accept": "text/plain,application/json"}
        return self.perform_request(  # type: ignore[return-value]
            "GET",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="cat.indices",
            path_parts=__path_parts,
        )

    @_rewrite_parameters()
    def master(
        self,
        *,
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        format: t.Optional[str] = None,
        h: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        help: t.Optional[bool] = None,
        human: t.Optional[bool] = None,
        local: t.Optional[bool] = None,
        master_timeout: t.Optional[t.Union[str, t.Literal[-1], t.Literal[0]]] = None,
        pretty: t.Optional[bool] = None,
        s: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        v: t.Optional[bool] = None,
    ) -> t.Union[ObjectApiResponse[t.Any], TextApiResponse]:
        """
        .. raw:: html

          <p>Get master node information.</p>
          <p>Get information about the master node, including the ID, bound IP address, and name.</p>
          <p>IMPORTANT: cat APIs are only intended for human consumption using the command line or Kibana console. They are not intended for use by applications. For application consumption, use the nodes info API.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/cat-master.html>`_

        :param format: Specifies the format to return the columnar data in, can be set
            to `text`, `json`, `cbor`, `yaml`, or `smile`.
        :param h: List of columns to appear in the response. Supports simple wildcards.
        :param help: When set to `true` will output available columns. This option can't
            be combined with any other query string option.
        :param local: If `true`, the request computes the list of selected nodes from
            the local cluster state. If `false` the list of selected nodes are computed
            from the cluster state of the master node. In both cases the coordinating
            node will send requests for further information to each selected node.
        :param master_timeout: Period to wait for a connection to the master node.
        :param s: List of columns that determine how the table should be sorted. Sorting
            defaults to ascending and can be changed by setting `:asc` or `:desc` as
            a suffix to the column name.
        :param v: When set to `true` will enable verbose output.
        """
        __path_parts: t.Dict[str, str] = {}
        __path = "/_cat/master"
        __query: t.Dict[str, t.Any] = {}
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if format is not None:
            __query["format"] = format
        if h is not None:
            __query["h"] = h
        if help is not None:
            __query["help"] = help
        if human is not None:
            __query["human"] = human
        if local is not None:
            __query["local"] = local
        if master_timeout is not None:
            __query["master_timeout"] = master_timeout
        if pretty is not None:
            __query["pretty"] = pretty
        if s is not None:
            __query["s"] = s
        if v is not None:
            __query["v"] = v
        __headers = {"accept": "text/plain,application/json"}
        return self.perform_request(  # type: ignore[return-value]
            "GET",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="cat.master",
            path_parts=__path_parts,
        )

    @_rewrite_parameters()
    def ml_data_frame_analytics(
        self,
        *,
        id: t.Optional[str] = None,
        allow_no_match: t.Optional[bool] = None,
        bytes: t.Optional[
            t.Union[str, t.Literal["b", "gb", "kb", "mb", "pb", "tb"]]
        ] = None,
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        format: t.Optional[str] = None,
        h: t.Optional[
            t.Union[
                t.Sequence[
                    t.Union[
                        str,
                        t.Literal[
                            "assignment_explanation",
                            "create_time",
                            "description",
                            "dest_index",
                            "failure_reason",
                            "id",
                            "model_memory_limit",
                            "node.address",
                            "node.ephemeral_id",
                            "node.id",
                            "node.name",
                            "progress",
                            "source_index",
                            "state",
                            "type",
                            "version",
                        ],
                    ]
                ],
                t.Union[
                    str,
                    t.Literal[
                        "assignment_explanation",
                        "create_time",
                        "description",
                        "dest_index",
                        "failure_reason",
                        "id",
                        "model_memory_limit",
                        "node.address",
                        "node.ephemeral_id",
                        "node.id",
                        "node.name",
                        "progress",
                        "source_index",
                        "state",
                        "type",
                        "version",
                    ],
                ],
            ]
        ] = None,
        help: t.Optional[bool] = None,
        human: t.Optional[bool] = None,
        pretty: t.Optional[bool] = None,
        s: t.Optional[
            t.Union[
                t.Sequence[
                    t.Union[
                        str,
                        t.Literal[
                            "assignment_explanation",
                            "create_time",
                            "description",
                            "dest_index",
                            "failure_reason",
                            "id",
                            "model_memory_limit",
                            "node.address",
                            "node.ephemeral_id",
                            "node.id",
                            "node.name",
                            "progress",
                            "source_index",
                            "state",
                            "type",
                            "version",
                        ],
                    ]
                ],
                t.Union[
                    str,
                    t.Literal[
                        "assignment_explanation",
                        "create_time",
                        "description",
                        "dest_index",
                        "failure_reason",
                        "id",
                        "model_memory_limit",
                        "node.address",
                        "node.ephemeral_id",
                        "node.id",
                        "node.name",
                        "progress",
                        "source_index",
                        "state",
                        "type",
                        "version",
                    ],
                ],
            ]
        ] = None,
        time: t.Optional[
            t.Union[str, t.Literal["d", "h", "m", "micros", "ms", "nanos", "s"]]
        ] = None,
        v: t.Optional[bool] = None,
    ) -> t.Union[ObjectApiResponse[t.Any], TextApiResponse]:
        """
        .. raw:: html

          <p>Get data frame analytics jobs.</p>
          <p>Get configuration and usage information about data frame analytics jobs.</p>
          <p>IMPORTANT: CAT APIs are only intended for human consumption using the Kibana
          console or command line. They are not intended for use by applications. For
          application consumption, use the get data frame analytics jobs statistics API.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/cat-dfanalytics.html>`_

        :param id: The ID of the data frame analytics to fetch
        :param allow_no_match: Whether to ignore if a wildcard expression matches no
            configs. (This includes `_all` string or when no configs have been specified)
        :param bytes: The unit in which to display byte values
        :param format: Specifies the format to return the columnar data in, can be set
            to `text`, `json`, `cbor`, `yaml`, or `smile`.
        :param h: Comma-separated list of column names to display.
        :param help: When set to `true` will output available columns. This option can't
            be combined with any other query string option.
        :param s: Comma-separated list of column names or column aliases used to sort
            the response.
        :param time: Unit used to display time values.
        :param v: When set to `true` will enable verbose output.
        """
        __path_parts: t.Dict[str, str]
        if id not in SKIP_IN_PATH:
            __path_parts = {"id": _quote(id)}
            __path = f'/_cat/ml/data_frame/analytics/{__path_parts["id"]}'
        else:
            __path_parts = {}
            __path = "/_cat/ml/data_frame/analytics"
        __query: t.Dict[str, t.Any] = {}
        if allow_no_match is not None:
            __query["allow_no_match"] = allow_no_match
        if bytes is not None:
            __query["bytes"] = bytes
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if format is not None:
            __query["format"] = format
        if h is not None:
            __query["h"] = h
        if help is not None:
            __query["help"] = help
        if human is not None:
            __query["human"] = human
        if pretty is not None:
            __query["pretty"] = pretty
        if s is not None:
            __query["s"] = s
        if time is not None:
            __query["time"] = time
        if v is not None:
            __query["v"] = v
        __headers = {"accept": "text/plain,application/json"}
        return self.perform_request(  # type: ignore[return-value]
            "GET",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="cat.ml_data_frame_analytics",
            path_parts=__path_parts,
        )

    @_rewrite_parameters()
    def ml_datafeeds(
        self,
        *,
        datafeed_id: t.Optional[str] = None,
        allow_no_match: t.Optional[bool] = None,
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        format: t.Optional[str] = None,
        h: t.Optional[
            t.Union[
                t.Sequence[
                    t.Union[
                        str,
                        t.Literal[
                            "ae",
                            "bc",
                            "id",
                            "na",
                            "ne",
                            "ni",
                            "nn",
                            "s",
                            "sba",
                            "sc",
                            "seah",
                            "st",
                        ],
                    ]
                ],
                t.Union[
                    str,
                    t.Literal[
                        "ae",
                        "bc",
                        "id",
                        "na",
                        "ne",
                        "ni",
                        "nn",
                        "s",
                        "sba",
                        "sc",
                        "seah",
                        "st",
                    ],
                ],
            ]
        ] = None,
        help: t.Optional[bool] = None,
        human: t.Optional[bool] = None,
        pretty: t.Optional[bool] = None,
        s: t.Optional[
            t.Union[
                t.Sequence[
                    t.Union[
                        str,
                        t.Literal[
                            "ae",
                            "bc",
                            "id",
                            "na",
                            "ne",
                            "ni",
                            "nn",
                            "s",
                            "sba",
                            "sc",
                            "seah",
                            "st",
                        ],
                    ]
                ],
                t.Union[
                    str,
                    t.Literal[
                        "ae",
                        "bc",
                        "id",
                        "na",
                        "ne",
                        "ni",
                        "nn",
                        "s",
                        "sba",
                        "sc",
                        "seah",
                        "st",
                    ],
                ],
            ]
        ] = None,
        time: t.Optional[
            t.Union[str, t.Literal["d", "h", "m", "micros", "ms", "nanos", "s"]]
        ] = None,
        v: t.Optional[bool] = None,
    ) -> t.Union[ObjectApiResponse[t.Any], TextApiResponse]:
        """
        .. raw:: html

          <p>Get datafeeds.</p>
          <p>Get configuration and usage information about datafeeds.
          This API returns a maximum of 10,000 datafeeds.
          If the Elasticsearch security features are enabled, you must have <code>monitor_ml</code>, <code>monitor</code>, <code>manage_ml</code>, or <code>manage</code>
          cluster privileges to use this API.</p>
          <p>IMPORTANT: CAT APIs are only intended for human consumption using the Kibana
          console or command line. They are not intended for use by applications. For
          application consumption, use the get datafeed statistics API.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/cat-datafeeds.html>`_

        :param datafeed_id: A numerical character string that uniquely identifies the
            datafeed.
        :param allow_no_match: Specifies what to do when the request: * Contains wildcard
            expressions and there are no datafeeds that match. * Contains the `_all`
            string or no identifiers and there are no matches. * Contains wildcard expressions
            and there are only partial matches. If `true`, the API returns an empty datafeeds
            array when there are no matches and the subset of results when there are
            partial matches. If `false`, the API returns a 404 status code when there
            are no matches or only partial matches.
        :param format: Specifies the format to return the columnar data in, can be set
            to `text`, `json`, `cbor`, `yaml`, or `smile`.
        :param h: Comma-separated list of column names to display.
        :param help: When set to `true` will output available columns. This option can't
            be combined with any other query string option.
        :param s: Comma-separated list of column names or column aliases used to sort
            the response.
        :param time: The unit used to display time values.
        :param v: When set to `true` will enable verbose output.
        """
        __path_parts: t.Dict[str, str]
        if datafeed_id not in SKIP_IN_PATH:
            __path_parts = {"datafeed_id": _quote(datafeed_id)}
            __path = f'/_cat/ml/datafeeds/{__path_parts["datafeed_id"]}'
        else:
            __path_parts = {}
            __path = "/_cat/ml/datafeeds"
        __query: t.Dict[str, t.Any] = {}
        if allow_no_match is not None:
            __query["allow_no_match"] = allow_no_match
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if format is not None:
            __query["format"] = format
        if h is not None:
            __query["h"] = h
        if help is not None:
            __query["help"] = help
        if human is not None:
            __query["human"] = human
        if pretty is not None:
            __query["pretty"] = pretty
        if s is not None:
            __query["s"] = s
        if time is not None:
            __query["time"] = time
        if v is not None:
            __query["v"] = v
        __headers = {"accept": "text/plain,application/json"}
        return self.perform_request(  # type: ignore[return-value]
            "GET",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="cat.ml_datafeeds",
            path_parts=__path_parts,
        )

    @_rewrite_parameters()
    def ml_jobs(
        self,
        *,
        job_id: t.Optional[str] = None,
        allow_no_match: t.Optional[bool] = None,
        bytes: t.Optional[
            t.Union[str, t.Literal["b", "gb", "kb", "mb", "pb", "tb"]]
        ] = None,
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        format: t.Optional[str] = None,
        h: t.Optional[
            t.Union[
                t.Sequence[
                    t.Union[
                        str,
                        t.Literal[
                            "assignment_explanation",
                            "buckets.count",
                            "buckets.time.exp_avg",
                            "buckets.time.exp_avg_hour",
                            "buckets.time.max",
                            "buckets.time.min",
                            "buckets.time.total",
                            "data.buckets",
                            "data.earliest_record",
                            "data.empty_buckets",
                            "data.input_bytes",
                            "data.input_fields",
                            "data.input_records",
                            "data.invalid_dates",
                            "data.last",
                            "data.last_empty_bucket",
                            "data.last_sparse_bucket",
                            "data.latest_record",
                            "data.missing_fields",
                            "data.out_of_order_timestamps",
                            "data.processed_fields",
                            "data.processed_records",
                            "data.sparse_buckets",
                            "forecasts.memory.avg",
                            "forecasts.memory.max",
                            "forecasts.memory.min",
                            "forecasts.memory.total",
                            "forecasts.records.avg",
                            "forecasts.records.max",
                            "forecasts.records.min",
                            "forecasts.records.total",
                            "forecasts.time.avg",
                            "forecasts.time.max",
                            "forecasts.time.min",
                            "forecasts.time.total",
                            "forecasts.total",
                            "id",
                            "model.bucket_allocation_failures",
                            "model.by_fields",
                            "model.bytes",
                            "model.bytes_exceeded",
                            "model.categorization_status",
                            "model.categorized_doc_count",
                            "model.dead_category_count",
                            "model.failed_category_count",
                            "model.frequent_category_count",
                            "model.log_time",
                            "model.memory_limit",
                            "model.memory_status",
                            "model.over_fields",
                            "model.partition_fields",
                            "model.rare_category_count",
                            "model.timestamp",
                            "model.total_category_count",
                            "node.address",
                            "node.ephemeral_id",
                            "node.id",
                            "node.name",
                            "opened_time",
                            "state",
                        ],
                    ]
                ],
                t.Union[
                    str,
                    t.Literal[
                        "assignment_explanation",
                        "buckets.count",
                        "buckets.time.exp_avg",
                        "buckets.time.exp_avg_hour",
                        "buckets.time.max",
                        "buckets.time.min",
                        "buckets.time.total",
                        "data.buckets",
                        "data.earliest_record",
                        "data.empty_buckets",
                        "data.input_bytes",
                        "data.input_fields",
                        "data.input_records",
                        "data.invalid_dates",
                        "data.last",
                        "data.last_empty_bucket",
                        "data.last_sparse_bucket",
                        "data.latest_record",
                        "data.missing_fields",
                        "data.out_of_order_timestamps",
                        "data.processed_fields",
                        "data.processed_records",
                        "data.sparse_buckets",
                        "forecasts.memory.avg",
                        "forecasts.memory.max",
                        "forecasts.memory.min",
                        "forecasts.memory.total",
                        "forecasts.records.avg",
                        "forecasts.records.max",
                        "forecasts.records.min",
                        "forecasts.records.total",
                        "forecasts.time.avg",
                        "forecasts.time.max",
                        "forecasts.time.min",
                        "forecasts.time.total",
                        "forecasts.total",
                        "id",
                        "model.bucket_allocation_failures",
                        "model.by_fields",
                        "model.bytes",
                        "model.bytes_exceeded",
                        "model.categorization_status",
                        "model.categorized_doc_count",
                        "model.dead_category_count",
                        "model.failed_category_count",
                        "model.frequent_category_count",
                        "model.log_time",
                        "model.memory_limit",
                        "model.memory_status",
                        "model.over_fields",
                        "model.partition_fields",
                        "model.rare_category_count",
                        "model.timestamp",
                        "model.total_category_count",
                        "node.address",
                        "node.ephemeral_id",
                        "node.id",
                        "node.name",
                        "opened_time",
                        "state",
                    ],
                ],
            ]
        ] = None,
        help: t.Optional[bool] = None,
        human: t.Optional[bool] = None,
        pretty: t.Optional[bool] = None,
        s: t.Optional[
            t.Union[
                t.Sequence[
                    t.Union[
                        str,
                        t.Literal[
                            "assignment_explanation",
                            "buckets.count",
                            "buckets.time.exp_avg",
                            "buckets.time.exp_avg_hour",
                            "buckets.time.max",
                            "buckets.time.min",
                            "buckets.time.total",
                            "data.buckets",
                            "data.earliest_record",
                            "data.empty_buckets",
                            "data.input_bytes",
                            "data.input_fields",
                            "data.input_records",
                            "data.invalid_dates",
                            "data.last",
                            "data.last_empty_bucket",
                            "data.last_sparse_bucket",
                            "data.latest_record",
                            "data.missing_fields",
                            "data.out_of_order_timestamps",
                            "data.processed_fields",
                            "data.processed_records",
                            "data.sparse_buckets",
                            "forecasts.memory.avg",
                            "forecasts.memory.max",
                            "forecasts.memory.min",
                            "forecasts.memory.total",
                            "forecasts.records.avg",
                            "forecasts.records.max",
                            "forecasts.records.min",
                            "forecasts.records.total",
                            "forecasts.time.avg",
                            "forecasts.time.max",
                            "forecasts.time.min",
                            "forecasts.time.total",
                            "forecasts.total",
                            "id",
                            "model.bucket_allocation_failures",
                            "model.by_fields",
                            "model.bytes",
                            "model.bytes_exceeded",
                            "model.categorization_status",
                            "model.categorized_doc_count",
                            "model.dead_category_count",
                            "model.failed_category_count",
                            "model.frequent_category_count",
                            "model.log_time",
                            "model.memory_limit",
                            "model.memory_status",
                            "model.over_fields",
                            "model.partition_fields",
                            "model.rare_category_count",
                            "model.timestamp",
                            "model.total_category_count",
                            "node.address",
                            "node.ephemeral_id",
                            "node.id",
                            "node.name",
                            "opened_time",
                            "state",
                        ],
                    ]
                ],
                t.Union[
                    str,
                    t.Literal[
                        "assignment_explanation",
                        "buckets.count",
                        "buckets.time.exp_avg",
                        "buckets.time.exp_avg_hour",
                        "buckets.time.max",
                        "buckets.time.min",
                        "buckets.time.total",
                        "data.buckets",
                        "data.earliest_record",
                        "data.empty_buckets",
                        "data.input_bytes",
                        "data.input_fields",
                        "data.input_records",
                        "data.invalid_dates",
                        "data.last",
                        "data.last_empty_bucket",
                        "data.last_sparse_bucket",
                        "data.latest_record",
                        "data.missing_fields",
                        "data.out_of_order_timestamps",
                        "data.processed_fields",
                        "data.processed_records",
                        "data.sparse_buckets",
                        "forecasts.memory.avg",
                        "forecasts.memory.max",
                        "forecasts.memory.min",
                        "forecasts.memory.total",
                        "forecasts.records.avg",
                        "forecasts.records.max",
                        "forecasts.records.min",
                        "forecasts.records.total",
                        "forecasts.time.avg",
                        "forecasts.time.max",
                        "forecasts.time.min",
                        "forecasts.time.total",
                        "forecasts.total",
                        "id",
                        "model.bucket_allocation_failures",
                        "model.by_fields",
                        "model.bytes",
                        "model.bytes_exceeded",
                        "model.categorization_status",
                        "model.categorized_doc_count",
                        "model.dead_category_count",
                        "model.failed_category_count",
                        "model.frequent_category_count",
                        "model.log_time",
                        "model.memory_limit",
                        "model.memory_status",
                        "model.over_fields",
                        "model.partition_fields",
                        "model.rare_category_count",
                        "model.timestamp",
                        "model.total_category_count",
                        "node.address",
                        "node.ephemeral_id",
                        "node.id",
                        "node.name",
                        "opened_time",
                        "state",
                    ],
                ],
            ]
        ] = None,
        time: t.Optional[
            t.Union[str, t.Literal["d", "h", "m", "micros", "ms", "nanos", "s"]]
        ] = None,
        v: t.Optional[bool] = None,
    ) -> t.Union[ObjectApiResponse[t.Any], TextApiResponse]:
        """
        .. raw:: html

          <p>Get anomaly detection jobs.</p>
          <p>Get configuration and usage information for anomaly detection jobs.
          This API returns a maximum of 10,000 jobs.
          If the Elasticsearch security features are enabled, you must have <code>monitor_ml</code>,
          <code>monitor</code>, <code>manage_ml</code>, or <code>manage</code> cluster privileges to use this API.</p>
          <p>IMPORTANT: CAT APIs are only intended for human consumption using the Kibana
          console or command line. They are not intended for use by applications. For
          application consumption, use the get anomaly detection job statistics API.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/cat-anomaly-detectors.html>`_

        :param job_id: Identifier for the anomaly detection job.
        :param allow_no_match: Specifies what to do when the request: * Contains wildcard
            expressions and there are no jobs that match. * Contains the `_all` string
            or no identifiers and there are no matches. * Contains wildcard expressions
            and there are only partial matches. If `true`, the API returns an empty jobs
            array when there are no matches and the subset of results when there are
            partial matches. If `false`, the API returns a 404 status code when there
            are no matches or only partial matches.
        :param bytes: The unit used to display byte values.
        :param format: Specifies the format to return the columnar data in, can be set
            to `text`, `json`, `cbor`, `yaml`, or `smile`.
        :param h: Comma-separated list of column names to display.
        :param help: When set to `true` will output available columns. This option can't
            be combined with any other query string option.
        :param s: Comma-separated list of column names or column aliases used to sort
            the response.
        :param time: The unit used to display time values.
        :param v: When set to `true` will enable verbose output.
        """
        __path_parts: t.Dict[str, str]
        if job_id not in SKIP_IN_PATH:
            __path_parts = {"job_id": _quote(job_id)}
            __path = f'/_cat/ml/anomaly_detectors/{__path_parts["job_id"]}'
        else:
            __path_parts = {}
            __path = "/_cat/ml/anomaly_detectors"
        __query: t.Dict[str, t.Any] = {}
        if allow_no_match is not None:
            __query["allow_no_match"] = allow_no_match
        if bytes is not None:
            __query["bytes"] = bytes
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if format is not None:
            __query["format"] = format
        if h is not None:
            __query["h"] = h
        if help is not None:
            __query["help"] = help
        if human is not None:
            __query["human"] = human
        if pretty is not None:
            __query["pretty"] = pretty
        if s is not None:
            __query["s"] = s
        if time is not None:
            __query["time"] = time
        if v is not None:
            __query["v"] = v
        __headers = {"accept": "text/plain,application/json"}
        return self.perform_request(  # type: ignore[return-value]
            "GET",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="cat.ml_jobs",
            path_parts=__path_parts,
        )

    @_rewrite_parameters(
        parameter_aliases={"from": "from_"},
    )
    def ml_trained_models(
        self,
        *,
        model_id: t.Optional[str] = None,
        allow_no_match: t.Optional[bool] = None,
        bytes: t.Optional[
            t.Union[str, t.Literal["b", "gb", "kb", "mb", "pb", "tb"]]
        ] = None,
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        format: t.Optional[str] = None,
        from_: t.Optional[int] = None,
        h: t.Optional[
            t.Union[
                t.Sequence[
                    t.Union[
                        str,
                        t.Literal[
                            "create_time",
                            "created_by",
                            "data_frame_analytics_id",
                            "description",
                            "heap_size",
                            "id",
                            "ingest.count",
                            "ingest.current",
                            "ingest.failed",
                            "ingest.pipelines",
                            "ingest.time",
                            "license",
                            "operations",
                            "version",
                        ],
                    ]
                ],
                t.Union[
                    str,
                    t.Literal[
                        "create_time",
                        "created_by",
                        "data_frame_analytics_id",
                        "description",
                        "heap_size",
                        "id",
                        "ingest.count",
                        "ingest.current",
                        "ingest.failed",
                        "ingest.pipelines",
                        "ingest.time",
                        "license",
                        "operations",
                        "version",
                    ],
                ],
            ]
        ] = None,
        help: t.Optional[bool] = None,
        human: t.Optional[bool] = None,
        pretty: t.Optional[bool] = None,
        s: t.Optional[
            t.Union[
                t.Sequence[
                    t.Union[
                        str,
                        t.Literal[
                            "create_time",
                            "created_by",
                            "data_frame_analytics_id",
                            "description",
                            "heap_size",
                            "id",
                            "ingest.count",
                            "ingest.current",
                            "ingest.failed",
                            "ingest.pipelines",
                            "ingest.time",
                            "license",
                            "operations",
                            "version",
                        ],
                    ]
                ],
                t.Union[
                    str,
                    t.Literal[
                        "create_time",
                        "created_by",
                        "data_frame_analytics_id",
                        "description",
                        "heap_size",
                        "id",
                        "ingest.count",
                        "ingest.current",
                        "ingest.failed",
                        "ingest.pipelines",
                        "ingest.time",
                        "license",
                        "operations",
                        "version",
                    ],
                ],
            ]
        ] = None,
        size: t.Optional[int] = None,
        time: t.Optional[
            t.Union[str, t.Literal["d", "h", "m", "micros", "ms", "nanos", "s"]]
        ] = None,
        v: t.Optional[bool] = None,
    ) -> t.Union[ObjectApiResponse[t.Any], TextApiResponse]:
        """
        .. raw:: html

          <p>Get trained models.</p>
          <p>Get configuration and usage information about inference trained models.</p>
          <p>IMPORTANT: CAT APIs are only intended for human consumption using the Kibana
          console or command line. They are not intended for use by applications. For
          application consumption, use the get trained models statistics API.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/cat-trained-model.html>`_

        :param model_id: A unique identifier for the trained model.
        :param allow_no_match: Specifies what to do when the request: contains wildcard
            expressions and there are no models that match; contains the `_all` string
            or no identifiers and there are no matches; contains wildcard expressions
            and there are only partial matches. If `true`, the API returns an empty array
            when there are no matches and the subset of results when there are partial
            matches. If `false`, the API returns a 404 status code when there are no
            matches or only partial matches.
        :param bytes: The unit used to display byte values.
        :param format: Specifies the format to return the columnar data in, can be set
            to `text`, `json`, `cbor`, `yaml`, or `smile`.
        :param from_: Skips the specified number of transforms.
        :param h: A comma-separated list of column names to display.
        :param help: When set to `true` will output available columns. This option can't
            be combined with any other query string option.
        :param s: A comma-separated list of column names or aliases used to sort the
            response.
        :param size: The maximum number of transforms to display.
        :param time: Unit used to display time values.
        :param v: When set to `true` will enable verbose output.
        """
        __path_parts: t.Dict[str, str]
        if model_id not in SKIP_IN_PATH:
            __path_parts = {"model_id": _quote(model_id)}
            __path = f'/_cat/ml/trained_models/{__path_parts["model_id"]}'
        else:
            __path_parts = {}
            __path = "/_cat/ml/trained_models"
        __query: t.Dict[str, t.Any] = {}
        if allow_no_match is not None:
            __query["allow_no_match"] = allow_no_match
        if bytes is not None:
            __query["bytes"] = bytes
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if format is not None:
            __query["format"] = format
        if from_ is not None:
            __query["from"] = from_
        if h is not None:
            __query["h"] = h
        if help is not None:
            __query["help"] = help
        if human is not None:
            __query["human"] = human
        if pretty is not None:
            __query["pretty"] = pretty
        if s is not None:
            __query["s"] = s
        if size is not None:
            __query["size"] = size
        if time is not None:
            __query["time"] = time
        if v is not None:
            __query["v"] = v
        __headers = {"accept": "text/plain,application/json"}
        return self.perform_request(  # type: ignore[return-value]
            "GET",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="cat.ml_trained_models",
            path_parts=__path_parts,
        )

    @_rewrite_parameters()
    def nodeattrs(
        self,
        *,
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        format: t.Optional[str] = None,
        h: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        help: t.Optional[bool] = None,
        human: t.Optional[bool] = None,
        local: t.Optional[bool] = None,
        master_timeout: t.Optional[t.Union[str, t.Literal[-1], t.Literal[0]]] = None,
        pretty: t.Optional[bool] = None,
        s: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        v: t.Optional[bool] = None,
    ) -> t.Union[ObjectApiResponse[t.Any], TextApiResponse]:
        """
        .. raw:: html

          <p>Get node attribute information.</p>
          <p>Get information about custom node attributes.
          IMPORTANT: cat APIs are only intended for human consumption using the command line or Kibana console. They are not intended for use by applications. For application consumption, use the nodes info API.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/cat-nodeattrs.html>`_

        :param format: Specifies the format to return the columnar data in, can be set
            to `text`, `json`, `cbor`, `yaml`, or `smile`.
        :param h: List of columns to appear in the response. Supports simple wildcards.
        :param help: When set to `true` will output available columns. This option can't
            be combined with any other query string option.
        :param local: If `true`, the request computes the list of selected nodes from
            the local cluster state. If `false` the list of selected nodes are computed
            from the cluster state of the master node. In both cases the coordinating
            node will send requests for further information to each selected node.
        :param master_timeout: Period to wait for a connection to the master node.
        :param s: List of columns that determine how the table should be sorted. Sorting
            defaults to ascending and can be changed by setting `:asc` or `:desc` as
            a suffix to the column name.
        :param v: When set to `true` will enable verbose output.
        """
        __path_parts: t.Dict[str, str] = {}
        __path = "/_cat/nodeattrs"
        __query: t.Dict[str, t.Any] = {}
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if format is not None:
            __query["format"] = format
        if h is not None:
            __query["h"] = h
        if help is not None:
            __query["help"] = help
        if human is not None:
            __query["human"] = human
        if local is not None:
            __query["local"] = local
        if master_timeout is not None:
            __query["master_timeout"] = master_timeout
        if pretty is not None:
            __query["pretty"] = pretty
        if s is not None:
            __query["s"] = s
        if v is not None:
            __query["v"] = v
        __headers = {"accept": "text/plain,application/json"}
        return self.perform_request(  # type: ignore[return-value]
            "GET",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="cat.nodeattrs",
            path_parts=__path_parts,
        )

    @_rewrite_parameters()
    def nodes(
        self,
        *,
        bytes: t.Optional[
            t.Union[str, t.Literal["b", "gb", "kb", "mb", "pb", "tb"]]
        ] = None,
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        format: t.Optional[str] = None,
        full_id: t.Optional[t.Union[bool, str]] = None,
        h: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        help: t.Optional[bool] = None,
        human: t.Optional[bool] = None,
        include_unloaded_segments: t.Optional[bool] = None,
        master_timeout: t.Optional[t.Union[str, t.Literal[-1], t.Literal[0]]] = None,
        pretty: t.Optional[bool] = None,
        s: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        time: t.Optional[
            t.Union[str, t.Literal["d", "h", "m", "micros", "ms", "nanos", "s"]]
        ] = None,
        v: t.Optional[bool] = None,
    ) -> t.Union[ObjectApiResponse[t.Any], TextApiResponse]:
        """
        .. raw:: html

          <p>Get node information.</p>
          <p>Get information about the nodes in a cluster.
          IMPORTANT: cat APIs are only intended for human consumption using the command line or Kibana console. They are not intended for use by applications. For application consumption, use the nodes info API.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/cat-nodes.html>`_

        :param bytes: The unit used to display byte values.
        :param format: Specifies the format to return the columnar data in, can be set
            to `text`, `json`, `cbor`, `yaml`, or `smile`.
        :param full_id: If `true`, return the full node ID. If `false`, return the shortened
            node ID.
        :param h: List of columns to appear in the response. Supports simple wildcards.
        :param help: When set to `true` will output available columns. This option can't
            be combined with any other query string option.
        :param include_unloaded_segments: If true, the response includes information
            from segments that are not loaded into memory.
        :param master_timeout: Period to wait for a connection to the master node.
        :param s: List of columns that determine how the table should be sorted. Sorting
            defaults to ascending and can be changed by setting `:asc` or `:desc` as
            a suffix to the column name.
        :param time: Unit used to display time values.
        :param v: When set to `true` will enable verbose output.
        """
        __path_parts: t.Dict[str, str] = {}
        __path = "/_cat/nodes"
        __query: t.Dict[str, t.Any] = {}
        if bytes is not None:
            __query["bytes"] = bytes
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if format is not None:
            __query["format"] = format
        if full_id is not None:
            __query["full_id"] = full_id
        if h is not None:
            __query["h"] = h
        if help is not None:
            __query["help"] = help
        if human is not None:
            __query["human"] = human
        if include_unloaded_segments is not None:
            __query["include_unloaded_segments"] = include_unloaded_segments
        if master_timeout is not None:
            __query["master_timeout"] = master_timeout
        if pretty is not None:
            __query["pretty"] = pretty
        if s is not None:
            __query["s"] = s
        if time is not None:
            __query["time"] = time
        if v is not None:
            __query["v"] = v
        __headers = {"accept": "text/plain,application/json"}
        return self.perform_request(  # type: ignore[return-value]
            "GET",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="cat.nodes",
            path_parts=__path_parts,
        )

    @_rewrite_parameters()
    def pending_tasks(
        self,
        *,
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        format: t.Optional[str] = None,
        h: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        help: t.Optional[bool] = None,
        human: t.Optional[bool] = None,
        local: t.Optional[bool] = None,
        master_timeout: t.Optional[t.Union[str, t.Literal[-1], t.Literal[0]]] = None,
        pretty: t.Optional[bool] = None,
        s: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        time: t.Optional[
            t.Union[str, t.Literal["d", "h", "m", "micros", "ms", "nanos", "s"]]
        ] = None,
        v: t.Optional[bool] = None,
    ) -> t.Union[ObjectApiResponse[t.Any], TextApiResponse]:
        """
        .. raw:: html

          <p>Get pending task information.</p>
          <p>Get information about cluster-level changes that have not yet taken effect.
          IMPORTANT: cat APIs are only intended for human consumption using the command line or Kibana console. They are not intended for use by applications. For application consumption, use the pending cluster tasks API.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/cat-pending-tasks.html>`_

        :param format: Specifies the format to return the columnar data in, can be set
            to `text`, `json`, `cbor`, `yaml`, or `smile`.
        :param h: List of columns to appear in the response. Supports simple wildcards.
        :param help: When set to `true` will output available columns. This option can't
            be combined with any other query string option.
        :param local: If `true`, the request computes the list of selected nodes from
            the local cluster state. If `false` the list of selected nodes are computed
            from the cluster state of the master node. In both cases the coordinating
            node will send requests for further information to each selected node.
        :param master_timeout: Period to wait for a connection to the master node.
        :param s: List of columns that determine how the table should be sorted. Sorting
            defaults to ascending and can be changed by setting `:asc` or `:desc` as
            a suffix to the column name.
        :param time: Unit used to display time values.
        :param v: When set to `true` will enable verbose output.
        """
        __path_parts: t.Dict[str, str] = {}
        __path = "/_cat/pending_tasks"
        __query: t.Dict[str, t.Any] = {}
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if format is not None:
            __query["format"] = format
        if h is not None:
            __query["h"] = h
        if help is not None:
            __query["help"] = help
        if human is not None:
            __query["human"] = human
        if local is not None:
            __query["local"] = local
        if master_timeout is not None:
            __query["master_timeout"] = master_timeout
        if pretty is not None:
            __query["pretty"] = pretty
        if s is not None:
            __query["s"] = s
        if time is not None:
            __query["time"] = time
        if v is not None:
            __query["v"] = v
        __headers = {"accept": "text/plain,application/json"}
        return self.perform_request(  # type: ignore[return-value]
            "GET",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="cat.pending_tasks",
            path_parts=__path_parts,
        )

    @_rewrite_parameters()
    def plugins(
        self,
        *,
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        format: t.Optional[str] = None,
        h: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        help: t.Optional[bool] = None,
        human: t.Optional[bool] = None,
        include_bootstrap: t.Optional[bool] = None,
        local: t.Optional[bool] = None,
        master_timeout: t.Optional[t.Union[str, t.Literal[-1], t.Literal[0]]] = None,
        pretty: t.Optional[bool] = None,
        s: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        v: t.Optional[bool] = None,
    ) -> t.Union[ObjectApiResponse[t.Any], TextApiResponse]:
        """
        .. raw:: html

          <p>Get plugin information.</p>
          <p>Get a list of plugins running on each node of a cluster.
          IMPORTANT: cat APIs are only intended for human consumption using the command line or Kibana console. They are not intended for use by applications. For application consumption, use the nodes info API.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/cat-plugins.html>`_

        :param format: Specifies the format to return the columnar data in, can be set
            to `text`, `json`, `cbor`, `yaml`, or `smile`.
        :param h: List of columns to appear in the response. Supports simple wildcards.
        :param help: When set to `true` will output available columns. This option can't
            be combined with any other query string option.
        :param include_bootstrap: Include bootstrap plugins in the response
        :param local: If `true`, the request computes the list of selected nodes from
            the local cluster state. If `false` the list of selected nodes are computed
            from the cluster state of the master node. In both cases the coordinating
            node will send requests for further information to each selected node.
        :param master_timeout: Period to wait for a connection to the master node.
        :param s: List of columns that determine how the table should be sorted. Sorting
            defaults to ascending and can be changed by setting `:asc` or `:desc` as
            a suffix to the column name.
        :param v: When set to `true` will enable verbose output.
        """
        __path_parts: t.Dict[str, str] = {}
        __path = "/_cat/plugins"
        __query: t.Dict[str, t.Any] = {}
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if format is not None:
            __query["format"] = format
        if h is not None:
            __query["h"] = h
        if help is not None:
            __query["help"] = help
        if human is not None:
            __query["human"] = human
        if include_bootstrap is not None:
            __query["include_bootstrap"] = include_bootstrap
        if local is not None:
            __query["local"] = local
        if master_timeout is not None:
            __query["master_timeout"] = master_timeout
        if pretty is not None:
            __query["pretty"] = pretty
        if s is not None:
            __query["s"] = s
        if v is not None:
            __query["v"] = v
        __headers = {"accept": "text/plain,application/json"}
        return self.perform_request(  # type: ignore[return-value]
            "GET",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="cat.plugins",
            path_parts=__path_parts,
        )

    @_rewrite_parameters()
    def recovery(
        self,
        *,
        index: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        active_only: t.Optional[bool] = None,
        bytes: t.Optional[
            t.Union[str, t.Literal["b", "gb", "kb", "mb", "pb", "tb"]]
        ] = None,
        detailed: t.Optional[bool] = None,
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        format: t.Optional[str] = None,
        h: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        help: t.Optional[bool] = None,
        human: t.Optional[bool] = None,
        pretty: t.Optional[bool] = None,
        s: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        time: t.Optional[
            t.Union[str, t.Literal["d", "h", "m", "micros", "ms", "nanos", "s"]]
        ] = None,
        v: t.Optional[bool] = None,
    ) -> t.Union[ObjectApiResponse[t.Any], TextApiResponse]:
        """
        .. raw:: html

          <p>Get shard recovery information.</p>
          <p>Get information about ongoing and completed shard recoveries.
          Shard recovery is the process of initializing a shard copy, such as restoring a primary shard from a snapshot or syncing a replica shard from a primary shard. When a shard recovery completes, the recovered shard is available for search and indexing.
          For data streams, the API returns information about the stream’s backing indices.
          IMPORTANT: cat APIs are only intended for human consumption using the command line or Kibana console. They are not intended for use by applications. For application consumption, use the index recovery API.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/cat-recovery.html>`_

        :param index: A comma-separated list of data streams, indices, and aliases used
            to limit the request. Supports wildcards (`*`). To target all data streams
            and indices, omit this parameter or use `*` or `_all`.
        :param active_only: If `true`, the response only includes ongoing shard recoveries.
        :param bytes: The unit used to display byte values.
        :param detailed: If `true`, the response includes detailed information about
            shard recoveries.
        :param format: Specifies the format to return the columnar data in, can be set
            to `text`, `json`, `cbor`, `yaml`, or `smile`.
        :param h: List of columns to appear in the response. Supports simple wildcards.
        :param help: When set to `true` will output available columns. This option can't
            be combined with any other query string option.
        :param s: List of columns that determine how the table should be sorted. Sorting
            defaults to ascending and can be changed by setting `:asc` or `:desc` as
            a suffix to the column name.
        :param time: Unit used to display time values.
        :param v: When set to `true` will enable verbose output.
        """
        __path_parts: t.Dict[str, str]
        if index not in SKIP_IN_PATH:
            __path_parts = {"index": _quote(index)}
            __path = f'/_cat/recovery/{__path_parts["index"]}'
        else:
            __path_parts = {}
            __path = "/_cat/recovery"
        __query: t.Dict[str, t.Any] = {}
        if active_only is not None:
            __query["active_only"] = active_only
        if bytes is not None:
            __query["bytes"] = bytes
        if detailed is not None:
            __query["detailed"] = detailed
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if format is not None:
            __query["format"] = format
        if h is not None:
            __query["h"] = h
        if help is not None:
            __query["help"] = help
        if human is not None:
            __query["human"] = human
        if pretty is not None:
            __query["pretty"] = pretty
        if s is not None:
            __query["s"] = s
        if time is not None:
            __query["time"] = time
        if v is not None:
            __query["v"] = v
        __headers = {"accept": "text/plain,application/json"}
        return self.perform_request(  # type: ignore[return-value]
            "GET",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="cat.recovery",
            path_parts=__path_parts,
        )

    @_rewrite_parameters()
    def repositories(
        self,
        *,
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        format: t.Optional[str] = None,
        h: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        help: t.Optional[bool] = None,
        human: t.Optional[bool] = None,
        local: t.Optional[bool] = None,
        master_timeout: t.Optional[t.Union[str, t.Literal[-1], t.Literal[0]]] = None,
        pretty: t.Optional[bool] = None,
        s: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        v: t.Optional[bool] = None,
    ) -> t.Union[ObjectApiResponse[t.Any], TextApiResponse]:
        """
        .. raw:: html

          <p>Get snapshot repository information.</p>
          <p>Get a list of snapshot repositories for a cluster.
          IMPORTANT: cat APIs are only intended for human consumption using the command line or Kibana console. They are not intended for use by applications. For application consumption, use the get snapshot repository API.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/cat-repositories.html>`_

        :param format: Specifies the format to return the columnar data in, can be set
            to `text`, `json`, `cbor`, `yaml`, or `smile`.
        :param h: List of columns to appear in the response. Supports simple wildcards.
        :param help: When set to `true` will output available columns. This option can't
            be combined with any other query string option.
        :param local: If `true`, the request computes the list of selected nodes from
            the local cluster state. If `false` the list of selected nodes are computed
            from the cluster state of the master node. In both cases the coordinating
            node will send requests for further information to each selected node.
        :param master_timeout: Period to wait for a connection to the master node.
        :param s: List of columns that determine how the table should be sorted. Sorting
            defaults to ascending and can be changed by setting `:asc` or `:desc` as
            a suffix to the column name.
        :param v: When set to `true` will enable verbose output.
        """
        __path_parts: t.Dict[str, str] = {}
        __path = "/_cat/repositories"
        __query: t.Dict[str, t.Any] = {}
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if format is not None:
            __query["format"] = format
        if h is not None:
            __query["h"] = h
        if help is not None:
            __query["help"] = help
        if human is not None:
            __query["human"] = human
        if local is not None:
            __query["local"] = local
        if master_timeout is not None:
            __query["master_timeout"] = master_timeout
        if pretty is not None:
            __query["pretty"] = pretty
        if s is not None:
            __query["s"] = s
        if v is not None:
            __query["v"] = v
        __headers = {"accept": "text/plain,application/json"}
        return self.perform_request(  # type: ignore[return-value]
            "GET",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="cat.repositories",
            path_parts=__path_parts,
        )

    @_rewrite_parameters()
    def segments(
        self,
        *,
        index: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        bytes: t.Optional[
            t.Union[str, t.Literal["b", "gb", "kb", "mb", "pb", "tb"]]
        ] = None,
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        format: t.Optional[str] = None,
        h: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        help: t.Optional[bool] = None,
        human: t.Optional[bool] = None,
        local: t.Optional[bool] = None,
        master_timeout: t.Optional[t.Union[str, t.Literal[-1], t.Literal[0]]] = None,
        pretty: t.Optional[bool] = None,
        s: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        v: t.Optional[bool] = None,
    ) -> t.Union[ObjectApiResponse[t.Any], TextApiResponse]:
        """
        .. raw:: html

          <p>Get segment information.</p>
          <p>Get low-level information about the Lucene segments in index shards.
          For data streams, the API returns information about the backing indices.
          IMPORTANT: cat APIs are only intended for human consumption using the command line or Kibana console. They are not intended for use by applications. For application consumption, use the index segments API.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/cat-segments.html>`_

        :param index: A comma-separated list of data streams, indices, and aliases used
            to limit the request. Supports wildcards (`*`). To target all data streams
            and indices, omit this parameter or use `*` or `_all`.
        :param bytes: The unit used to display byte values.
        :param format: Specifies the format to return the columnar data in, can be set
            to `text`, `json`, `cbor`, `yaml`, or `smile`.
        :param h: List of columns to appear in the response. Supports simple wildcards.
        :param help: When set to `true` will output available columns. This option can't
            be combined with any other query string option.
        :param local: If `true`, the request computes the list of selected nodes from
            the local cluster state. If `false` the list of selected nodes are computed
            from the cluster state of the master node. In both cases the coordinating
            node will send requests for further information to each selected node.
        :param master_timeout: Period to wait for a connection to the master node.
        :param s: List of columns that determine how the table should be sorted. Sorting
            defaults to ascending and can be changed by setting `:asc` or `:desc` as
            a suffix to the column name.
        :param v: When set to `true` will enable verbose output.
        """
        __path_parts: t.Dict[str, str]
        if index not in SKIP_IN_PATH:
            __path_parts = {"index": _quote(index)}
            __path = f'/_cat/segments/{__path_parts["index"]}'
        else:
            __path_parts = {}
            __path = "/_cat/segments"
        __query: t.Dict[str, t.Any] = {}
        if bytes is not None:
            __query["bytes"] = bytes
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if format is not None:
            __query["format"] = format
        if h is not None:
            __query["h"] = h
        if help is not None:
            __query["help"] = help
        if human is not None:
            __query["human"] = human
        if local is not None:
            __query["local"] = local
        if master_timeout is not None:
            __query["master_timeout"] = master_timeout
        if pretty is not None:
            __query["pretty"] = pretty
        if s is not None:
            __query["s"] = s
        if v is not None:
            __query["v"] = v
        __headers = {"accept": "text/plain,application/json"}
        return self.perform_request(  # type: ignore[return-value]
            "GET",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="cat.segments",
            path_parts=__path_parts,
        )

    @_rewrite_parameters()
    def shards(
        self,
        *,
        index: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        bytes: t.Optional[
            t.Union[str, t.Literal["b", "gb", "kb", "mb", "pb", "tb"]]
        ] = None,
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        format: t.Optional[str] = None,
        h: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        help: t.Optional[bool] = None,
        human: t.Optional[bool] = None,
        master_timeout: t.Optional[t.Union[str, t.Literal[-1], t.Literal[0]]] = None,
        pretty: t.Optional[bool] = None,
        s: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        time: t.Optional[
            t.Union[str, t.Literal["d", "h", "m", "micros", "ms", "nanos", "s"]]
        ] = None,
        v: t.Optional[bool] = None,
    ) -> t.Union[ObjectApiResponse[t.Any], TextApiResponse]:
        """
        .. raw:: html

          <p>Get shard information.</p>
          <p>Get information about the shards in a cluster.
          For data streams, the API returns information about the backing indices.
          IMPORTANT: cat APIs are only intended for human consumption using the command line or Kibana console. They are not intended for use by applications.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/cat-shards.html>`_

        :param index: A comma-separated list of data streams, indices, and aliases used
            to limit the request. Supports wildcards (`*`). To target all data streams
            and indices, omit this parameter or use `*` or `_all`.
        :param bytes: The unit used to display byte values.
        :param format: Specifies the format to return the columnar data in, can be set
            to `text`, `json`, `cbor`, `yaml`, or `smile`.
        :param h: List of columns to appear in the response. Supports simple wildcards.
        :param help: When set to `true` will output available columns. This option can't
            be combined with any other query string option.
        :param master_timeout: Period to wait for a connection to the master node.
        :param s: List of columns that determine how the table should be sorted. Sorting
            defaults to ascending and can be changed by setting `:asc` or `:desc` as
            a suffix to the column name.
        :param time: Unit used to display time values.
        :param v: When set to `true` will enable verbose output.
        """
        __path_parts: t.Dict[str, str]
        if index not in SKIP_IN_PATH:
            __path_parts = {"index": _quote(index)}
            __path = f'/_cat/shards/{__path_parts["index"]}'
        else:
            __path_parts = {}
            __path = "/_cat/shards"
        __query: t.Dict[str, t.Any] = {}
        if bytes is not None:
            __query["bytes"] = bytes
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if format is not None:
            __query["format"] = format
        if h is not None:
            __query["h"] = h
        if help is not None:
            __query["help"] = help
        if human is not None:
            __query["human"] = human
        if master_timeout is not None:
            __query["master_timeout"] = master_timeout
        if pretty is not None:
            __query["pretty"] = pretty
        if s is not None:
            __query["s"] = s
        if time is not None:
            __query["time"] = time
        if v is not None:
            __query["v"] = v
        __headers = {"accept": "text/plain,application/json"}
        return self.perform_request(  # type: ignore[return-value]
            "GET",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="cat.shards",
            path_parts=__path_parts,
        )

    @_rewrite_parameters()
    def snapshots(
        self,
        *,
        repository: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        format: t.Optional[str] = None,
        h: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        help: t.Optional[bool] = None,
        human: t.Optional[bool] = None,
        ignore_unavailable: t.Optional[bool] = None,
        master_timeout: t.Optional[t.Union[str, t.Literal[-1], t.Literal[0]]] = None,
        pretty: t.Optional[bool] = None,
        s: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        time: t.Optional[
            t.Union[str, t.Literal["d", "h", "m", "micros", "ms", "nanos", "s"]]
        ] = None,
        v: t.Optional[bool] = None,
    ) -> t.Union[ObjectApiResponse[t.Any], TextApiResponse]:
        """
        .. raw:: html

          <p>Get snapshot information.</p>
          <p>Get information about the snapshots stored in one or more repositories.
          A snapshot is a backup of an index or running Elasticsearch cluster.
          IMPORTANT: cat APIs are only intended for human consumption using the command line or Kibana console. They are not intended for use by applications. For application consumption, use the get snapshot API.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/cat-snapshots.html>`_

        :param repository: A comma-separated list of snapshot repositories used to limit
            the request. Accepts wildcard expressions. `_all` returns all repositories.
            If any repository fails during the request, Elasticsearch returns an error.
        :param format: Specifies the format to return the columnar data in, can be set
            to `text`, `json`, `cbor`, `yaml`, or `smile`.
        :param h: List of columns to appear in the response. Supports simple wildcards.
        :param help: When set to `true` will output available columns. This option can't
            be combined with any other query string option.
        :param ignore_unavailable: If `true`, the response does not include information
            from unavailable snapshots.
        :param master_timeout: Period to wait for a connection to the master node.
        :param s: List of columns that determine how the table should be sorted. Sorting
            defaults to ascending and can be changed by setting `:asc` or `:desc` as
            a suffix to the column name.
        :param time: Unit used to display time values.
        :param v: When set to `true` will enable verbose output.
        """
        __path_parts: t.Dict[str, str]
        if repository not in SKIP_IN_PATH:
            __path_parts = {"repository": _quote(repository)}
            __path = f'/_cat/snapshots/{__path_parts["repository"]}'
        else:
            __path_parts = {}
            __path = "/_cat/snapshots"
        __query: t.Dict[str, t.Any] = {}
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if format is not None:
            __query["format"] = format
        if h is not None:
            __query["h"] = h
        if help is not None:
            __query["help"] = help
        if human is not None:
            __query["human"] = human
        if ignore_unavailable is not None:
            __query["ignore_unavailable"] = ignore_unavailable
        if master_timeout is not None:
            __query["master_timeout"] = master_timeout
        if pretty is not None:
            __query["pretty"] = pretty
        if s is not None:
            __query["s"] = s
        if time is not None:
            __query["time"] = time
        if v is not None:
            __query["v"] = v
        __headers = {"accept": "text/plain,application/json"}
        return self.perform_request(  # type: ignore[return-value]
            "GET",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="cat.snapshots",
            path_parts=__path_parts,
        )

    @_rewrite_parameters()
    @_stability_warning(Stability.EXPERIMENTAL)
    def tasks(
        self,
        *,
        actions: t.Optional[t.Sequence[str]] = None,
        detailed: t.Optional[bool] = None,
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        format: t.Optional[str] = None,
        h: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        help: t.Optional[bool] = None,
        human: t.Optional[bool] = None,
        nodes: t.Optional[t.Sequence[str]] = None,
        parent_task_id: t.Optional[str] = None,
        pretty: t.Optional[bool] = None,
        s: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        time: t.Optional[
            t.Union[str, t.Literal["d", "h", "m", "micros", "ms", "nanos", "s"]]
        ] = None,
        timeout: t.Optional[t.Union[str, t.Literal[-1], t.Literal[0]]] = None,
        v: t.Optional[bool] = None,
        wait_for_completion: t.Optional[bool] = None,
    ) -> t.Union[ObjectApiResponse[t.Any], TextApiResponse]:
        """
        .. raw:: html

          <p>Get task information.</p>
          <p>Get information about tasks currently running in the cluster.
          IMPORTANT: cat APIs are only intended for human consumption using the command line or Kibana console. They are not intended for use by applications. For application consumption, use the task management API.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/tasks.html>`_

        :param actions: The task action names, which are used to limit the response.
        :param detailed: If `true`, the response includes detailed information about
            shard recoveries.
        :param format: Specifies the format to return the columnar data in, can be set
            to `text`, `json`, `cbor`, `yaml`, or `smile`.
        :param h: List of columns to appear in the response. Supports simple wildcards.
        :param help: When set to `true` will output available columns. This option can't
            be combined with any other query string option.
        :param nodes: Unique node identifiers, which are used to limit the response.
        :param parent_task_id: The parent task identifier, which is used to limit the
            response.
        :param s: List of columns that determine how the table should be sorted. Sorting
            defaults to ascending and can be changed by setting `:asc` or `:desc` as
            a suffix to the column name.
        :param time: Unit used to display time values.
        :param timeout: Period to wait for a response. If no response is received before
            the timeout expires, the request fails and returns an error.
        :param v: When set to `true` will enable verbose output.
        :param wait_for_completion: If `true`, the request blocks until the task has
            completed.
        """
        __path_parts: t.Dict[str, str] = {}
        __path = "/_cat/tasks"
        __query: t.Dict[str, t.Any] = {}
        if actions is not None:
            __query["actions"] = actions
        if detailed is not None:
            __query["detailed"] = detailed
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if format is not None:
            __query["format"] = format
        if h is not None:
            __query["h"] = h
        if help is not None:
            __query["help"] = help
        if human is not None:
            __query["human"] = human
        if nodes is not None:
            __query["nodes"] = nodes
        if parent_task_id is not None:
            __query["parent_task_id"] = parent_task_id
        if pretty is not None:
            __query["pretty"] = pretty
        if s is not None:
            __query["s"] = s
        if time is not None:
            __query["time"] = time
        if timeout is not None:
            __query["timeout"] = timeout
        if v is not None:
            __query["v"] = v
        if wait_for_completion is not None:
            __query["wait_for_completion"] = wait_for_completion
        __headers = {"accept": "text/plain,application/json"}
        return self.perform_request(  # type: ignore[return-value]
            "GET",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="cat.tasks",
            path_parts=__path_parts,
        )

    @_rewrite_parameters()
    def templates(
        self,
        *,
        name: t.Optional[str] = None,
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        format: t.Optional[str] = None,
        h: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        help: t.Optional[bool] = None,
        human: t.Optional[bool] = None,
        local: t.Optional[bool] = None,
        master_timeout: t.Optional[t.Union[str, t.Literal[-1], t.Literal[0]]] = None,
        pretty: t.Optional[bool] = None,
        s: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        v: t.Optional[bool] = None,
    ) -> t.Union[ObjectApiResponse[t.Any], TextApiResponse]:
        """
        .. raw:: html

          <p>Get index template information.</p>
          <p>Get information about the index templates in a cluster.
          You can use index templates to apply index settings and field mappings to new indices at creation.
          IMPORTANT: cat APIs are only intended for human consumption using the command line or Kibana console. They are not intended for use by applications. For application consumption, use the get index template API.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/cat-templates.html>`_

        :param name: The name of the template to return. Accepts wildcard expressions.
            If omitted, all templates are returned.
        :param format: Specifies the format to return the columnar data in, can be set
            to `text`, `json`, `cbor`, `yaml`, or `smile`.
        :param h: List of columns to appear in the response. Supports simple wildcards.
        :param help: When set to `true` will output available columns. This option can't
            be combined with any other query string option.
        :param local: If `true`, the request computes the list of selected nodes from
            the local cluster state. If `false` the list of selected nodes are computed
            from the cluster state of the master node. In both cases the coordinating
            node will send requests for further information to each selected node.
        :param master_timeout: Period to wait for a connection to the master node.
        :param s: List of columns that determine how the table should be sorted. Sorting
            defaults to ascending and can be changed by setting `:asc` or `:desc` as
            a suffix to the column name.
        :param v: When set to `true` will enable verbose output.
        """
        __path_parts: t.Dict[str, str]
        if name not in SKIP_IN_PATH:
            __path_parts = {"name": _quote(name)}
            __path = f'/_cat/templates/{__path_parts["name"]}'
        else:
            __path_parts = {}
            __path = "/_cat/templates"
        __query: t.Dict[str, t.Any] = {}
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if format is not None:
            __query["format"] = format
        if h is not None:
            __query["h"] = h
        if help is not None:
            __query["help"] = help
        if human is not None:
            __query["human"] = human
        if local is not None:
            __query["local"] = local
        if master_timeout is not None:
            __query["master_timeout"] = master_timeout
        if pretty is not None:
            __query["pretty"] = pretty
        if s is not None:
            __query["s"] = s
        if v is not None:
            __query["v"] = v
        __headers = {"accept": "text/plain,application/json"}
        return self.perform_request(  # type: ignore[return-value]
            "GET",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="cat.templates",
            path_parts=__path_parts,
        )

    @_rewrite_parameters()
    def thread_pool(
        self,
        *,
        thread_pool_patterns: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        format: t.Optional[str] = None,
        h: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        help: t.Optional[bool] = None,
        human: t.Optional[bool] = None,
        local: t.Optional[bool] = None,
        master_timeout: t.Optional[t.Union[str, t.Literal[-1], t.Literal[0]]] = None,
        pretty: t.Optional[bool] = None,
        s: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        time: t.Optional[
            t.Union[str, t.Literal["d", "h", "m", "micros", "ms", "nanos", "s"]]
        ] = None,
        v: t.Optional[bool] = None,
    ) -> t.Union[ObjectApiResponse[t.Any], TextApiResponse]:
        """
        .. raw:: html

          <p>Get thread pool statistics.</p>
          <p>Get thread pool statistics for each node in a cluster.
          Returned information includes all built-in thread pools and custom thread pools.
          IMPORTANT: cat APIs are only intended for human consumption using the command line or Kibana console. They are not intended for use by applications. For application consumption, use the nodes info API.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/cat-thread-pool.html>`_

        :param thread_pool_patterns: A comma-separated list of thread pool names used
            to limit the request. Accepts wildcard expressions.
        :param format: Specifies the format to return the columnar data in, can be set
            to `text`, `json`, `cbor`, `yaml`, or `smile`.
        :param h: List of columns to appear in the response. Supports simple wildcards.
        :param help: When set to `true` will output available columns. This option can't
            be combined with any other query string option.
        :param local: If `true`, the request computes the list of selected nodes from
            the local cluster state. If `false` the list of selected nodes are computed
            from the cluster state of the master node. In both cases the coordinating
            node will send requests for further information to each selected node.
        :param master_timeout: Period to wait for a connection to the master node.
        :param s: List of columns that determine how the table should be sorted. Sorting
            defaults to ascending and can be changed by setting `:asc` or `:desc` as
            a suffix to the column name.
        :param time: The unit used to display time values.
        :param v: When set to `true` will enable verbose output.
        """
        __path_parts: t.Dict[str, str]
        if thread_pool_patterns not in SKIP_IN_PATH:
            __path_parts = {"thread_pool_patterns": _quote(thread_pool_patterns)}
            __path = f'/_cat/thread_pool/{__path_parts["thread_pool_patterns"]}'
        else:
            __path_parts = {}
            __path = "/_cat/thread_pool"
        __query: t.Dict[str, t.Any] = {}
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if format is not None:
            __query["format"] = format
        if h is not None:
            __query["h"] = h
        if help is not None:
            __query["help"] = help
        if human is not None:
            __query["human"] = human
        if local is not None:
            __query["local"] = local
        if master_timeout is not None:
            __query["master_timeout"] = master_timeout
        if pretty is not None:
            __query["pretty"] = pretty
        if s is not None:
            __query["s"] = s
        if time is not None:
            __query["time"] = time
        if v is not None:
            __query["v"] = v
        __headers = {"accept": "text/plain,application/json"}
        return self.perform_request(  # type: ignore[return-value]
            "GET",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="cat.thread_pool",
            path_parts=__path_parts,
        )

    @_rewrite_parameters(
        parameter_aliases={"from": "from_"},
    )
    def transforms(
        self,
        *,
        transform_id: t.Optional[str] = None,
        allow_no_match: t.Optional[bool] = None,
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        format: t.Optional[str] = None,
        from_: t.Optional[int] = None,
        h: t.Optional[
            t.Union[
                t.Sequence[
                    t.Union[
                        str,
                        t.Literal[
                            "changes_last_detection_time",
                            "checkpoint",
                            "checkpoint_duration_time_exp_avg",
                            "checkpoint_progress",
                            "create_time",
                            "delete_time",
                            "description",
                            "dest_index",
                            "docs_per_second",
                            "documents_deleted",
                            "documents_indexed",
                            "documents_processed",
                            "frequency",
                            "id",
                            "index_failure",
                            "index_time",
                            "index_total",
                            "indexed_documents_exp_avg",
                            "last_search_time",
                            "max_page_search_size",
                            "pages_processed",
                            "pipeline",
                            "processed_documents_exp_avg",
                            "processing_time",
                            "reason",
                            "search_failure",
                            "search_time",
                            "search_total",
                            "source_index",
                            "state",
                            "transform_type",
                            "trigger_count",
                            "version",
                        ],
                    ]
                ],
                t.Union[
                    str,
                    t.Literal[
                        "changes_last_detection_time",
                        "checkpoint",
                        "checkpoint_duration_time_exp_avg",
                        "checkpoint_progress",
                        "create_time",
                        "delete_time",
                        "description",
                        "dest_index",
                        "docs_per_second",
                        "documents_deleted",
                        "documents_indexed",
                        "documents_processed",
                        "frequency",
                        "id",
                        "index_failure",
                        "index_time",
                        "index_total",
                        "indexed_documents_exp_avg",
                        "last_search_time",
                        "max_page_search_size",
                        "pages_processed",
                        "pipeline",
                        "processed_documents_exp_avg",
                        "processing_time",
                        "reason",
                        "search_failure",
                        "search_time",
                        "search_total",
                        "source_index",
                        "state",
                        "transform_type",
                        "trigger_count",
                        "version",
                    ],
                ],
            ]
        ] = None,
        help: t.Optional[bool] = None,
        human: t.Optional[bool] = None,
        pretty: t.Optional[bool] = None,
        s: t.Optional[
            t.Union[
                t.Sequence[
                    t.Union[
                        str,
                        t.Literal[
                            "changes_last_detection_time",
                            "checkpoint",
                            "checkpoint_duration_time_exp_avg",
                            "checkpoint_progress",
                            "create_time",
                            "delete_time",
                            "description",
                            "dest_index",
                            "docs_per_second",
                            "documents_deleted",
                            "documents_indexed",
                            "documents_processed",
                            "frequency",
                            "id",
                            "index_failure",
                            "index_time",
                            "index_total",
                            "indexed_documents_exp_avg",
                            "last_search_time",
                            "max_page_search_size",
                            "pages_processed",
                            "pipeline",
                            "processed_documents_exp_avg",
                            "processing_time",
                            "reason",
                            "search_failure",
                            "search_time",
                            "search_total",
                            "source_index",
                            "state",
                            "transform_type",
                            "trigger_count",
                            "version",
                        ],
                    ]
                ],
                t.Union[
                    str,
                    t.Literal[
                        "changes_last_detection_time",
                        "checkpoint",
                        "checkpoint_duration_time_exp_avg",
                        "checkpoint_progress",
                        "create_time",
                        "delete_time",
                        "description",
                        "dest_index",
                        "docs_per_second",
                        "documents_deleted",
                        "documents_indexed",
                        "documents_processed",
                        "frequency",
                        "id",
                        "index_failure",
                        "index_time",
                        "index_total",
                        "indexed_documents_exp_avg",
                        "last_search_time",
                        "max_page_search_size",
                        "pages_processed",
                        "pipeline",
                        "processed_documents_exp_avg",
                        "processing_time",
                        "reason",
                        "search_failure",
                        "search_time",
                        "search_total",
                        "source_index",
                        "state",
                        "transform_type",
                        "trigger_count",
                        "version",
                    ],
                ],
            ]
        ] = None,
        size: t.Optional[int] = None,
        time: t.Optional[
            t.Union[str, t.Literal["d", "h", "m", "micros", "ms", "nanos", "s"]]
        ] = None,
        v: t.Optional[bool] = None,
    ) -> t.Union[ObjectApiResponse[t.Any], TextApiResponse]:
        """
        .. raw:: html

          <p>Get transform information.</p>
          <p>Get configuration and usage information about transforms.</p>
          <p>CAT APIs are only intended for human consumption using the Kibana
          console or command line. They are not intended for use by applications. For
          application consumption, use the get transform statistics API.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/cat-transforms.html>`_

        :param transform_id: A transform identifier or a wildcard expression. If you
            do not specify one of these options, the API returns information for all
            transforms.
        :param allow_no_match: Specifies what to do when the request: contains wildcard
            expressions and there are no transforms that match; contains the `_all` string
            or no identifiers and there are no matches; contains wildcard expressions
            and there are only partial matches. If `true`, it returns an empty transforms
            array when there are no matches and the subset of results when there are
            partial matches. If `false`, the request returns a 404 status code when there
            are no matches or only partial matches.
        :param format: Specifies the format to return the columnar data in, can be set
            to `text`, `json`, `cbor`, `yaml`, or `smile`.
        :param from_: Skips the specified number of transforms.
        :param h: Comma-separated list of column names to display.
        :param help: When set to `true` will output available columns. This option can't
            be combined with any other query string option.
        :param s: Comma-separated list of column names or column aliases used to sort
            the response.
        :param size: The maximum number of transforms to obtain.
        :param time: The unit used to display time values.
        :param v: When set to `true` will enable verbose output.
        """
        __path_parts: t.Dict[str, str]
        if transform_id not in SKIP_IN_PATH:
            __path_parts = {"transform_id": _quote(transform_id)}
            __path = f'/_cat/transforms/{__path_parts["transform_id"]}'
        else:
            __path_parts = {}
            __path = "/_cat/transforms"
        __query: t.Dict[str, t.Any] = {}
        if allow_no_match is not None:
            __query["allow_no_match"] = allow_no_match
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if format is not None:
            __query["format"] = format
        if from_ is not None:
            __query["from"] = from_
        if h is not None:
            __query["h"] = h
        if help is not None:
            __query["help"] = help
        if human is not None:
            __query["human"] = human
        if pretty is not None:
            __query["pretty"] = pretty
        if s is not None:
            __query["s"] = s
        if size is not None:
            __query["size"] = size
        if time is not None:
            __query["time"] = time
        if v is not None:
            __query["v"] = v
        __headers = {"accept": "text/plain,application/json"}
        return self.perform_request(  # type: ignore[return-value]
            "GET",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="cat.transforms",
            path_parts=__path_parts,
        )
