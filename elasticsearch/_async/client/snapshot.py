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

from elastic_transport import ObjectApiResponse

from ._base import NamespacedClient
from .utils import (
    SKIP_IN_PATH,
    Stability,
    _quote,
    _rewrite_parameters,
    _stability_warning,
)


class SnapshotClient(NamespacedClient):

    @_rewrite_parameters()
    async def cleanup_repository(
        self,
        *,
        name: str,
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        human: t.Optional[bool] = None,
        master_timeout: t.Optional[t.Union[str, t.Literal[-1], t.Literal[0]]] = None,
        pretty: t.Optional[bool] = None,
        timeout: t.Optional[t.Union[str, t.Literal[-1], t.Literal[0]]] = None,
    ) -> ObjectApiResponse[t.Any]:
        """
        .. raw:: html

          <p>Clean up the snapshot repository.
          Trigger the review of the contents of a snapshot repository and delete any stale data not referenced by existing snapshots.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/clean-up-snapshot-repo-api.html>`_

        :param name: Snapshot repository to clean up.
        :param master_timeout: Period to wait for a connection to the master node.
        :param timeout: Period to wait for a response.
        """
        if name in SKIP_IN_PATH:
            raise ValueError("Empty value passed for parameter 'name'")
        __path_parts: t.Dict[str, str] = {"repository": _quote(name)}
        __path = f'/_snapshot/{__path_parts["repository"]}/_cleanup'
        __query: t.Dict[str, t.Any] = {}
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if human is not None:
            __query["human"] = human
        if master_timeout is not None:
            __query["master_timeout"] = master_timeout
        if pretty is not None:
            __query["pretty"] = pretty
        if timeout is not None:
            __query["timeout"] = timeout
        __headers = {"accept": "application/json"}
        return await self.perform_request(  # type: ignore[return-value]
            "POST",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="snapshot.cleanup_repository",
            path_parts=__path_parts,
        )

    @_rewrite_parameters(
        body_fields=("indices",),
    )
    async def clone(
        self,
        *,
        repository: str,
        snapshot: str,
        target_snapshot: str,
        indices: t.Optional[str] = None,
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        human: t.Optional[bool] = None,
        master_timeout: t.Optional[t.Union[str, t.Literal[-1], t.Literal[0]]] = None,
        pretty: t.Optional[bool] = None,
        timeout: t.Optional[t.Union[str, t.Literal[-1], t.Literal[0]]] = None,
        body: t.Optional[t.Dict[str, t.Any]] = None,
    ) -> ObjectApiResponse[t.Any]:
        """
        .. raw:: html

          <p>Clone a snapshot.
          Clone part of all of a snapshot into another snapshot in the same repository.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/clone-snapshot-api.html>`_

        :param repository: A repository name
        :param snapshot: The name of the snapshot to clone from
        :param target_snapshot: The name of the cloned snapshot to create
        :param indices:
        :param master_timeout: Explicit operation timeout for connection to master node
        :param timeout:
        """
        if repository in SKIP_IN_PATH:
            raise ValueError("Empty value passed for parameter 'repository'")
        if snapshot in SKIP_IN_PATH:
            raise ValueError("Empty value passed for parameter 'snapshot'")
        if target_snapshot in SKIP_IN_PATH:
            raise ValueError("Empty value passed for parameter 'target_snapshot'")
        if indices is None and body is None:
            raise ValueError("Empty value passed for parameter 'indices'")
        __path_parts: t.Dict[str, str] = {
            "repository": _quote(repository),
            "snapshot": _quote(snapshot),
            "target_snapshot": _quote(target_snapshot),
        }
        __path = f'/_snapshot/{__path_parts["repository"]}/{__path_parts["snapshot"]}/_clone/{__path_parts["target_snapshot"]}'
        __query: t.Dict[str, t.Any] = {}
        __body: t.Dict[str, t.Any] = body if body is not None else {}
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if human is not None:
            __query["human"] = human
        if master_timeout is not None:
            __query["master_timeout"] = master_timeout
        if pretty is not None:
            __query["pretty"] = pretty
        if timeout is not None:
            __query["timeout"] = timeout
        if not __body:
            if indices is not None:
                __body["indices"] = indices
        __headers = {"accept": "application/json", "content-type": "application/json"}
        return await self.perform_request(  # type: ignore[return-value]
            "PUT",
            __path,
            params=__query,
            headers=__headers,
            body=__body,
            endpoint_id="snapshot.clone",
            path_parts=__path_parts,
        )

    @_rewrite_parameters(
        body_fields=(
            "feature_states",
            "ignore_unavailable",
            "include_global_state",
            "indices",
            "metadata",
            "partial",
        ),
    )
    async def create(
        self,
        *,
        repository: str,
        snapshot: str,
        error_trace: t.Optional[bool] = None,
        feature_states: t.Optional[t.Sequence[str]] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        human: t.Optional[bool] = None,
        ignore_unavailable: t.Optional[bool] = None,
        include_global_state: t.Optional[bool] = None,
        indices: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        master_timeout: t.Optional[t.Union[str, t.Literal[-1], t.Literal[0]]] = None,
        metadata: t.Optional[t.Mapping[str, t.Any]] = None,
        partial: t.Optional[bool] = None,
        pretty: t.Optional[bool] = None,
        wait_for_completion: t.Optional[bool] = None,
        body: t.Optional[t.Dict[str, t.Any]] = None,
    ) -> ObjectApiResponse[t.Any]:
        """
        .. raw:: html

          <p>Create a snapshot.
          Take a snapshot of a cluster or of data streams and indices.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/create-snapshot-api.html>`_

        :param repository: Repository for the snapshot.
        :param snapshot: Name of the snapshot. Must be unique in the repository.
        :param feature_states: Feature states to include in the snapshot. Each feature
            state includes one or more system indices containing related data. You can
            view a list of eligible features using the get features API. If `include_global_state`
            is `true`, all current feature states are included by default. If `include_global_state`
            is `false`, no feature states are included by default.
        :param ignore_unavailable: If `true`, the request ignores data streams and indices
            in `indices` that are missing or closed. If `false`, the request returns
            an error for any data stream or index that is missing or closed.
        :param include_global_state: If `true`, the current cluster state is included
            in the snapshot. The cluster state includes persistent cluster settings,
            composable index templates, legacy index templates, ingest pipelines, and
            ILM policies. It also includes data stored in system indices, such as Watches
            and task records (configurable via `feature_states`).
        :param indices: Data streams and indices to include in the snapshot. Supports
            multi-target syntax. Includes all data streams and indices by default.
        :param master_timeout: Period to wait for a connection to the master node. If
            no response is received before the timeout expires, the request fails and
            returns an error.
        :param metadata: Optional metadata for the snapshot. May have any contents. Must
            be less than 1024 bytes. This map is not automatically generated by Elasticsearch.
        :param partial: If `true`, allows restoring a partial snapshot of indices with
            unavailable shards. Only shards that were successfully included in the snapshot
            will be restored. All missing shards will be recreated as empty. If `false`,
            the entire restore operation will fail if one or more indices included in
            the snapshot do not have all primary shards available.
        :param wait_for_completion: If `true`, the request returns a response when the
            snapshot is complete. If `false`, the request returns a response when the
            snapshot initializes.
        """
        if repository in SKIP_IN_PATH:
            raise ValueError("Empty value passed for parameter 'repository'")
        if snapshot in SKIP_IN_PATH:
            raise ValueError("Empty value passed for parameter 'snapshot'")
        __path_parts: t.Dict[str, str] = {
            "repository": _quote(repository),
            "snapshot": _quote(snapshot),
        }
        __path = f'/_snapshot/{__path_parts["repository"]}/{__path_parts["snapshot"]}'
        __query: t.Dict[str, t.Any] = {}
        __body: t.Dict[str, t.Any] = body if body is not None else {}
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if human is not None:
            __query["human"] = human
        if master_timeout is not None:
            __query["master_timeout"] = master_timeout
        if pretty is not None:
            __query["pretty"] = pretty
        if wait_for_completion is not None:
            __query["wait_for_completion"] = wait_for_completion
        if not __body:
            if feature_states is not None:
                __body["feature_states"] = feature_states
            if ignore_unavailable is not None:
                __body["ignore_unavailable"] = ignore_unavailable
            if include_global_state is not None:
                __body["include_global_state"] = include_global_state
            if indices is not None:
                __body["indices"] = indices
            if metadata is not None:
                __body["metadata"] = metadata
            if partial is not None:
                __body["partial"] = partial
        if not __body:
            __body = None  # type: ignore[assignment]
        __headers = {"accept": "application/json"}
        if __body is not None:
            __headers["content-type"] = "application/json"
        return await self.perform_request(  # type: ignore[return-value]
            "PUT",
            __path,
            params=__query,
            headers=__headers,
            body=__body,
            endpoint_id="snapshot.create",
            path_parts=__path_parts,
        )

    @_rewrite_parameters(
        body_name="repository",
    )
    async def create_repository(
        self,
        *,
        name: str,
        repository: t.Optional[t.Mapping[str, t.Any]] = None,
        body: t.Optional[t.Mapping[str, t.Any]] = None,
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        human: t.Optional[bool] = None,
        master_timeout: t.Optional[t.Union[str, t.Literal[-1], t.Literal[0]]] = None,
        pretty: t.Optional[bool] = None,
        timeout: t.Optional[t.Union[str, t.Literal[-1], t.Literal[0]]] = None,
        verify: t.Optional[bool] = None,
    ) -> ObjectApiResponse[t.Any]:
        """
        .. raw:: html

          <p>Create or update a snapshot repository.
          IMPORTANT: If you are migrating searchable snapshots, the repository name must be identical in the source and destination clusters.
          To register a snapshot repository, the cluster's global metadata must be writeable.
          Ensure there are no cluster blocks (for example, <code>cluster.blocks.read_only</code> and <code>clsuter.blocks.read_only_allow_delete</code> settings) that prevent write access.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/modules-snapshots.html>`_

        :param name: A repository name
        :param repository:
        :param master_timeout: Explicit operation timeout for connection to master node
        :param timeout: Explicit operation timeout
        :param verify: Whether to verify the repository after creation
        """
        if name in SKIP_IN_PATH:
            raise ValueError("Empty value passed for parameter 'name'")
        if repository is None and body is None:
            raise ValueError(
                "Empty value passed for parameters 'repository' and 'body', one of them should be set."
            )
        elif repository is not None and body is not None:
            raise ValueError("Cannot set both 'repository' and 'body'")
        __path_parts: t.Dict[str, str] = {"repository": _quote(name)}
        __path = f'/_snapshot/{__path_parts["repository"]}'
        __query: t.Dict[str, t.Any] = {}
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if human is not None:
            __query["human"] = human
        if master_timeout is not None:
            __query["master_timeout"] = master_timeout
        if pretty is not None:
            __query["pretty"] = pretty
        if timeout is not None:
            __query["timeout"] = timeout
        if verify is not None:
            __query["verify"] = verify
        __body = repository if repository is not None else body
        __headers = {"accept": "application/json", "content-type": "application/json"}
        return await self.perform_request(  # type: ignore[return-value]
            "PUT",
            __path,
            params=__query,
            headers=__headers,
            body=__body,
            endpoint_id="snapshot.create_repository",
            path_parts=__path_parts,
        )

    @_rewrite_parameters()
    async def delete(
        self,
        *,
        repository: str,
        snapshot: str,
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        human: t.Optional[bool] = None,
        master_timeout: t.Optional[t.Union[str, t.Literal[-1], t.Literal[0]]] = None,
        pretty: t.Optional[bool] = None,
    ) -> ObjectApiResponse[t.Any]:
        """
        .. raw:: html

          <p>Delete snapshots.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/delete-snapshot-api.html>`_

        :param repository: A repository name
        :param snapshot: A comma-separated list of snapshot names
        :param master_timeout: Explicit operation timeout for connection to master node
        """
        if repository in SKIP_IN_PATH:
            raise ValueError("Empty value passed for parameter 'repository'")
        if snapshot in SKIP_IN_PATH:
            raise ValueError("Empty value passed for parameter 'snapshot'")
        __path_parts: t.Dict[str, str] = {
            "repository": _quote(repository),
            "snapshot": _quote(snapshot),
        }
        __path = f'/_snapshot/{__path_parts["repository"]}/{__path_parts["snapshot"]}'
        __query: t.Dict[str, t.Any] = {}
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if human is not None:
            __query["human"] = human
        if master_timeout is not None:
            __query["master_timeout"] = master_timeout
        if pretty is not None:
            __query["pretty"] = pretty
        __headers = {"accept": "application/json"}
        return await self.perform_request(  # type: ignore[return-value]
            "DELETE",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="snapshot.delete",
            path_parts=__path_parts,
        )

    @_rewrite_parameters()
    async def delete_repository(
        self,
        *,
        name: t.Union[str, t.Sequence[str]],
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        human: t.Optional[bool] = None,
        master_timeout: t.Optional[t.Union[str, t.Literal[-1], t.Literal[0]]] = None,
        pretty: t.Optional[bool] = None,
        timeout: t.Optional[t.Union[str, t.Literal[-1], t.Literal[0]]] = None,
    ) -> ObjectApiResponse[t.Any]:
        """
        .. raw:: html

          <p>Delete snapshot repositories.
          When a repository is unregistered, Elasticsearch removes only the reference to the location where the repository is storing the snapshots.
          The snapshots themselves are left untouched and in place.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/delete-snapshot-repo-api.html>`_

        :param name: Name of the snapshot repository to unregister. Wildcard (`*`) patterns
            are supported.
        :param master_timeout: Explicit operation timeout for connection to master node
        :param timeout: Explicit operation timeout
        """
        if name in SKIP_IN_PATH:
            raise ValueError("Empty value passed for parameter 'name'")
        __path_parts: t.Dict[str, str] = {"repository": _quote(name)}
        __path = f'/_snapshot/{__path_parts["repository"]}'
        __query: t.Dict[str, t.Any] = {}
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if human is not None:
            __query["human"] = human
        if master_timeout is not None:
            __query["master_timeout"] = master_timeout
        if pretty is not None:
            __query["pretty"] = pretty
        if timeout is not None:
            __query["timeout"] = timeout
        __headers = {"accept": "application/json"}
        return await self.perform_request(  # type: ignore[return-value]
            "DELETE",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="snapshot.delete_repository",
            path_parts=__path_parts,
        )

    @_rewrite_parameters()
    async def get(
        self,
        *,
        repository: str,
        snapshot: t.Union[str, t.Sequence[str]],
        after: t.Optional[str] = None,
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        from_sort_value: t.Optional[str] = None,
        human: t.Optional[bool] = None,
        ignore_unavailable: t.Optional[bool] = None,
        include_repository: t.Optional[bool] = None,
        index_details: t.Optional[bool] = None,
        index_names: t.Optional[bool] = None,
        master_timeout: t.Optional[t.Union[str, t.Literal[-1], t.Literal[0]]] = None,
        offset: t.Optional[int] = None,
        order: t.Optional[t.Union[str, t.Literal["asc", "desc"]]] = None,
        pretty: t.Optional[bool] = None,
        size: t.Optional[int] = None,
        slm_policy_filter: t.Optional[str] = None,
        sort: t.Optional[
            t.Union[
                str,
                t.Literal[
                    "duration",
                    "failed_shard_count",
                    "index_count",
                    "name",
                    "repository",
                    "shard_count",
                    "start_time",
                ],
            ]
        ] = None,
        verbose: t.Optional[bool] = None,
    ) -> ObjectApiResponse[t.Any]:
        """
        .. raw:: html

          <p>Get snapshot information.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/get-snapshot-api.html>`_

        :param repository: Comma-separated list of snapshot repository names used to
            limit the request. Wildcard (*) expressions are supported.
        :param snapshot: Comma-separated list of snapshot names to retrieve. Also accepts
            wildcards (*). - To get information about all snapshots in a registered repository,
            use a wildcard (*) or _all. - To get information about any snapshots that
            are currently running, use _current.
        :param after: Offset identifier to start pagination from as returned by the next
            field in the response body.
        :param from_sort_value: Value of the current sort column at which to start retrieval.
            Can either be a string snapshot- or repository name when sorting by snapshot
            or repository name, a millisecond time value or a number when sorting by
            index- or shard count.
        :param ignore_unavailable: If false, the request returns an error for any snapshots
            that are unavailable.
        :param include_repository: If true, returns the repository name in each snapshot.
        :param index_details: If true, returns additional information about each index
            in the snapshot comprising the number of shards in the index, the total size
            of the index in bytes, and the maximum number of segments per shard in the
            index. Defaults to false, meaning that this information is omitted.
        :param index_names: If true, returns the name of each index in each snapshot.
        :param master_timeout: Period to wait for a connection to the master node. If
            no response is received before the timeout expires, the request fails and
            returns an error.
        :param offset: Numeric offset to start pagination from based on the snapshots
            matching this request. Using a non-zero value for this parameter is mutually
            exclusive with using the after parameter. Defaults to 0.
        :param order: Sort order. Valid values are asc for ascending and desc for descending
            order. Defaults to asc, meaning ascending order.
        :param size: Maximum number of snapshots to return. Defaults to 0 which means
            return all that match the request without limit.
        :param slm_policy_filter: Filter snapshots by a comma-separated list of SLM policy
            names that snapshots belong to. Also accepts wildcards (*) and combinations
            of wildcards followed by exclude patterns starting with -. To include snapshots
            not created by an SLM policy you can use the special pattern _none that will
            match all snapshots without an SLM policy.
        :param sort: Allows setting a sort order for the result. Defaults to start_time,
            i.e. sorting by snapshot start time stamp.
        :param verbose: If true, returns additional information about each snapshot such
            as the version of Elasticsearch which took the snapshot, the start and end
            times of the snapshot, and the number of shards snapshotted.
        """
        if repository in SKIP_IN_PATH:
            raise ValueError("Empty value passed for parameter 'repository'")
        if snapshot in SKIP_IN_PATH:
            raise ValueError("Empty value passed for parameter 'snapshot'")
        __path_parts: t.Dict[str, str] = {
            "repository": _quote(repository),
            "snapshot": _quote(snapshot),
        }
        __path = f'/_snapshot/{__path_parts["repository"]}/{__path_parts["snapshot"]}'
        __query: t.Dict[str, t.Any] = {}
        if after is not None:
            __query["after"] = after
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if from_sort_value is not None:
            __query["from_sort_value"] = from_sort_value
        if human is not None:
            __query["human"] = human
        if ignore_unavailable is not None:
            __query["ignore_unavailable"] = ignore_unavailable
        if include_repository is not None:
            __query["include_repository"] = include_repository
        if index_details is not None:
            __query["index_details"] = index_details
        if index_names is not None:
            __query["index_names"] = index_names
        if master_timeout is not None:
            __query["master_timeout"] = master_timeout
        if offset is not None:
            __query["offset"] = offset
        if order is not None:
            __query["order"] = order
        if pretty is not None:
            __query["pretty"] = pretty
        if size is not None:
            __query["size"] = size
        if slm_policy_filter is not None:
            __query["slm_policy_filter"] = slm_policy_filter
        if sort is not None:
            __query["sort"] = sort
        if verbose is not None:
            __query["verbose"] = verbose
        __headers = {"accept": "application/json"}
        return await self.perform_request(  # type: ignore[return-value]
            "GET",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="snapshot.get",
            path_parts=__path_parts,
        )

    @_rewrite_parameters()
    async def get_repository(
        self,
        *,
        name: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        human: t.Optional[bool] = None,
        local: t.Optional[bool] = None,
        master_timeout: t.Optional[t.Union[str, t.Literal[-1], t.Literal[0]]] = None,
        pretty: t.Optional[bool] = None,
    ) -> ObjectApiResponse[t.Any]:
        """
        .. raw:: html

          <p>Get snapshot repository information.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/get-snapshot-repo-api.html>`_

        :param name: A comma-separated list of repository names
        :param local: Return local information, do not retrieve the state from master
            node (default: false)
        :param master_timeout: Explicit operation timeout for connection to master node
        """
        __path_parts: t.Dict[str, str]
        if name not in SKIP_IN_PATH:
            __path_parts = {"repository": _quote(name)}
            __path = f'/_snapshot/{__path_parts["repository"]}'
        else:
            __path_parts = {}
            __path = "/_snapshot"
        __query: t.Dict[str, t.Any] = {}
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if human is not None:
            __query["human"] = human
        if local is not None:
            __query["local"] = local
        if master_timeout is not None:
            __query["master_timeout"] = master_timeout
        if pretty is not None:
            __query["pretty"] = pretty
        __headers = {"accept": "application/json"}
        return await self.perform_request(  # type: ignore[return-value]
            "GET",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="snapshot.get_repository",
            path_parts=__path_parts,
        )

    @_rewrite_parameters()
    async def repository_analyze(
        self,
        *,
        name: str,
        blob_count: t.Optional[int] = None,
        concurrency: t.Optional[int] = None,
        detailed: t.Optional[bool] = None,
        early_read_node_count: t.Optional[int] = None,
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        human: t.Optional[bool] = None,
        max_blob_size: t.Optional[t.Union[int, str]] = None,
        max_total_data_size: t.Optional[t.Union[int, str]] = None,
        pretty: t.Optional[bool] = None,
        rare_action_probability: t.Optional[float] = None,
        rarely_abort_writes: t.Optional[bool] = None,
        read_node_count: t.Optional[int] = None,
        register_operation_count: t.Optional[int] = None,
        seed: t.Optional[int] = None,
        timeout: t.Optional[t.Union[str, t.Literal[-1], t.Literal[0]]] = None,
    ) -> ObjectApiResponse[t.Any]:
        """
        .. raw:: html

          <p>Analyze a snapshot repository.
          Analyze the performance characteristics and any incorrect behaviour found in a repository.</p>
          <p>The response exposes implementation details of the analysis which may change from version to version.
          The response body format is therefore not considered stable and may be different in newer versions.</p>
          <p>There are a large number of third-party storage systems available, not all of which are suitable for use as a snapshot repository by Elasticsearch.
          Some storage systems behave incorrectly, or perform poorly, especially when accessed concurrently by multiple clients as the nodes of an Elasticsearch cluster do. This API performs a collection of read and write operations on your repository which are designed to detect incorrect behaviour and to measure the performance characteristics of your storage system.</p>
          <p>The default values for the parameters are deliberately low to reduce the impact of running an analysis inadvertently and to provide a sensible starting point for your investigations.
          Run your first analysis with the default parameter values to check for simple problems.
          If successful, run a sequence of increasingly large analyses until you encounter a failure or you reach a <code>blob_count</code> of at least <code>2000</code>, a <code>max_blob_size</code> of at least <code>2gb</code>, a <code>max_total_data_size</code> of at least <code>1tb</code>, and a <code>register_operation_count</code> of at least <code>100</code>.
          Always specify a generous timeout, possibly <code>1h</code> or longer, to allow time for each analysis to run to completion.
          Perform the analyses using a multi-node cluster of a similar size to your production cluster so that it can detect any problems that only arise when the repository is accessed by many nodes at once.</p>
          <p>If the analysis fails, Elasticsearch detected that your repository behaved unexpectedly.
          This usually means you are using a third-party storage system with an incorrect or incompatible implementation of the API it claims to support.
          If so, this storage system is not suitable for use as a snapshot repository.
          You will need to work with the supplier of your storage system to address the incompatibilities that Elasticsearch detects.</p>
          <p>If the analysis is successful, the API returns details of the testing process, optionally including how long each operation took.
          You can use this information to determine the performance of your storage system.
          If any operation fails or returns an incorrect result, the API returns an error.
          If the API returns an error, it may not have removed all the data it wrote to the repository.
          The error will indicate the location of any leftover data and this path is also recorded in the Elasticsearch logs.
          You should verify that this location has been cleaned up correctly.
          If there is still leftover data at the specified location, you should manually remove it.</p>
          <p>If the connection from your client to Elasticsearch is closed while the client is waiting for the result of the analysis, the test is cancelled.
          Some clients are configured to close their connection if no response is received within a certain timeout.
          An analysis takes a long time to complete so you might need to relax any such client-side timeouts.
          On cancellation the analysis attempts to clean up the data it was writing, but it may not be able to remove it all.
          The path to the leftover data is recorded in the Elasticsearch logs.
          You should verify that this location has been cleaned up correctly.
          If there is still leftover data at the specified location, you should manually remove it.</p>
          <p>If the analysis is successful then it detected no incorrect behaviour, but this does not mean that correct behaviour is guaranteed.
          The analysis attempts to detect common bugs but it does not offer 100% coverage.
          Additionally, it does not test the following:</p>
          <ul>
          <li>Your repository must perform durable writes. Once a blob has been written it must remain in place until it is deleted, even after a power loss or similar disaster.</li>
          <li>Your repository must not suffer from silent data corruption. Once a blob has been written, its contents must remain unchanged until it is deliberately modified or deleted.</li>
          <li>Your repository must behave correctly even if connectivity from the cluster is disrupted. Reads and writes may fail in this case, but they must not return incorrect results.</li>
          </ul>
          <p>IMPORTANT: An analysis writes a substantial amount of data to your repository and then reads it back again.
          This consumes bandwidth on the network between the cluster and the repository, and storage space and I/O bandwidth on the repository itself.
          You must ensure this load does not affect other users of these systems.
          Analyses respect the repository settings <code>max_snapshot_bytes_per_sec</code> and <code>max_restore_bytes_per_sec</code> if available and the cluster setting <code>indices.recovery.max_bytes_per_sec</code> which you can use to limit the bandwidth they consume.</p>
          <p>NOTE: This API is intended for exploratory use by humans. You should expect the request parameters and the response format to vary in future versions.</p>
          <p>NOTE: Different versions of Elasticsearch may perform different checks for repository compatibility, with newer versions typically being stricter than older ones.
          A storage system that passes repository analysis with one version of Elasticsearch may fail with a different version.
          This indicates it behaves incorrectly in ways that the former version did not detect.
          You must work with the supplier of your storage system to address the incompatibilities detected by the repository analysis API in any version of Elasticsearch.</p>
          <p>NOTE: This API may not work correctly in a mixed-version cluster.</p>
          <p><em>Implementation details</em></p>
          <p>NOTE: This section of documentation describes how the repository analysis API works in this version of Elasticsearch, but you should expect the implementation to vary between versions. The request parameters and response format depend on details of the implementation so may also be different in newer versions.</p>
          <p>The analysis comprises a number of blob-level tasks, as set by the <code>blob_count</code> parameter and a number of compare-and-exchange operations on linearizable registers, as set by the <code>register_operation_count</code> parameter.
          These tasks are distributed over the data and master-eligible nodes in the cluster for execution.</p>
          <p>For most blob-level tasks, the executing node first writes a blob to the repository and then instructs some of the other nodes in the cluster to attempt to read the data it just wrote.
          The size of the blob is chosen randomly, according to the <code>max_blob_size</code> and <code>max_total_data_size</code> parameters.
          If any of these reads fails then the repository does not implement the necessary read-after-write semantics that Elasticsearch requires.</p>
          <p>For some blob-level tasks, the executing node will instruct some of its peers to attempt to read the data before the writing process completes.
          These reads are permitted to fail, but must not return partial data.
          If any read returns partial data then the repository does not implement the necessary atomicity semantics that Elasticsearch requires.</p>
          <p>For some blob-level tasks, the executing node will overwrite the blob while its peers are reading it.
          In this case the data read may come from either the original or the overwritten blob, but the read operation must not return partial data or a mix of data from the two blobs.
          If any of these reads returns partial data or a mix of the two blobs then the repository does not implement the necessary atomicity semantics that Elasticsearch requires for overwrites.</p>
          <p>The executing node will use a variety of different methods to write the blob.
          For instance, where applicable, it will use both single-part and multi-part uploads.
          Similarly, the reading nodes will use a variety of different methods to read the data back again.
          For instance they may read the entire blob from start to end or may read only a subset of the data.</p>
          <p>For some blob-level tasks, the executing node will cancel the write before it is complete.
          In this case, it still instructs some of the other nodes in the cluster to attempt to read the blob but all of these reads must fail to find the blob.</p>
          <p>Linearizable registers are special blobs that Elasticsearch manipulates using an atomic compare-and-exchange operation.
          This operation ensures correct and strongly-consistent behavior even when the blob is accessed by multiple nodes at the same time.
          The detailed implementation of the compare-and-exchange operation on linearizable registers varies by repository type.
          Repository analysis verifies that that uncontended compare-and-exchange operations on a linearizable register blob always succeed.
          Repository analysis also verifies that contended operations either succeed or report the contention but do not return incorrect results.
          If an operation fails due to contention, Elasticsearch retries the operation until it succeeds.
          Most of the compare-and-exchange operations performed by repository analysis atomically increment a counter which is represented as an 8-byte blob.
          Some operations also verify the behavior on small blobs with sizes other than 8 bytes.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/repo-analysis-api.html>`_

        :param name: The name of the repository.
        :param blob_count: The total number of blobs to write to the repository during
            the test. For realistic experiments, you should set it to at least `2000`.
        :param concurrency: The number of operations to run concurrently during the test.
        :param detailed: Indicates whether to return detailed results, including timing
            information for every operation performed during the analysis. If false,
            it returns only a summary of the analysis.
        :param early_read_node_count: The number of nodes on which to perform an early
            read operation while writing each blob. Early read operations are only rarely
            performed.
        :param max_blob_size: The maximum size of a blob to be written during the test.
            For realistic experiments, you should set it to at least `2gb`.
        :param max_total_data_size: An upper limit on the total size of all the blobs
            written during the test. For realistic experiments, you should set it to
            at least `1tb`.
        :param rare_action_probability: The probability of performing a rare action such
            as an early read, an overwrite, or an aborted write on each blob.
        :param rarely_abort_writes: Indicates whether to rarely cancel writes before
            they complete.
        :param read_node_count: The number of nodes on which to read a blob after writing.
        :param register_operation_count: The minimum number of linearizable register
            operations to perform in total. For realistic experiments, you should set
            it to at least `100`.
        :param seed: The seed for the pseudo-random number generator used to generate
            the list of operations performed during the test. To repeat the same set
            of operations in multiple experiments, use the same seed in each experiment.
            Note that the operations are performed concurrently so might not always happen
            in the same order on each run.
        :param timeout: The period of time to wait for the test to complete. If no response
            is received before the timeout expires, the test is cancelled and returns
            an error.
        """
        if name in SKIP_IN_PATH:
            raise ValueError("Empty value passed for parameter 'name'")
        __path_parts: t.Dict[str, str] = {"repository": _quote(name)}
        __path = f'/_snapshot/{__path_parts["repository"]}/_analyze'
        __query: t.Dict[str, t.Any] = {}
        if blob_count is not None:
            __query["blob_count"] = blob_count
        if concurrency is not None:
            __query["concurrency"] = concurrency
        if detailed is not None:
            __query["detailed"] = detailed
        if early_read_node_count is not None:
            __query["early_read_node_count"] = early_read_node_count
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if human is not None:
            __query["human"] = human
        if max_blob_size is not None:
            __query["max_blob_size"] = max_blob_size
        if max_total_data_size is not None:
            __query["max_total_data_size"] = max_total_data_size
        if pretty is not None:
            __query["pretty"] = pretty
        if rare_action_probability is not None:
            __query["rare_action_probability"] = rare_action_probability
        if rarely_abort_writes is not None:
            __query["rarely_abort_writes"] = rarely_abort_writes
        if read_node_count is not None:
            __query["read_node_count"] = read_node_count
        if register_operation_count is not None:
            __query["register_operation_count"] = register_operation_count
        if seed is not None:
            __query["seed"] = seed
        if timeout is not None:
            __query["timeout"] = timeout
        __headers = {"accept": "application/json"}
        return await self.perform_request(  # type: ignore[return-value]
            "POST",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="snapshot.repository_analyze",
            path_parts=__path_parts,
        )

    @_rewrite_parameters()
    @_stability_warning(Stability.EXPERIMENTAL)
    async def repository_verify_integrity(
        self,
        *,
        name: t.Union[str, t.Sequence[str]],
        blob_thread_pool_concurrency: t.Optional[int] = None,
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        human: t.Optional[bool] = None,
        index_snapshot_verification_concurrency: t.Optional[int] = None,
        index_verification_concurrency: t.Optional[int] = None,
        max_bytes_per_sec: t.Optional[str] = None,
        max_failed_shard_snapshots: t.Optional[int] = None,
        meta_thread_pool_concurrency: t.Optional[int] = None,
        pretty: t.Optional[bool] = None,
        snapshot_verification_concurrency: t.Optional[int] = None,
        verify_blob_contents: t.Optional[bool] = None,
    ) -> ObjectApiResponse[t.Any]:
        """
        .. raw:: html

          <p>Verify the repository integrity.
          Verify the integrity of the contents of a snapshot repository.</p>
          <p>This API enables you to perform a comprehensive check of the contents of a repository, looking for any anomalies in its data or metadata which might prevent you from restoring snapshots from the repository or which might cause future snapshot create or delete operations to fail.</p>
          <p>If you suspect the integrity of the contents of one of your snapshot repositories, cease all write activity to this repository immediately, set its <code>read_only</code> option to <code>true</code>, and use this API to verify its integrity.
          Until you do so:</p>
          <ul>
          <li>It may not be possible to restore some snapshots from this repository.</li>
          <li>Searchable snapshots may report errors when searched or may have unassigned shards.</li>
          <li>Taking snapshots into this repository may fail or may appear to succeed but have created a snapshot which cannot be restored.</li>
          <li>Deleting snapshots from this repository may fail or may appear to succeed but leave the underlying data on disk.</li>
          <li>Continuing to write to the repository while it is in an invalid state may causing additional damage to its contents.</li>
          </ul>
          <p>If the API finds any problems with the integrity of the contents of your repository, Elasticsearch will not be able to repair the damage.
          The only way to bring the repository back into a fully working state after its contents have been damaged is by restoring its contents from a repository backup which was taken before the damage occurred.
          You must also identify what caused the damage and take action to prevent it from happening again.</p>
          <p>If you cannot restore a repository backup, register a new repository and use this for all future snapshot operations.
          In some cases it may be possible to recover some of the contents of a damaged repository, either by restoring as many of its snapshots as needed and taking new snapshots of the restored data, or by using the reindex API to copy data from any searchable snapshots mounted from the damaged repository.</p>
          <p>Avoid all operations which write to the repository while the verify repository integrity API is running.
          If something changes the repository contents while an integrity verification is running then Elasticsearch may incorrectly report having detected some anomalies in its contents due to the concurrent writes.
          It may also incorrectly fail to report some anomalies that the concurrent writes prevented it from detecting.</p>
          <p>NOTE: This API is intended for exploratory use by humans. You should expect the request parameters and the response format to vary in future versions.</p>
          <p>NOTE: This API may not work correctly in a mixed-version cluster.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/verify-repo-integrity-api.html>`_

        :param name: A repository name
        :param blob_thread_pool_concurrency: Number of threads to use for reading blob
            contents
        :param index_snapshot_verification_concurrency: Number of snapshots to verify
            concurrently within each index
        :param index_verification_concurrency: Number of indices to verify concurrently
        :param max_bytes_per_sec: Rate limit for individual blob verification
        :param max_failed_shard_snapshots: Maximum permitted number of failed shard snapshots
        :param meta_thread_pool_concurrency: Number of threads to use for reading metadata
        :param snapshot_verification_concurrency: Number of snapshots to verify concurrently
        :param verify_blob_contents: Whether to verify the contents of individual blobs
        """
        if name in SKIP_IN_PATH:
            raise ValueError("Empty value passed for parameter 'name'")
        __path_parts: t.Dict[str, str] = {"repository": _quote(name)}
        __path = f'/_snapshot/{__path_parts["repository"]}/_verify_integrity'
        __query: t.Dict[str, t.Any] = {}
        if blob_thread_pool_concurrency is not None:
            __query["blob_thread_pool_concurrency"] = blob_thread_pool_concurrency
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if human is not None:
            __query["human"] = human
        if index_snapshot_verification_concurrency is not None:
            __query["index_snapshot_verification_concurrency"] = (
                index_snapshot_verification_concurrency
            )
        if index_verification_concurrency is not None:
            __query["index_verification_concurrency"] = index_verification_concurrency
        if max_bytes_per_sec is not None:
            __query["max_bytes_per_sec"] = max_bytes_per_sec
        if max_failed_shard_snapshots is not None:
            __query["max_failed_shard_snapshots"] = max_failed_shard_snapshots
        if meta_thread_pool_concurrency is not None:
            __query["meta_thread_pool_concurrency"] = meta_thread_pool_concurrency
        if pretty is not None:
            __query["pretty"] = pretty
        if snapshot_verification_concurrency is not None:
            __query["snapshot_verification_concurrency"] = (
                snapshot_verification_concurrency
            )
        if verify_blob_contents is not None:
            __query["verify_blob_contents"] = verify_blob_contents
        __headers = {"accept": "application/json"}
        return await self.perform_request(  # type: ignore[return-value]
            "POST",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="snapshot.repository_verify_integrity",
            path_parts=__path_parts,
        )

    @_rewrite_parameters(
        body_fields=(
            "feature_states",
            "ignore_index_settings",
            "ignore_unavailable",
            "include_aliases",
            "include_global_state",
            "index_settings",
            "indices",
            "partial",
            "rename_pattern",
            "rename_replacement",
        ),
    )
    async def restore(
        self,
        *,
        repository: str,
        snapshot: str,
        error_trace: t.Optional[bool] = None,
        feature_states: t.Optional[t.Sequence[str]] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        human: t.Optional[bool] = None,
        ignore_index_settings: t.Optional[t.Sequence[str]] = None,
        ignore_unavailable: t.Optional[bool] = None,
        include_aliases: t.Optional[bool] = None,
        include_global_state: t.Optional[bool] = None,
        index_settings: t.Optional[t.Mapping[str, t.Any]] = None,
        indices: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        master_timeout: t.Optional[t.Union[str, t.Literal[-1], t.Literal[0]]] = None,
        partial: t.Optional[bool] = None,
        pretty: t.Optional[bool] = None,
        rename_pattern: t.Optional[str] = None,
        rename_replacement: t.Optional[str] = None,
        wait_for_completion: t.Optional[bool] = None,
        body: t.Optional[t.Dict[str, t.Any]] = None,
    ) -> ObjectApiResponse[t.Any]:
        """
        .. raw:: html

          <p>Restore a snapshot.
          Restore a snapshot of a cluster or data streams and indices.</p>
          <p>You can restore a snapshot only to a running cluster with an elected master node.
          The snapshot repository must be registered and available to the cluster.
          The snapshot and cluster versions must be compatible.</p>
          <p>To restore a snapshot, the cluster's global metadata must be writable. Ensure there are't any cluster blocks that prevent writes. The restore operation ignores index blocks.</p>
          <p>Before you restore a data stream, ensure the cluster contains a matching index template with data streams enabled. To check, use the index management feature in Kibana or the get index template API:</p>
          <pre><code>GET _index_template/*?filter_path=index_templates.name,index_templates.index_template.index_patterns,index_templates.index_template.data_stream
          </code></pre>
          <p>If no such template exists, you can create one or restore a cluster state that contains one. Without a matching index template, a data stream can't roll over or create backing indices.</p>
          <p>If your snapshot contains data from App Search or Workplace Search, you must restore the Enterprise Search encryption key before you restore the snapshot.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/restore-snapshot-api.html>`_

        :param repository: A repository name
        :param snapshot: A snapshot name
        :param feature_states:
        :param ignore_index_settings:
        :param ignore_unavailable:
        :param include_aliases:
        :param include_global_state:
        :param index_settings:
        :param indices:
        :param master_timeout: Explicit operation timeout for connection to master node
        :param partial:
        :param rename_pattern:
        :param rename_replacement:
        :param wait_for_completion: Should this request wait until the operation has
            completed before returning
        """
        if repository in SKIP_IN_PATH:
            raise ValueError("Empty value passed for parameter 'repository'")
        if snapshot in SKIP_IN_PATH:
            raise ValueError("Empty value passed for parameter 'snapshot'")
        __path_parts: t.Dict[str, str] = {
            "repository": _quote(repository),
            "snapshot": _quote(snapshot),
        }
        __path = f'/_snapshot/{__path_parts["repository"]}/{__path_parts["snapshot"]}/_restore'
        __query: t.Dict[str, t.Any] = {}
        __body: t.Dict[str, t.Any] = body if body is not None else {}
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if human is not None:
            __query["human"] = human
        if master_timeout is not None:
            __query["master_timeout"] = master_timeout
        if pretty is not None:
            __query["pretty"] = pretty
        if wait_for_completion is not None:
            __query["wait_for_completion"] = wait_for_completion
        if not __body:
            if feature_states is not None:
                __body["feature_states"] = feature_states
            if ignore_index_settings is not None:
                __body["ignore_index_settings"] = ignore_index_settings
            if ignore_unavailable is not None:
                __body["ignore_unavailable"] = ignore_unavailable
            if include_aliases is not None:
                __body["include_aliases"] = include_aliases
            if include_global_state is not None:
                __body["include_global_state"] = include_global_state
            if index_settings is not None:
                __body["index_settings"] = index_settings
            if indices is not None:
                __body["indices"] = indices
            if partial is not None:
                __body["partial"] = partial
            if rename_pattern is not None:
                __body["rename_pattern"] = rename_pattern
            if rename_replacement is not None:
                __body["rename_replacement"] = rename_replacement
        if not __body:
            __body = None  # type: ignore[assignment]
        __headers = {"accept": "application/json"}
        if __body is not None:
            __headers["content-type"] = "application/json"
        return await self.perform_request(  # type: ignore[return-value]
            "POST",
            __path,
            params=__query,
            headers=__headers,
            body=__body,
            endpoint_id="snapshot.restore",
            path_parts=__path_parts,
        )

    @_rewrite_parameters()
    async def status(
        self,
        *,
        repository: t.Optional[str] = None,
        snapshot: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        human: t.Optional[bool] = None,
        ignore_unavailable: t.Optional[bool] = None,
        master_timeout: t.Optional[t.Union[str, t.Literal[-1], t.Literal[0]]] = None,
        pretty: t.Optional[bool] = None,
    ) -> ObjectApiResponse[t.Any]:
        """
        .. raw:: html

          <p>Get the snapshot status.
          Get a detailed description of the current state for each shard participating in the snapshot.
          Note that this API should be used only to obtain detailed shard-level information for ongoing snapshots.
          If this detail is not needed or you want to obtain information about one or more existing snapshots, use the get snapshot API.</p>
          <p>WARNING: Using the API to return the status of any snapshots other than currently running snapshots can be expensive.
          The API requires a read from the repository for each shard in each snapshot.
          For example, if you have 100 snapshots with 1,000 shards each, an API request that includes all snapshots will require 100,000 reads (100 snapshots x 1,000 shards).</p>
          <p>Depending on the latency of your storage, such requests can take an extremely long time to return results.
          These requests can also tax machine resources and, when using cloud storage, incur high processing costs.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/get-snapshot-status-api.html>`_

        :param repository: A repository name
        :param snapshot: A comma-separated list of snapshot names
        :param ignore_unavailable: Whether to ignore unavailable snapshots, defaults
            to false which means a SnapshotMissingException is thrown
        :param master_timeout: Explicit operation timeout for connection to master node
        """
        __path_parts: t.Dict[str, str]
        if repository not in SKIP_IN_PATH and snapshot not in SKIP_IN_PATH:
            __path_parts = {
                "repository": _quote(repository),
                "snapshot": _quote(snapshot),
            }
            __path = f'/_snapshot/{__path_parts["repository"]}/{__path_parts["snapshot"]}/_status'
        elif repository not in SKIP_IN_PATH:
            __path_parts = {"repository": _quote(repository)}
            __path = f'/_snapshot/{__path_parts["repository"]}/_status'
        else:
            __path_parts = {}
            __path = "/_snapshot/_status"
        __query: t.Dict[str, t.Any] = {}
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if human is not None:
            __query["human"] = human
        if ignore_unavailable is not None:
            __query["ignore_unavailable"] = ignore_unavailable
        if master_timeout is not None:
            __query["master_timeout"] = master_timeout
        if pretty is not None:
            __query["pretty"] = pretty
        __headers = {"accept": "application/json"}
        return await self.perform_request(  # type: ignore[return-value]
            "GET",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="snapshot.status",
            path_parts=__path_parts,
        )

    @_rewrite_parameters()
    async def verify_repository(
        self,
        *,
        name: str,
        error_trace: t.Optional[bool] = None,
        filter_path: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        human: t.Optional[bool] = None,
        master_timeout: t.Optional[t.Union[str, t.Literal[-1], t.Literal[0]]] = None,
        pretty: t.Optional[bool] = None,
        timeout: t.Optional[t.Union[str, t.Literal[-1], t.Literal[0]]] = None,
    ) -> ObjectApiResponse[t.Any]:
        """
        .. raw:: html

          <p>Verify a snapshot repository.
          Check for common misconfigurations in a snapshot repository.</p>


        `<https://www.elastic.co/guide/en/elasticsearch/reference/8.17/verify-snapshot-repo-api.html>`_

        :param name: A repository name
        :param master_timeout: Explicit operation timeout for connection to master node
        :param timeout: Explicit operation timeout
        """
        if name in SKIP_IN_PATH:
            raise ValueError("Empty value passed for parameter 'name'")
        __path_parts: t.Dict[str, str] = {"repository": _quote(name)}
        __path = f'/_snapshot/{__path_parts["repository"]}/_verify'
        __query: t.Dict[str, t.Any] = {}
        if error_trace is not None:
            __query["error_trace"] = error_trace
        if filter_path is not None:
            __query["filter_path"] = filter_path
        if human is not None:
            __query["human"] = human
        if master_timeout is not None:
            __query["master_timeout"] = master_timeout
        if pretty is not None:
            __query["pretty"] = pretty
        if timeout is not None:
            __query["timeout"] = timeout
        __headers = {"accept": "application/json"}
        return await self.perform_request(  # type: ignore[return-value]
            "POST",
            __path,
            params=__query,
            headers=__headers,
            endpoint_id="snapshot.verify_repository",
            path_parts=__path_parts,
        )
