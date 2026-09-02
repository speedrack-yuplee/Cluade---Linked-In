"""Loading and filtering the HOMEDANT product catalog."""

from __future__ import annotations

import json
from pathlib import Path

from .models import Product

DEFAULT_CATALOG_PATH = Path(__file__).parent / "data" / "products.json"


class Catalog:
    """The products the agent may promote, plus the brand identity around them."""

    def __init__(self, brand: str, company: str, author: str, products: list[Product]):
        self.brand = brand
        self.company = company
        self.author = author
        self._products = list(products)

    @classmethod
    def load(cls, path: str | Path | None = None) -> "Catalog":
        path = Path(path) if path else DEFAULT_CATALOG_PATH
        raw = json.loads(path.read_text(encoding="utf-8"))
        products = [Product.from_dict(item) for item in raw.get("products", [])]
        if not products:
            raise ValueError(f"catalog at {path} contains no products")
        return cls(
            brand=raw.get("brand", "HOMEDANT"),
            company=raw.get("company", "HOMEDANT USA"),
            author=raw.get("author", ""),
            products=products,
        )

    def __len__(self) -> int:
        return len(self._products)

    def __iter__(self):
        return iter(self._products)

    @property
    def products(self) -> list[Product]:
        return list(self._products)

    def by_asin(self, asin: str) -> Product:
        for product in self._products:
            if product.asin.upper() == asin.upper():
                return product
        raise KeyError(f"no product with ASIN {asin}")

    def filter(self, marketplace: str | None = None, category: str | None = None) -> "Catalog":
        selected = self._products
        if marketplace:
            selected = [p for p in selected if p.marketplace.upper() == marketplace.upper()]
        if category:
            selected = [p for p in selected if p.category == category]
        return Catalog(self.brand, self.company, self.author, selected)

    @property
    def categories(self) -> list[str]:
        return sorted({p.category for p in self._products})
