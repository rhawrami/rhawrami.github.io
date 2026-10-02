#!/usr/bin/env python3
"""Update only SITE_CONTENT.publications from Ravan's public AIBM profile."""

import argparse
from datetime import datetime
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import time
from urllib.error import URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

PROFILE_URL = "https://aibm.org/who-we-are/ravan-hawrami/"
CONTENT_PATH = Path(__file__).resolve().parents[1] / "js/content.js"
PUBLICATIONS_BLOCK = re.compile(
    r"(?P<prefix>\n  publications: )(?P<array>\[.*?\])(?=,\n  citations:)",
    re.DOTALL,
)
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input",
             "link", "meta", "param", "source", "track", "wbr"}


def publication_url(value):
    url = urlsplit(urljoin(PROFILE_URL, value))
    if url.scheme != "https" or url.netloc != "aibm.org":
        raise ValueError(f"Unexpected publication URL: {value!r}")
    if not re.fullmatch(r"/(research|commentary|policy)/[^/]+/?", url.path):
        raise ValueError(f"Unexpected publication path: {url.path!r}")
    return f"https://aibm.org{url.path.rstrip('/')}/"


class ProfileParser(HTMLParser):
    """Read cards inside the profile list, including cards hidden by View More."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.card = None
        self.publications = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = set(attrs.get("class", "").split())
        in_list = any("publications-list" in entry[1] for entry in self.stack)
        if tag == "a" and in_list:
            href = attrs.get("href", "")
            path = urlsplit(urljoin(PROFILE_URL, href)).path
            # The profile also lists events; only import publication articles.
            if re.match(r"^/(research|commentary|policy)/[^/]+/?$", path):
                if self.card is not None:
                    raise ValueError("Nested publication cards in AIBM profile")
                self.card = {"url": publication_url(href), "title": [], "date": []}
        if tag not in VOID_TAGS:
            self.stack.append((tag, classes))

    def handle_data(self, data):
        if self.card is None:
            return
        if any(tag == "h3" for tag, _ in self.stack):
            self.card["title"].append(data)
        if any("date" in classes for _, classes in self.stack):
            self.card["date"].append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.card is not None:
            title = " ".join("".join(self.card["title"]).split())
            date_text = " ".join("".join(self.card["date"]).split())
            if not title or not date_text:
                raise ValueError(f"Missing title/date for {self.card['url']}")
            date = datetime.strptime(date_text, "%b %d, %Y").strftime("%Y/%m/%d")
            self.publications.append({"title": title, "url": self.card["url"], "date": date})
            self.card = None
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break


def parse_profile(html):
    parser = ProfileParser()
    parser.feed(html)
    parser.close()
    if parser.card is not None or not parser.publications:
        raise ValueError("Incomplete or empty AIBM publication list; keeping existing data")
    return parser.publications


def merge_publications(existing, fetched):
    by_url = {}
    # Preserve articles omitted from the profile; refresh matching titles and dates.
    for publication in [*existing, *fetched]:
        title, date = publication["title"], publication["date"]
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Publication title must be nonempty")
        datetime.strptime(date, "%Y/%m/%d")
        url = publication_url(publication["url"])
        by_url[url] = {"title": title, "url": url, "date": date}
    return sorted(by_url.values(), key=lambda item: (item["date"], item["url"]), reverse=True)


def update_content(content, fetched):
    matches = list(PUBLICATIONS_BLOCK.finditer(content))
    if len(matches) != 1:
        raise ValueError("Expected exactly one publications block in js/content.js")
    match = matches[0]
    # Accept the original JS object keys as well as the generated JSON keys.
    array = re.sub(r'^(\s*)(title|url|date):', r'\1"\2":', match["array"], flags=re.MULTILINE)
    existing = json.loads(array)
    publications = merge_publications(existing, fetched)
    rendered = json.dumps(publications, ensure_ascii=False, indent=2)
    rendered = rendered.replace("\n", "\n  ")
    updated = content[:match.start("array")] + rendered + content[match.end("array"):]
    return updated, len(publications)


def fetch_profile():
    request = Request(PROFILE_URL, headers={
        "User-Agent": "rhawrami-publications-sync/1.0 (+https://rhawrami.github.io/)",
        "Accept": "text/html",
    })
    for attempt in range(3):
        try:
            with urlopen(request, timeout=30) as response:
                return response.read().decode("utf-8")
        except (URLError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(2 ** (attempt + 1))


def main():
    argument_parser = argparse.ArgumentParser(description=__doc__)
    argument_parser.add_argument("--check", action="store_true", help="Check for changes without writing")
    args = argument_parser.parse_args()
    try:
        original = CONTENT_PATH.read_text(encoding="utf-8")
        fetched = parse_profile(fetch_profile())
        updated, count = update_content(original, fetched)
        if updated == original:
            print(f"Publications are current ({count} articles; {len(fetched)} on AIBM profile).")
            return 0
        if args.check:
            print(f"Publication updates available ({count} articles; {len(fetched)} on AIBM profile).")
            return 1
        temporary = CONTENT_PATH.with_suffix(".js.tmp")
        temporary.write_text(updated, encoding="utf-8")
        temporary.replace(CONTENT_PATH)
        print(f"Updated {count} articles from {len(fetched)} AIBM profile entries.")
        return 0
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f"Publication sync failed; existing data was not changed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
