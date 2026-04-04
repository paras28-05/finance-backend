"""
seed.py — Populates the database with demo users and financial records.

Run once after initial setup:
    python seed.py
"""
import sys
from datetime import datetime, timedelta
import random
from app.database import SessionLocal, engine
from app.models import Base, User, FinancialRecord, UserRole, RecordType
from app.auth import hash_password

Base.metadata.create_all(bind=engine)

CATEGORIES_INCOME = ["Salary", "Freelance", "Investment Returns", "Bonus", "Consulting"]
CATEGORIES_EXPENSE = ["Rent", "Utilities", "Salaries Paid", "Marketing", "Software", "Travel", "Office Supplies"]

def seed():
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            print("⚠  Database already seeded. Skipping.")
            return

        # ── Users ──────────────────────────────────────────────────────────
        users = [
            User(username="admin",   email="admin@zorvyn.com",   full_name="System Admin",   hashed_password=hash_password("admin123"),   role=UserRole.admin),
            User(username="analyst", email="analyst@zorvyn.com", full_name="Data Analyst",   hashed_password=hash_password("analyst123"), role=UserRole.analyst),
            User(username="viewer",  email="viewer@zorvyn.com",  full_name="Dashboard Viewer", hashed_password=hash_password("viewer123"), role=UserRole.viewer),
        ]
        db.add_all(users)
        db.commit()
        for u in users:
            db.refresh(u)

        admin_id = users[0].id

        # ── Financial Records (12 months of demo data) ─────────────────────
        records = []
        base_date = datetime(2024, 1, 1)

        for month_offset in range(12):
            month_start = base_date + timedelta(days=30 * month_offset)

            # 2–4 income entries per month
            for _ in range(random.randint(2, 4)):
                records.append(FinancialRecord(
                    amount=round(random.uniform(5000, 50000), 2),
                    type=RecordType.income,
                    category=random.choice(CATEGORIES_INCOME),
                    date=month_start + timedelta(days=random.randint(0, 27)),
                    notes=f"Income entry for {month_start.strftime('%B %Y')}",
                    created_by=admin_id,
                ))

            # 3–6 expense entries per month
            for _ in range(random.randint(3, 6)):
                records.append(FinancialRecord(
                    amount=round(random.uniform(500, 20000), 2),
                    type=RecordType.expense,
                    category=random.choice(CATEGORIES_EXPENSE),
                    date=month_start + timedelta(days=random.randint(0, 27)),
                    notes=f"Expense entry for {month_start.strftime('%B %Y')}",
                    created_by=admin_id,
                ))

        db.add_all(records)
        db.commit()

        print("✅ Seeding complete!")
        print(f"   Users created : {len(users)}")
        print(f"   Records created: {len(records)}")
        print()
        print("Default credentials:")
        print("  admin   / admin123   (role: admin)")
        print("  analyst / analyst123 (role: analyst)")
        print("  viewer  / viewer123  (role: viewer)")

    finally:
        db.close()

if __name__ == "__main__":
    seed()
