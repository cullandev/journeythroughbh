# Design plan: Journey Through Behavioral Health

Written before the code. Reviewed once for generic defaults (see "Revisions" at the end).

## The one idea

The name is a path, not a place. The site borrows one thing from that: **a single drawn line**.
It appears once, large, in the home hero, and then continues quietly down the home page as a
thin "trail" with a waypoint at each section. In the navigation, the current page is marked
with the same waypoint dot. That is where the boldness goes. Everything else is quiet:
generous whitespace, a warm paper background, no cards-for-everything, no gradients.

## Palette (6 colors)

| Name  | Hex       | Use                                              |
|-------|-----------|--------------------------------------------------|
| Paper | `#F5F1E8` | Page background                                  |
| Sand  | `#E9E2D3` | Secondary surfaces, footer, form fields          |
| Ink   | `#1E2A2B` | Body text, headings                              |
| Moss  | `#2E5A4E` | Primary action, links, focus ring                |
| Clay  | `#9E4524` | The drawn path, waypoints, one accent per screen |
| Stone | `#556062` | Secondary text, captions                         |

Measured contrast (WCAG 2.2 AA, normal text needs 4.5:1):

| Pair            | Ratio |
|-----------------|-------|
| Ink on Paper    | 13.1  |
| Ink on Sand     | 11.5  |
| Moss on Paper   | 6.9   |
| Moss on Sand    | 6.1   |
| Clay on Paper   | 5.6   |
| Clay on Sand    | 4.9   |
| Stone on Paper  | 5.8   |
| Stone on Sand   | 5.0   |
| Paper on Moss   | 6.9   |
| Paper on Ink    | 13.1  |

Every text combination used on the site is in that table. Nothing else is used for text.

## Type

Two typefaces, both open-licensed and self-hosted from `/fonts/` (no Google Fonts CDN):

- **Fraunces** (variable, SIL OFL) for headings. A warm, slightly old-style serif with
  optical sizing. It reads as "a person," not "a clinic," without being decorative.
- **Atkinson Hyperlegible Next** (SIL OFL) for body and UI. Designed by the Braille Institute
  for low-vision readers. Choosing it is itself a statement about who the site is for.

Fallback stacks are real (Georgia / system-ui), so the site is fully usable before the font
files are added (see `public/fonts/README.md`).

Type scale (ratio 1.25, base 17px on mobile, 18px from 48em):

| Step | Size (rem)                   | Used for                        |
|------|------------------------------|---------------------------------|
| -1   | 0.85                         | captions, footer meta           |
| 0    | 1.0                          | body                            |
| 1    | 1.2                          | lead paragraphs                 |
| 2    | 1.5                          | h3                              |
| 3    | 1.9                          | h2                              |
| 4    | 2.4                          | h1 on inner pages               |
| 5    | clamp(2.4rem, 5.5vw, 3.6rem) | home hero h1                    |

Line length is capped at 65ch for prose. Body line-height 1.6, headings 1.15.

## Motion

Exactly one moment: the hero path draws itself once on first paint (CSS stroke-dashoffset,
about 1.6 s). Under `prefers-reduced-motion: reduce` the path is simply present, fully drawn,
and no other transitions run.

## Layout principles

- Mobile first. One column until 48em; two columns for text + aside from 48em; the nav
  collapses to a button below 60em.
- Sections are separated by space and the trail line, not by boxes.
- One primary call to action per screen: "Book a free 15-minute consultation".
  It always says exactly what happens.
- The crisis notice sits in the footer of every page, and again beside the contact form.
- `TODO:` items the owner must fill in are rendered as a visible amber mark so nothing
  invented slips into production.

## Home page wireframe (mobile)

```
+------------------------------+
| [o] Journey Through   [Menu] |
+------------------------------+
|                              |
|  Therapy for adults who      |
|  want to move forward,       |
|  at their own pace.          |
|                              |
|  Short lead sentence.        |
|                              |
|  [Book a free 15-minute      |
|   consultation]              |
|  Telehealth . In person TODO |
|                              |
|      /---\                   |
|  ___/     \___   <- path     |
|               \              |
+---------------|--------------+
|  *  Who I work with          |
|  |  Anxiety                  |
|  |  Life transitions         |
|  |  Relationships    (TODO)  |
|  |                           |
|  *  Meet your therapist      |
|  |  [photo slot]             |
|  |  Two sentences. -> About  |
|  |                           |
|  *  How it starts            |
|  |  1 Reach out              |
|  |  2 Free consultation      |
|  |  3 First session          |
|  |                           |
|  *  The practical parts      |
|  |  Fees . Insurance .       |
|  |  Formats  -> details      |
|  |                           |
|  *  Ready when you are.      |
|     [Book]  Send a message   |
+------------------------------+
| footer                       |
|  Crisis notice (988 / 911)   |
|  License TODO . links        |
+------------------------------+
```

## Home page wireframe (desktop, 60em and up)

```
+------------------------------------------------------------------+
| [o] Journey Through Behavioral Health   About Services Expect    |
|                                         Fees FAQ  [Contact]      |
+------------------------------------------------------------------+
|                                                                  |
|  Therapy for adults who want to          /----\                  |
|  move forward, at their own pace.   ____/      \                 |
|                                                 \____            |
|  Lead sentence, 65ch max.                             \          |
|  [Book a free 15-minute consultation]                  \         |
|  Telehealth . In person . TODO city                     \        |
|                                                          |       |
+----------------------------------------------------------|-------+
|  * Who I work with        | Anxiety | Transitions | Relationships|
|  |                                                               |
|  * Meet your therapist    [photo]  Two sentences.  -> About      |
|  |                                                               |
|  * How it starts          1 ----- 2 ----- 3                      |
|  |                                                               |
|  * The practical parts    Fees / Insurance / Formats             |
|  |                                                               |
|  * Ready when you are.    [Book]   or send a message             |
+------------------------------------------------------------------+
| Crisis notice . License TODO . Privacy . NPP . Crisis resources  |
+------------------------------------------------------------------+
```

## Revisions after review

The first draft of this plan had: an off-white + sage + terracotta palette (the standard
"wellness" set), Inter for body, and a three-card "specialties" row. Changes made:

1. Sage became **Moss**, darker and greener, so it can carry buttons at 6.9:1 rather than
   being a decorative tint. Terracotta became **Clay**, darker for the same reason.
2. Inter was replaced with **Atkinson Hyperlegible Next**. Inter is fine; it is also the
   default of every template, and the accessibility rationale for Atkinson fits this site.
3. The three cards became a plain three-column list attached to the trail line.
   Cards are reserved for exactly one place: the fee table on the Fees page, where a box
   genuinely helps scanning.
4. No leaf, lotus, or brain icons anywhere. The only graphic is the path.
