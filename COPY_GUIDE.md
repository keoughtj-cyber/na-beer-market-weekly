# Writing copy.json

`copy.json` holds every word for the week. Write it after `pick`, using
`plan.json` (each beer's name, styles, price, stock and description excerpt).

## Voice

Warm, personal, upbeat and casual. Lean on discovery ("discover your new favorite
NA beer", "an adventure in every can"). **Never preach.** The line is "Whatever your
reason...", never a lecture on why someone isn't drinking. Everything is
non-alcoholic, so never imply otherwise and never call a beer "alcohol-free" unless
the product says 0.0%. Make no health claims. Base facts only on the product
description: no invented awards, ABVs or tasting notes.

## Selling without pushing

The goal is orders. Make each beer sound worth trying now. Name a specific occasion this week (game day, a holiday, the weekend). Use real urgency only, such as low stock (`stock_quantity` < 15) or a limited or seasonal release. Never invent discounts, deadlines or scarcity.
- End the intro and outro with a clear next step: build your own 12-pack, or shop the picks.
- Market copy is about choice: you pick, we guide. **Never contrast the Market with subscriptions**, and never knock subscriptions. The outro may add one soft line pointing to NA Beer Club for people who'd rather have the club pick for them.
- Write for adults aged about 35 to 65 who research before buying. Be knowledgeable and warm, like a friendly cicerone, with no slang. Facebook matters as much as Instagram for this audience.
- Don't use recovery or sobriety framing, and don't make health claims.

## Gift 12 Days of NA Beer (Nov 21 to early December)

From Nov 21 the Market pitches "Gift someone 12 Days of NA Beer": build a 12-pack
as a gift, and they open one can a day from Dec 13 to Dec 24 (12 nights; it arrives by Dec 12). It's a gift angle first.
- On the "Gift 12 Days of NA Beer" theme week (Dec 3), lead the intro with the gift idea,
  then present the picks as great days for the 12. The outro ends on building their pack.
- On the Thanksgiving week (Nov 24), end the outro with this short 12 Days block (Tyler approved 2026-11-13; it goes in the weekly email too, no extra send). Use it as written, then the usual Build Your Own 12-Pack line:
  "**Gift someone 12 nights of NA beer.** You pick 12 cans. They open one a night, Dec 13 to Christmas Eve. Crisp pils, a lime amber, a few IPAs, something dark for the last night. Start with our list or build your own. Free shipping. **Order by Thursday, Dec 3** for Dec 12 delivery."
  Keep the Facebook and Instagram captions to one 12 Days line.
- Order-by date: `config.json → gift_12_days.order_by` (order by Thursday, Dec 3 for Dec 12 delivery). Use it in every 12 Days mention; on Dec 3 itself say "order today". Never invent another deadline.
- Never compare it to the Advent calendar, name Advent beers or say it's cheaper.

## Fields

| Field | Notes |
|---|---|
| `title` | SEO title, about 50 to 65 characters. Include "Non-Alcoholic Beer(s)" or "NA Beer". |
| `slug` | Optional. Lowercase, hyphens. |
| `excerpt` | 1 to 2 sentences. Used by the post listing and the Mailchimp RSS email. |
| `image_headline` | Up to about 28 characters so it fits on one or two lines of the image. |
| `intro` | 2 short paragraphs (blank line between). Hook first, then "here are N…". |
| `blurbs` | `{ "<product id>": "2 to 3 sentences" }` for every beer in plan.json. Cover what it tastes like, one line on the brewery or what makes it different, and when to drink it (a meal, an occasion, a time of year). Mention low stock if `stock_quantity` < 15. |
| `outro` | 1 to 2 sentences ending on the Build Your Own 12-Pack. Free shipping to all 50 states. When naming the store in text, use **nabeermarket.com**. |
| `instagram_caption` | Under 2,200 characters. Links don't work, so name the site as **nabeermarket.com** and say "link in bio". One line per beer with an emoji is fine. 4 to 6 hashtags at the end: #nabeer #nonalcoholicbeer #craftnabeer #sobercurious #nabeerclub. |
| `facebook_caption` | 1 to 3 sentences and **must contain `{url}`**, which is replaced by the post link. |

All fields are plain text. HTML is escaped, and a blank line starts a new paragraph.
