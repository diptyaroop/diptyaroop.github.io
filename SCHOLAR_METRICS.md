# Google Scholar metrics

The profile displays verified **all-time** citations and h-index, with the date of the last successful check. The initial values were read directly from the public Scholar profile on 27 September 2026: 342 citations and h-index 8.

## Automatic refresh

Commit and push this site, including `.github/workflows/scholar-metrics.yml`, to the repository's default branch (`master`). With GitHub Actions enabled and bot commits allowed on that branch, the workflow checks Scholar every six hours. It can also be run from **Actions → Refresh Google Scholar metrics → Run workflow**. No API key or paid service is needed.

The workflow commits only `assets/data/scholar.json`. On the public site, `assets/js/scholar.js` reads that file directly from this repository's raw GitHub endpoint, avoiding the limitation that commits made with `GITHUB_TOKEN` do not trigger a Pages rebuild. Local previews read the local copy. The page checks on load, when a tab becomes visible, and every 30 minutes while visible.

This is periodic polling, not an instant notification from Google. GitHub may delay scheduled runs, and Google may block automated requests. A failed fetch or unexpected page leaves the last verified snapshot untouched and fails the workflow visibly; it never inserts zeroes. After two days without a successful check, the page labels the numbers as last-known values and directs visitors to Scholar. Without JavaScript, the initial dated snapshot is still visible.

If GitHub disables a schedule after extended repository inactivity, re-enable it in the Actions tab. Branch protection may require allowing bot commits or adapting the workflow to your repository policy. No repository settings are changed by this code.

## Local check

```sh
python3 -m unittest discover -s tests -v
node tests/test_scholar_client.cjs
python3 scripts/update_scholar.py
```

GitHub references: [Scheduled workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule), [Pages publishing and bot commits](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).
