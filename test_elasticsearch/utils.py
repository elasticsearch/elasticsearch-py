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
import re
import time
from pathlib import Path
from typing import Optional, Tuple

from elastic_transport import TransportError

from elasticsearch import (
    AuthorizationException,
    Elasticsearch,
    NotFoundError,
    RequestError,
)

SOURCE_DIR = Path(__file__).absolute().parent.parent
CA_CERTS = str(SOURCE_DIR / ".ci/certs/ca.crt")


def es_url() -> str:
    """Grabs an Elasticsearch URL which can be designated via
    an environment variable otherwise falls back on localhost.
    """
    urls_to_try = []

    # Try user-supplied URLs before generic localhost ones.
    if os.environ.get("ELASTICSEARCH_URL", ""):
        urls_to_try.append(os.environ["ELASTICSEARCH_URL"])
    if os.environ.get("elasticsearch_url", ""):
        urls_to_try.append(os.environ["elasticsearch_url"])
    urls_to_try.extend(
        [
            "https://localhost:9200",
            "http://localhost:9200",
            "https://elastic:changeme@localhost:9200",
            "http://elastic:changeme@localhost:9200",
        ]
    )

    error = None
    for url in urls_to_try:
        if url.startswith("https://"):
            client = Elasticsearch(url, ca_certs=CA_CERTS, verify_certs=False)
        else:
            client = Elasticsearch(url)
        try:
            # Check that we get any sort of connection first.
            client.info()

            # After we get a connection let's wait for the cluster
            # to be in 'yellow' state, otherwise we could start
            # tests too early and get failures.
            for _ in range(100):
                try:
                    client.cluster.health(wait_for_status="yellow")
                    break
                except ConnectionError:
                    time.sleep(0.1)

        except TransportError as e:
            if error is None:
                error = str(e)
        else:
            successful_url = url
            break
    else:
        raise RuntimeError(
            "Could not connect to Elasticsearch (tried %s): %s"
            % (", ".join(urls_to_try), error)
        )
    return successful_url


def es_version(client) -> Tuple[int, ...]:
    """Determines the version number and parses the number as a tuple of ints"""
    resp = client.info()
    return parse_version(resp["version"]["number"])


def parse_version(version: Optional[str]) -> Optional[Tuple[int, ...]]:
    """Parses a version number string into it's major, minor, patch as a tuple"""
    if not version:
        return None
    version_number = tuple(
        int(x)
        for x in re.search(r"^([0-9]+(?:\.[0-9]+)*)", version).group(1).split(".")
    )
    return version_number


def wipe_cluster(client):
    """Wipes a cluster clean between test cases"""
    close_after_wipe = False
    try:
        # If client is async we need to replace the client
        # with a synchronous one.
        from elasticsearch import AsyncElasticsearch

        if isinstance(client, AsyncElasticsearch):
            node_config = client.transport.node_pool.get().config
            client = Elasticsearch([node_config], verify_certs=False)
            close_after_wipe = True
    except ImportError:
        pass

    is_xpack = True
    if is_xpack:
        wipe_rollup_jobs(client)
        wait_for_pending_tasks(client, filter="xpack/rollup/job")
        wipe_slm_policies(client)

        # Searchable snapshot indices start in 7.8+
        if es_version(client) >= (7, 8):
            wipe_searchable_snapshot_indices(client)

    wipe_snapshots(client)
    if is_xpack:
        wipe_data_streams(client)
    wipe_indices(client)

    if is_xpack:
        wipe_xpack_templates(client)
    else:
        client.indices.delete_template(name="*")
        client.indices.delete_index_template(name="*")
        client.cluster.delete_component_template(name="*")

    wipe_cluster_settings(client)

    if is_xpack:
        wipe_ilm_policies(client)
        wipe_auto_follow_patterns(client)
        wipe_tasks(client)
        wipe_node_shutdown_metadata(client)
        wait_for_pending_datafeeds_and_jobs(client)

    wait_for_cluster_state_updates_to_finish(client)
    if close_after_wipe:
        client.close()


def wipe_cluster_settings(client):
    settings = client.cluster.get_settings()
    new_settings = {}
    for name, value in settings.items():
        if value:
            new_settings.setdefault(name, {})
            for key in value.keys():
                new_settings[name][key + ".*"] = None
    if new_settings:
        client.cluster.put_settings(body=new_settings)


def wipe_rollup_jobs(client):
    rollup_jobs = client.rollup.get_jobs(id="_all").get("jobs", ())
    for job in rollup_jobs:
        job_id = job["config"]["id"]
        client.options(ignore_status=404).rollup.stop_job(
            id=job_id, wait_for_completion=True
        )
        client.options(ignore_status=404).rollup.delete_job(id=job_id)


def wipe_snapshots(client):
    """Deletes all the snapshots and repositories from the cluster"""
    in_progress_snapshots = []

    repos = client.snapshot.get_repository(name="_all")
    for repo_name, repo in repos.items():
        if repo_name in {"found-snapshots"}:
            continue

        if repo["type"] == "fs":
            snapshots = client.snapshot.get(
                repository=repo_name, snapshot="_all", ignore_unavailable=True
            )
            for snapshot in snapshots["snapshots"]:
                if snapshot["state"] == "IN_PROGRESS":
                    in_progress_snapshots.append(snapshot)
                else:
                    client.options(ignore_status=404).snapshot.delete(
                        repository=repo_name,
                        snapshot=snapshot["snapshot"],
                    )

        client.options(ignore_status=404).snapshot.delete_repository(
            repository=repo_name
        )

    assert in_progress_snapshots == []


def wipe_data_streams(client):
    try:
        client.indices.delete_data_stream(name="*", expand_wildcards="all")
    except Exception:
        client.indices.delete_data_stream(name="*")


def wipe_indices(client):
    client.options(ignore_status=404).indices.delete(
        index="*,-.ds-ilm-history-*",
        expand_wildcards="all",
    )


def wipe_searchable_snapshot_indices(client):
    cluster_metadata = client.cluster.state(
        metric="metadata",
        filter_path="metadata.indices.*.settings.index.store.snapshot",
    )
    if cluster_metadata:
        for index in cluster_metadata["metadata"]["indices"].keys():
            client.indices.delete(index=index)


def wipe_xpack_templates(client):
    templates = [
        x.strip() for x in client.cat.templates(h="name").split("\n") if x.strip()
    ]
    for template in templates:
        if is_xpack_template(template):
            continue
        try:
            client.indices.delete_template(name=template)
        except NotFoundError as e:
            if f"index_template [{template}] missing" in str(e):
                client.indices.delete_index_template(name=template)

    # Delete component templates, need to retry because sometimes
    # indices aren't cleaned up in time before we issue the delete.
    templates = client.cluster.get_component_template()["component_templates"]
    templates_to_delete = [
        template for template in templates if not is_xpack_template(template["name"])
    ]
    for _ in range(3):
        for template in list(templates_to_delete):
            try:
                client.cluster.delete_component_template(
                    name=template["name"],
                )
            except RequestError:
                pass
            else:
                templates_to_delete.remove(template)

        if not templates_to_delete:
            break
        time.sleep(0.01)


def wipe_ilm_policies(client):
    for policy in client.ilm.get_lifecycle():
        if policy not in {
            "ilm-history-ilm-policy",
            "slm-history-ilm-policy",
            "watch-history-ilm-policy",
            "ml-size-based-ilm-policy",
            "logs",
            "metrics",
            "synthetics",
            "7-days-default",
            "30-days-default",
            "90-days-default",
            "180-days-default",
            "365-days-default",
            ".fleet-actions-results-ilm-policy",
            ".deprecation-indexing-ilm-policy",
        }:
            client.ilm.delete_lifecycle(name=policy)


def wipe_slm_policies(client):
    policies = client.slm.get_lifecycle()
    for policy in policies:
        if policy not in {"cloud-snapshot-policy"}:
            client.slm.delete_lifecycle(policy_id=policy)


def wipe_auto_follow_patterns(client):
    for pattern in client.ccr.get_auto_follow_pattern()["patterns"]:
        client.ccr.delete_auto_follow_pattern(name=pattern["name"])


def wipe_node_shutdown_metadata(client):
    try:
        shutdown_status = client.shutdown.get_node()
        # If response contains these two keys the feature flag isn't enabled
        # on this cluster so skip this step now.
        if "_nodes" in shutdown_status and "cluster_name" in shutdown_status:
            return

        for shutdown_node in shutdown_status.get("nodes", []):
            node_id = shutdown_node["node_id"]
            client.shutdown.delete_node(node_id=node_id)

    # Elastic Cloud doesn't allow this so we skip.
    except AuthorizationException:
        pass


def wipe_tasks(client):
    tasks = client.tasks.list()
    for node_name, node in tasks.get("node", {}).items():
        for task_id in node.get("tasks", ()):
            client.tasks.cancel(task_id=task_id, wait_for_completion=True)


def wait_for_pending_tasks(client, filter, timeout=30):
    end_time = time.time() + timeout
    while time.time() < end_time:
        tasks = client.cat.tasks(detailed=True).split("\n")
        if not any(filter in task for task in tasks):
            break


def wait_for_pending_datafeeds_and_jobs(client, timeout=30):
    end_time = time.time() + timeout
    while time.time() < end_time:
        if client.ml.get_datafeeds(datafeed_id="*", allow_no_match=True)["count"] == 0:
            break
    while time.time() < end_time:
        if client.ml.get_jobs(job_id="*", allow_no_match=True)["count"] == 0:
            break


def wait_for_cluster_state_updates_to_finish(client, timeout=30):
    end_time = time.time() + timeout
    while time.time() < end_time:
        if not client.cluster.pending_tasks().get("tasks", ()):
            break


def is_xpack_template(name):
    if ".monitoring-" in name:
        return True
    if ".watch" in name or ".triggered_watches" in name:
        return True
    if ".data-frame-" in name:
        return True
    if ".ml-" in name:
        return True
    if ".transform-" in name:
        return True
    if name in {
        ".watches",
        "logstash-index-template",
        ".logstash-management",
        "security_audit_log",
        ".slm-history",
        ".async-search",
        ".geoip_databases",
        "saml-service-provider",
        "ilm-history",
        "logs",
        "logs-settings",
        "logs-mappings",
        "metrics",
        "metrics-settings",
        "metrics-mappings",
        "synthetics",
        "synthetics-settings",
        "synthetics-mappings",
        ".snapshot-blob-cache",
        "data-streams-mappings",
    }:
        return True
    return False
