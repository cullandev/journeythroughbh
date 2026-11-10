# Unpublished pages

Pages here are kept but not built or deployed. `scripts/build.py` only reads
`src/pages/`, so nothing in this folder reaches the live site.

To publish one again:

1. Move it back: `git mv src/drafts/faq.html src/pages/faq.html`
2. Add it back to `NAV` in `scripts/build.py` if it should appear in the menu.
3. Restore any links to it from other pages (see the commit that moved it here).
4. Run `python scripts/build.py`, commit, push.
