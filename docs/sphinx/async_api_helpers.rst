Async Helpers
=============

Async variants of all helpers are available in ``elasticsearch.helpers``
and are all prefixed with ``async_*``. You'll notice that these APIs
are identical to the ones in the sync :ref:`helpers` documentation.

All async helpers that accept an iterator or generator also accept async iterators
and async generators.

 .. py:module:: elasticsearch.helpers
    :no-index:

Streaming Bulk
--------------
 .. autofunction:: async_streaming_bulk

Bulk
----
 .. autofunction:: async_bulk

Scan
----
 .. autofunction:: async_scan

Reindex
-------
 .. autofunction:: async_reindex

