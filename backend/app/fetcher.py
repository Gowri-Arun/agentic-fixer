import requests


class FetchError(Exception):
    pass


def fetch_html(url: str) -> str:
    headers = {"User-Agent": "AgenticFixerBot/0.1"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise FetchError(f"Failed to fetch URL: {exc}") from exc

    return response.text
