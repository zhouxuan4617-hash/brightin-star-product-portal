# brightin-star-product-portal

Brightin Star Dealer Catalog is a public-safe static catalog for overseas resellers. It presents public product information, launch status, basic specifications, public pricing fields, Google Drive marketing-material links, and inquiry entry points.

## Public-safe scope

This repository is intended for a public GitHub Pages website. Every committed file may be visible externally, so only public-safe catalog data should be stored here.

Do **not** upload or commit:

- Wholesale prices
- Dealer pickup prices
- Cost prices
- Customer information
- Sales data
- Profit data
- Internal remarks
- Large marketing-material files such as high-resolution images, videos, ZIP files, or PDFs

Large marketing materials should stay in Google Drive. This site should only contain webpage code, public product data, lightweight thumbnails, and external Google Drive links.

## Project structure

```text
index.html
styles.css
script.js
products.json
asset-links.csv
.nojekyll
README.md
update-report.md
source/
  current/
  incoming/
  archive/
current/
incoming/
archive/
scripts/
  generate-products.py
assets/
  thumbnails/
    placeholder.svg
```

## Local preview

This site loads `products.json` with `fetch`, so do not preview it by double-clicking `index.html`. Use a local web server instead:

```bash
python -m http.server 8000
```

Then open:

```text
http://localhost:8000
```

## Editing products.json

`products.json` is the public catalog data source. Keep each product in the existing schema and leave unknown values blank instead of guessing.

Important rules:

1. Only enter confirmed public information.
2. Leave unconfirmed prices, launch dates, EANs, mounts, specifications, or feature copy blank.
3. Do not add dealer prices, wholesale prices, cost prices, margins, customer data, sales data, or internal notes.
4. Keep thumbnails lightweight and suitable for GitHub Pages.
5. Store large source materials outside this repository.

## Maintaining Google Drive material links

Use `asset-links.csv` to maintain the relationship between catalog products and Google Drive folders.

CSV fields:

```text
productKey,folderName,googleDriveFolderUrl
```

- `productKey`: public product key used for matching.
- `folderName`: Google Drive folder display name.
- `googleDriveFolderUrl`: public or permission-controlled Google Drive folder URL.

The website displays an asset button only when a product has a non-empty Google Drive URL. If a URL is blank, the site displays `Assets Coming Soon`.

## Data generation script

Run the generator from the repository root:

```bash
python scripts/generate-products.py
```

The first version keeps `products.json` as the public-safe source of truth, applies available Google Drive links from `asset-links.csv`, filters sensitive fields, and writes `update-report.md`.

Future data-source files should be placed locally in `source/current/` only when needed for generation. Raw Excel source files must not be committed to this public repository. Excel files should be treated as local or temporary inputs, and only public-safe generated `products.json` should be committed.

## Pre-publish validation

Before pushing a public GitHub Pages update, run:

```bash
python scripts/validate-site.py
```

The validator checks for the required static files, root-relative path mistakes, missing `products.json` loading, oversized or packaged marketing files, sensitive product-field keys, and forbidden sales-dashboard files.

## Deploying to GitHub Pages

1. Commit and push the static files to GitHub.
2. Open the repository on GitHub.
3. Go to **Settings → Pages**.
4. Under **Build and deployment**, choose **Deploy from a branch**.
5. Select the target branch, usually `main`, and folder `/ (root)`.
6. Save the settings and wait for GitHub Pages to publish the site.

The `.nojekyll` file is included so GitHub Pages serves the static files directly without Jekyll processing.

## Git workflow

```bash
git status
git add .
git commit -m "Create first Brightin Star dealer catalog"
git push origin <branch-name>
```

After pushing, enable GitHub Pages in the repository settings as described above.
