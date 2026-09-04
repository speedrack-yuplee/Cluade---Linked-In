"""Loading the HOMEDANT product catalog and brand profile."""

from __future__ import annotations

import json
from pathlib import Path

from .models import Brand, Installation, Product

DATA_DIR = Path(__file__).parent / "data"
DEFAULT_CATALOG_PATH = DATA_DIR / "products.json"
DEFAULT_BRAND_PATH = DATA_DIR / "brand.json"
DEFAULT_INSTALLATIONS_PATH = DATA_DIR / "installations.json"


class Catalog:
    """The products the agent may promote, plus the brand posting them."""

    def __init__(self, brand: Brand, products: list[Product], installations: list[Installation] | None = None):
        self.brand_profile = brand
        self._products = list(products)
        self._installations = list(installations or ())

    @classmethod
    def load(cls, path: str | Path | None = None, brand_path: str | Path | None = None) -> "Catalog":
        path = Path(path) if path else DEFAULT_CATALOG_PATH
        raw = json.loads(path.read_text(encoding="utf-8"))
        products = [Product.from_dict(item) for item in raw.get("products", [])]
        if not products:
            raise ValueError(f"catalog at {path} contains no products")

        brand_path = Path(brand_path) if brand_path else DEFAULT_BRAND_PATH
        brand = Brand.from_dict(json.loads(brand_path.read_text(encoding="utf-8")))

        # Optional: a checkout without the photographs still has to plan.
        installations: list[Installation] = []
        if DEFAULT_INSTALLATIONS_PATH.exists():
            raw = json.loads(DEFAULT_INSTALLATIONS_PATH.read_text(encoding="utf-8"))
            installations = [Installation.from_dict(i) for i in raw.get("installations", ())]
        return cls(brand, products, installations)

    def __len__(self) -> int:
        return len(self._products)

    def __iter__(self):
        return iter(self._products)

    @property
    def products(self) -> list[Product]:
        return list(self._products)

    @property
    def installations(self) -> list[Installation]:
        """Rooms the shelving went into, for which a photograph exists."""
        from .image import ASSET_DIR

        return [i for i in self._installations if (ASSET_DIR / "library" / i.photo).exists()]

    @property
    def brand(self) -> str:
        return self.brand_profile.brand

    @property
    def company(self) -> str:
        return self.brand_profile.company

    @property
    def author(self) -> str:
        return self.brand_profile.author

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
        return Catalog(self.brand_profile, selected, self._installations)

    @property
    def categories(self) -> list[str]:
        return sorted({p.category for p in self._products})
