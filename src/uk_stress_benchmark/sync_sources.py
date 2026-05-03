"""Sync raw input files declared in SOURCES.md into a target directory.

The companion ``SOURCES.md`` file at the repo root carries a "Verified direct
URLs" section listing each raw file we know how to fetch. Each entry is a
markdown bullet of the form::

    - `filename.ext` -> <https://example.com/path/filename.ext>

Running ``python -m uk_stress_benchmark.sync_sources`` walks that list and
downloads any file not already present under ``raw_inputs/``. The operation is
idempotent: re-running it after a successful sync does nothing.

Public surface is intentionally small: :func:`sync` is the one-shot entrypoint
and :func:`parse_verified_urls` is exposed for testing and reuse.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.request import Request, urlopen

# Match a verified-URL bullet. The line must start with "- `name`" and
# contain an http(s) URL further along on the same line. Anything in between
# (em dash, arrow, "->", angle brackets, etc.) is treated as separator junk.
_VERIFIED_URL_RE = re.compile(
    r"^\s*-\s*`(?P<name>[^`]+)`.*?(?P<url>https?://[^\s>]+)",
    re.MULTILINE,
)


@dataclass
class SyncReport:
    downloaded: list[tuple[str, int]] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)

    def summary(self) -> str:
        lines: list[str] = []
        if self.downloaded:
            lines.append(f"Downloaded {len(self.downloaded)}:")
            for name, size in self.downloaded:
                lines.append(f"  + {name} ({size:,} bytes)")
        if self.skipped:
            lines.append(f"Skipped {len(self.skipped)} (already present):")
            for name in self.skipped:
                lines.append(f"  . {name}")
        if self.failed:
            lines.append(f"Failed {len(self.failed)}:")
            for name, err in self.failed:
                lines.append(f"  ! {name}: {err}")
        return "\n".join(lines) if lines else "Nothing to do."


def parse_verified_urls(md_text: str) -> dict[str, str]:
    """Return {filename: url} for every verified-URL bullet in ``md_text``."""
    return {m.group("name"): m.group("url") for m in _VERIFIED_URL_RE.finditer(md_text)}


def _download(url: str, dest: Path, *, chunk: int = 1 << 16) -> int:
    req = Request(
        url,
        headers={
            "User-Agent": "uk_stress_benchmark/0.1 (+https://github.com/quietsnooze/Pm_benchmarking)"
        },
    )
    written = 0
    with urlopen(req) as resp, dest.open("wb") as fh:
        while data := resp.read(chunk):
            fh.write(data)
            written += len(data)
    return written


def sync(sources_md: Path, target_dir: Path) -> SyncReport:
    """Sync verified URLs in ``sources_md`` into ``target_dir``.

    Idempotent: existing files in ``target_dir`` are not re-downloaded. Failed
    downloads leave no partial file behind.
    """
    md_text = sources_md.read_text(encoding="utf-8")
    pairs = parse_verified_urls(md_text)
    target_dir.mkdir(parents=True, exist_ok=True)

    report = SyncReport()
    for name, url in pairs.items():
        dest = target_dir / name
        if dest.exists():
            report.skipped.append(name)
            continue
        try:
            size = _download(url, dest)
            report.downloaded.append((name, size))
        except Exception as exc:  # network, HTTP, disk — all surface here
            if dest.exists():
                dest.unlink()
            report.failed.append((name, f"{type(exc).__name__}: {exc}"))
    return report


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    sources_md = repo_root / "SOURCES.md"
    target_dir = repo_root / "raw_inputs"
    print(f"Syncing {sources_md.name} -> {target_dir.relative_to(repo_root)}")
    report = sync(sources_md, target_dir)
    print(report.summary())


if __name__ == "__main__":
    main()
