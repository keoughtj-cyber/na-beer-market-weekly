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

## Fields

| Field | Notes |
|---|---|
| `title` | SEO title, about 50 to 65 characters. Include "Non-Alcoholic Beer(s)" or "NA Beer". |
| `slug` | Optional. Lowercase, hyphens. |
| `excerpt` | 1 to 2 sentences. Used by the post listing and the Mailchimp RSS email. |
| `image_headline` | Up to about 28 characters so it fits on one or two lines of the image. |
| `intro` | 2 short paragraphs (blank line between). Hook first, then "here are N…". |
| `blurbs` | `{ "<product id>": "2 to 3 sentences" }` for every beer in plan.json. Mention low stock if `stock_quantity` < 15. |
| `outro` | 1 to 2 sentences ending on the Build Your Own 12-Pack. Free shipping to all 50 states. |
| `instagram_caption` | Under 2,200 characters. Links don't work, so say "link in bio". One line per beer with an emoji is fine. 4 to 6 hashtags at the end: #nabeer #nonalcoholicbeer #craftnabeer #sobercurious #nabeerclub. |
| `facebook_caption` | 1 to 3 sentences and **must contain `{url}`**, which is replaced by the post link. |

All fields are plain text. HTML is escaped, and a blank line starts a new paragraph.
