from .trustpilot import TrustpilotConnector
from .google_play import GooglePlayConnector
from .reddit import RedditConnector

CONNECTORS = {
    "trustpilot.com": TrustpilotConnector,
    "play.google.com": GooglePlayConnector,
    "reddit.com": RedditConnector
}

def detect_connector(url: str):
    """Detects the appropriate connector based on the URL domain."""
    for domain, connector_class in CONNECTORS.items():
        if domain in url:
            return connector_class()
    return None
