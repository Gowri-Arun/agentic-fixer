from app.parser import parse_html


def test_parser_extracts_visible_text():
    html = "<html><body><h1>Hello</h1><p>World</p></body></html>"

    parsed = parse_html(html)

    assert "Hello" in parsed["text"]
    assert "World" in parsed["text"]


def test_parser_extracts_headings():
    html = """
    <html>
      <body>
        <h1>Main</h1>
        <h2>Section</h2>
      </body>
    </html>
    """

    parsed = parse_html(html)

    assert {"level": 1, "text": "Main"} in parsed["headings"]
    assert {"level": 2, "text": "Section"} in parsed["headings"]


def test_parser_extracts_valid_json_ld():
    html = """
    <html>
      <head>
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "FAQPage"
        }
        </script>
      </head>
      <body></body>
    </html>
    """

    parsed = parse_html(html)

    assert parsed["json_ld"][0]["@type"] == "FAQPage"


def test_parser_ignores_invalid_json_ld():
    html = """
    <html>
      <head>
        <script type="application/ld+json">
        { invalid json
        </script>
      </head>
      <body><h1>Test</h1></body>
    </html>
    """

    parsed = parse_html(html)

    assert parsed["json_ld"] == []
    assert "Test" in parsed["text"]
