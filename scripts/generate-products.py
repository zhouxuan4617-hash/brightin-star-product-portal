#!/usr/bin/env python3
"""Generate public-safe Brightin Star catalog data and an update report.

Excel original files must not be committed to the Public GitHub repository.
Excel files should only be used as local or temporary data sources.
Only the final public-safe products.json should be committed.
"""

from __future__ import annotations

import csv
import json
import re
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
    "dealerprice",
    "pickup",
    "pickup price",
    "launch pickup",
    "launchpickup",
    "cost",
    "cost price",
    "profit",
    "margin",
    "customer",
    "sales",
    "internal",
    "remark",
    "private",
    "批发价",
    "提货价",
    "首发提货价",
    "成本价",
    "成本",
    "利润",
    "客户信息",
    "客户",
    "销售数据",
    "销售",
    "内部备注",
    "内部",
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

FIELD_ALIASES = {
    "id": "id",
    "productid": "id",
    "product_id": "id",
    "sku": "id",
    "ean": "ean",
    "barcode": "ean",
    "upc": "ean",
    "productname": "productName",
    "product_name": "productName",
    "name": "productName",
    "产品名称": "productName",
    "model": "model",
    "型号": "model",
    "cnname": "cnName",
    "cn_name": "cnName",
    "chinesename": "cnName",
    "中文名": "cnName",
    "中文名称": "cnName",
    "enname": "enName",
    "en_name": "enName",
    "englishname": "enName",
    "英文名": "enName",
    "英文名称": "enName",
    "focustype": "focusType",
    "focus_type": "focusType",
    "af/mf": "focusType",
    "对焦类型": "focusType",
    "series": "series",
    "系列": "series",
    "mount": "mount",
    "卡口": "mount",
    "format": "format",
    "sensorformat": "format",
    "sensor_format": "format",
    "画幅": "format",
    "color": "color",
    "颜色": "color",
    "status": "status",
    "状态": "status",
    "isnewlaunch": "isNewLaunch",
    "is_new_launch": "isNewLaunch",
    "newlaunch": "isNewLaunch",
    "新品": "isNewLaunch",
    "arrivaldate": "arrivalDate",
    "arrival_date": "arrivalDate",
    "到货时间": "arrivalDate",
    "launchdate": "launchDate",
    "launch_date": "launchDate",
    "上市时间": "launchDate",
    "launchperiod": "launchPeriod",
    "launch_period": "launchPeriod",
    "上市周期": "launchPeriod",
    "rrp": "rrp",
    "msrp": "rrp",
    "publicprice": "rrp",
    "public_price": "rrp",
    "零售价": "rrp",
    "建议零售价": "rrp",
    "launchprice": "launchPrice",
    "launch_price": "launchPrice",
    "首发价": "launchPrice",
    "thumbnail": "thumbnail",
    "thumbnailurl": "thumbnail",
    "thumbnail_url": "thumbnail",
    "缩略图": "thumbnail",
    "notes": "notes",
    "note": "notes",
}

SPEC_ALIASES = {
    "productmaterial": "productMaterial",
    "product_material": "productMaterial",
    "material": "productMaterial",
    "材质": "productMaterial",
    "productdimensions": "productDimensions",
    "product_dimensions": "productDimensions",
    "dimensions": "productDimensions",
    "尺寸": "productDimensions",
    "productweight": "productWeight",
    "product_weight": "productWeight",
    "weight": "productWeight",
    "重量": "productWeight",
    "includedaccessories": "includedAccessories",
    "included_accessories": "includedAccessories",
    "accessories": "includedAccessories",
    "配件": "includedAccessories",
    "manual": "manual",
    "说明书": "manual",
    "angleofview": "angleOfView",
    "angle_of_view": "angleOfView",
    "视角": "angleOfView",
    "minimumfocusdistance": "minimumFocusDistance",
    "minimum_focus_distance": "minimumFocusDistance",
    "minfocusdistance": "minimumFocusDistance",
    "最近对焦距离": "minimumFocusDistance",
    "magnification": "magnification",
    "放大倍率": "magnification",
    "opticaldesign": "opticalDesign",
    "optical_design": "opticalDesign",
    "镜头结构": "opticalDesign",
    "aperture": "aperture",
    "光圈": "aperture",
    "irisblades": "irisBlades",
    "iris_blades": "irisBlades",
    "blades": "irisBlades",
    "光圈叶片": "irisBlades",
    "focustype": "focusType",
    "focus_type": "focusType",
    "对焦类型": "focusType",
    "imagestabilization": "imageStabilization",
    "image_stabilization": "imageStabilization",
    "stabilization": "imageStabilization",
    "防抖": "imageStabilization",
    "filtersize": "filterSize",
    "filter_size": "filterSize",
    "滤镜尺寸": "filterSize",
    "weathersealing": "weatherSealing",
    "weather_sealing": "weatherSealing",
    "防尘防滴": "weatherSealing",
    "buttonsandknobsdescription": "buttonsAndKnobsDescription",
    "buttons_and_knobs_description": "buttonsAndKnobsDescription",
    "buttonsknobs": "buttonsAndKnobsDescription",
    "按钮旋钮说明": "buttonsAndKnobsDescription",
}


def normalized_key(value: str) -> str:
    return re.sub(r"[\s\-()]+", "", value.strip().lower())


def normalize_product_name(value: str) -> str:
    """Normalize catalog and Google Drive names for matching."""
    normalized = str(value).strip().lower()
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
    compact = normalized_key(field_name)
    return any(keyword in lowered or normalized_key(keyword) in compact for keyword in SENSITIVE_FIELD_KEYWORDS)


def record_filtered_field(filtered_sensitive_fields: set[str], field_name: str) -> None:
    filtered_sensitive_fields.add(field_name)


def list_from_value(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        parts = [part.strip(" -•\t") for part in re.split(r"\n|;|\|", value) if part.strip(" -•\t")]
        return parts
    return [str(value)]


def bool_from_value(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or value == "":
        return default
    return str(value).strip().lower() in {"true", "yes", "y", "1", "new", "新品", "是"}


def merge_key_features(product: dict[str, Any], value: Any, unrecognized_fields: set[str]) -> None:
    if not value:
        return
    if isinstance(value, dict):
        product["keyFeatures"]["en"] = list_from_value(value.get("en") or value.get("english") or value.get("English") or product["keyFeatures"]["en"])
        product["keyFeatures"]["cn"] = list_from_value(value.get("cn") or value.get("chinese") or value.get("中文") or product["keyFeatures"]["cn"])
        for key in value:
            if normalized_key(key) not in {"en", "english", "cn", "chinese", "中文"}:
                unrecognized_fields.add(f"keyFeatures.{key}")
    else:
        product["keyFeatures"]["en"] = list_from_value(value)


def merge_asset_links(product: dict[str, Any], value: Any) -> None:
    if not value:
        return
    links: list[dict[str, str]] = []
    values = value if isinstance(value, list) else [value]
    for item in values:
        if isinstance(item, dict):
            links.append({
                "label": str(item.get("label") or item.get("folderName") or "Google Drive Asset Folder"),
                "type": str(item.get("type") or "Google Drive Folder"),
                "url": str(item.get("url") or item.get("googleDriveFolderUrl") or ""),
            })
        elif isinstance(item, str):
            links.append({"label": "Google Drive Asset Folder", "type": "Google Drive Folder", "url": item})
    if links:
        product["assetLinks"] = links


def infer_defaults(product: dict[str, Any], is_new_source: bool) -> None:
    name = product.get("productName", "")
    if not product["id"] and name:
        prefix = "new" if is_new_source or product.get("isNewLaunch") else "catalog"
        product["id"] = f"{prefix}-" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not product["enName"]:
        product["enName"] = name
    if not product["model"] and name:
        product["model"] = re.sub(r"^(AF|MF)\s+", "", name, flags=re.IGNORECASE)
        product["model"] = re.sub(r"\s+(Full-frame|APS-C).*$", "", product["model"], flags=re.IGNORECASE)
    if not product["focusType"] and name:
        if name.upper().startswith("AF "):
            product["focusType"] = "AF"
        elif name.upper().startswith("MF "):
            product["focusType"] = "MF"
        elif "adapter" in name.lower():
            product["focusType"] = "Adapter"
    if not product["format"] and name:
        if "aps-c" in name.lower() or "apsc" in name.lower():
            product["format"] = "APS-C"
        elif "full-frame" in name.lower() or "fullframe" in name.lower():
            product["format"] = "Full-frame"
    if not product["status"]:
        product["status"] = "Launching" if is_new_source or product.get("isNewLaunch") else "Available"
    if is_new_source:
        product["isNewLaunch"] = True
    if not product["thumbnail"]:
        product["thumbnail"] = "assets/thumbnails/placeholder.svg"


def sanitize_product(raw_product: dict[str, Any], unrecognized_fields: set[str], filtered_sensitive_fields: set[str], *, is_new_source: bool = False) -> dict[str, Any]:
    """Keep only public-safe schema fields and drop sensitive or unknown fields."""
    product = deepcopy(PRODUCT_TEMPLATE)
    allowed_top_level = set(PRODUCT_TEMPLATE)
    allowed_specs = set(SPEC_TEMPLATE)

    for key, value in raw_product.items():
        if contains_sensitive_field(key):
            record_filtered_field(filtered_sensitive_fields, key)
            continue

        canonical_key = FIELD_ALIASES.get(normalized_key(key), key if key in allowed_top_level else "")
        spec_key = SPEC_ALIASES.get(normalized_key(key), "")

        if key == "specs" and isinstance(value, dict):
            for raw_spec_key, spec_value in value.items():
                if contains_sensitive_field(raw_spec_key):
                    record_filtered_field(filtered_sensitive_fields, f"specs.{raw_spec_key}")
                    continue
                canonical_spec_key = SPEC_ALIASES.get(normalized_key(raw_spec_key), raw_spec_key if raw_spec_key in allowed_specs else "")
                if canonical_spec_key in allowed_specs:
                    product["specs"][canonical_spec_key] = spec_value or ""
                else:
                    unrecognized_fields.add(f"specs.{raw_spec_key}")
        elif canonical_key in allowed_top_level:
            if canonical_key == "specs" and isinstance(value, dict):
                continue
            if canonical_key == "keyFeatures":
                merge_key_features(product, value, unrecognized_fields)
            elif canonical_key == "assetLinks":
                merge_asset_links(product, value)
            elif canonical_key == "isNewLaunch":
                product[canonical_key] = bool_from_value(value, is_new_source)
            else:
                product[canonical_key] = value if value is not None else ""
        elif spec_key in allowed_specs:
            product["specs"][spec_key] = value or ""
        elif normalized_key(key) in {"keyfeatures", "features", "sellingpoints", "卖点"}:
            merge_key_features(product, value, unrecognized_fields)
        else:
            unrecognized_fields.add(key)

    infer_defaults(product, is_new_source)
    return product


def load_json_file(path: Path) -> Any:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def extract_records(data: Any, preferred_keys: tuple[str, ...]) -> list[dict[str, Any]]:
    """Accept either a raw list or common wrapper keys from source-data JSON files."""
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in preferred_keys + ("products", "items", "data", "records"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def extract_product_records(data: Any) -> list[dict[str, Any]]:
    return extract_records(data, ("products", "catalog", "productDatabase", "newProducts"))


def extract_drive_records(data: Any) -> list[dict[str, Any]]:
    records = extract_records(data, ("links", "driveLinks", "assetLinks", "folders"))
    if records:
        return records
    if isinstance(data, dict) and isinstance(data.get("sheets"), dict):
        sheet_records: list[dict[str, Any]] = []
        for sheet in data["sheets"].values():
            if isinstance(sheet, dict):
                sheet_records.extend(extract_records(sheet, ("records",)))
        return sheet_records
    return []


def read_source_products(unrecognized_fields: set[str], filtered_sensitive_fields: set[str]) -> list[dict[str, Any]]:
    """Read public-safe product records from source-data JSON files.

    `source-data/new-products.json` and `source-data/product-database.json` are the
    authoritative source files. The existing generated products.json is used only as
    a fallback when both source-data files are missing, so valid data is not lost
    during initial setup.
    """
    source_files = ((NEW_PRODUCTS_SOURCE, True), (PRODUCT_DATABASE_SOURCE, False))
    if any(path.exists() for path, _ in source_files):
        products: list[dict[str, Any]] = []
        for path, is_new_source in source_files:
            raw_products = extract_product_records(load_json_file(path))
            products.extend(
                sanitize_product(product, unrecognized_fields, filtered_sensitive_fields, is_new_source=is_new_source)
                for product in raw_products
            )
        return products

    if not PRODUCTS_PATH.exists():
        return []
    return [
        sanitize_product(product, unrecognized_fields, filtered_sensitive_fields)
        for product in extract_product_records(load_json_file(PRODUCTS_PATH))
    ]


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
                    value.get("productKey") or value.get("productName") or product_key,
                    value.get("folderName") or product_key,
                    value.get("googleDriveFolderUrl") or value.get("url") or value.get("driveUrl") or "",
                )
        records = extract_drive_records(data)
    else:
        records = extract_drive_records(data)

    for row in records:
        add_link(
            links,
            row.get("productKey") or row.get("productName") or row.get("model") or row.get("name") or "",
            row.get("folderName") or row.get("folder") or row.get("model") or "",
            row.get("googleDriveFolderUrl") or row.get("url") or row.get("driveUrl") or row.get("link") or "",
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
        candidates = [
            product.get("productName", ""),
            product.get("enName", ""),
            product.get("model", ""),
            " ".join(value for value in (product.get("focusType", ""), product.get("model", ""), product.get("format", "")) if value),
        ]
        url = ""
        for candidate in candidates:
            url = links.get(normalize_product_name(candidate), "")
            if url:
                break
        product["assetLinks"] = [{"label": "Google Drive Asset Folder", "type": "Google Drive Folder", "url": url}]


def missing_key_fields(product: dict[str, Any]) -> list[str]:
    return [field for field in REQUIRED_FIELDS if not str(product.get(field, "")).strip()]


def write_products(products: list[dict[str, Any]]) -> None:
    with PRODUCTS_PATH.open("w", encoding="utf-8") as file:
        json.dump(products, file, ensure_ascii=False, indent=2)
        file.write("\n")


def write_report(products: list[dict[str, Any]], unrecognized_fields: set[str], filtered_sensitive_fields: set[str]) -> None:
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
    lines.extend(["", "## Filtered Sensitive Fields", ""])
    lines.extend(f"- {field}" for field in sorted(filtered_sensitive_fields) or ["None"])
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
    filtered_sensitive_fields: set[str] = set()
    products = read_source_products(unrecognized_fields, filtered_sensitive_fields)
    asset_links = read_asset_links()
    apply_asset_links(products, asset_links)
    write_products(products)
    write_report(products, unrecognized_fields, filtered_sensitive_fields)


if __name__ == "__main__":
    main()
