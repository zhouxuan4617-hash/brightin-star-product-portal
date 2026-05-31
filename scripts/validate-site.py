#!/usr/bin/env python3
"""Validate that the static catalog is safe to publish on GitHub Pages."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_PUBLIC_FILE_BYTES = 1_000_000
REQUIRED_FILES = (
    "index.html",
    "styles.css",
    "script.js",
    "products.json",
    "asset-links.csv",
    ".nojekyll",
    "README.md",
    "update-report.md",
    "assets/thumbnails/placeholder.svg",
    "source-data/new-products.json",
    "source-data/product-database.json",
    "source-data/drive-links.json",
    "source-data/README.md",
    "source-data/conversion-report.md",
)
FORBIDDEN_DASHBOARD_PATHS = (
    "app",
    "app/app.py",
    "app/charts.py",
    "app/data_loader.py",
    "app/metrics.py",
    "charts.py",
    "data_loader.py",
    "metrics.py",
)
SENSITIVE_PRODUCT_KEYS = (
    "wholesale",
    "dealerPrice",
    "dealer_price",
    "pickup",
    "cost",
    "profit",
    "customer",
    "sales",
    "internal",
    "remark",
    "批发价",
    "提货价",
    "成本价",
    "利润",
    "客户",
    "销售",
    "内部",
    "备注",
)
LARGE_FILE_SUFFIXES = {".zip", ".rar", ".7z", ".mp4", ".mov", ".avi", ".psd", ".ai", ".pdf"}


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def walk_public_files() -> list[Path]:
    return sorted(path for path in ROOT.rglob("*") if path.is_file() and ".git" not in path.parts)


def validate_required_files() -> None:
    for relative_path in REQUIRED_FILES:
        if not (ROOT / relative_path).exists():
            fail(f"Missing required file: {relative_path}")


def validate_no_dashboard_files() -> None:
    for relative_path in FORBIDDEN_DASHBOARD_PATHS:
        if (ROOT / relative_path).exists():
            fail(f"Sales dashboard file/path must not exist: {relative_path}")


def validate_file_sizes() -> None:
    for path in walk_public_files():
        if path.suffix.lower() in LARGE_FILE_SUFFIXES:
            fail(f"Large marketing/source file type is not allowed: {path.relative_to(ROOT)}")
        if path.stat().st_size > MAX_PUBLIC_FILE_BYTES:
            fail(f"File is too large for the public static repo: {path.relative_to(ROOT)}")


def validate_relative_static_paths() -> None:
    index_html = (ROOT / "index.html").read_text(encoding="utf-8")
    for attr in ("href", "src"):
        for value in re.findall(rf'{attr}=["\']([^"\']+)["\']', index_html):
            if value.startswith(("http://", "https://", "mailto:", "#")):
                continue
            if value.startswith("/"):
                fail(f"Root-relative path is not allowed in index.html: {value}")
            if not (ROOT / value).exists():
                fail(f"Referenced path does not exist: {value}")

    script_js = (ROOT / "script.js").read_text(encoding="utf-8")
    if "fetch('products.json')" not in script_js and 'fetch("products.json")' not in script_js:
        fail("script.js should fetch products.json with a relative path")
    if "target=\"_blank\"" not in script_js or "rel=\"noopener\"" not in script_js:
        fail("Asset folder links should open in a new tab with noopener")
    if "mailto:" not in script_js:
        fail("Email inquiry mailto link is missing")


def validate_products_json() -> None:
    with (ROOT / "products.json").open(encoding="utf-8") as file:
        products = json.load(file)
    if not isinstance(products, list):
        fail("products.json must contain a list of products")
    if not products:
        fail("products.json must contain at least one product")

    def scan_keys(value: object, path: str = "") -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                lowered = key.lower()
                if any(sensitive.lower() in lowered for sensitive in SENSITIVE_PRODUCT_KEYS):
                    fail(f"Sensitive field key found in products.json: {path}{key}")
                scan_keys(nested, f"{path}{key}.")
        elif isinstance(value, list):
            for index, nested in enumerate(value):
                scan_keys(nested, f"{path}{index}.")

    scan_keys(products)


def main() -> None:
    validate_required_files()
    validate_no_dashboard_files()
    validate_file_sizes()
    validate_relative_static_paths()
    validate_products_json()
    print("PASS: GitHub Pages readiness validation completed successfully.")


if __name__ == "__main__":
    main()
