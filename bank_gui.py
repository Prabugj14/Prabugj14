import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import hashlib
from datetime import datetime, timezone

# -------------------------
# Settings
# -------------------------

DATA_FILE = "bank_data.json"
MIN_PIN_LENGTH = 4
INITIAL_ACCOUNT_NUMBER = 10000001

accounts = {}
next_acc_no = INITIAL_ACCOUNT_NUMBER


# -------------------------
# Helper functions
# -------------------------

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


# Data saving/loading


def save_data():
    data = {
        "next_acc_no": next_acc_no,
        "accounts": list(accounts.values()),
    }

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_data():
    global accounts, next_acc_no

    if not os.path.exists(DATA_FILE):
        save_data()
        return

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        accounts = {
            account["acc_no"]: account
            for account in data.get("accounts", [])
        }

        next_acc_no = data.get("next_acc_no", INITIAL_ACCOUNT_NUMBER)

    except Exception as e:
        print("Failed to load data:", e)
        accounts = {}
        next_acc_no = INITIAL_ACCOUNT_NUMBER


# -------------------------
# Bank logic
# -------------------------

def add_transaction(account, ttype, amount, note=""):
    account["transactions"].append({
        "time": now_str(),
        "type": ttype,
        "amount": round(float(amount), 2),
        "balance_after": round(float(account["balance"]), 2),
        "note": note,
    })


def create_account(name, email, pin):
    global next_acc_no

    acc_no = next_acc_no
    next_acc_no += 1

    account = {
        "acc_no": acc_no,
        "name": name,
        "email": email,
        "pin_hash": hash_password(pin),
        "balance": 0.0,
        "transactions": [],
    }

    accounts[acc_no] = account
    add_transaction(account, "account_created", 0.0, "Account created")
    save_data()

    return acc_no


def authenticate(acc_no, pin):
    account = accounts.get(acc_no)

    if not account:
        raise ValueError("Account not found.")

    if account["pin_hash"] != hash_password(pin):
        raise ValueError("Invalid PIN.")

    return account


def deposit(account, amount):
    amount = float(amount)

    if amount <= 0:
        raise ValueError("Deposit amount must be positive.")

    account["balance"] = round(account["balance"] + amount, 2)
    add_transaction(account, "deposit", amount, "Deposit via GUI")
    save_data()


def withdraw(account, amount):
    amount = float(amount)

    if amount <= 0:
        raise ValueError("Withdraw amount must be positive.")

    if amount > account["balance"]:
        raise ValueError("Insufficient funds.")

    account["balance"] = round(account["balance"] - amount, 2)
    add_transaction(account, "withdraw", amount, "Withdraw via GUI")
    save_data()


def transfer(from_account, to_acc_no, amount):
    amount = float(amount)

    if amount <= 0:
        raise ValueError("Transfer amount must be positive.")

    to_account = accounts.get(to_acc_no)

    if not to_account:
        raise ValueError("Destination account not found.")

    if from_account["acc_no"] == to_acc_no:
        raise ValueError("Cannot transfer to the same account.")

    if amount > from_account["balance"]:
        raise ValueError("Insufficient funds.")

    from_account["balance"] = round(from_account["balance"] - amount, 2)
    to_account["balance"] = round(to_account["balance"] + amount, 2)

    add_transaction(
        from_account,
        "transfer_out",
        amount,
        f"Transfer to {to_acc_no}"
    )

    add_transaction(
        to_account,
        "transfer_in",
        amount,
        f"Transfer from {from_account['acc_no']}"
    )

    save_data()


# -------------------------
# GUI Setup
# -------------------------

root = tk.Tk()
root.title("Simple Bank GUI")
root.geometry("800x620")

main_frame = ttk.Frame(root, padding=20)
main_frame.pack(fill="both", expand=True)


def clear_frame():
    for widget in main_frame.winfo_children():
        widget.destroy()


# -------------------------
# Screens
# -------------------------

def show_main_menu():
    clear_frame()

    ttk.Label(
        main_frame,
        text="Simple Bank GUI",
        font=("Segoe UI", 20, "bold")
    ).pack(pady=25)

    ttk.Button(
        main_frame,
        text="Create Account",
        command=show_create_account
    ).pack(fill="x", pady=6)

    ttk.Button(
        main_frame,
        text="Login",
        command=show_login
    ).pack(fill="x", pady=6)

    ttk.Button(
        main_frame,
        text="Admin: List Accounts",
        command=admin_list
    ).pack(fill="x", pady=6)

    ttk.Button(
        main_frame,
        text="Exit",
        command=root.destroy
    ).pack(fill="x", pady=6)


def show_create_account():
    clear_frame()

    ttk.Label(
        main_frame,
        text="Create Account",
        font=("Segoe UI", 16, "bold")
    ).pack(pady=10)

    form = ttk.Frame(main_frame)
    form.pack(pady=10)

    ttk.Label(form, text="Full Name:").grid(row=0, column=0, sticky="e", pady=5, padx=5)
    name_entry = ttk.Entry(form, width=35)
    name_entry.grid(row=0, column=1, pady=5, padx=5)

    ttk.Label(form, text="Email:").grid(row=1, column=0, sticky="e", pady=5, padx=5)
    email_entry = ttk.Entry(form, width=35)
    email_entry.grid(row=1, column=1, pady=5, padx=5)

    ttk.Label(form, text="PIN:").grid(row=2, column=0, sticky="e", pady=5, padx=5)
    pin_entry = ttk.Entry(form, show="*", width=35)
    pin_entry.grid(row=2, column=1, pady=5, padx=5)

    ttk.Label(form, text="Confirm PIN:").grid(row=3, column=0, sticky="e", pady=5, padx=5)
    confirm_pin_entry = ttk.Entry(form, show="*", width=35)
    confirm_pin_entry.grid(row=3, column=1, pady=5, padx=5)

    def submit():
        name = name_entry.get().strip()
        email = email_entry.get().strip()
        pin = pin_entry.get()
        confirm_pin = confirm_pin_entry.get()

        if not name or not email:
            messagebox.showwarning("Missing Info", "Name and email cannot be empty.")
            return

        if pin != confirm_pin:
            messagebox.showerror("Error", "PINs do not match.")
            return

        if len(pin) < MIN_PIN_LENGTH:
            messagebox.showerror(
                "Error",
                f"PIN must be at least {MIN_PIN_LENGTH} characters."
            )
            return

        try:
            acc_no = create_account(name, email, pin)
            messagebox.showinfo(
                "Success",
                f"Account created successfully!\n\nAccount Number: {acc_no}"
            )
            show_main_menu()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    ttk.Button(
        form,
        text="Create Account",
        command=submit
    ).grid(row=4, column=0, columnspan=2, pady=15)

    ttk.Button(
        main_frame,
        text="Back",
        command=show_main_menu
    ).pack(pady=10)


def show_login():
    clear_frame()

    ttk.Label(
        main_frame,
        text="Login",
        font=("Segoe UI", 16, "bold")
    ).pack(pady=10)

    form = ttk.Frame(main_frame)
    form.pack(pady=10)

    ttk.Label(form, text="Account Number:").grid(row=0, column=0, sticky="e", pady=5, padx=5)
    acc_entry = ttk.Entry(form, width=35)
    acc_entry.grid(row=0, column=1, pady=5, padx=5)

    ttk.Label(form, text="PIN:").grid(row=1, column=0, sticky="e", pady=5, padx=5)
    pin_entry = ttk.Entry(form, show="*", width=35)
    pin_entry.grid(row=1, column=1, pady=5, padx=5)

    def submit():
        try:
            acc_no = int(acc_entry.get().strip())
            pin = pin_entry.get()

            account = authenticate(acc_no, pin)
            show_dashboard(account)

        except ValueError as e:
            messagebox.showerror("Login Failed", str(e))

    ttk.Button(
        form,
        text="Login",
        command=submit
    ).grid(row=2, column=0, columnspan=2, pady=15)

    ttk.Button(
        main_frame,
        text="Back",
        command=show_main_menu
    ).pack(pady=10)


def show_dashboard(account):
    clear_frame()

    top_frame = ttk.Frame(main_frame)
    top_frame.pack(fill="x")

    ttk.Label(
        top_frame,
        text=f"Welcome, {account['name']}",
        font=("Segoe UI", 14, "bold")
    ).pack(side="left")

    ttk.Button(
        top_frame,
        text="Logout",
        command=show_main_menu
    ).pack(side="right")

    ttk.Label(
        main_frame,
        text=f"Account Number: {account['acc_no']}"
    ).pack(anchor="w", pady=(10, 0))

    balance_label = ttk.Label(
        main_frame,
        text=f"Balance: {account['balance']:.2f}",
        font=("Segoe UI", 12, "bold")
    )
    balance_label.pack(anchor="w", pady=5)

    action_frame = ttk.LabelFrame(main_frame, text="Actions", padding=10)
    action_frame.pack(fill="x", pady=10)

    ttk.Label(action_frame, text="Amount:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
    amount_entry = ttk.Entry(action_frame, width=18)
    amount_entry.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(action_frame, text="Transfer To Account:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
    dest_entry = ttk.Entry(action_frame, width=18)
    dest_entry.grid(row=1, column=1, padx=5, pady=5)

    history_text = tk.Text(main_frame, height=14, width=90)
    history_text.pack(fill="both", expand=True, pady=10)

    def update_history():
        history_text.delete("1.0", tk.END)

        transactions = account["transactions"][-50:]

        for t in reversed(transactions):
            line = (
                f"{t['time']} | "
                f"{t['type']:<15} | "
                f"Amount: {t['amount']:>10.2f} | "
                f"Balance After: {t['balance_after']:>10.2f} | "
                f"{t['note']}\n"
            )
            history_text.insert(tk.END, line)

    def refresh():
        balance_label.config(text=f"Balance: {account['balance']:.2f}")
        update_history()

    def do_deposit():
        try:
            amount = float(amount_entry.get())
            deposit(account, amount)
            messagebox.showinfo("Success", "Deposit successful.")
            amount_entry.delete(0, tk.END)
            refresh()
        except Exception as e:
            messagebox.showerror("Failed", str(e))

    def do_withdraw():
        try:
            amount = float(amount_entry.get())
            withdraw(account, amount)
            messagebox.showinfo("Success", "Withdraw successful.")
            amount_entry.delete(0, tk.END)
            refresh()
        except Exception as e:
            messagebox.showerror("Failed", str(e))

    def do_transfer():
        try:
            to_acc_no = int(dest_entry.get().strip())
            amount = float(amount_entry.get())

            transfer(account, to_acc_no, amount)

            messagebox.showinfo(
                "Success",
                f"Transferred {amount:.2f} to account {to_acc_no}."
            )

            amount_entry.delete(0, tk.END)
            dest_entry.delete(0, tk.END)
            refresh()

        except Exception as e:
            messagebox.showerror("Failed", str(e))

    ttk.Button(
        action_frame,
        text="Deposit",
        command=do_deposit
    ).grid(row=0, column=2, padx=5, pady=5)

    ttk.Button(
        action_frame,
        text="Withdraw",
        command=do_withdraw
    ).grid(row=0, column=3, padx=5, pady=5)

    ttk.Button(
        action_frame,
        text="Transfer",
        command=do_transfer
    ).grid(row=1, column=2, columnspan=2, padx=5, pady=5)

    refresh()


def admin_list():
    password = simpledialog.askstring(
        "Admin Login",
        "Enter admin password:",
        show="*",
        parent=root
    )

    if password is None:
        return

    if password != "admin":
        messagebox.showerror("Error", "Wrong admin password.")
        return

    show_admin_screen()


def show_admin_screen():
    clear_frame()

    ttk.Label(
        main_frame,
        text="All Accounts",
        font=("Segoe UI", 16, "bold")
    ).pack(pady=10)

    text = tk.Text(main_frame, height=18, width=90)
    text.pack(fill="both", expand=True)

    sorted_accounts = sorted(accounts.values(), key=lambda a: a["acc_no"])

    for acc in sorted_accounts:
        line = (
            f"Account: {acc['acc_no']} | "
            f"Name: {acc['name']} | "
            f"Email: {acc['email']} | "
            f"Balance: {acc['balance']:.2f} | "
            f"Transactions: {len(acc['transactions'])}\n"
        )
        text.insert(tk.END, line)

    text.config(state="disabled")

    ttk.Button(
        main_frame,
        text="Back",
        command=show_main_menu
    ).pack(pady=10)


# -------------------------
# Start app
# -------------------------

load_data()
show_main_menu()
root.mainloop()