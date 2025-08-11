import tkinter as tk
from tkinter import messagebox, ttk
import data
from collections import defaultdict
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.dates import DateFormatter
import datetime
import time
from dotenv import load_dotenv
import os

load_dotenv()
FILE_PATH = os.getenv("DATABASE_PATH")
if FILE_PATH == "" or not FILE_PATH:
    print("Using default")
    FILE_PATH = "casino.db"

print(f"current file = {FILE_PATH}")

root = tk.Tk()
root.title("Casino Management System")
root.geometry("600x700")

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

data.start_up(FILE_PATH)
read_data = data.DatabaseReadConnection(FILE_PATH)

# OverView
def get_overview_data():
    casinos = read_data.get_casinos()
    get_overview_casino_stats()

    deposit = 0
    remaining = 0
    payment = 0
    for casino in casinos:
        deposit += casino[3]
        remaining += casino[4]
        payment += casino[5]
    overview_deposit_label.config(text=f"Total Deposit: {deposit}")
    overview_remaining_label.config(text=f"Total Remaining: {remaining}")
    overview_payment_label.config(text=f"Total Payment: {payment}")
    overview_profit_label.config(text=f"Total Profit: {payment+remaining-deposit}")

def get_overview_casino_stats():
    transactions = read_data.get_transactions()
    casinos = read_data.get_casinos()

    # Using defaultdict to store cumulative values per date
    cumulative_deposits = defaultdict(float)
    cumulative_remaining = defaultdict(float)
    cumulative_payments = defaultdict(float)

    total_deposit = 0  # Running total for deposits
    total_payment = 0  # Running total for payments
    total_remaining_per_site = [0 for _ in range(len(casinos))]

    for transaction in transactions:
        date = datetime.datetime.strptime(transaction[5], "%Y-%m-%d %H:%M:%S").date()

        # Increment cumulative sums
        total_deposit += transaction[2]     # Add new deposit
        total_remaining_per_site[transaction[1] - 1] = transaction[3]          # Add remaining balance
        total_payment += transaction[4]     # Add new payment

        # Store cumulative values, ensuring no decreases
        cumulative_deposits[date] = total_deposit
        cumulative_remaining[date] = sum(total_remaining_per_site)
        cumulative_payments[date] = total_payment

    # Ensure values never decrease by filling in missing dates with last known values
    sorted_dates = sorted(cumulative_deposits.keys())

    last_deposit = 0
    last_payment = 0
    deposits = []
    remaining = []
    payments = []
    profits = []

    for date in sorted_dates:
        # Ensure values never decrease
        last_deposit = max(last_deposit, cumulative_deposits[date])
        last_remaining = cumulative_remaining[date]
        last_payment = max(last_payment, cumulative_payments[date])

        deposits.append(last_deposit)
        remaining.append(last_remaining)
        payments.append(last_payment)
        profits.append(last_payment + last_remaining - last_deposit)

    # Create Matplotlib figure
    fig, ax = plt.subplots(figsize=(8, 5), dpi=100)

    # Plot cumulative data
    ax.plot(sorted_dates, deposits, marker='o', linestyle='-', label="Total Deposits", color='red')
    ax.plot(sorted_dates, remaining, marker='s', linestyle='--', label="Total Remaining", color='blue')
    ax.plot(sorted_dates, payments, marker='x', linestyle=':', label="Total Payments", color='green')
    ax.plot(sorted_dates, profits, marker='p', linestyle='-', label="Total Profit", color='purple')

    # Formatting the date axis
    ax.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d"))
    plt.xticks(rotation=45)
    ax.set_xlabel("Date")
    ax.set_ylabel("Amount ($)")
    ax.set_title("Cumulative Casino Transaction Trends")
    ax.legend()
    ax.grid(True)
    plt.tight_layout()

    # Embed figure into Tkinter
    global canvas_overview
    if 'canvas_overview' in globals():
        canvas_overview.get_tk_widget().destroy()

    canvas_overview = FigureCanvasTkAgg(fig, master=graph_overview_frame)
    canvas_overview.draw()
    canvas_overview.get_tk_widget().pack(fill=tk.BOTH, expand=True)

overview_tab = ttk.Frame(notebook)
notebook.add(overview_tab, text="Overview")

overview_deposit_label = tk.Label(overview_tab, text="")
overview_deposit_label.pack()
overview_remaining_label = tk.Label(overview_tab, text="")
overview_remaining_label.pack()
overview_payment_label = tk.Label(overview_tab, text="")
overview_payment_label.pack()
overview_profit_label = tk.Label(overview_tab, text="")
overview_profit_label.pack()

graph_overview_frame = ttk.Frame(overview_tab)
graph_overview_frame.pack(fill=tk.BOTH, expand=False)

tk.Button(overview_tab, text="Refresh Overview", command=get_overview_data).pack(pady=5)

# Casino Stats Tab
def get_casino_stats():
    try:
        casino_name = stats_casino_name_entry.get()
    except ValueError:
        messagebox.showerror("Error", "Plase enter a valid Casino Name.")
        return
    
    casino_stats = read_data.get_casino_stats_by_name(casino_name)

    if not casino_stats:
        messagebox.showerror("Error", "No transactions found for this casino.")
        return
    
    deposit = 0
    payment = 0
    stats = []
    for casino in casino_stats:
        deposit += casino[1]
        payment += casino[3]
        stats.append((casino[0], deposit, casino[2], payment))

    # Extract values for plotting
    dates = [datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S") for row in casino_stats]
    deposits = [row[1] for row in stats]
    remaining = [row[2] for row in stats]
    payments = [row[3] for row in stats]
    profits = [row[3]+row[2]-row[1] for row in stats]

    # Create a Matplotlib figure
    fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
    
    ax.plot(dates, deposits, marker='o', linestyle='-', label="Deposit", color='red')
    ax.plot(dates, remaining, marker='s', linestyle='--', label="Remaining", color='blue')
    ax.plot(dates, payments, marker='x', linestyle=':', label="Payment", color='green')
    ax.plot(dates, profits, marker='p', linestyle=':', label="Profit", color='purple')

    # Formatting the date axis
    ax.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d"))
    plt.xticks(rotation=45)
    ax.set_xlabel("Date")
    ax.set_ylabel("Amount ($)")
    ax.set_title(f"Transaction Trends for {casino_name}")
    ax.legend()
    ax.grid(True)

    # Embed the figure into Tkinter
    global canvas  # Avoid garbage collection removing the plot
    if 'canvas' in globals():
        canvas.get_tk_widget().destroy()  # Remove previous canvas

    canvas = FigureCanvasTkAgg(fig, master=graph_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    total_deposit = 0
    total_payment = 0
    for casino in casino_stats:
        total_deposit += casino[1]
        total_payment += casino[3]
    total_remaining = casino_stats[-1][2]
    
    casino_name_label.config(text=f"Casino: {casino_name}")
    total_deposit_label.config(text=f"Total Deposit: ${total_deposit:.2f}")
    total_remaining_label.config(text=f"Total Remaining: ${total_remaining:.2f}")
    total_payment_label.config(text=f"Total Payment: ${ total_payment:.2f}")
    total_profit_label.config(text=f"Total Profit: ${ total_payment+total_remaining-total_deposit }")
   

casino_stats_tab = ttk.Frame(notebook)
notebook.add(casino_stats_tab, text="Casino Stats")

tk.Label(casino_stats_tab, text="Enter Casino Name:").pack()
stats_casino_name_entry = tk.Entry(casino_stats_tab)
stats_casino_name_entry.pack()

tk.Button(casino_stats_tab, text="Get Stats", command=get_casino_stats).pack(pady=5)

casino_name_label = tk.Label(casino_stats_tab, text="Casino: -")
casino_name_label.pack()

total_deposit_label = tk.Label(casino_stats_tab, text="Total Deposit: $0.00")
total_deposit_label.pack()

total_remaining_label = tk.Label(casino_stats_tab, text="Total Remaining: $0.00")
total_remaining_label.pack()

total_payment_label = tk.Label(casino_stats_tab, text="Total Payment: $0.00")
total_payment_label.pack()

total_profit_label = tk.Label(casino_stats_tab, text="Total Profit: $0.00")
total_profit_label.pack()

# Graph Display Section
graph_frame = ttk.Frame(casino_stats_tab)
graph_frame.pack(fill=tk.BOTH, expand=False)


# View Casinos Section
def fill_casino_frame():
    casinos = read_data.get_casinos()

    casino_listbox.delete(*casino_listbox.get_children())
    for casino in casinos:
        profit = casino[5] + casino[4] - casino[3]
        casino_listbox.insert("", tk.END, values=(*casino, profit))
# View Casinos Tab
view_casinos_tab = ttk.Frame(notebook)
notebook.add(view_casinos_tab, text="View Casinos")

casino_listbox = ttk.Treeview(view_casinos_tab, columns=("ID", "Name", "Link", "Deposit", "Remaining", "Payment", "Profit"), show="headings")
for col in ("ID", "Name", "Link", "Deposit", "Remaining", "Payment", "Profit"):
    casino_listbox.heading(col, text=col)
casino_listbox.pack(fill="both", expand=True)

tk.Button(view_casinos_tab, text="Refresh Casinos", command=fill_casino_frame).pack(pady=5)

# View Transactions Section
def fill_transaction_frame():
    transactions = read_data.get_transactions()
    casinos = read_data.get_casinos()
    transaction_listbox.delete(*transaction_listbox.get_children())
    for transaction in transactions:
        casino = casinos[transaction[1]-1]
        trans = (transaction[0], casino[1], *transaction[2::])
        transaction_listbox.insert("", tk.END, values=trans)

# View Transactions Tab
view_transactions_tab = ttk.Frame(notebook)
notebook.add(view_transactions_tab, text="View Transactions")

transaction_listbox = ttk.Treeview(view_transactions_tab, columns=("ID", "Casino ID", "Deposit", "Remaining", "Payment", "Date"), show="headings")
for col in ("ID", "Casino ID", "Deposit", "Remaining", "Payment", "Date"):
    transaction_listbox.heading(col, text=col)

transaction_listbox.pack(fill="both", expand=True)

tk.Button(view_transactions_tab, text="Refresh Transactions", command=fill_transaction_frame).pack(pady=5)


# Casino Section
def add_casino():
    name = casino_name_entry.get()
    link = casino_link_entry.get()
    if link == "":
        link = None
    data.add_casino(name, link, FILE_PATH)
# Add Casino Tab
casino_tab = ttk.Frame(notebook)
notebook.add(casino_tab, text="Add Casino")

tk.Label(casino_tab, text="Casino Name:").pack()
casino_name_entry = tk.Entry(casino_tab)
casino_name_entry.pack()

tk.Label(casino_tab, text="Casino Link (optional):").pack()
casino_link_entry = tk.Entry(casino_tab)
casino_link_entry.pack()

tk.Button(casino_tab, text="Add Casino", command=add_casino).pack(pady=5)


# Transaction Section
def add_transaction():
    casino_name = transaction_casino_id_entry.get()
    deposit = int(transaction_deposit_entry.get())
    remaining = int(transaction_remaining_entry.get())
    payment = int(transaction_payment_entry.get())

    casinos = read_data.get_casinos()
    time.sleep(0.1)
    transaction_added = False
    for casino in casinos:
        if casino[1] == casino_name:
            data.add_transaction(casino[0], deposit, remaining, payment, FILE_PATH)
            transaction_added = True

    if not transaction_added:
        messagebox.showerror("Error", "No casino with that name.")
        return
    
# Add Transaction Tab
transaction_tab = ttk.Frame(notebook)
notebook.add(transaction_tab, text="Add Transaction")

tk.Label(transaction_tab, text="Casino Name:").pack()
transaction_casino_id_entry = tk.Entry(transaction_tab)
transaction_casino_id_entry.pack()

tk.Label(transaction_tab, text="Deposit:").pack()
transaction_deposit_entry = tk.Entry(transaction_tab)
transaction_deposit_entry.pack()

tk.Label(transaction_tab, text="Remaining:").pack()
transaction_remaining_entry = tk.Entry(transaction_tab)
transaction_remaining_entry.pack()

tk.Label(transaction_tab, text="Payment:").pack()
transaction_payment_entry = tk.Entry(transaction_tab)
transaction_payment_entry.pack()

tk.Button(transaction_tab, text="Add Transaction", command=add_transaction).pack(pady=5)
