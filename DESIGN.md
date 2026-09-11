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

## Revision 3: switched to the autumn variant (2026-09-11)

After seeing both side by side, the owner chose the **autumn** mark. `main` now carries the
maple illustration, the clay accent (`#98421F`, 4.8:1 on Sand) in place of horizon blue,
and a warm cream tint (`#F3E7D6`) in place of the pale green band. Everything else in
revision 2 still applies. The summer green version is preserved on branch `summer` and
tag `summer-v1`; switching back is `git merge summer` or a checkout of that tag.

## Revision 2: the "summer green" direction (2026-09-11)

Claude Design produced six rounds of logo work and two home-page directions; the owner
chose the summer (green tree, sky accent) version over the autumn (maple, clay accent).
What changed on the site as a result:

- **Signature element.** The abstract drawn path is replaced by the illustrated mark: a
  winding road through green hills toward a tree at sunrise. It is the hero image on Home,
  the header mark, the favicon, and, cropped to a horizon strip of just road and hills, the
  opener image on every inner page. The waypoint idea survives in the mobile menu, where
  each item is a hollow dot on a rule and the current page is the filled one.
- **Palette.** Clay is gone (it belonged to the autumn maple). Text and headings use the
  wordmark green; actions use the horizon blue. Two values were darkened slightly from the
  mockups so every pairing clears 4.5:1.

  | Name  | Hex       | Use                                   | Lowest ratio in use |
  |-------|-----------|---------------------------------------|---------------------|
  | Paper | `#F7F3EA` | Page background                       |                     |
  | Sand  | `#E2DACB` | Rules, fields, quiet surfaces         |                     |
  | Leaf  | `#E6EDE3` | Pale green section tint               |                     |
  | Ink   | `#2C4636` | Text, headings, dark CTA band         | 7.4 on Sand         |
  | Stone | `#575B55` | Secondary text                        | 5.0 on Sand         |
  | Sky   | `#2A6480` | Buttons, links, eyebrows              | 4.7 on Sand, 5.9 white-on-Sky |

- **Type.** Headings move from Fraunces to Newsreader (also OFL, self-hosted). Body stays
  Atkinson Hyperlegible Next.
- **Home structure.** Hero (headline left, round mark right), a leaf-tinted "who I work
  with" band, formats, therapist intro with an arched photo, the practical parts, and a
  dark green closing band. The trail line is retired.
- **Fees.** The three tiles become a ruled row (a top rule, small caps label, large
  Newsreader amount) instead of sand cards.
- **Motion.** Still one moment: the hero mark settles in on first paint. Nothing under
  `prefers-reduced-motion`.
- **Copy.** Headline and section titles from the mockups were adopted. Practice facts the
  mockups revealed (Connecticut, LCSW, adolescents 13 to 18 and adults, online and in
  person) are now in the copy; name, town, and license number remain `TODO`.

## Revisions after review (revision 1)

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
