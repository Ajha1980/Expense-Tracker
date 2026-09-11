import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import csv
from datetime import datetime, date

DB_NAME = "expenses.db"

BG = "#121212"
CARD = "#1C1C1C"
CARD_LIGHT = "#252525"
CARD_HOVER = "#2D2D2D"
BORDER = "#303030"

TEXT = "#F5F5F5"
MUTED = "#999999"

GOLD = "#D9A441"
GOLD_HOVER = "#E8B653"

GREEN = "#63B875"
RED = "#D96555"
BLUE = "#6FA3C8"

FONT = "Tahoma"
TITLE_FONT = "Tahoma"

CATEGORIES = [
    "Food",
    "Travel",
    "Shopping",
    "Education",
    "Bills",
    "Health",
    "Entertainment",
    "Salary",
    "Freelance",
    "Other"
]

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    type TEXT NOT NULL,
    category TEXT NOT NULL,
    amount REAL NOT NULL,
    note TEXT
)
""")

conn.commit()

root = tk.Tk()
root.title("Ledger - Expense Tracker")
root.geometry("1280x800")
root.minsize(1150, 720)
root.configure(bg=BG)

style = ttk.Style(root)
style.theme_use("clam")

style.configure(
    "Treeview",
    background="#242424",
    foreground="#E8E8E8",
    fieldbackground="#242424",
    rowheight=36,
    borderwidth=0,
    relief="flat",
    font=(FONT, 10)
)

style.configure(
    "Treeview.Heading",
    background="#303030",
    foreground="#F2F2F2",
    font=(FONT, 9, "bold"),
    relief="flat",
    borderwidth=0
)

style.map(
    "Treeview",
    background=[
        ("selected", "#51472F")
    ],
    foreground=[
        ("selected", "#FFFFFF")
    ]
)

style.configure(
    "TCombobox",
    fieldbackground=CARD_LIGHT,
    background=CARD_LIGHT,
    foreground=TEXT,
    arrowcolor=GOLD,
    borderwidth=0,
    relief="flat",
    padding=7,
    font=(FONT, 10)
)

style.map(
    "TCombobox",
    fieldbackground=[
        ("readonly", CARD_LIGHT),
        ("focus", CARD_LIGHT)
    ],
    foreground=[
        ("readonly", TEXT),
        ("focus", TEXT)
    ]
)

style.configure(
    "Vertical.TScrollbar",
    background=CARD_LIGHT,
    troughcolor=CARD,
    borderwidth=0,
    arrowcolor=MUTED
)


def money(amount):
    return f"₹{amount:,.2f}"


def get_totals():
    cursor.execute("""
        SELECT
            COALESCE(
                SUM(CASE WHEN type = 'Income' THEN amount ELSE 0 END),
                0
            ),
            COALESCE(
                SUM(CASE WHEN type = 'Expense' THEN amount ELSE 0 END),
                0
            )
        FROM transactions
    """)

    return cursor.fetchone()


def get_monthly_expense():
    current_month = datetime.now().strftime("%Y-%m")

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE type = 'Expense'
        AND date LIKE ?
    """, (current_month + "%",))

    return cursor.fetchone()[0]


def create_entry(parent):
    return tk.Entry(
        parent,
        bg=CARD_LIGHT,
        fg=TEXT,
        insertbackground=TEXT,
        selectbackground="#5A4B2A",
        selectforeground=TEXT,
        relief="flat",
        bd=0,
        font=(FONT, 10)
    )


def refresh():
    income, expenses = get_totals()
    balance = income - expenses
    monthly = get_monthly_expense()

    balance_value.config(
        text=money(balance),
        fg=GREEN if balance >= 0 else RED
    )

    income_value.config(
        text=money(income)
    )

    expense_value.config(
        text=money(expenses)
    )

    monthly_value.config(
        text=money(monthly)
    )

    load_transactions()
    update_chart()


def load_transactions(search=""):
    for item in transaction_tree.get_children():
        transaction_tree.delete(item)

    cursor.execute("""
        SELECT id, date, type, category, amount, note
        FROM transactions
        ORDER BY date DESC, id DESC
    """)

    rows = cursor.fetchall()
    search = search.lower().strip()

    for row in rows:
        transaction_id = row[0]
        transaction_date = row[1]
        transaction_type = row[2]
        category = row[3]
        amount = row[4]
        note = row[5] or ""

        searchable = (
            f"{transaction_date} "
            f"{transaction_type} "
            f"{category} "
            f"{note}"
        ).lower()

        if search and search not in searchable:
            continue

        transaction_tree.insert(
            "",
            tk.END,
            iid=str(transaction_id),
            values=(
                transaction_date,
                transaction_type,
                category,
                money(amount),
                note
            )
        )


def add_transaction():
    transaction_date = date_entry.get().strip()
    transaction_type = type_var.get()
    category = category_var.get()
    amount_text = amount_entry.get().strip()
    note = note_entry.get().strip()

    try:
        datetime.strptime(
            transaction_date,
            "%Y-%m-%d"
        )
    except ValueError:
        messagebox.showerror(
            "Invalid Date",
            "Enter the date in YYYY-MM-DD format."
        )
        return

    try:
        amount = float(amount_text)

        if amount <= 0:
            raise ValueError

    except ValueError:
        messagebox.showerror(
            "Invalid Amount",
            "Enter a valid amount greater than zero."
        )
        return

    cursor.execute("""
        INSERT INTO transactions
        (date, type, category, amount, note)
        VALUES (?, ?, ?, ?, ?)
    """, (
        transaction_date,
        transaction_type,
        category,
        amount,
        note
    ))

    conn.commit()

    amount_entry.delete(0, tk.END)
    note_entry.delete(0, tk.END)

    date_entry.delete(0, tk.END)
    date_entry.insert(
        0,
        date.today().isoformat()
    )

    type_var.set("Expense")
    category_var.set("Food")

    refresh()


def search_transactions(*args):
    load_transactions(search_var.get())


def delete_transaction():
    selected = transaction_tree.selection()

    if not selected:
        messagebox.showinfo(
            "Select Transaction",
            "Please select a transaction first."
        )
        return

    transaction_id = int(selected[0])

    answer = messagebox.askyesno(
        "Delete Transaction",
        "Are you sure you want to delete this transaction?"
    )

    if not answer:
        return

    cursor.execute(
        "DELETE FROM transactions WHERE id = ?",
        (transaction_id,)
    )

    conn.commit()

    refresh()


def edit_transaction():
    selected = transaction_tree.selection()

    if not selected:
        messagebox.showinfo(
            "Select Transaction",
            "Please select a transaction first."
        )
        return

    transaction_id = int(selected[0])

    cursor.execute("""
        SELECT date, type, category, amount, note
        FROM transactions
        WHERE id = ?
    """, (transaction_id,))

    row = cursor.fetchone()

    if not row:
        return

    window = tk.Toplevel(root)
    window.title("Edit Transaction")
    window.geometry("440x520")
    window.configure(bg=CARD)
    window.resizable(False, False)

    tk.Label(
        window,
        text="EDIT TRANSACTION",
        bg=CARD,
        fg=TEXT,
        font=(FONT, 13, "bold")
    ).pack(
        anchor="w",
        padx=30,
        pady=(25, 22)
    )

    tk.Label(
        window,
        text="DATE",
        bg=CARD,
        fg=MUTED,
        font=(FONT, 9)
    ).pack(
        anchor="w",
        padx=30
    )

    edit_date = create_entry(window)
    edit_date.insert(0, row[0])
    edit_date.pack(
        fill="x",
        padx=30,
        pady=(5, 15),
        ipady=8
    )

    tk.Label(
        window,
        text="TYPE",
        bg=CARD,
        fg=MUTED,
        font=(FONT, 9)
    ).pack(
        anchor="w",
        padx=30
    )

    edit_type_var = tk.StringVar(value=row[1])

    edit_type = ttk.Combobox(
        window,
        textvariable=edit_type_var,
        values=["Expense", "Income"],
        state="readonly"
    )

    edit_type.pack(
        fill="x",
        padx=30,
        pady=(5, 15)
    )

    tk.Label(
        window,
        text="CATEGORY",
        bg=CARD,
        fg=MUTED,
        font=(FONT, 9)
    ).pack(
        anchor="w",
        padx=30
    )

    edit_category_var = tk.StringVar(value=row[2])

    edit_category = ttk.Combobox(
        window,
        textvariable=edit_category_var,
        values=CATEGORIES,
        state="readonly"
    )

    edit_category.pack(
        fill="x",
        padx=30,
        pady=(5, 15)
    )

    tk.Label(
        window,
        text="AMOUNT",
        bg=CARD,
        fg=MUTED,
        font=(FONT, 9)
    ).pack(
        anchor="w",
        padx=30
    )

    edit_amount = create_entry(window)
    edit_amount.insert(0, str(row[3]))
    edit_amount.pack(
        fill="x",
        padx=30,
        pady=(5, 15),
        ipady=8
    )

    tk.Label(
        window,
        text="NOTE",
        bg=CARD,
        fg=MUTED,
        font=(FONT, 9)
    ).pack(
        anchor="w",
        padx=30
    )

    edit_note = create_entry(window)
    edit_note.insert(0, row[4] or "")
    edit_note.pack(
        fill="x",
        padx=30,
        pady=(5, 22),
        ipady=8
    )

    def save():
        try:
            datetime.strptime(
                edit_date.get().strip(),
                "%Y-%m-%d"
            )

            amount = float(
                edit_amount.get().strip()
            )

            if amount <= 0:
                raise ValueError

        except ValueError:
            messagebox.showerror(
                "Invalid Input",
                "Check the date and amount."
            )
            return

        cursor.execute("""
            UPDATE transactions
            SET date = ?,
                type = ?,
                category = ?,
                amount = ?,
                note = ?
            WHERE id = ?
        """, (
            edit_date.get().strip(),
            edit_type_var.get(),
            edit_category_var.get(),
            amount,
            edit_note.get().strip(),
            transaction_id
        ))

        conn.commit()

        window.destroy()

        refresh()

    tk.Button(
        window,
        text="SAVE CHANGES",
        command=save,
        bg=GOLD,
        fg="#121212",
        activebackground=GOLD_HOVER,
        activeforeground="#121212",
        relief="flat",
        bd=0,
        font=(FONT, 10, "bold"),
        cursor="hand2"
    ).pack(
        fill="x",
        padx=30,
        ipady=10
    )


def export_csv():
    cursor.execute("""
        SELECT date, type, category, amount, note
        FROM transactions
        ORDER BY date DESC
    """)

    rows = cursor.fetchall()

    if not rows:
        messagebox.showinfo(
            "No Data",
            "There are no transactions to export."
        )
        return

    path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[
            ("CSV Files", "*.csv")
        ],
        initialfile="ledger_transactions.csv"
    )

    if not path:
        return

    with open(
        path,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "Date",
            "Type",
            "Category",
            "Amount",
            "Note"
        ])

        writer.writerows(rows)

    messagebox.showinfo(
        "Export Complete",
        "Transactions exported successfully."
    )


def update_chart():
    for widget in chart_container.winfo_children():
        widget.destroy()

    cursor.execute("""
        SELECT category, SUM(amount)
        FROM transactions
        WHERE type = 'Expense'
        GROUP BY category
        ORDER BY SUM(amount) DESC
        LIMIT 5
    """)

    data = cursor.fetchall()

    if not data:
        tk.Label(
            chart_container,
            text="No expense data available.",
            bg=CARD,
            fg=MUTED,
            font=(FONT, 10)
        ).pack(
            pady=25
        )

        return

    highest = max(
        amount
        for _, amount in data
    )

    for category, amount in data:

        row = tk.Frame(
            chart_container,
            bg=CARD
        )

        row.pack(
            fill="x",
            padx=20,
            pady=5
        )

        tk.Label(
            row,
            text=category,
            width=15,
            anchor="w",
            bg=CARD,
            fg=TEXT,
            font=(FONT, 9)
        ).pack(
            side="left"
        )

        background = tk.Frame(
            row,
            bg="#353535",
            height=12
        )

        background.pack(
            side="left",
            fill="x",
            expand=True,
            padx=10
        )

        width = max(
            8,
            int(260 * amount / highest)
        )

        tk.Frame(
            background,
            bg=GOLD,
            width=width,
            height=12
        ).pack(
            side="left"
        )

        tk.Label(
            row,
            text=money(amount),
            width=14,
            anchor="e",
            bg=CARD,
            fg=MUTED,
            font=(FONT, 9)
        ).pack(
            side="right"
        )


def clear_all_data():
    answer = messagebox.askyesno(
        "Clear All Data",
        "This will permanently delete every transaction.\n\nContinue?"
    )

    if not answer:
        return

    cursor.execute(
        "DELETE FROM transactions"
    )

    conn.commit()

    refresh()


def close_app():
    conn.close()
    root.destroy()


header = tk.Frame(
    root,
    bg=BG
)

header.pack(
    fill="x",
    padx=35,
    pady=(28, 20)
)

title_area = tk.Frame(
    header,
    bg=BG
)

title_area.pack(
    side="left"
)

tk.Label(
    title_area,
    text="LEDGER",
    bg=BG,
    fg=TEXT,
    font=(TITLE_FONT, 25, "bold")
).pack(
    side="left"
)

tk.Label(
    title_area,
    text="  PERSONAL EXPENSE TRACKER",
    bg=BG,
    fg=MUTED,
    font=(FONT, 9)
).pack(
    side="left",
    pady=(10, 0)
)

tk.Button(
    header,
    text="EXPORT CSV",
    command=export_csv,
    bg=CARD_LIGHT,
    fg=TEXT,
    activebackground=CARD_HOVER,
    activeforeground=TEXT,
    relief="flat",
    bd=0,
    font=(FONT, 9, "bold"),
    cursor="hand2"
).pack(
    side="right",
    ipadx=14,
    ipady=8
)


summary = tk.Frame(
    root,
    bg=BG
)

summary.pack(
    fill="x",
    padx=35,
    pady=(0, 18)
)


def summary_card(title):
    frame = tk.Frame(
        summary,
        bg=CARD,
        highlightbackground=BORDER,
        highlightthickness=1
    )

    frame.pack(
        side="left",
        fill="both",
        expand=True,
        padx=(0, 12)
    )

    tk.Label(
        frame,
        text=title.upper(),
        bg=CARD,
        fg=MUTED,
        font=(FONT, 9, "bold")
    ).pack(
        anchor="w",
        padx=20,
        pady=(17, 5)
    )

    value = tk.Label(
        frame,
        text="₹0.00",
        bg=CARD,
        fg=TEXT,
        font=(TITLE_FONT, 18, "bold")
    )

    value.pack(
        anchor="w",
        padx=20,
        pady=(0, 18)
    )

    return value


balance_value = summary_card("Balance")
income_value = summary_card("Income")
expense_value = summary_card("Total Expenses")
monthly_value = summary_card("This Month")


main_area = tk.Frame(
    root,
    bg=BG
)

main_area.pack(
    fill="both",
    expand=True,
    padx=35,
    pady=(0, 18)
)


left_panel = tk.Frame(
    main_area,
    bg=CARD,
    width=320,
    highlightbackground=BORDER,
    highlightthickness=1
)

left_panel.pack(
    side="left",
    fill="y",
    padx=(0, 15)
)

left_panel.pack_propagate(False)

tk.Label(
    left_panel,
    text="NEW TRANSACTION",
    bg=CARD,
    fg=TEXT,
    font=(FONT, 12, "bold")
).pack(
    anchor="w",
    padx=23,
    pady=(23, 20)
)


def field_label(text):
    tk.Label(
        left_panel,
        text=text,
        bg=CARD,
        fg=MUTED,
        font=(FONT, 9)
    ).pack(
        anchor="w",
        padx=23,
        pady=(8, 5)
    )


field_label("DATE")

date_entry = create_entry(left_panel)

date_entry.insert(
    0,
    date.today().isoformat()
)

date_entry.pack(
    fill="x",
    padx=23,
    ipady=8
)


field_label("TYPE")

type_var = tk.StringVar(
    value="Expense"
)

type_box = ttk.Combobox(
    left_panel,
    textvariable=type_var,
    values=["Expense", "Income"],
    state="readonly"
)

type_box.pack(
    fill="x",
    padx=23
)


field_label("CATEGORY")

category_var = tk.StringVar(
    value="Food"
)

category_box = ttk.Combobox(
    left_panel,
    textvariable=category_var,
    values=CATEGORIES,
    state="readonly"
)

category_box.pack(
    fill="x",
    padx=23
)


field_label("AMOUNT")

amount_entry = create_entry(left_panel)

amount_entry.pack(
    fill="x",
    padx=23,
    ipady=8
)


field_label("NOTE")

note_entry = create_entry(left_panel)

note_entry.pack(
    fill="x",
    padx=23,
    ipady=8
)


tk.Button(
    left_panel,
    text="+  ADD TRANSACTION",
    command=add_transaction,
    bg=GOLD,
    fg="#121212",
    activebackground=GOLD_HOVER,
    activeforeground="#121212",
    relief="flat",
    bd=0,
    font=(FONT, 10, "bold"),
    cursor="hand2"
).pack(
    fill="x",
    padx=23,
    pady=25,
    ipady=10
)


right_panel = tk.Frame(
    main_area,
    bg=BG
)

right_panel.pack(
    side="left",
    fill="both",
    expand=True
)


transaction_header = tk.Frame(
    right_panel,
    bg=BG
)

transaction_header.pack(
    fill="x",
    pady=(0, 10)
)

tk.Label(
    transaction_header,
    text="TRANSACTIONS",
    bg=BG,
    fg=TEXT,
    font=(FONT, 12, "bold")
).pack(
    side="left"
)

search_var = tk.StringVar()

search_var.trace_add(
    "write",
    search_transactions
)

search_entry = create_entry(
    transaction_header
)

search_entry.config(
    width=28
)

search_entry.pack(
    side="right",
    ipady=7
)


table_frame = tk.Frame(
    right_panel,
    bg=CARD,
    highlightbackground=BORDER,
    highlightthickness=1
)

table_frame.pack(
    fill="both",
    expand=True
)

columns = (
    "date",
    "type",
    "category",
    "amount",
    "note"
)

transaction_tree = ttk.Treeview(
    table_frame,
    columns=columns,
    show="headings"
)

transaction_tree.heading(
    "date",
    text="DATE"
)

transaction_tree.heading(
    "type",
    text="TYPE"
)

transaction_tree.heading(
    "category",
    text="CATEGORY"
)

transaction_tree.heading(
    "amount",
    text="AMOUNT"
)

transaction_tree.heading(
    "note",
    text="NOTE"
)

transaction_tree.column(
    "date",
    width=110,
    anchor="w"
)

transaction_tree.column(
    "type",
    width=100,
    anchor="w"
)

transaction_tree.column(
    "category",
    width=130,
    anchor="w"
)

transaction_tree.column(
    "amount",
    width=135,
    anchor="w"
)

transaction_tree.column(
    "note",
    width=220,
    anchor="w"
)

scrollbar = ttk.Scrollbar(
    table_frame,
    orient="vertical",
    command=transaction_tree.yview,
    style="Vertical.TScrollbar"
)

transaction_tree.configure(
    yscrollcommand=scrollbar.set
)

transaction_tree.pack(
    side="left",
    fill="both",
    expand=True,
    padx=(10, 0),
    pady=10
)

scrollbar.pack(
    side="right",
    fill="y",
    pady=10
)


actions = tk.Frame(
    right_panel,
    bg=BG
)

actions.pack(
    fill="x",
    pady=(10, 0)
)

tk.Button(
    actions,
    text="EDIT",
    command=edit_transaction,
    bg=CARD_LIGHT,
    fg=TEXT,
    activebackground=CARD_HOVER,
    activeforeground=TEXT,
    relief="flat",
    bd=0,
    font=(FONT, 9, "bold"),
    cursor="hand2"
).pack(
    side="left",
    ipadx=18,
    ipady=7,
    padx=(0, 8)
)

tk.Button(
    actions,
    text="DELETE",
    command=delete_transaction,
    bg=CARD_LIGHT,
    fg=RED,
    activebackground=CARD_HOVER,
    activeforeground=RED,
    relief="flat",
    bd=0,
    font=(FONT, 9, "bold"),
    cursor="hand2"
).pack(
    side="left",
    ipadx=18,
    ipady=7
)


analytics = tk.Frame(
    root,
    bg=CARD,
    highlightbackground=BORDER,
    highlightthickness=1
)

analytics.pack(
    fill="x",
    padx=35,
    pady=(0, 25)
)

analytics_header = tk.Frame(
    analytics,
    bg=CARD
)

analytics_header.pack(
    fill="x"
)

tk.Label(
    analytics_header,
    text="SPENDING BY CATEGORY",
    bg=CARD,
    fg=TEXT,
    font=(FONT, 10, "bold")
).pack(
    side="left",
    padx=20,
    pady=(17, 5)
)

tk.Button(
    analytics_header,
    text="CLEAR ALL DATA",
    command=clear_all_data,
    bg=CARD_LIGHT,
    fg=RED,
    activebackground=CARD_HOVER,
    activeforeground=RED,
    relief="flat",
    bd=0,
    font=(FONT, 8, "bold"),
    cursor="hand2"
).pack(
    side="right",
    padx=15,
    pady=(12, 4)
)

chart_container = tk.Frame(
    analytics,
    bg=CARD
)

chart_container.pack(
    fill="x",
    pady=(0, 15)
)


root.protocol(
    "WM_DELETE_WINDOW",
    close_app
)

refresh()

root.mainloop()