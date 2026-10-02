# Ravan Hawrami's website

Static personal site hosted on GitHub Pages.

## Automatic publications

`.github/workflows/sync-publications.yml` checks
[my AIBM profile](https://aibm.org/who-we-are/ravan-hawrami/) weekly on
Mondays at 12:17 UTC, on pushes to `main`, and on manual runs.
It updates only the `publications` array in `js/content.js`, which feeds both
the homepage's recent publications and the full publications page.

The sync imports research, commentary, and policy articles, including cards
hidden behind the profile's **View More** button. It reads titles, links, and
publication dates, removes duplicate URLs, and sorts newest first. Existing
articles absent from the AIBM profile stay in the list; matching entries get
AIBM's current title and date. Events are excluded. Citations and other site
content remain manually maintained.

A fetch or parsing error fails the run before changing the data or deploying.
Unchanged scheduled runs do not commit or deploy. Runs with updates commit the
publication data back to `main` and explicitly deploy the site, since commits
made with `GITHUB_TOKEN` don't trigger another Pages build. Pushes and manual
runs deploy even if the publications are already current. No personal token or
third-party dependencies are required.

### Activate

1. Push these changes to `main`.
2. In the repository's **Settings → Pages → Build and deployment**, set
   **Source** to **GitHub Actions**. This workflow handles future site deployments.
3. In **Actions → Sync publications and deploy site**, choose **Run workflow**
   if the initial push ran before you changed the Pages setting.

GitHub Actions must be enabled. The workflow requests `contents: write` for
its sync job and `pages: write` plus `id-token: write` for deployment. Rules
protecting `main` must allow the bot's update commits; otherwise the run fails
without deploying uncommitted data.

GitHub schedules can be delayed, so a weekly schedule is not an exact freshness
guarantee. In a public repository, GitHub disables scheduled workflows after
60 days without repository activity. If that happens during a gap between
publications, re-enable this workflow in Actions.

### Run locally

Requires Python 3.10 or newer and no additional packages:

```sh
python3 scripts/sync_publications.py
python3 scripts/sync_publications.py --check
python3 -m unittest discover -s tests -v
```

`--check` does not write. It exits `0` if current, `1` if changes are available,
and `2` on failure. To remove an old publication intentionally, delete its
entry from `js/content.js`; it will return if it is still listed on AIBM.
