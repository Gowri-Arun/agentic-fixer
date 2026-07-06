import json

from bs4 import BeautifulSoup


def parse_html(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text(" ", strip=True)

    headings = []
    for level in range(1, 7):
        for tag in soup.find_all(f"h{level}"):
            headings.append(
                {
                    "level": level,
                    "text": tag.get_text(" ", strip=True),
                }
            )

    json_ld = []
    invalid_json_ld_count = 0
    for script in soup.find_all("script", type="application/ld+json"):
        raw_json = script.string
        if not raw_json:
            continue

        try:
            json_ld.append(json.loads(raw_json))
        except json.JSONDecodeError:
            invalid_json_ld_count += 1
            continue

    return {
        "text": text,
        "text_lower": text.lower(),
        "headings": headings,
        "json_ld": json_ld,
        "invalid_json_ld_count": invalid_json_ld_count,
    }
