from uk_stress_benchmark.sync_sources import parse_verified_urls


def test_parse_handles_arrow_em_dash_and_hyphen_separators_and_strips_brackets():
    md = """
Some prose above.

**Verified direct URLs**:

- `arrow.pdf` → <https://example.com/a.pdf>
- `em-dash.xlsx` — https://example.com/b.xlsx
- `hyphen.csv` - <https://example.com/c.csv>

Some prose below.
"""
    assert parse_verified_urls(md) == {
        "arrow.pdf": "https://example.com/a.pdf",
        "em-dash.xlsx": "https://example.com/b.xlsx",
        "hyphen.csv": "https://example.com/c.csv",
    }


def test_parse_ignores_bullets_without_a_url():
    md = """
- `no-url.pdf` - source unknown
- `with-url.pdf` -> <https://example.com/x.pdf>
"""
    assert parse_verified_urls(md) == {"with-url.pdf": "https://example.com/x.pdf"}


def test_parse_ignores_inline_code_in_prose():
    md = "Some prose mentioning `not-a-bullet.pdf` somewhere."
    assert parse_verified_urls(md) == {}
