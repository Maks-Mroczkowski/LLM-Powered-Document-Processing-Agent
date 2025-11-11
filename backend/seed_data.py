"""
Seed script to populate the database with sample data.
Run: python seed_data.py
"""
from app.database import SessionLocal, engine, Base
from app.models.models import User, VendorDatabase
from app.utils.auth import get_password_hash
from loguru import logger

def create_sample_vendors(db):
    """Create sample vendors for validation."""
    vendors = [
        {
            "vendor_name": "Acme Corporation",
            "vendor_id": "ACME001",
            "email": "billing@acme.com",
            "phone": "+1-555-0100",
            "address": "123 Business St, New York, NY 10001",
            "is_approved": True
        },
        {
            "vendor_name": "Global Tech Solutions",
            "vendor_id": "GTS002",
            "email": "accounts@globaltech.com",
            "phone": "+1-555-0200",
            "address": "456 Tech Ave, San Francisco, CA 94102",
            "is_approved": True
        },
        {
            "vendor_name": "Best Services Inc",
            "vendor_id": "BSI003",
            "email": "finance@bestservices.com",
            "phone": "+1-555-0300",
            "address": "789 Service Rd, Chicago, IL 60601",
            "is_approved": True
        },
        {
            "vendor_name": "Premium Supplies Co",
            "vendor_id": "PSC004",
            "email": "ar@premiumsupplies.com",
            "phone": "+1-555-0400",
            "address": "321 Supply Ln, Boston, MA 02101",
            "is_approved": True
        },
        {
            "vendor_name": "Reliable Partners LLC",
            "vendor_id": "RPL005",
            "email": "invoices@reliablepartners.com",
            "phone": "+1-555-0500",
            "address": "654 Partner Blvd, Seattle, WA 98101",
            "is_approved": True
        }
    ]

    for vendor_data in vendors:
        existing = db.query(VendorDatabase).filter(
            VendorDatabase.vendor_id == vendor_data["vendor_id"]
        ).first()

        if not existing:
            vendor = VendorDatabase(**vendor_data)
            db.add(vendor)
            logger.info(f"Added vendor: {vendor_data['vendor_name']}")

    db.commit()


def create_demo_user(db):
    """Create a demo user for testing."""
    existing_user = db.query(User).filter(User.username == "demo").first()

    if not existing_user:
        demo_user = User(
            email="demo@docprocessor.com",
            username="demo",
            hashed_password=get_password_hash("demo123"),
            is_active=True,
            is_superuser=False
        )
        db.add(demo_user)
        db.commit()
        logger.info("Created demo user: demo / demo123")
    else:
        logger.info("Demo user already exists")


def main():
    """Main seeding function."""
    logger.info("Starting database seeding...")

    # Create tables
    Base.metadata.create_all(bind=engine)

    # Create session
    db = SessionLocal()

    try:
        # Seed vendors
        logger.info("Seeding vendors...")
        create_sample_vendors(db)

        # Create demo user
        logger.info("Creating demo user...")
        create_demo_user(db)

        logger.info("Database seeding completed successfully!")

    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
