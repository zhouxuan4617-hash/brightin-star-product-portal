# Codex Source Data for Brightin Star Dealer Catalog

These JSON files are converted from the original multi-sheet Excel workbooks into a Codex-friendly text format.

## Files

- `new-products.json`: Public-safe converted data from the new product workbook. Sensitive price fields such as wholesale price and promotion wholesale price were removed.
- `product-database.json`: Public-safe converted data from the old product database. Only the `产品信息库` sheet is included. Price sheets and customer information sheets were excluded.
- `drive-links.json`: Google Drive product asset links.

## JSON Format

Each file keeps the original workbook and sheet structure:

```json
{
  "workbookName": "...",
  "sheets": {
    "Sheet Name": {
      "address": "A1:K13",
      "rawRows": [],
      "headerRowIndex": 1,
      "headers": [],
      "records": []
    }
  }
}
```

Use `records` for normal table-like sheets. Use `rawRows` for specification sheets where the format is key-value rather than a clean table.

## Safety Rules

Do not commit the original `.xlsx` files to the public GitHub repository.
Do not expose dealer/wholesale prices, pickup prices, costs, customer information, sales data, profit, or internal remarks.
These JSON files are intended to generate a public-safe `products.json` for GitHub Pages.
