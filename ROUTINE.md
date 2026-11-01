# Weekly routine (what the scheduled Claude session does each Monday)

1. `pip install -r requirements.txt`
2. `python -m weekly pick`. This targets the coming Thursday. If fewer than 3
   beers qualify, rerun with another `--theme`.
3. Write `weeks/<date>/copy.json` following COPY_GUIDE.md and the brand brief.
4. `python -m weekly draft --date <date>`. This creates or updates the WordPress
   **draft** and uploads the social image.
5. Commit `weeks/<date>/` on a branch named `week/<date>` and open a PR titled
   "Weekly picks <date>: <theme label>".
6. Send Tyler the preview: draft link (`out.json → preview_link`), the social
   image, both captions and the list of beers. Ask him to approve or request changes.
7. **Stop. Do not run `publish` until Tyler approves in writing.** For changes,
   edit copy.json (or re-pick) and rerun `draft`. It updates the same draft.
8. On approval: `python -m weekly publish --date <date> --approved-by Tyler`, then
   commit `out.json` and `state/featured.json`, and merge the PR.
9. With no approval by Wednesday 23:59 ET, do nothing. The draft just stays a draft.
