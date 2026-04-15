# Prompt History


---

## Step 1: Database Setup

**Prompt:**
> Write a Python script called `db_setup.py` that initializes a minimal SQLite database for a double-entry accounting system using the built-in `sqlite3` library. Create the necessary tables for double-entry bookkeeping, such as Accounts, Transactions, and TransactionLines. The Accounts table must be pre-populated with exactly five fixed accounts: 1000 for Cash, 1100 for Accounts Receivable, 2000 for Accounts Payable, 4000 for Revenue, and 5000 for Expense. Write ONLY the database creation and initialization script, and do not write any other functions.

**AI Response:**
```python
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
```

---

## Step 2: Core Accounting Logic

**Prompt:**
> Based on the database schema created in the previous step, write a new Python file called `accounting_logic.py`. Write four plain Python functions that insert records into the database for specific business events, ensuring a balanced double-entry transaction where total debits equal total credits, and accepting partner_name, amount, and description. The first function is issue_customer_invoice, which increases 1100 AR and increases 4000 Revenue. The second is receive_customer_payment, which increases 1000 Cash and decreases 1100 AR. The third is receive_vendor_bill, which increases 5000 Expense and increases 2000 AP. The fourth is pay_vendor_bill, which decreases 2000 AP and decreases 1000 Cash. Do not use any external frameworks, just sqlite3 and Python.

**AI Response:**
```python
# accounting_logic.py
import sqlite3

def _record_transaction(partner_name, description, debit_account, credit_account, amount):
    """
    Internal helper function to record a balanced double-entry transaction.
    Ensures that total debits equal total credits by using the same amount.
    """
    conn = sqlite3.connect('accounting.db')
    cursor = conn.cursor()
    
    try:
        # Enforce foreign key constraints
        cursor.execute('PRAGMA foreign_keys = ON;')
        
        # Combine partner name and description for the transaction record
        full_description = f"{partner_name}: {description}"
        
        # 1. Create the header Transaction record
        cursor.execute('''
            INSERT INTO Transactions (description)
            VALUES (?)
        ''', (full_description,))
        
        transaction_id = cursor.lastrowid
        
        # 2. Insert the Debit TransactionLine
        cursor.execute('''
            INSERT INTO TransactionLines (transaction_id, account_code, debit, credit)
            VALUES (?, ?, ?, ?)
        ''', (transaction_id, debit_account, amount, 0.0))
        
        # 3. Insert the Credit TransactionLine
        cursor.execute('''
            INSERT INTO TransactionLines (transaction_id, account_code, debit, credit)
            VALUES (?, ?, ?, ?)
        ''', (transaction_id, credit_account, 0.0, amount))
        
        # Commit the atomic transaction
        conn.commit()
        print(f"Successfully recorded transaction: {full_description} for {amount}")
        
    except sqlite3.Error as e:
        # Roll back any changes if an error occurs (e.g., invalid account code)
        conn.rollback()
        print(f"Failed to record transaction. Database error: {e}")
    finally:
        conn.close()

def issue_customer_invoice(partner_name, amount, description):
    """
    Records a customer invoice.
    Increases Accounts Receivable (Debit 1100) and increases Revenue (Credit 4000).
    """
    _record_transaction(partner_name, description, debit_account=1100, credit_account=4000, amount=amount)

def receive_customer_payment(partner_name, amount, description):
    """
    Records a payment received from a customer.
    Increases Cash (Debit 1000) and decreases Accounts Receivable (Credit 1100).
    """
    _record_transaction(partner_name, description, debit_account=1000, credit_account=1100, amount=amount)

def receive_vendor_bill(partner_name, amount, description):
    """
    Records a bill received from a vendor.
    Increases Expense (Debit 5000) and increases Accounts Payable (Credit 2000).
    """
    _record_transaction(partner_name, description, debit_account=5000, credit_account=2000, amount=amount)

def pay_vendor_bill(partner_name, amount, description):
    """
    Records a payment made to a vendor.
    Decreases Accounts Payable (Debit 2000) and decreases Cash (Credit 1000).
    """
    _record_transaction(partner_name, description, debit_account=2000, credit_account=1000, amount=amount)
```

---

## Step 3: Reporting Logic

**Prompt:**
> Add two more functions to `accounting_logic.py` to retrieve data for reports. The first function is `get_pnl_report`, which calculates Total Revenue from account 4000 and Total Expenses from account 5000, and returns the Net Income. The second function is `get_partner_ledger`, which accepts a partner name and returns the total AR or AP balance for that specific partner along with a list of all their transaction lines. Write just the data retrieval logic.

**AI Response:**
```python
import sqlite3

def get_pnl_report():
    """
    Calculates Total Revenue, Total Expenses, and Net Income.
    Revenue normal balance is Credit (Account 4000).
    Expense normal balance is Debit (Account 5000).
    """
    conn = sqlite3.connect('accounting.db')
    cursor = conn.cursor()
    
    try:
        # Calculate Revenue (Sum of Credits - Sum of Debits for Account 4000)
        cursor.execute('''
            SELECT SUM(credit) - SUM(debit) 
            FROM TransactionLines 
            WHERE account_code = 4000
        ''')
        revenue = cursor.fetchone()[0] or 0.0
        
        # Calculate Expenses (Sum of Debits - Sum of Credits for Account 5000)
        cursor.execute('''
            SELECT SUM(debit) - SUM(credit) 
            FROM TransactionLines 
            WHERE account_code = 5000
        ''')
        expense = cursor.fetchone()[0] or 0.0
        
        net_income = revenue - expense
        
        return {
            'Total Revenue': revenue,
            'Total Expenses': expense,
            'Net Income': net_income
        }
        
    finally:
        conn.close()

def get_partner_ledger(partner_name):
    """
    Retrieves the total AR/AP balances and a list of all transaction lines 
    associated with a specific partner.
    """
    conn = sqlite3.connect('accounting.db')
    conn.row_factory = sqlite3.Row  # Returns rows as dictionary-like objects
    cursor = conn.cursor()
    
    try:
        # Match the exact partner string pattern defined in the insertion logic
        like_pattern = f"{partner_name}: %"
        
        # 1. Calculate Accounts Receivable Balance (Account 1100 - Normal Balance: Debit)
        cursor.execute('''
            SELECT SUM(l.debit) - SUM(l.credit)
            FROM Transactions t
            JOIN TransactionLines l ON t.id = l.transaction_id
            WHERE t.description LIKE ? AND l.account_code = 1100
        ''', (like_pattern,))
        ar_balance = cursor.fetchone()[0] or 0.0
        
        # 2. Calculate Accounts Payable Balance (Account 2000 - Normal Balance: Credit)
        cursor.execute('''
            SELECT SUM(l.credit) - SUM(l.debit)
            FROM Transactions t
            JOIN TransactionLines l ON t.id = l.transaction_id
            WHERE t.description LIKE ? AND l.account_code = 2000
        ''', (like_pattern,))
        ap_balance = cursor.fetchone()[0] or 0.0
        
        # 3. Retrieve all transaction lines for this partner
        cursor.execute('''
            SELECT t.date, t.description, l.account_code, l.debit, l.credit
            FROM Transactions t
            JOIN TransactionLines l ON t.id = l.transaction_id
            WHERE t.description LIKE ?
            ORDER BY t.date, t.id
        ''', (like_pattern,))
        
        transactions = [dict(row) for row in cursor.fetchall()]
        
        return {
            'partner_name': partner_name,
            'AR_balance': ar_balance,
            'AP_balance': ap_balance,
            'transaction_lines': transactions
        }
        
    finally:
        conn.close()
```

---

## Step 4: Streamlit Frontend

**Prompt:**
> Wrap the functions from `accounting_logic.py` into a minimal web UI using Streamlit in a new file called `app.py`. The application must have a sidebar to navigate between three pages named Data Entry, Journal, and Reports. The Data Entry page must contain simple forms to execute the four business events for invoices, bills, and payments. The Journal page must display all transactions from the database in a simple table. The Reports page must display the Profit and Loss report and allow the user to select a partner to view their specific ledger. Keep the UI clean, pragmatic, and simple.

**AI Response:**
Here is the `app.py` script. It uses Streamlit to create a clean, interactive UI that directly imports and utilizes the functions from your `accounting_logic.py` file.

```python
# app.py
import streamlit as st
import sqlite3
from accounting_logic import (
    issue_customer_invoice,
    receive_customer_payment,
    receive_vendor_bill,
    pay_vendor_bill,
    get_pnl_report,
    get_partner_ledger
)

# Set page configuration
st.set_page_config(page_title="Minimal Accounting", layout="wide")

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Data Entry", "Journal", "Reports"])

if page == "Data Entry":
    st.header("Data Entry")
    
    # Select the type of business event
    txn_type = st.selectbox("Transaction Type", [
        "Issue Customer Invoice",
        "Receive Customer Payment",
        "Receive Vendor Bill",
        "Pay Vendor Bill"
    ])

    # Form for data entry to ensure data is only submitted on button click
    with st.form("entry_form"):
        partner_name = st.text_input("Partner Name (e.g., Acme Corp)")
        amount = st.number_input("Amount", min_value=0.01, format="%.2f")
        description = st.text_input("Description")
        
        submitted = st.form_submit_button("Record Transaction")

        if submitted:
            if not partner_name or not description:
                st.error("Please fill in all text fields.")
            else:
                # Route to the appropriate accounting logic function
                if txn_type == "Issue Customer Invoice":
                    issue_customer_invoice(partner_name, amount, description)
                elif txn_type == "Receive Customer Payment":
                    receive_customer_payment(partner_name, amount, description)
                elif txn_type == "Receive Vendor Bill":
                    receive_vendor_bill(partner_name, amount, description)
                elif txn_type == "Pay Vendor Bill":
                    pay_vendor_bill(partner_name, amount, description)
                
                st.success(f"Successfully recorded: {txn_type} for {partner_name} (${amount:,.2f})")

elif page == "Journal":
    st.header("Journal")
    
    # Fetch all transactions and lines, joining with Accounts for readability
    conn = sqlite3.connect('accounting.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT t.date as Date, t.id as Txn_ID, t.description as Description, 
               l.account_code || ' - ' || a.name as Account, 
               l.debit as Debit, l.credit as Credit
        FROM Transactions t
        JOIN TransactionLines l ON t.id = l.transaction_id
        JOIN Accounts a ON l.account_code = a.code
        ORDER BY t.date DESC, t.id DESC, l.credit ASC
    ''')
    
    # Convert cursor results to a list of dictionaries for Streamlit
    columns = [column[0] for column in cursor.description]
    journal_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    
    if journal_data:
        st.dataframe(journal_data, use_container_width=True)
    else:
        st.info("No transactions found in the database. Go to Data Entry to record your first event.")

elif page == "Reports":
    st.header("Reports")
    
    # --- Profit and Loss Section ---
    st.subheader("Profit & Loss")
    pnl = get_pnl_report()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Revenue", f"${pnl['Total Revenue']:,.2f}")
    col2.metric("Total Expenses", f"${pnl['Total Expenses']:,.2f}")
    
    # Color-code net income depending on profitability
    net_income = pnl['Net Income']
    delta_color = "normal" if net_income >= 0 else "inverse"
    col3.metric("Net Income", f"${net_income:,.2f}", delta_color=delta_color)

    st.divider()

    # --- Partner Ledger Section ---
    st.subheader("Partner Ledger")
    partner_search = st.text_input("Enter Partner Name to view their ledger:")
    
    if partner_search:
        ledger = get_partner_ledger(partner_search)
        
        # Display summary balances
        st.markdown(f"**Accounts Receivable (AR) Balance:** ${ledger['AR_balance']:,.2f}")
        st.markdown(f"**Accounts Payable (AP) Balance:** ${ledger['AP_balance']:,.2f}")
        
        # Display the line items associated with this partner
        if ledger['transaction_lines']:
            st.dataframe(ledger['transaction_lines'], use_container_width=True)
        else:
            st.info(f"No transactions found for partner: '{partner_search}'. Note that searches are case-sensitive.")
```

---

## Step 5: Dockerization & Environment Setup

**Prompt:**
> Package the application for delivery by creating a `pyproject.toml` file to manage dependencies and a standard `Dockerfile` for this Streamlit application using a lightweight base image like `python:3.11-slim`. Expose port 8501 and provide the correct CMD to run Streamlit within the container. Additionally, provide a `.dockerignore` file to exclude the SQLite database file and the `__pycache__` directory.

**AI Response:**
Here are the configuration files needed to package your minimal accounting application for deployment.

**pyproject.toml:**
```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "minimal-accounting"
version = "0.1.0"
description = "A minimal double-entry accounting Streamlit application"
requires-python = ">=3.11"
dependencies = [
    "streamlit>=1.30.0",
]
```

**.dockerignore:**
```plaintext
# Ignore local database
accounting.db

# Ignore Python cache directories and compiled files
__pycache__/
*.pyc
*.pyo

# Ignore virtual environments and git history
.venv/
venv/
env/
.git/
```

**Dockerfile:**
```dockerfile
# Use the official Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables to prevent Python from writing .pyc files
# and to ensure output is logged directly to the terminal
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy the pyproject.toml first to leverage Docker caching for dependencies
COPY pyproject.toml ./

# Install the dependencies defined in pyproject.toml
RUN pip install --no-cache-dir .

# Copy the rest of the application code
COPY . .

# Initialize the fresh SQLite database inside the image
RUN python db_setup.py

# Expose the standard Streamlit port
EXPOSE 8501

# Command to run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

---

## Step 6: Documentation

**Prompt:**
> Write the `README.md` for the GitHub repository containing a short and clear explanation of the product and technical decisions, specifically mentioning the double-entry model, fixed chart of accounts, and Streamlit. The README must also include clear step-by-step instructions on how to build and run the Docker container.

**AI Response:**
```markdown
# Minimal Accounting

A pragmatic, lightweight web application for recording business transactions and generating basic financial reports. 

## Overview and Technical Decisions

This application was designed to demonstrate a robust accounting core with a minimal, easy-to-use interface. The architecture relies entirely on the Python standard library for data management and Streamlit for the frontend UI. 

Key technical decisions include:

* **Double-Entry Model:** The core database schema strictly adheres to double-entry bookkeeping principles. Every business event generates a single header record (`Transactions`) and at least two balanced line items (`TransactionLines`) ensuring total Debits always equal total Credits. 
* **Fixed Chart of Accounts:** To maintain simplicity and focus on the core flow, the system is hardcoded with exactly five fundamental accounts:
    * `1000`: Cash (Asset)
    * `1100`: Accounts Receivable (Asset)
    * `2000`: Accounts Payable (Liability)
    * `4000`: Revenue (Equity/Income)
    * `5000`: Expense (Equity/Expense)
* **Streamlit Frontend:** Chosen for its ability to rapidly deploy clean, interactive data web apps purely in Python, eliminating the need for a separate Javascript frontend or complex API routing.
* **SQLite Database:** Utilizes Python's built-in `sqlite3` module. The database is initialized fresh inside the Docker container at build time, ensuring a predictable, zero-dependency environment.

## Prerequisites

* [Docker](https://docs.docker.com/get-docker/) installed on your machine.

## Getting Started

Follow these steps to build and run the application via Docker:

1. **Clone the repository and navigate into the directory.**

2. **Build the Docker image:**
   ```bash
   docker build -t minimal-accounting .
   ```

3. **Run the Docker container:**
   ```bash
   docker run -p 8501:8501 minimal-accounting
   ```

4. **Access the application:**
   Open your web browser and navigate to `http://localhost:8501`.


