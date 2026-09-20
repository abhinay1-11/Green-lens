import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_session: requests.Session = None

def get_http_session() -> requests.Session:
    """
    Returns a singleton HTTP Session with connection pooling and retry configuration
    to minimize TCP/TLS handshake latency for external APIs.
    """
    global _session
    if _session is None:
        _session = requests.Session()
        retries = Retry(
            total=2,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(
            pool_connections=15,
            pool_maxsize=30,
            max_retries=retries
        )
        _session.mount("https://", adapter)
        _session.mount("http://", adapter)
        _session.headers.update({
            "User-Agent": "GreenLensBiodiversityApp/1.0 (contact@greenlens.org)"
        })
    return _session
