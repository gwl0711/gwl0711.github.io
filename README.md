# Gyuwon Lee — personal research website

Live site: **https://gwl0711.github.io/**

A responsive English-language academic website for conference introductions, with publications, an email-only CV, contact downloads, and print-ready QR assets. Plain HTML, CSS, and a small progressive-enhancement script; no build step, tracking, cookies, CDN, or runtime dependencies.

## Preview locally

```bash
python3 -m http.server 4173 --directory site
```

Open http://localhost:4173. All substantive content, paper links, CV downloads, and contact links also work without JavaScript.

## Update content

- `site/index.html`: biography, affiliation, conference highlight, research, publications, experience, and education.
- `site/styles.css`: visual design and mobile / print layouts.
- `site/assets/Gyuwon_Lee_CV.pdf`: downloadable CV. The published version excludes the telephone number.
- `site/assets/publications.bib`: citation download; update alongside publication entries.
- `site/assets/Gyuwon_Lee.vcf`: contact card, using email and website only.
- `site/assets/gyuwon-lee.jpg`: profile portrait.
- `site/sitemap.xml` and footer: update the revision date after content changes.

The current conference highlight is the accepted SfN 2026 poster listed in the September 2026 CV. Add a poster number, session, or poster download only when confirmed. The original cover letter and application materials are not deployed.

## QR for a poster or slide

- `site/assets/qr-code.svg`: vector format for lossless resizing.
- `site/assets/qr-code.png`: 1320 × 1320 pixels, 300 dpi.
- `site/assets/Gyuwon_Lee_QR.pdf`: vector A4 handout.
- https://gwl0711.github.io/qr.html: download and print page.

The QR directly encodes `https://gwl0711.github.io/`, with no third-party redirect. Keep the white quiet zone when placing it in a poster, and test the QR at final print size. Website content can change without reprinting the code.

## Deployment

The `.github/workflows/pages.yml` workflow deploys only `site/` on pushes to `main`. In **Settings → Pages → Build and deployment**, the source is **GitHub Actions**. The repository name `gwl0711.github.io` provides the root user-site address.

See [GitHub’s Pages documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site).

## Regenerate downloadable assets

Generated assets are committed, so deployment does not run Python. For maintenance, install Pillow, ReportLab, and PyMuPDF in a virtual environment, then run:

```bash
python3 scripts/build_assets.py --cv /path/to/CV_Gyuwon_Lee.pdf
```

The script creates QR assets, the social preview, and a copy of the source CV with its contact header replaced by an email-only header. It also corrects the known incomplete 2025 Scientific Reports author list against the publisher. The source PDF is never changed. If its layout changes, the script stops when it cannot find the expected header or fit the corrected citation.

## Browser verification

With Python Playwright and Chromium installed:

```bash
python3 scripts/check_site.py
```

Checks mobile and desktop overflow, local links and assets, JavaScript errors, sharing dialog, clipboard controls, and the no-JavaScript page. Screenshots go to the ignored `test-results/` directory.
