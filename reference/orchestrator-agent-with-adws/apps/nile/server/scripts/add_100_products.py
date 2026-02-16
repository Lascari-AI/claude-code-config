"""
Script to add 100 new products to the Nile database.
- Reads all metadata files from images_and_metadata directory
- Checks against existing products in database to avoid duplicates
- Adds 100 new products with their reviews
- Images are already in public directory
"""
import asyncio
import json

# Add parent to path for imports
import sys
from pathlib import Path
from typing import Dict, List, Set

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from src.database import async_session
from src.models import Product, Review

# Paths
METADATA_DIR = Path(__file__).parent.parent.parent.parent.parent / "temp" / "_nile" / "images_and_metadata"
PUBLIC_IMAGES_DIR = Path(__file__).parent.parent.parent.parent / "client" / "public" / "images" / "products"


async def get_existing_product_names() -> Set[str]:
    """Get all product names currently in the database."""
    async with async_session() as db:
        result = await db.execute(select(Product.name))
        names = {row[0] for row in result.fetchall()}
        return names


def get_available_products_from_metadata() -> List[Dict]:
    """Read all metadata JSON files and return product data."""
    products = []

    for metadata_file in METADATA_DIR.glob("*_metadata.json"):
        # Skip empty _metadata.json
        if metadata_file.name == "_metadata.json":
            continue

        # Get corresponding image file
        image_name = metadata_file.name.replace("_metadata.json", ".jpg")
        image_path = METADATA_DIR / image_name

        if not image_path.exists():
            print(f"  Warning: No image for {metadata_file.name}")
            continue

        try:
            with open(metadata_file, 'r') as f:
                data = json.load(f)

            # Add image file path
            data['image_file_path'] = f"/images/products/{image_name}"
            data['_source_file'] = metadata_file.name
            products.append(data)
        except json.JSONDecodeError as e:
            print(f"  Error parsing {metadata_file.name}: {e}")
            continue

    return products


async def add_products_to_database(products: List[Dict]) -> int:
    """Add products and their reviews to the database."""
    added_count = 0

    async with async_session() as db:
        for product_data in products:
            try:
                # Extract reviews before creating product
                reviews_data = product_data.pop('reviews', [])
                product_data.pop('_source_file', None)  # Remove helper field

                # Create product
                product = Product(
                    name=product_data['name'],
                    description=product_data['description'],
                    price=product_data['price'],
                    image_file_path=product_data['image_file_path'],
                    category=product_data['category'],
                    brand=product_data['brand'],
                    rating=product_data['rating'],
                    shipping_speed=product_data['shipping_speed'],
                )
                db.add(product)
                await db.flush()  # Get the product ID

                # Add reviews
                for review_data in reviews_data:
                    review = Review(
                        product_id=product.id,
                        review_text=review_data['review_text'],
                        rating=review_data['rating'],
                        reviewer_name=review_data['reviewer_name'],
                        review_date=review_data['review_date'],
                    )
                    db.add(review)

                added_count += 1

            except Exception as e:
                print(f"  Error adding {product_data.get('name', 'unknown')}: {e}")
                continue

        await db.commit()

    return added_count


async def main():
    print("=" * 60)
    print("ADD 100 NEW PRODUCTS TO NILE DATABASE")
    print("=" * 60)

    # Step 1: Get existing products
    print("\n1. Getting existing products from database...")
    existing_names = await get_existing_product_names()
    print(f"   Found {len(existing_names)} existing products")

    # Step 2: Get available products from metadata
    print("\n2. Reading metadata files...")
    available_products = get_available_products_from_metadata()
    print(f"   Found {len(available_products)} products in metadata")

    # Step 3: Find products not in database
    print("\n3. Finding products not yet in database...")
    new_products = [
        p for p in available_products
        if p['name'] not in existing_names
    ]
    print(f"   Found {len(new_products)} new products available")

    if len(new_products) == 0:
        print("\n   ⚠️  No new products to add!")
        return

    # Step 4: Select 100 products (or all if less than 100)
    products_to_add = new_products[:100]
    print(f"\n4. Will add {len(products_to_add)} products")

    # Show what we're adding
    print("\n   Products to add:")
    for i, p in enumerate(products_to_add, 1):
        print(f"   {i:3d}. {p['name']} ({p['category']}) - ${p['price']}")

    # Step 5: Add to database
    print(f"\n5. Adding {len(products_to_add)} products to database...")
    added = await add_products_to_database(products_to_add)
    print(f"   ✅ Successfully added {added} products")

    # Step 6: Verify
    print("\n6. Verifying...")
    final_count = len(await get_existing_product_names())
    print(f"   Total products in database: {final_count}")

    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
