# Source Data Package

This folder stores the public-safe JSON source files used by `scripts/generate-products.py`.

Expected files:

- `new-products.json`: public-safe new-launch product records.
- `product-database.json`: public-safe existing catalog product records.
- `drive-links.json`: Google Drive folder mapping records with `productKey`, `folderName`, and `googleDriveFolderUrl`.
- `conversion-report.md`: notes from the latest source-data conversion.

Do not place raw Excel files, wholesale prices, dealer pickup prices, cost prices, customer data, sales data, profit data, or internal remarks in this folder.
