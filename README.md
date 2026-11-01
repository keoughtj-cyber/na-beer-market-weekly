# NA Beer Market weekly

Every week this publishes one "Weekly Picks" post on
[market.nabeerclub.com](https://market.nabeerclub.com), featuring 4 or 5 in-stock
non-alcoholic beers. It then schedules the same picks to Instagram and Facebook
through Buffer. Mailchimp's RSS-to-email campaign picks up the new post from the
category feed and sends the weekly email.

**Nothing goes live without Tyler's approval.** Each week is previewed first, and
only `publish --approved-by` schedules anything.

## The weekly loop

| When | What happens |
|---|---|
| Monday | A scheduled Claude session follows [ROUTINE.md](ROUTINE.md). It runs `pick`, writes `copy.json` per [COPY_GUIDE.md](COPY_GUIDE.md), runs `draft` (WordPress **draft** + social image), and sends Tyler the preview. |
| On approval | `publish --approved-by Tyler` schedules the post for **Thursday 10:00 ET**, plus Buffer posts 15 minutes later. |
| Thursday 10:00 ET | WordPress publishes the post, then Buffer posts to Instagram and Facebook. Mailchimp RSS sends the email on its schedule. |
| No approval | Nothing is scheduled, so the week is skipped. |

## Commands

```bash
pip install -r requirements.txt
python -m weekly pick [--date 2026-11-05] [--theme new-arrivals]   # writes weeks/<date>/plan.json
# write weeks/<date>/copy.json
python -m weekly draft   --date 2026-11-05 [--dry-run]              # WP draft + na-beer-market-weekly-picks-<date>.png + preview.html
python -m weekly publish --date 2026-11-05 --approved-by Tyler [--dry-run]
python -m weekly buffer-channels                                     # list Buffer channel ids
python -m weekly buffer-test --date 2026-11-05                       # save the week to Buffer as drafts only
python -m unittest discover -s tests
```

`--date` is the Thursday the week goes live. `--dry-run` renders locally and never
writes to WordPress or Buffer.

## How beers are picked

- In stock, published, with a photo and at least `min_stock` (6) units.
- Not featured in the last `no_repeat_weeks` (6) weeks. History is kept in `state/featured.json`.
- At most `max_per_brand` (2) per brand.
- The theme rotates through `config.json → rotation`: new arrivals, hoppy, crisp,
  hidden gems, dark and malty, fruity and sour. Seasonal windows override the rotation
  (Thanksgiving, holiday party, Dry January).
- To keep a product out for good, use `always_exclude_product_ids` or `always_exclude_name_contains`.

## Secrets (cloud environment variables, never committed)

| Variable | What |
|---|---|
| `MARKET_WP_USER`, `MARKET_WP_APP_PASSWORD` | WordPress application password for the Market |
| `BUFFER_API_KEY` | Buffer personal API key (Buffer settings → API) |

The environment's network policy must allow `market.nabeerclub.com` and `api.buffer.com`.

## Files

- `weekly/`: the code (stdlib + Pillow).
- `weeks/<date>/`: `plan.json` (picked beers), `copy.json` (the words), `na-beer-market-weekly-picks-<date>.png`,
  `preview.html`, and `out.json` (WordPress/Buffer ids and status). Committed every week as a record.
- `state/featured.json`: which beers ran which week.
- `assets/logo-market.png`: NA Beer Market logo for the social image.

## Notes

- Channel ids are pinned in `config.json → buffer.channel_ids` because the Buffer org also holds an unrelated Instagram account.
- Buffer's GraphQL API is in public beta. If Instagram needs extra post fields, set
  them in `config.json → buffer.extra_input.instagram` without changing code.
- The Market host returns 406 to Python's default User-Agent, so `weekly/http.py`
  sends a curl-like one.
