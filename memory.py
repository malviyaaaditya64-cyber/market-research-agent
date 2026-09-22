"""Memory management for the autonomous market research system."""

import sqlite3


class SharedMemory:
    """Simple local storage using SQLite for research findings.

    Creates a local memory.db SQLite database automatically on first use.
    All data is stored persistently in the current working directory.
    """

    def __init__(self, db_path="memory.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self._create_table()

    def _create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                source TEXT,
                date_collected TEXT,
                content TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def save_finding(self, company_name, source, date_collected, content):
        """Insert one research finding into the database.

        Args:
            company_name: Name of the company/product researched.
            source: URL or source identifier where data was collected.
            date_collected: ISO format date string when data was collected.
            content: Raw text content collected from the source.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO findings (company_name, source, date_collected, content) VALUES (?, ?, ?, ?)",
            (company_name, source, date_collected, content),
        )
        self.conn.commit()

    def get_findings(self, company_name):
        """Return all findings for a given company as a list of dictionaries.

        Args:
            company_name: Name of the company to look up.

        Returns:
            List of dictionaries with keys: id, company_name, source,
            date_collected, content, created_at.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, company_name, source, date_collected, content, created_at FROM findings WHERE company_name = ?",
            (company_name,),
        )
        rows = cursor.fetchall()
        return [
            {
                "id": row[0],
                "company_name": row[1],
                "source": row[2],
                "date_collected": row[3],
                "content": row[4],
                "created_at": row[5],
            }
            for row in rows
        ]

    def clear_findings(self, company_name):
        """Delete all findings for a given company.

        Useful for re-running research on the same company.

        Args:
            company_name: Name of the company whose findings to delete.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM findings WHERE company_name = ?",
            (company_name,),
        )
        self.conn.commit()

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()