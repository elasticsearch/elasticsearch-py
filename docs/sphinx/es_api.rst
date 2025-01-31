.. _api:

Elasticsearch API
=================

All the API calls map the raw REST API as closely as possible, including the
distinction between required and optional arguments to the calls. Keyword
arguments are required for all calls.

.. note::

   Some API parameters in Elasticsearch are reserved keywords in Python.
   For example the ``from`` query parameter for pagination would be aliased as
   ``from_``.

.. toctree::
   :maxdepth: 1

   api/elasticsearch
   api/async-search
   api/autoscaling
   api/cat
   api/ccr
   api/cluster
   api/connector
   api/dangling-indices
   api/enrich-policies
   api/eql
   api/esql
   api/fleet
   api/graph-explore
   api/index-lifecycle-management
   api/indices
   api/inference
   api/ingest-pipelines
   api/license
   api/logstash
   api/migration
   api/ml
   api/monitoring
   api/nodes
   api/query-rules
   api/rollup-indices
   api/search-application
   api/searchable-snapshots
   api/security
   api/shutdown
   api/simulate
   api/snapshot-lifecycle-management
   api/snapshots
   api/snapshottable-features
   api/sql
   api/synonyms
   api/tls-ssl
   api/tasks
   api/text-structure
   api/transforms
   api/watcher
   api/x-pack
