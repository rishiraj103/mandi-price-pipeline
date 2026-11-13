"""Client for the data.gov.in mandi price API."""
import logging
import time

import requests

BASE_URL = "https://api.data.gov.in/resource/{resource_id}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "application/json",
}
RETRY_STATUS = {429, 500, 502, 503, 504}

log = logging.getLogger(__name__)


class ApiAuthError(Exception):
    """The API rejected the key (HTTP 401/403)."""


class ApiUnavailableError(Exception):
    """The API kept failing after all retries."""


class MandiApiClient:
    def __init__(self, api_key, resource_id, timeout=(15, 120), max_retries=3, page_size=10000):
        self.api_key = api_key
        self.url = BASE_URL.format(resource_id=resource_id)
        self.timeout = timeout
        self.max_retries = max_retries
        self.page_size = page_size
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def fetch_page(self, filters, limit, offset):
        params = {"api-key": self.api_key, "format": "json", "limit": limit, "offset": offset}
        params.update({f"filters[{k}]": v for k, v in filters.items()})

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(self.url, params=params, timeout=self.timeout)
            except (requests.Timeout, requests.ConnectionError) as exc:
                reason = type(exc).__name__
            else:
                if resp.status_code in (401, 403):
                    raise ApiAuthError(f"HTTP {resp.status_code}: check DATA_GOV_API_KEY")
                if resp.status_code not in RETRY_STATUS:
                    resp.raise_for_status()
                    return resp.json()
                reason = f"HTTP {resp.status_code}"

            log.warning("attempt %d/%d failed (%s) filters=%s offset=%d",
                        attempt, self.max_retries, reason, filters, offset)
            if attempt < self.max_retries:
                time.sleep(2 ** attempt)

        raise ApiUnavailableError(f"gave up after {self.max_retries} attempts: {reason}")

    def fetch_all(self, filters):
        records, offset = [], 0
        while True:
            page = self.fetch_page(filters, self.page_size, offset).get("records", [])
            records.extend(page)
            if len(page) < self.page_size:
                return records
            offset += self.page_size
