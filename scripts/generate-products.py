#!/usr/bin/env python3
"""Generate public-safe Brightin Star catalog data and an update report.

Excel original files must not be committed to the Public GitHub repository.
Excel files should only be used as local or temporary data sources.
Only the final public-safe products.json should be committed.
"""

from __future__ import annotations

import csv
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS_PATH = ROOT / "products.json"
ASSET_LINKS_PATH = ROOT / "asset-links.csv"
REPORT_PATH = ROOT / "update-report.md"
SOURCE_DATA_DIR = ROOT / "source-data"
NEW_PRODUCTS_SOURCE = SOURCE_DATA_DIR / "new-products.json"
PRODUCT_DATABASE_SOURCE = SOURCE_DATA_DIR / "product-database.json"
DRIVE_LINKS_SOURCE = SOURCE_DATA_DIR / "drive-links.json"
SOURCE_CURRENT = ROOT / "source" / "current"

SENSITIVE_FIELD_KEYWORDS = {
    "wholesale",
    "dealer price",
    "dealer_price",
    "pickup",
    "提货价",
    "首发提货价",
    "cost",
    "成本",
    "profit",
    "利润",
    "customer",
    "客户",
    "sales",
    "销售",
    "internal",
    "内部",
    "remark",
    "备注",
}

REQUIRED_FIELDS = ("id", "productName", "focusType", "status")

SPEC_TEMPLATE = {
    "productMaterial": "",
    "productDimensions": "",
    "productWeight": "",
    "includedAccessories": "",
    "manual": "",
    "angleOfView": "",
    "minimumFocusDistance": "",
    "magnification": "",
    "opticalDesign": "",
    "aperture": "",
    "irisBlades": "",
    "focusType": "",
    "imageStabilization": "",
    "filterSize": "",
    "weatherSealing": "",
    "buttonsAndKnobsDescription": "",
}

PRODUCT_TEMPLATE = {
    "id": "",
    "ean": "",
    "productName": "",
    "model": "",
    "cnName": "",
    "enName": "",
    "focusType": "",
    "series": "",
    "mount": "",
    "format": "",
    "color": "",
    "status": "",
    "isNewLaunch": False,
    "arrivalDate": "",
    "launchDate": "",
    "launchPeriod": "",
    "rrp": "",
    "launchPrice": "",
    "thumbnail": "assets/thumbnails/placeholder.svg",
    "specs": deepcopy(SPEC_TEMPLATE),
    "keyFeatures": {"en": [], "cn": []},
    "assetLinks": [{"label": "Google Drive Asset Folder", "type": "Google Drive Folder", "url": ""}],
    "notes": "",
}


def normalize_product_name(value: str) -> str:
    """Normalize catalog and Google Drive names for matching."""
    normalized = value.strip().lower()
    replacements = {
        "Ⅱ": "ii",
        "Ⅲ": "iii",
        "Ⅳ": "iv",
        "full-frame": "fullframe",
        "full frame": "fullframe",
        "aps-c": "apsc",
        "aps c": "apsc",
    }
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    normalized = normalized.replace("af12mmf2.8", "af 12mm f2.8")
    normalized = normalized.replace("af 50mmf1.4", "af 50mm f1.4")
    normalized = " ".join(normalized.split())
    return normalized


def contains_sensitive_field(field_name: str) -> bool:
    lowered = field_name.lower()
    return any(keyword in lowered for keyword in SENSITIVE_FIELD_KEYWORDS)


def sanitize_product(raw_product: dict[str, Any], unrecognized_fields: set[str]) -> dict[str, Any]:
    """Keep only public-safe schema fields and drop sensitive or unknown fields."""
    product = deepcopy(PRODUCT_TEMPLATE)
    allowed_top_level = set(PRODUCT_TEMPLATE)
    allowed_specs = set(SPEC_TEMPLATE)

    for key, value in raw_product.items():
        if contains_sensitive_field(key):
            continue
        if key == "specs" and isinstance(value, dict):
            for spec_key, spec_value in value.items():
                if contains_sensitive_field(spec_key):
                    continue
                if spec_key in allowed_specs:
                    product["specs"][spec_key] = spec_value
                else:
                    unrecognized_fields.add(f"specs.{spec_key}")
        elif key in allowed_top_level:
            product[key] = value
        else:
            unrecognized_fields.add(key)
    return product


def load_json_file(path: Path) -> Any:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def extract_product_records(data: Any) -> list[dict[str, Any]]:
    """Accept either a raw list or common wrapper keys from source-data JSON files."""
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ("products", "items", "data", "records"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def read_source_products(unrecognized_fields: set[str]) -> list[dict[str, Any]]:
    """Read public-safe product records from source-data JSON files.

    `new-products.json` and `product-database.json` are the preferred source files.
    If both are absent, the script falls back to the existing generated products.json
    so maintainers can bootstrap the source-data package without losing data.
    """
    source_files = (NEW_PRODUCTS_SOURCE, PRODUCT_DATABASE_SOURCE)
    if any(path.exists() for path in source_files):
        raw_products: list[dict[str, Any]] = []
        for path in source_files:
            raw_products.extend(extract_product_records(load_json_file(path)))
        return [sanitize_product(product, unrecognized_fields) for product in raw_products]

    if not PRODUCTS_PATH.exists():
        return []
    return [sanitize_product(product, unrecognized_fields) for product in extract_product_records(load_json_file(PRODUCTS_PATH))]


def add_link(links: dict[str, str], product_key: str, folder_name: str, url: str) -> None:
    url = (url or "").strip()
    if not url:
        return
    for value in (product_key, folder_name):
        if value:
            links[normalize_product_name(value)] = url


def read_drive_links_json() -> dict[str, str]:
    links: dict[str, str] = {}
    data = load_json_file(DRIVE_LINKS_SOURCE)
    if isinstance(data, dict):
        for product_key, value in data.items():
            if isinstance(value, str):
                add_link(links, product_key, product_key, value)
            elif isinstance(value, dict):
                add_link(
                    links,
                    value.get("productKey") or product_key,
                    value.get("folderName") or product_key,
                    value.get("googleDriveFolderUrl") or value.get("url") or "",
                )
        records = extract_product_records(data)
    else:
        records = extract_product_records(data)

    for row in records:
        add_link(
            links,
            row.get("productKey", ""),
            row.get("folderName", ""),
            row.get("googleDriveFolderUrl") or row.get("url") or "",
        )
    return links


def read_asset_links_csv() -> dict[str, str]:
    if not ASSET_LINKS_PATH.exists():
        return {}
    links: dict[str, str] = {}
    with ASSET_LINKS_PATH.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            add_link(
                links,
                row.get("productKey", ""),
                row.get("folderName", ""),
                row.get("googleDriveFolderUrl", ""),
            )
    return links


def read_asset_links() -> dict[str, str]:
    links = read_asset_links_csv()
    links.update(read_drive_links_json())
    return links


def apply_asset_links(products: list[dict[str, Any]], links: dict[str, str]) -> None:
    for product in products:
        normalized = normalize_product_name(product.get("productName", ""))
        url = links.get(normalized, "")
        product["assetLinks"] = [{"label": "Google Drive Asset Folder", "type": "Google Drive Folder", "url": url}]


def missing_key_fields(product: dict[str, Any]) -> list[str]:
    return [field for field in REQUIRED_FIELDS if not str(product.get(field, "")).strip()]


def write_products(products: list[dict[str, Any]]) -> None:
    with PRODUCTS_PATH.open("w", encoding="utf-8") as file:
        json.dump(products, file, ensure_ascii=False, indent=2)
        file.write("\n")


def write_report(products: list[dict[str, Any]], unrecognized_fields: set[str]) -> None:
    total = len(products)
    new_count = sum(1 for product in products if product.get("isNewLaunch"))
    old_count = total - new_count
    linked = [product for product in products if any(link.get("url", "").strip() for link in product.get("assetLinks", []))]
    missing_links = [product.get("productName", product.get("id", "Unknown product")) for product in products if product not in linked]
    missing_fields = {
        product.get("productName", product.get("id", "Unknown product")): missing_key_fields(product)
        for product in products
        if missing_key_fields(product)
    }

    lines = [
        "# Brightin Star Dealer Catalog Update Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Summary",
        "",
        f"- Total products: {total}",
        f"- New launches: {new_count}",
        f"- Existing catalog products: {old_count}",
        f"- Products with matched Google Drive links: {len(linked)}",
        "",
        "## Products Missing Google Drive Links",
        "",
    ]
    lines.extend(f"- {name}" for name in missing_links or ["None"])
    lines.extend(["", "## Products Missing Key Fields", ""])
    if missing_fields:
        lines.extend(f"- {name}: {', '.join(fields)}" for name, fields in missing_fields.items())
    else:
        lines.append("None")
    lines.extend(["", "## Unrecognized Fields", ""])
    lines.extend(f"- {field}" for field in sorted(unrecognized_fields) or ["None"])
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    # First-version framework: read public-safe JSON from source-data/.
    # Future versions can parse local files from source/current/ and map them into PRODUCT_TEMPLATE.
    # Raw Excel files should remain local-only and should never be committed.
    SOURCE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_CURRENT.mkdir(parents=True, exist_ok=True)
    unrecognized_fields: set[str] = set()
    products = read_source_products(unrecognized_fields)
    asset_links = read_asset_links()
    apply_asset_links(products, asset_links)
    write_products(products)
    write_report(products, unrecognized_fields)


if __name__ == "__main__":
    main()
