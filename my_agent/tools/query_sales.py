import sqlite3

DB_PATH = "./db/sales.db"


def query_sales(query: str) -> dict:
    """Query the sales database using SQL.

    The sales database contains sales transaction data with the following schema:

    Table: sales
        - id: INTEGER PRIMARY KEY
        - date: DATE (format: YYYY-MM-DD)
        - year: INTEGER (e.g., 2025)
        - month: INTEGER (1-12)
        - category: VARCHAR(100) (e.g., 'Electronics', 'Clothing', 'Home & Garden')
        - amount: DECIMAL(10,2) (sale amount in dollars)

    Args:
        query (str): A SQL SELECT query to execute against the sales database.
            Only SELECT statements are allowed for security.

    Returns:
        dict: Contains 'status', 'columns' (list of column names),
              and 'results' (list of row tuples).

    Example queries:
        - "SELECT * FROM sales WHERE year = 2025 AND month >= 10"
        - "SELECT category, SUM(amount) as total FROM sales GROUP BY category"
        - "SELECT * FROM sales ORDER BY amount DESC LIMIT 5"
    """
    try:
        # Security: Only allow SELECT statements
        normalized = query.strip().upper()
        if not normalized.startswith("SELECT"):
            return {
                "status": "error",
                "message": "Only SELECT queries are allowed"
            }

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(query)

        columns = [description[0] for description in cursor.description]
        results = cursor.fetchall()

        conn.close()

        return {
            "status": "success",
            "columns": columns,
            "results": results
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
