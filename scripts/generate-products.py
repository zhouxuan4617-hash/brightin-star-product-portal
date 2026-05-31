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


def read_existing_products() -> list[dict[str, Any]]:
    if not PRODUCTS_PATH.exists():
        return []
    with PRODUCTS_PATH.open(encoding="utf-8") as file:
        data = json.load(file)
    return [sanitize_product(product, set()) for product in data]


def read_asset_links() -> dict[str, str]:
    if not ASSET_LINKS_PATH.exists():
        return {}
    links: dict[str, str] = {}
    with ASSET_LINKS_PATH.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            url = (row.get("googleDriveFolderUrl") or "").strip()
            if not url:
                continue
            product_key = row.get("productKey") or row.get("folderName") or ""
            links[normalize_product_name(product_key)] = url
            folder_name = row.get("folderName") or ""
            if folder_name:
                links[normalize_product_name(folder_name)] = url
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
    # First-version framework: keep current public-safe JSON as the source of truth.
    # Future versions can parse local files from source/current/ and map them into PRODUCT_TEMPLATE.
    SOURCE_CURRENT.mkdir(parents=True, exist_ok=True)
    unrecognized_fields: set[str] = set()
    products = [sanitize_product(product, unrecognized_fields) for product in read_existing_products()]
    asset_links = read_asset_links()
    apply_asset_links(products, asset_links)
    write_products(products)
    write_report(products, unrecognized_fields)


if __name__ == "__main__":
    main()
