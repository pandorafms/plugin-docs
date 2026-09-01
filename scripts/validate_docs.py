#!/usr/bin/env python3
"""Validate documentation quality gates without third-party dependencies."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit


SEVERITY_ORDER = {"BLOCKING": 0, "REPORT": 1}
MARKERS = ("SCREENSHOT NEEDED", "TODO", "FIXME", "TBD")
LEGACY_URL_PREFIXES = (
    "https://prewebs.pandorafms.com/docs/index.php",
    "https://pandorafms.com/docs/index.php",
    "https://pandorafms.com/manual/en/documentation/02_installation/",
    "https://pandorafms.com/manual/en/documentation/04_using/",
    "https://pandorafms.com/manual/en/documentation/05_big_environments/",
    "https://pandorafms.com/manual/es/documentation/02_installation/",
    "https://pandorafms.com/manual/es/documentation/04_using/",
    "https://pandorafms.com/manual/es/documentation/05_big_environments/",
    "https://developers.google.com/hangouts/",
)

LINK_RE = re.compile(r"(?P<image>!)?\[[^\]]*\]\((?P<target><[^>]+>|[^\s)]+)(?:\s+[^)]*)?\)")
URL_RE = re.compile(r"https?://[^\s<>\])\"']+")
INLINE_CODE_RE = re.compile(r"(`+)(.*?)\1")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->")
H1_RE = re.compile(r"^#(?!#)\s+\S")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
BRAND_RE = re.compile(r"(?<![\w/])PandoraFMS(?![\w/])")
MARKER_LINE_RE = re.compile(
    r"^\s*(?:[-*+]\s+|\[\s*\]\s*)?(SCREENSHOT NEEDED|TODO|FIXME|TBD)(?:\s*[:—-].*)?\s*$"
)
SECRET_PATTERNS = (
    ("PEM private key", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----")),
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("GitHub token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,255}|github_pat_[A-Za-z0-9_]{22,255})\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("OpenAI API key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}\b")),
    ("Stripe live secret key", re.compile(r"\bsk_live_[A-Za-z0-9]{24,}\b")),
)


class ValidationError(Exception):
    """A configuration or filesystem error that prevents validation."""


@dataclass(frozen=True)
class Issue:
    severity: str
    code: str
    path: str
    line: int
    message: str

    def sort_key(self) -> tuple[int, str, int, str, str]:
        return (SEVERITY_ORDER[self.severity], self.path, self.line, self.code, self.message)


@dataclass(frozen=True)
class MarkdownFile:
    path: Path
    display_path: str
    language: str
    lines: tuple[str, ...]
    visible_lines: tuple[str | None, ...]


def _visible_lines(lines: tuple[str, ...]) -> tuple[str | None, ...]:
    visible: list[str | None] = []
    fence_char = ""
    fence_length = 0
    for line in lines:
        match = re.match(r"^\s*(`{3,}|~{3,})", line)
        if match:
            marker = match.group(1)
            if not fence_char:
                fence_char, fence_length = marker[0], len(marker)
            elif marker[0] == fence_char and len(marker) >= fence_length:
                fence_char, fence_length = "", 0
            visible.append(None)
        elif fence_char:
            visible.append(None)
        else:
            visible.append(line)
    return tuple(visible)


def _read_markdown(path: Path, docs_dir: Path) -> MarkdownFile:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ValidationError(f"cannot read {path}: {error}") from error
    lines = tuple(text.splitlines())
    relative = path.relative_to(docs_dir)
    language = relative.parts[0] if relative.parts else ""
    display_path = (Path(docs_dir.name) / relative).as_posix()
    return MarkdownFile(path, display_path, language, lines, _visible_lines(lines))


def _markdown_files(docs_dir: Path) -> list[MarkdownFile]:
    if not docs_dir.is_dir():
        raise ValidationError(f"docs directory does not exist or is not a directory: {docs_dir}")
    for language in ("en", "es"):
        if not (docs_dir / language).is_dir():
            raise ValidationError(f"missing language directory: {docs_dir / language}")
    try:
        paths = sorted(
            path
            for language in ("en", "es")
            for path in (docs_dir / language).rglob("*.md")
            if path.is_file()
        )
    except OSError as error:
        raise ValidationError(f"cannot enumerate {docs_dir}: {error}") from error
    return [_read_markdown(path, docs_dir) for path in paths]


def _parity_issues(files: list[MarkdownFile], docs_dir: Path) -> list[Issue]:
    by_language = {
        language: {
            markdown.path.relative_to(docs_dir / language).as_posix(): markdown
            for markdown in files
            if markdown.language == language
        }
        for language in ("en", "es")
    }
    issues: list[Issue] = []
    for relative in sorted(set(by_language["en"]) ^ set(by_language["es"])):
        present = "en" if relative in by_language["en"] else "es"
        missing = "es" if present == "en" else "en"
        markdown = by_language[present][relative]
        issues.append(
            Issue(
                "BLOCKING",
                "PARITY",
                markdown.display_path,
                1,
                f"missing {missing} counterpart for {relative}",
            )
        )
    return issues


def _strip_inline_code(text: str) -> str:
    return INLINE_CODE_RE.sub("", text)


def _rendered_text(line: str) -> str:
    text = HTML_COMMENT_RE.sub("", _strip_inline_code(line))
    text = LINK_RE.sub(lambda match: "" if match.group("image") else match.group(0).split("]", 1)[0][1:], text)
    text = re.sub(r"<https?://[^>]+>", "", text)
    text = URL_RE.sub("", text)
    return text


def _slugify_heading(heading: str) -> str:
    text = _strip_inline_code(heading)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[*_~]", "", text)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[-\s]+", "-", text).strip("-")


def _anchors(markdown: MarkdownFile) -> set[str]:
    anchors: set[str] = set()
    counts: dict[str, int] = {}
    for line in markdown.visible_lines:
        if line is None:
            continue
        match = HEADING_RE.match(line)
        if not match:
            continue
        base = _slugify_heading(match.group(2))
        if not base:
            continue
        count = counts.get(base, 0)
        counts[base] = count + 1
        anchors.add(base if count == 0 else f"{base}_{count}")
    return anchors


def _resolve_local_target(source: MarkdownFile, raw_target: str, docs_dir: Path) -> tuple[Path | None, str]:
    target = raw_target[1:-1] if raw_target.startswith("<") and raw_target.endswith(">") else raw_target
    parsed = urlsplit(target)
    fragment = unquote(parsed.fragment)
    path_text = unquote(parsed.path)
    if not path_text:
        return source.path, fragment
    candidate = docs_dir / path_text.lstrip("/") if path_text.startswith("/") else source.path.parent / path_text
    candidates = [candidate]
    if not candidate.suffix:
        candidates.extend((candidate.with_suffix(".md"), candidate / "index.md"))
    elif candidate.suffix.lower() in (".html", ".htm"):
        candidates.append(candidate.with_suffix(".md"))
    for possible in candidates:
        if possible.exists():
            return possible.resolve(), fragment
    return None, fragment


def _image_exists(source: MarkdownFile, target: str, docs_dir: Path) -> bool:
    parsed = urlsplit(target.strip("<>"))
    path_text = unquote(parsed.path)
    candidate = docs_dir / path_text.lstrip("/") if path_text.startswith("/") else source.path.parent / path_text
    if candidate.is_file():
        return True
    if source.language != "es":
        return False
    try:
        source_in_en = docs_dir / "en" / source.path.relative_to(docs_dir / "es")
    except ValueError:
        return False
    if path_text.startswith("/"):
        relative = Path(path_text.lstrip("/"))
        fallback = docs_dir / "en" / Path(*relative.parts[1:]) if relative.parts[:1] == ("es",) else docs_dir / relative
    else:
        fallback = source_in_en.parent / path_text
    return fallback.is_file()


def _is_external(target: str) -> bool:
    scheme = urlsplit(target.strip("<>")).scheme.lower()
    return scheme in {"http", "https", "mailto", "tel", "data"}


def _crosses_language(source: MarkdownFile, target: str, docs_dir: Path) -> bool:
    parsed = urlsplit(target.strip("<>"))
    path_text = unquote(parsed.path)
    if not path_text:
        return False
    parts = tuple(part for part in Path(path_text).parts if part not in ("/", ".", ".."))
    other = "es" if source.language == "en" else "en"
    if other not in parts:
        return False
    if parsed.scheme.lower() in {"http", "https"}:
        return True
    resolved = docs_dir / path_text.lstrip("/") if path_text.startswith("/") else source.path.parent / path_text
    try:
        return resolved.resolve().is_relative_to((docs_dir / other).resolve())
    except (OSError, ValueError):
        return f"/{other}/" in f"/{path_text.strip('/')}/"


def _content_issues(markdown: MarkdownFile, docs_dir: Path, file_index: dict[Path, MarkdownFile]) -> list[Issue]:
    issues: list[Issue] = []
    h1_lines = [number for number, line in enumerate(markdown.visible_lines, 1) if line is not None and H1_RE.match(line)]
    if len(h1_lines) != 1:
        line = h1_lines[1] if len(h1_lines) > 1 else 1
        issues.append(Issue("BLOCKING", "H1", markdown.display_path, line, f"expected exactly one H1, found {len(h1_lines)}"))

    for number, original_line in enumerate(markdown.lines, 1):
        for label, pattern in SECRET_PATTERNS:
            if pattern.search(original_line):
                issues.append(Issue("BLOCKING", "SECRET", markdown.display_path, number, f"high-confidence {label} detected"))

    for number, line in enumerate(markdown.visible_lines, 1):
        if line is None:
            continue
        scan_line = INLINE_CODE_RE.sub("", line)
        for match in LINK_RE.finditer(scan_line):
            target = match.group("target").strip("<>")
            if match.group("image"):
                if not _is_external(target) and not _image_exists(markdown, target, docs_dir):
                    issues.append(Issue("BLOCKING", "IMAGE", markdown.display_path, number, f"missing local image: {target}"))
                continue
            if _crosses_language(markdown, target, docs_dir):
                issues.append(Issue("REPORT", "CROSS_LANGUAGE", markdown.display_path, number, f"explicit cross-language link: {target}"))
            if _is_external(target):
                continue
            resolved, fragment = _resolve_local_target(markdown, target, docs_dir)
            if resolved is None:
                issues.append(Issue("REPORT", "LOCAL_LINK", markdown.display_path, number, f"missing local link target: {target}"))
            elif fragment:
                target_markdown = file_index.get(resolved)
                if target_markdown is not None and fragment not in _anchors(target_markdown):
                    issues.append(Issue("REPORT", "ANCHOR", markdown.display_path, number, f"missing anchor #{fragment} in {target}"))

        rendered = _rendered_text(line)
        for _ in BRAND_RE.finditer(rendered):
            issues.append(Issue("REPORT", "BRAND", markdown.display_path, number, "rendered text uses PandoraFMS; prefer Pandora FMS"))

        comments = " ".join(HTML_COMMENT_RE.findall(line))
        marker_match = MARKER_LINE_RE.match(_strip_inline_code(HTML_COMMENT_RE.sub("", line)))
        found_markers = {marker for marker in MARKERS if marker in comments}
        if marker_match:
            found_markers.add(marker_match.group(1))
        for marker in sorted(found_markers):
            issues.append(Issue("REPORT", "MARKER", markdown.display_path, number, f"pending marker: {marker}"))

        for url_match in URL_RE.finditer(scan_line):
            url = url_match.group(0).rstrip(".,;:")
            if any(url.startswith(prefix) for prefix in LEGACY_URL_PREFIXES):
                issues.append(Issue("REPORT", "LEGACY_URL", markdown.display_path, number, f"legacy URL: {url}"))

    issues.extend(_contamination_issues(markdown))
    return issues


def _contamination_issues(markdown: MarkdownFile) -> list[Issue]:
    issues: list[Issue] = []
    relative = "/".join(markdown.path.parts[-3:])
    for number, line in enumerate(markdown.lines, 1):
        if relative.endswith("integrations/teams.md") and "Slack connector CLI" in line:
            issues.append(Issue("REPORT", "CONTAMINATION", markdown.display_path, number, "Slack connector reference in Microsoft Teams page"))
        if relative.endswith("integrations/google-chat.md") and "developers.google.com/hangouts/" in line:
            issues.append(Issue("REPORT", "CONTAMINATION", markdown.display_path, number, "Hangouts URL in Google Chat page"))
        if relative.endswith("discovery/apache-discovery.md"):
            for match in URL_RE.finditer(line):
                path = urlsplit(match.group(0)).path.rstrip("/")
                if path.endswith("/server") or path.endswith("/example"):
                    issues.append(Issue("REPORT", "CONTAMINATION", markdown.display_path, number, f"known Apache endpoint mismatch: {match.group(0).rstrip('.,;:')}"))
    if markdown.language == "en" and relative.endswith("integrations/telegram.md"):
        for number, line in enumerate(markdown.visible_lines, 1):
            if line is not None and "/manual/es/" in line:
                issues.append(Issue("REPORT", "CONTAMINATION", markdown.display_path, number, "Spanish manual target in English Telegram page"))
    return issues


def validate(docs_dir: Path) -> list[Issue]:
    docs_dir = docs_dir.resolve()
    files = _markdown_files(docs_dir)
    file_index = {markdown.path.resolve(): markdown for markdown in files}
    issues = _parity_issues(files, docs_dir)
    for markdown in files:
        issues.extend(_content_issues(markdown, docs_dir, file_index))
    return sorted(issues, key=Issue.sort_key)


def _summary(issues: list[Issue]) -> dict[str, int]:
    blocking = sum(issue.severity == "BLOCKING" for issue in issues)
    report = len(issues) - blocking
    return {"blocking": blocking, "report": report, "total": len(issues)}


def format_text(issues: list[Issue]) -> str:
    lines = [f"{issue.severity} {issue.code} {issue.path}:{issue.line} {issue.message}" for issue in issues]
    summary = _summary(issues)
    lines.append(f"SUMMARY blocking={summary['blocking']} report={summary['report']} total={summary['total']}")
    return "\n".join(lines)


def format_json(issues: list[Issue]) -> str:
    payload = {"issues": [asdict(issue) for issue in issues], "summary": _summary(issues)}
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)


def _should_fail(issues: list[Issue], fail_on: str) -> bool:
    if fail_on == "none":
        return False
    if fail_on == "all":
        return bool(issues)
    return any(issue.severity == "BLOCKING" for issue in issues)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs-dir", type=Path, default=Path("docs"), help="documentation root (default: docs)")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="output format (default: text)")
    parser.add_argument("--fail-on", choices=("blocking", "all", "none"), default="blocking", help="issue severity that controls exit status (default: blocking)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        issues = validate(args.docs_dir)
    except ValidationError as error:
        print(f"ERROR {error}", file=sys.stderr)
        return 2
    print(format_json(issues) if args.format == "json" else format_text(issues))
    return 1 if _should_fail(issues, args.fail_on) else 0


if __name__ == "__main__":
    raise SystemExit(main())
