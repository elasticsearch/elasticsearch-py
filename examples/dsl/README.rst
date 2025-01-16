Elasticsearch DSL Examples
==========================

In this directory you can see several complete examples demonstrating key
concepts and patterns exposed by ``elasticsearch-dsl``.

``alias_migration.py``
----------------------

The alias migration example shows a useful pattern where we use versioned
indices (``test-blog-0``, ``test-blog-1``, ...) to manage schema changes and
hides that behind an alias so that the application doesn't have to be aware of
the versions and just refer to the ``test-blog`` alias for both read and write
operations.

For simplicity we use a timestamp as version in the index name.

``parent_child.py``
-------------------

More complex example highlighting the possible relationships available in
elasticsearch - `parent/child
<https://www.elastic.co/guide/en/elasticsearch/reference/6.3/nested.html>`_ and
`nested
<https://www.elastic.co/guide/en/elasticsearch/reference/6.3/nested.html>`_.

``composite_agg.py``
--------------------

A helper function using the `composite aggregation
<https://www.elastic.co/guide/en/elasticsearch/reference/current/search-aggregations-bucket-composite-aggregation.html>`_
to paginate over aggregation results.

``percolate.py``
----------------

A ``BlogPost`` document with automatic classification using the `percolator
<https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-percolate-query.html>`_
functionality.

``completion.py``
-----------------

As example using `completion suggester
<https://www.elastic.co/guide/en/elasticsearch/reference/current/search-suggesters-completion.html>`_
to auto complete people's names.

