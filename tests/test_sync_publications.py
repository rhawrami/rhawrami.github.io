import unittest
from scripts.sync_publications import parse_profile, update_content


def card(slug="new", title="New &amp; updated", date="Sep 22, 2026", section="research"):
    return (f'<a href="https://aibm.org/{section}/{slug}/"><h3>{title}</h3>'
            f'<div class="date-author"><div class="date">{date}</div></div>'
            '<img src="example.jpg"></a>')


def profile(cards):
    return f'<div class="publications-list">{cards}</div>'


def content():
    return '''window.SITE_CONTENT = {
  summary: "Keep this exactly as written",
  publications: [
    {
      title: "Existing article",
      url: "https://aibm.org/research/existing/",
      date: "2024/08/29"
    }
  ],
  citations: ["Keep citations too"]
};
'''


class PublicationSyncTests(unittest.TestCase):
    def test_hidden_cards_entities_and_events(self):
        html = card("outside") + profile(
            card(title="Research <em>&amp;</em> policy")
            + '<div hidden>' + card("older", date="Aug 29, 2024", section="policy") + '</div>'
            + card("event", section="events")
        )
        result = parse_profile(html)
        self.assertEqual([p["title"] for p in result], ["Research & policy", "New & updated"])
        self.assertEqual(result[0]["date"], "2026/09/22")

    def test_bad_response_does_not_replace_data(self):
        for html in ["<html>Unavailable</html>", profile(card(date="unknown")),
                     profile(card(title="")), profile('<a href="/research/new/"><h3>Partial')]:
            with self.subTest(html=html), self.assertRaises(ValueError):
                parse_profile(html)

    def test_rejects_external_publication(self):
        with self.assertRaises(ValueError):
            parse_profile(profile(card().replace("https://aibm.org", "https://example.com")))

    def test_merges_deduplicates_sorts_and_only_changes_publications(self):
        fetched = parse_profile(profile(card() + card("existing", title="Corrected title", date="Aug 29, 2024") + card()))
        original = content()
        updated, count = update_content(original, fetched)
        self.assertEqual(count, 2)
        self.assertIn('"title": "Corrected title"', updated)
        self.assertLess(updated.index("New & updated"), updated.index("Corrected title"))
        self.assertEqual(updated.split("  publications:")[0], original.split("  publications:")[0])
        self.assertEqual(updated.split("  citations:")[1], original.split("  citations:")[1])
        self.assertEqual(update_content(updated, fetched)[0], updated)

    def test_preserves_articles_missing_from_profile(self):
        updated, count = update_content(content(), parse_profile(profile(card())))
        self.assertEqual(count, 2)
        self.assertIn("Existing article", updated)

    def test_rejects_missing_content_block(self):
        with self.assertRaises(ValueError):
            update_content("window.SITE_CONTENT = {};", parse_profile(profile(card())))


if __name__ == "__main__":
    unittest.main()
