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
                       WHERE t.description LIKE ?
                         AND l.account_code = 1100
                       ''', (like_pattern,))
        ar_balance = cursor.fetchone()[0] or 0.0

        # 2. Calculate Accounts Payable Balance (Account 2000 - Normal Balance: Credit)
        cursor.execute('''
                       SELECT SUM(l.credit) - SUM(l.debit)
                       FROM Transactions t
                                JOIN TransactionLines l ON t.id = l.transaction_id
                       WHERE t.description LIKE ?
                         AND l.account_code = 2000
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

