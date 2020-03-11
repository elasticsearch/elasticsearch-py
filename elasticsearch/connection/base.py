import logging
import binascii
import gzip
import io
from platform import python_version

try:
    import simplejson as json
except ImportError:
    import json

from ..exceptions import TransportError, ImproperlyConfigured, HTTP_EXCEPTIONS
from .. import __versionstr__

logger = logging.getLogger("elasticsearch")

# create the elasticsearch.trace logger, but only set propagate to False if the
# logger hasn't already been configured
_tracer_already_configured = "elasticsearch.trace" in logging.Logger.manager.loggerDict
tracer = logging.getLogger("elasticsearch.trace")
if not _tracer_already_configured:
    tracer.propagate = False


class Connection(object):
    """
    Class responsible for maintaining a connection to an Elasticsearch node. It
    holds persistent connection pool to it and it's main interface
    (`perform_request`) is thread-safe.

    Also responsible for logging.

    :arg host: hostname of the node (default: localhost)
    :arg port: port to use (integer, default: 9200)
    :arg use_ssl: use ssl for the connection if `True`
    :arg url_prefix: optional url prefix for elasticsearch
    :arg timeout: default timeout in seconds (float, default: 10)
    :arg http_compress: Use gzip compression
    :arg cloud_id: The Cloud ID from ElasticCloud. Convenient way to connect to cloud instances.
    """

    def __init__(
        self,
        host="localhost",
        port=None,
        use_ssl=False,
        url_prefix="",
        timeout=10,
        headers=None,
        http_compress=None,
        cloud_id=None,
        api_key=None,
        **kwargs
    ):

        if cloud_id:
            try:
                _, cloud_id = cloud_id.split(":")
                parent_dn, es_uuid = (
                    binascii.a2b_base64(cloud_id.encode("utf-8"))
                    .decode("utf-8")
                    .split("$")[:2]
                )
                if ":" in parent_dn:
                    parent_dn, _, parent_port = parent_dn.rpartition(":")
                    if port is None and parent_port != "443":
                        port = int(parent_port)
            except (ValueError, IndexError):
                raise ImproperlyConfigured("'cloud_id' is not properly formatted")

            host = "%s.%s" % (es_uuid, parent_dn)
            use_ssl = True
            if http_compress is None:
                http_compress = True

        # If cloud_id isn't set and port is default then use 9200.
        # Cloud should use '443' by default via the 'https' scheme.
        elif port is None:
            port = 9200

        # Work-around if the implementing class doesn't
        # define the headers property before calling super().__init__()
        if not hasattr(self, "headers"):
            self.headers = {}

        headers = headers or {}
        for key in headers:
            self.headers[key.lower()] = headers[key]

        self.headers.setdefault("content-type", "application/json")
        self.headers.setdefault("user-agent", self._get_default_user_agent())

        if api_key is not None:
            self.headers["authorization"] = self._get_api_key_header_val(api_key)

        if http_compress:
            self.headers["accept-encoding"] = "gzip,deflate"

        scheme = kwargs.get("scheme", "http")
        if use_ssl or scheme == "https":
            scheme = "https"
            use_ssl = True
        self.use_ssl = use_ssl
        self.http_compress = http_compress or False

        self.hostname = host
        self.port = port
        self.host = "%s://%s" % (scheme, host)
        if self.port is not None:
            self.host += ":%s" % self.port
        if url_prefix:
            url_prefix = "/" + url_prefix.strip("/")
        self.url_prefix = url_prefix
        self.timeout = timeout

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.host)

    def __eq__(self, other):
        if not isinstance(other, Connection):
            raise TypeError("Unsupported equality check for %s and %s" % (self, other))
        return self.__hash__() == other.__hash__()

    def __hash__(self):
        return id(self)

    def _gzip_compress(self, body):
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb") as f:
            f.write(body)
        return buf.getvalue()

    def _pretty_json(self, data):
        # pretty JSON in tracer curl logs
        try:
            return json.dumps(
                json.loads(data), sort_keys=True, indent=2, separators=(",", ": ")
            ).replace("'", r"\u0027")
        except (ValueError, TypeError):
            # non-json data or a bulk request
            return data

    def _log_trace(self, method, path, body, status_code, response, duration):
        if not tracer.isEnabledFor(logging.INFO) or not tracer.handlers:
            return

        # include pretty in trace curls
        path = path.replace("?", "?pretty&", 1) if "?" in path else path + "?pretty"
        if self.url_prefix:
            path = path.replace(self.url_prefix, "", 1)
        tracer.info(
            "curl %s-X%s 'http://localhost:9200%s' -d '%s'",
            "-H 'Content-Type: application/json' " if body else "",
            method,
            path,
            self._pretty_json(body) if body else "",
        )

        if tracer.isEnabledFor(logging.DEBUG):
            tracer.debug(
                "#[%s] (%.3fs)\n#%s",
                status_code,
                duration,
                self._pretty_json(response).replace("\n", "\n#") if response else "",
            )

    def log_request_success(
        self, method, full_url, path, body, status_code, response, duration
    ):
        """ Log a successful API call.  """
        #  TODO: optionally pass in params instead of full_url and do urlencode only when needed

        # body has already been serialized to utf-8, deserialize it for logging
        # TODO: find a better way to avoid (de)encoding the body back and forth
        if body:
            try:
                body = body.decode("utf-8", "ignore")
            except AttributeError:
                pass

        logger.info(
            "%s %s [status:%s request:%.3fs]", method, full_url, status_code, duration
        )
        logger.debug("> %s", body)
        logger.debug("< %s", response)

        self._log_trace(method, path, body, status_code, response, duration)

    def log_request_fail(
        self,
        method,
        full_url,
        path,
        body,
        duration,
        status_code=None,
        response=None,
        exception=None,
    ):
        """ Log an unsuccessful API call.  """
        # do not log 404s on HEAD requests
        if method == "HEAD" and status_code == 404:
            return
        logger.warning(
            "%s %s [status:%s request:%.3fs]",
            method,
            full_url,
            status_code or "N/A",
            duration,
            exc_info=exception is not None,
        )

        # body has already been serialized to utf-8, deserialize it for logging
        # TODO: find a better way to avoid (de)encoding the body back and forth
        if body:
            try:
                body = body.decode("utf-8", "ignore")
            except AttributeError:
                pass

        logger.debug("> %s", body)

        self._log_trace(method, path, body, status_code, response, duration)

        if response is not None:
            logger.debug("< %s", response)

    def _raise_error(self, status_code, raw_data):
        """ Locate appropriate exception and raise it. """
        error_message = raw_data
        additional_info = None
        try:
            if raw_data:
                additional_info = json.loads(raw_data)
                error_message = additional_info.get("error", error_message)
                if isinstance(error_message, dict) and "type" in error_message:
                    error_message = error_message["type"]
        except (ValueError, TypeError) as err:
            logger.warning("Undecodable raw error response from server: %s", err)

        raise HTTP_EXCEPTIONS.get(status_code, TransportError)(
            status_code, error_message, additional_info
        )

    def _get_default_user_agent(self):
        return "elasticsearch-py/%s (Python %s)" % (__versionstr__, python_version())

    def _get_api_key_header_val(self, api_key):
        """
        Check the type of the passed api_key and return the correct header value
        for the `API Key authentication <https://www.elastic.co/guide/en/elasticsearch/reference/current/security-api-create-api-key.html>`
        :arg api_key, either a tuple or a base64 encoded string
        """
        if isinstance(api_key, (tuple, list)):
            s = "{0}:{1}".format(api_key[0], api_key[1]).encode("utf-8")
            return "ApiKey " + binascii.b2a_base64(s).rstrip(b"\r\n").decode("utf-8")
        return "ApiKey " + api_key
