# Self-hosted fonts

`TODO:` add these two files. Until they exist the site falls back to Georgia and the
system UI font, and every page still works.

| File | Family | Source (SIL Open Font License) |
|------|--------|--------------------------------|
| `Fraunces-Variable.woff2` | Fraunces (variable, wght 300–700) | https://github.com/undercasetype/Fraunces |
| `AtkinsonHyperlegibleNext-Variable.woff2` | Atkinson Hyperlegible Next (variable) | https://github.com/googlefonts/atkinson-hyperlegible-next |

Steps:

1. Download the variable TTF from each repository's `fonts/` folder (or the latest release).
2. Convert to WOFF2 and, ideally, subset to Latin to keep each file well under 100 KB:
   ```bash
   pip install fonttools brotli
   pyftsubset Fraunces[SOFT,WONK,opsz,wght].ttf --unicodes="U+0000-00FF,U+2010-2027,U+2032-2033,U+20AC,U+2212" --flavor=woff2 --output-file=Fraunces-Variable.woff2
   pyftsubset AtkinsonHyperlegibleNext[wght].ttf --unicodes="U+0000-00FF,U+2010-2027,U+2032-2033,U+20AC,U+2212" --flavor=woff2 --output-file=AtkinsonHyperlegibleNext-Variable.woff2
   ```
3. Drop both `.woff2` files in this folder and commit them. The `@font-face` rules in
   `public/css/site.css` already point here, and `_headers` caches them for a year.

Do not link Google Fonts from the CDN. That would send every visitor's IP to Google.
