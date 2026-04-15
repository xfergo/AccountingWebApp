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
                       JOIN TransactionLines l
                   ON t.id = l.transaction_id
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