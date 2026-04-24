import csv
import random
from pathlib import Path


PRODUCTS = [
    {"sku": "SKU-001", "name": "Laptop", "category": "Electronics", "price": 899.99},
    {"sku": "SKU-002", "name": "Smartphone", "category": "Electronics", "price": 599.99},
    {"sku": "SKU-003", "name": "Headphones", "category": "Electronics", "price": 149.99},
    {"sku": "SKU-004", "name": "Laptop Bag", "category": "Accessories", "price": 49.99},
    {"sku": "SKU-005", "name": "USB-C Hub", "category": "Accessories", "price": 39.99},
    {"sku": "SKU-006", "name": "Mouse", "category": "Accessories", "price": 29.99},
    {"sku": "SKU-007", "name": "Keyboard", "category": "Accessories", "price": 79.99},
    {"sku": "SKU-008", "name": "Monitor", "category": "Electronics", "price": 349.99},
    {"sku": "SKU-009", "name": "Webcam", "category": "Electronics", "price": 89.99},
    {"sku": "SKU-010", "name": "Phone Case", "category": "Accessories", "price": 19.99},
    {"sku": "SKU-011", "name": "Screen Protector", "category": "Accessories", "price": 9.99},
    {"sku": "SKU-012", "name": "Wireless Charger", "category": "Accessories", "price": 34.99},
    {"sku": "SKU-013", "name": "Power Bank", "category": "Electronics", "price": 49.99},
    {"sku": "SKU-014", "name": "Smartwatch", "category": "Electronics", "price": 249.99},
    {"sku": "SKU-015", "name": "Earbuds", "category": "Electronics", "price": 99.99},
    {"sku": "SKU-016", "name": "HDMI Cable", "category": "Accessories", "price": 14.99},
    {"sku": "SKU-017", "name": "SD Card", "category": "Storage", "price": 24.99},
    {"sku": "SKU-018", "name": "External SSD", "category": "Storage", "price": 119.99},
    {"sku": "SKU-019", "name": "Desk Lamp", "category": "Office", "price": 44.99},
    {"sku": "SKU-020", "name": "Mousepad", "category": "Accessories", "price": 19.99},
]

PRODUCT_MAP = {p["sku"]: p for p in PRODUCTS}


def maybe_add(cart, trigger_sku, additions, chance):
    if trigger_sku in cart and random.random() < chance:
        cart.update(additions)


def random_qty(sku):
    if sku in {"SKU-011", "SKU-016", "SKU-017"} and random.random() < 0.2:
        return 2
    return 1


def build_session_cart():
    weighted_roots = [
        "SKU-001",
        "SKU-001",
        "SKU-001",
        "SKU-002",
        "SKU-002",
        "SKU-002",
        "SKU-018",
        "SKU-006",
        "SKU-003",
        "SKU-014",
        "SKU-008",
        "SKU-019",
    ]
    root = random.choice(weighted_roots)

    cart = {root}

    pool = [p["sku"] for p in PRODUCTS if p["sku"] != root]
    for sku in random.sample(pool, k=random.randint(0, 2)):
        if random.random() < 0.35:
            cart.add(sku)

    # Required co-purchase patterns.
    maybe_add(cart, "SKU-001", {"SKU-004", "SKU-005"}, 0.35)
    maybe_add(cart, "SKU-001", {"SKU-006", "SKU-007"}, 0.30)
    maybe_add(cart, "SKU-001", {"SKU-008", "SKU-016"}, 0.25)

    maybe_add(cart, "SKU-002", {"SKU-010", "SKU-011"}, 0.40)
    maybe_add(cart, "SKU-002", {"SKU-012", "SKU-015"}, 0.35)
    maybe_add(cart, "SKU-002", {"SKU-013", "SKU-014"}, 0.28)

    maybe_add(cart, "SKU-006", {"SKU-020", "SKU-007"}, 0.38)
    maybe_add(cart, "SKU-018", {"SKU-017"}, 0.45)

    return cart


def generate_transactions(num_sessions=2000):
    rows = []
    for idx in range(1, num_sessions + 1):
        session_id = f"S-{idx:05d}"
        cart = build_session_cart()
        for sku in sorted(cart):
            item = PRODUCT_MAP[sku]
            rows.append(
                {
                    "session_id": session_id,
                    "item_id": item["sku"],
                    "item_name": item["name"],
                    "category": item["category"],
                    "price": item["price"],
                    "qty": random_qty(sku),
                }
            )
    return rows


def write_csv(rows):
    output_path = Path(__file__).resolve().parent.parent / "data" / "transactions.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["session_id", "item_id", "item_name", "category", "price", "qty"]
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return output_path


if __name__ == "__main__":
    random.seed(42)
    generated_rows = generate_transactions(num_sessions=2000)
    target = write_csv(generated_rows)
    print(f"Generated {len(generated_rows)} transaction item rows at: {target}")
