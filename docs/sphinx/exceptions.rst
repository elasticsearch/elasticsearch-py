.. _exceptions:

Exceptions & Warnings
=====================

.. py:module:: elasticsearch
   :no-index:

API Errors
----------

These errors are triggered from an HTTP response that isn't 2XX:

.. autoclass:: ApiError
   :members:
.. autoclass:: NotFoundError
.. autoclass:: ConflictError
.. autoclass:: RequestError
.. autoclass:: AuthenticationException
.. autoclass:: AuthorizationException
.. autoclass:: ApiUnavailableException
.. autoclass:: UnsupportedProductError

Transport and Connection Errors
-------------------------------

These errors are triggered by an error occurring before an HTTP response arrives:

.. autoclass:: TransportError
.. autoclass:: SerializationError
.. autoclass:: ConnectionError
.. autoclass:: ConnectionTimeout
.. autoclass:: SSLError

Warnings
--------

.. autoclass:: ElasticsearchWarning
