"""Initialize the sales database with sample data."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "sales.db"


def init_database():
    """Create and populate the sales database."""
    # Remove existing database
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create table
    cursor.execute("""
        CREATE TABLE sales (
            id INTEGER PRIMARY KEY,
            date DATE NOT NULL,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            category VARCHAR(100),
            amount DECIMAL(10,2) NOT NULL
        )
    """)

    # Sample 2025 monthly sales data (complete year)
    # These are designed to be slightly different from typical forecasts
    # to demonstrate variance analysis
    sales_2025 = [
        # (month, category, amount)
        (1, "Electronics", 28500.00),
        (1, "Clothing", 15200.00),
        (1, "Home & Garden", 8300.00),
        (2, "Electronics", 31200.00),
        (2, "Clothing", 14800.00),
        (2, "Home & Garden", 9100.00),
        (3, "Electronics", 35600.00),
        (3, "Clothing", 18900.00),
        (3, "Home & Garden", 12500.00),
        (4, "Electronics", 33200.00),
        (4, "Clothing", 21500.00),
        (4, "Home & Garden", 15800.00),
        (5, "Electronics", 38900.00),
        (5, "Clothing", 24300.00),
        (5, "Home & Garden", 18200.00),
        (6, "Electronics", 42100.00),
        (6, "Clothing", 22800.00),
        (6, "Home & Garden", 16500.00),
        (7, "Electronics", 39800.00),
        (7, "Clothing", 19200.00),
        (7, "Home & Garden", 14300.00),
        (8, "Electronics", 44500.00),
        (8, "Clothing", 21100.00),
        (8, "Home & Garden", 13800.00),
        (9, "Electronics", 41200.00),
        (9, "Clothing", 25600.00),
        (9, "Home & Garden", 11900.00),
        (10, "Electronics", 48700.00),
        (10, "Clothing", 28900.00),
        (10, "Home & Garden", 14500.00),
        (11, "Electronics", 62300.00),
        (11, "Clothing", 38500.00),
        (11, "Home & Garden", 19200.00),
        (12, "Electronics", 71200.00),
        (12, "Clothing", 45600.00),
        (12, "Home & Garden", 22800.00),
    ]

    for month, category, amount in sales_2025:
        date = f"2025-{month:02d}-15"
        cursor.execute(
            """
            INSERT INTO sales (date, year, month, category, amount)
            VALUES (?, 2025, ?, ?, ?)
        """,
            (date, month, category, amount),
        )

    conn.commit()

    # Verify data
    cursor.execute("SELECT COUNT(*) FROM sales")
    count = cursor.fetchone()[0]

    cursor.execute("SELECT year, SUM(amount) as total FROM sales GROUP BY year")
    totals = cursor.fetchall()

    cursor.execute(
        """
        SELECT month, SUM(amount) as monthly_total
        FROM sales
        WHERE year = 2025
        GROUP BY month
        ORDER BY month
    """
    )
    monthly = cursor.fetchall()

    conn.close()

    print(f"Database initialized at: {DB_PATH}")
    print(f"Total records: {count}")
    print("\nYearly totals:")
    for year, total in totals:
        print(f"  {year}: ${total:,.2f}")
    print("\n2025 Monthly totals:")
    month_names = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]
    for month, total in monthly:
        print(f"  {month_names[month - 1]}: ${total:,.2f}")


if __name__ == "__main__":
    init_database()
