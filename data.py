import sqlite3

DB_NAME = "casino.db"

class DatabaseReadConnection:
    def __init__(self, file_path = DB_NAME):
        self.conn, self.cursor = create_connection(file_path)
    
    def close(self):
        self.cursor.close()
        self.conn.close()

    def get_casinos(self):
        self.cursor.execute("SELECT * FROM casino")
        casinos = self.cursor.fetchall()

        return casinos
    
    def get_casino_stats_by_name(self, name: str):
        self.cursor.execute("""
            SELECT t.created_at, t.deposit, t.remaining, t.payment
            FROM casino c
            LEFT JOIN transactions t ON c.id = t.casino_id
            WHERE c.name = ?
            ORDER BY t.created_at
        """, (name,))

        result = self.cursor.fetchall()
        return result

    def get_transactions(self):
        self.cursor.execute("SELECT * FROM transactions")
        transactions = self.cursor.fetchall()

        return transactions

    def get_transaction_by_id(self, casino_id: int):
        self.cursor.execute("SELECT * FROM transactions WHERE id = ?", (casino_id,))
        transactions = self.cursor.fetchall()

        return transactions

def create_connection(target = DB_NAME):
    if not target:
        target = DB_NAME
    conn = sqlite3.connect(target, timeout=5)
    cursor = conn.cursor()

    return (conn, cursor)

def start_up(target = DB_NAME) -> None:
    conn, cursor = create_connection(target)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS casino (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            link TEXT,
            deposit FLOAT NOT NULL,
            remaining FLOAT NOT NULL,
            payment FLOAT NOT NULL
        )
    """)
    conn.commit()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            casino_id INTEGER NOT NULL,
            deposit FLOAT NOT NULL,
            remaining FLOAT NOT NULL,
            payment FLOAT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (casino_id) REFERENCES casino(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    
def add_casino(name: str, link: str = None, target = DB_NAME):
    conn, cursor = create_connection(target)

    cursor.execute("INSERT INTO casino (name, link, deposit, remaining, payment) VALUES (?, ?, 0, 0, 0)", (name, link))

    conn.commit()
    cursor.close()
    conn.close()

def add_transaction(casino_id: int, deposit: float = 0, remaining: float = 0, payment: float = 0, target = DB_NAME):
    print(f"Adding transaction: Casino ID={casino_id}, Deposit={deposit}, Remaining={remaining}, Payment={payment}")

    conn, cursor = create_connection(target)
    if conn is None or cursor is None:
        print("Database connection failed.")
        return

    try:
        cursor.execute("SELECT * FROM casino WHERE id = ?", (casino_id,))
        casino = cursor.fetchone()

        print(f"Found casino: {casino}")

        if casino is None:
            raise ValueError(f"Casino with ID {casino_id} does not exist!")

        cursor.execute("""
            INSERT INTO transactions (casino_id, deposit, remaining, payment)
            VALUES (?, ?, ?, ?)
        """, (casino_id, deposit, remaining, payment))
        conn.commit()
        
        print("Inserted into database")

        cursor.execute("""
            UPDATE casino
            SET deposit = ?, remaining = ?, payment = ?
            WHERE id = ?
        """, (casino[3] + deposit, remaining, casino[5] + payment, casino_id))
        print("Updated")
        conn.commit()

    except sqlite3.OperationalError as e:
        print(f"Database Error: {e}")

    finally:
        cursor.close()
        conn.close()

def move_database_data(source_db, target_db):
    """
    Moves all data from the source database to the target database.
    Assumes both databases have the same schema.
    
    :param source_db: Path to the source database file
    :param target_db: Path to the target database file
    """
    try:
        # Connect to source and target databases
        source_conn = sqlite3.connect(source_db)
        target_conn = sqlite3.connect(target_db)
        
        source_cursor = source_conn.cursor()
        target_cursor = target_conn.cursor()
        
        # Get list of all tables
        source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = source_cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            
            # Fetch all data from the source table
            source_cursor.execute(f"SELECT * FROM {table_name}")
            rows = source_cursor.fetchall()
            
            # Get column names
            source_cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in source_cursor.fetchall()]
            
            if rows:
                # Insert data into target table
                placeholders = ', '.join(['?'] * len(columns))
                column_names = ', '.join(columns)
                insert_query = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
                target_cursor.executemany(insert_query, rows)
                target_conn.commit()
        
        print("Data transfer complete.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        source_conn.close()
        target_conn.close()


if __name__ == "__main__":
    offset_path = "C:/Users/matti/Desktop/"
    new_db = f"{offset_path}{DB_NAME}"
    # start_up(new_db)
    # move_database_data(DB_NAME, new_db)
  
