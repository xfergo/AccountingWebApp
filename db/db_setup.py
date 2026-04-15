# db_setup.py
import sqlite3

# Connect to the SQLite database (creates 'accounting.db' if it doesn't exist)
conn = sqlite3.connect('accounting.db')
cursor = conn.cursor()

# Enable foreign key support in SQLite
cursor.execute('PRAGMA foreign_keys = ON;')

# Create the Accounts table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Accounts (
    code INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
''')

# Create the Transactions table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL DEFAULT (date('now')),
    description TEXT
);
''')

# Create the TransactionLines table for double-entry bookkeeping
cursor.execute('''
CREATE TABLE IF NOT EXISTS TransactionLines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id INTEGER NOT NULL,
    account_code INTEGER NOT NULL,
    debit REAL NOT NULL DEFAULT 0.0,
    credit REAL NOT NULL DEFAULT 0.0,
    FOREIGN KEY (transaction_id) REFERENCES Transactions (id) ON DELETE CASCADE,
    FOREIGN KEY (account_code) REFERENCES Accounts (code)
);
''')

# Define the exact five fixed accounts required
fixed_accounts = [
    (1000, 'Cash'),
    (1100, 'Accounts Receivable'),
    (2000, 'Accounts Payable'),
    (4000, 'Revenue'),
    (5000, 'Expense')
]

# Pre-populate the Accounts table
# Using INSERT OR IGNORE allows the script to be safely run multiple times without throwing duplicate key errors
cursor.executemany('''
INSERT OR IGNORE INTO Accounts (code, name)
VALUES (?, ?)
''', fixed_accounts)

# Commit the transaction and close the database connection
conn.commit()
conn.close()

print("Database successfully initialized with Accounts, Transactions, and TransactionLines.")