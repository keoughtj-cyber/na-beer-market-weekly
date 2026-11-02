# Weekly routine (fully automatic)

A scheduled Claude session runs this every Monday. Tyler asked on 2026-11-01 for
the whole thing to run on its own with no approvals. **Do not ask anyone to
approve anything.** Finish the week, or skip it and leave a note. Never half-publish.

Work in a clone of this repo on `main`. Secrets come from the environment
(`MARKET_WP_USER`, `MARKET_WP_APP_PASSWORD`, `BUFFER_API_KEY`). Never print them.

1. `pip install -r requirements.txt`, then `python -m unittest discover -s tests`.
   If tests fail, stop and skip the week (step 8).
2. Work out the date: the coming Thursday, or the holiday override in config.json (`python -m weekly pick` handles both by default, and `plan.json` records the date).
   If `weeks/<date>/out.json` already says `"status": "scheduled"`, the week is
   done, so stop. If it says `"draft"`, go straight to step 5.
3. `python -m weekly pick`. If it exits with "only N eligible beers", rerun once
   with `--theme new-arrivals`, then `--theme hidden-gems`. If that still fails, skip the week.
4. Write `weeks/<date>/copy.json`. Follow COPY_GUIDE.md exactly, and use only
   facts from `plan.json` (each beer's description excerpt, styles and price).
   Read `/mnt/project-files/research/na-beer-club-brief.md` for voice if it's available.
5. `python -m weekly draft --date <date>`. It validates and lints the copy (banned
   phrases, placeholders, lengths). On a lint error, fix the copy and rerun. Then
   open `weeks/<date>/<image>.png` and `preview.html` and check them yourself:
   correct beers, no broken images, nothing off-brand. Fix and rerun if needed.
6. `python -m weekly publish --date <date> --approved-by auto-routine`.
   This schedules the WordPress post for 10:00 ET on that date and the Buffer
   carousel for 12:00 ET. Mailchimp's RSS campaign emails the post on its own.
6b. Add three events to Tyler's Google Calendar (primary, nabrewskey@gmail.com,
   time zone America/New_York, 15 min, shown as free) with the Google Calendar
   connector: "Market Weekly Picks post goes live (<theme label>)" at the post time
   (link and beers in the description), "Market Weekly Picks email sends (Mailchimp RSS)"
   one hour after it, and "Market Weekly Picks carousels post to Instagram and Facebook"
   at the social time (Buffer post ids in the description). Tyler wants every marketing
   item on his calendar (2026-11-02). If the connector is unavailable, note it in the
   summary; it never blocks publishing.
7. Commit `weeks/<date>/` and `state/featured.json` to `main` with the message
   "Weekly picks <date>: <theme label>" and push.
8. Skipping a week: delete nothing, publish nothing. Write `weeks/<date>/SKIPPED.md`
   with the reason and the exact error, commit, push.
9. Last, reply with a short summary: date, theme, beers, post link, Buffer post
   ids, calendar events added (or why the week was skipped).
