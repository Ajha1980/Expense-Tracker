import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import csv
from datetime import datetime, date
from collections import defaultdict

DB_NAME = "expenses.db"

BG = "#111111"
CARD = "#1A1A1A"
CARD2 = "#202020"
INPUT = "#272727"
BORDER = "#303030"
TEXT = "#F4F4F4"
MUTED = "#999999"
GOLD = "#D9A441"
GOLD_HOVER = "#E7B653"
GREEN = "#5FBA78"
RED = "#D86655"
BLUE = "#6C9FC7"

FONT = "Candara"

CATEGORIES = [
    "Food", "Travel", "Shopping", "Education", "Bills",
    "Health", "Entertainment", "Salary", "Freelance", "Other"
]

TYPES = ["Income", "Expense"]


class ExpenseTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker")
        self.root.geometry("1280x850")
        self.root.minsize(1050, 720)
        self.root.configure(bg=BG)

        self.conn = sqlite3.connect(DB_NAME)
        self.conn.row_factory = sqlite3.Row

        self.selected_id = None

        self.setup_database()
        self.setup_style()
        self.create_variables()
        self.build_ui()
        self.refresh()

        self.root.protocol("WM_DELETE_WINDOW", self.close_app)
        self.root.bind("<Control-f>", lambda event: self.focus_search())
        self.root.bind("<Control-n>", lambda event: self.clear_form())
        self.root.bind("<Delete>", lambda event: self.delete_transaction())

    def setup_database(self):
        cursor = self.conn.cursor()

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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        self.conn.commit()

    def setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background=INPUT,
            foreground=TEXT,
            fieldbackground=INPUT,
            borderwidth=0,
            rowheight=34,
            font=(FONT, 11)
        )

        style.configure(
            "Treeview.Heading",
            background=CARD2,
            foreground=TEXT,
            font=(FONT, 11, "bold"),
            padding=10
        )

        style.map(
            "Treeview",
            background=[("selected", "#3A3325")],
            foreground=[("selected", TEXT)]
        )

        style.configure(
            "TCombobox",
            fieldbackground=INPUT,
            background=INPUT,
            foreground=TEXT,
            arrowcolor=GOLD,
            bordercolor=BORDER,
            lightcolor=BORDER,
            darkcolor=BORDER,
            padding=8,
            font=(FONT, 11)
        )

        style.map(
            "TCombobox",
            fieldbackground=[("readonly", INPUT)],
            foreground=[("readonly", TEXT)]
        )

        style.configure(
            "Horizontal.TProgressbar",
            troughcolor=INPUT,
            background=GOLD,
            bordercolor=INPUT,
            lightcolor=GOLD,
            darkcolor=GOLD
        )

    def create_variables(self):
        self.date_var = tk.StringVar(value=date.today().isoformat())
        self.type_var = tk.StringVar(value="Expense")
        self.category_var = tk.StringVar(value="Food")
        self.amount_var = tk.StringVar()
        self.note_var = tk.StringVar()

        self.search_var = tk.StringVar()
        self.month_var = tk.StringVar(value="All Months")
        self.filter_type_var = tk.StringVar(value="All Types")
        self.filter_category_var = tk.StringVar(value="All Categories")

        self.income_var = tk.StringVar(value="₹0.00")
        self.expense_var = tk.StringVar(value="₹0.00")
        self.balance_var = tk.StringVar(value="₹0.00")
        self.month_expense_var = tk.StringVar(value="₹0.00")

        self.transaction_count_var = tk.StringVar(value="0")
        self.top_category_var = tk.StringVar(value="None")
        self.largest_expense_var = tk.StringVar(value="None")
        self.average_var = tk.StringVar(value="₹0.00")

        self.budget_var = tk.StringVar(value="")
        self.budget_status_var = tk.StringVar(value="No budget set")

    def button(self, parent, text, command, width=None, fg=TEXT, bg=CARD2):
        kwargs = {
            "text": text,
            "command": command,
            "bg": bg,
            "fg": fg,
            "activebackground": GOLD_HOVER,
            "activeforeground": "#111111",
            "relief": "flat",
            "bd": 0,
            "font": (FONT, 11, "bold"),
            "cursor": "hand2",
            "padx": 14,
            "pady": 9
        }

        if width:
            kwargs["width"] = width

        return tk.Button(parent, **kwargs)

    def label(self, parent, text="", size=10, bold=False, fg=TEXT, bg=None):
        if bg is None:
            bg = parent.cget("bg")

        return tk.Label(
            parent,
            text=text,
            font=(FONT, size, "bold" if bold else "normal"),
            fg=fg,
            bg=bg
        )

    def entry(self, parent, textvariable, width=20):
        return tk.Entry(
            parent,
            textvariable=textvariable,
            width=width,
            bg=INPUT,
            fg=TEXT,
            insertbackground=TEXT,
            selectbackground=GOLD,
            selectforeground="#111111",
            relief="flat",
            bd=0,
            font=(FONT, 11)
        )

    def build_ui(self):
        outer = tk.Frame(self.root, bg=BG)
        outer.pack(fill="both", expand=True)

        self.page_canvas = tk.Canvas(
            outer,
            bg=BG,
            highlightthickness=0,
            bd=0
        )

        page_scrollbar = ttk.Scrollbar(
            outer,
            orient="vertical",
            command=self.page_canvas.yview
        )

        self.page_canvas.configure(
            yscrollcommand=page_scrollbar.set
        )

        page_scrollbar.pack(side="right", fill="y")
        self.page_canvas.pack(side="left", fill="both", expand=True)

        main = tk.Frame(self.page_canvas, bg=BG)

        self.page_window = self.page_canvas.create_window(
            (0, 0),
            window=main,
            anchor="nw"
        )

        main.bind(
            "<Configure>",
            lambda event: self.page_canvas.configure(
                scrollregion=self.page_canvas.bbox("all")
            )
        )

        self.page_canvas.bind(
            "<Configure>",
            lambda event: self.page_canvas.itemconfigure(
                self.page_window,
                width=event.width
            )
        )

        self.page_canvas.bind(
            "<MouseWheel>",
            self.on_page_mousewheel
        )

        self.root.bind(
            "<MouseWheel>",
            self.on_root_mousewheel,
            add="+"
        )

        self.build_header(main)
        self.build_summary(main)

        body = tk.Frame(main, bg=BG)
        body.pack(fill="both", expand=True, padx=28, pady=(0, 18))

        self.build_form(body)
        self.build_transactions(body)

        self.build_analytics(main)

    def on_page_mousewheel(self, event):
        self.page_canvas.yview_scroll(
            int(-1 * (event.delta / 120)),
            "units"
        )

    def on_root_mousewheel(self, event):
        widget = event.widget

        current = widget

        while current is not None:
            if current == self.transaction_tree:
                return

            try:
                current = current.master
            except AttributeError:
                break

        self.page_canvas.yview_scroll(
            int(-1 * (event.delta / 120)),
            "units"
        )

    def build_header(self, parent):
        header = tk.Frame(parent, bg=BG)
        header.pack(fill="x", padx=28, pady=(22, 14))

        left = tk.Frame(header, bg=BG)
        left.pack(side="left")

        self.label(
            left,
            "EXPENSE TRACKER",
            25,
            True,
            GOLD
        ).pack(anchor="w")

        self.label(
            left,
            "Personal finance dashboard",
            10,
            False,
            MUTED
        ).pack(anchor="w", pady=(2, 0))

        right = tk.Frame(header, bg=BG)
        right.pack(side="right")

        self.button(
            right,
            "IMPORT",
            self.import_csv,
            fg=TEXT
        ).pack(side="left", padx=5)

        self.button(
            right,
            "EXPORT",
            self.export_csv,
            fg=TEXT
        ).pack(side="left", padx=5)

    def build_summary(self, parent):
        frame = tk.Frame(parent, bg=BG)
        frame.pack(fill="x", padx=28, pady=(0, 18))

        cards = [
            ("TOTAL INCOME", self.income_var, GREEN),
            ("TOTAL EXPENSES", self.expense_var, RED),
            ("CURRENT BALANCE", self.balance_var, GOLD),
            ("THIS MONTH", self.month_expense_var, BLUE)
        ]

        for title, variable, accent in cards:
            card = tk.Frame(
                frame,
                bg=CARD,
                highlightbackground=BORDER,
                highlightthickness=1
            )
            card.pack(side="left", fill="x", expand=True, padx=5)

            self.label(
                card,
                title,
                9,
                True,
                MUTED,
                CARD
            ).pack(anchor="w", padx=18, pady=(15, 4))

            self.label(
                card,
                variable.get(),
                20,
                True,
                accent,
                CARD
            ).pack(anchor="w", padx=18, pady=(0, 15))

            self.bind_variable_label(card, variable, accent)

    def bind_variable_label(self, parent, variable, color):
        label = tk.Label(
            parent,
            textvariable=variable,
            font=(FONT, 20, "bold"),
            fg=color,
            bg=CARD
        )
        label.place(x=18, y=31)

    def build_form(self, parent):
        form = tk.Frame(
            parent,
            bg=CARD,
            width=320,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        form.pack(side="left", fill="y", padx=(0, 10))
        form.pack_propagate(False)

        self.label(
            form,
            "ADD TRANSACTION",
            16,
            True,
            TEXT,
            CARD
        ).pack(anchor="w", padx=20, pady=(20, 22))

        self.label(form, "DATE", 9, True, MUTED, CARD).pack(anchor="w", padx=20)
        self.date_entry = self.entry(form, self.date_var, 24)
        self.date_entry.pack(fill="x", padx=20, pady=(5, 14))

        self.label(form, "TYPE", 9, True, MUTED, CARD).pack(anchor="w", padx=20)
        self.type_combo = ttk.Combobox(
            form,
            textvariable=self.type_var,
            values=TYPES,
            state="readonly"
        )
        self.type_combo.pack(fill="x", padx=20, pady=(5, 14))
        self.type_combo.bind("<<ComboboxSelected>>", self.category_for_type)

        self.label(form, "CATEGORY", 9, True, MUTED, CARD).pack(anchor="w", padx=20)
        self.category_combo = ttk.Combobox(
            form,
            textvariable=self.category_var,
            values=CATEGORIES,
            state="readonly"
        )
        self.category_combo.pack(fill="x", padx=20, pady=(5, 14))

        self.label(form, "AMOUNT", 9, True, MUTED, CARD).pack(anchor="w", padx=20)
        self.amount_entry = self.entry(form, self.amount_var, 24)
        self.amount_entry.pack(fill="x", padx=20, pady=(5, 14))

        self.label(form, "NOTE", 9, True, MUTED, CARD).pack(anchor="w", padx=20)
        self.note_entry = self.entry(form, self.note_var, 24)
        self.note_entry.pack(fill="x", padx=20, pady=(5, 18))

        actions = tk.Frame(form, bg=CARD)
        actions.pack(fill="x", padx=20)

        self.button(
            actions,
            "ADD",
            self.add_transaction,
            fg="#111111",
            bg=GOLD
        ).pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.button(
            actions,
            "UPDATE",
            self.update_selected,
            fg=TEXT
        ).pack(side="left", fill="x", expand=True, padx=(5, 0))

        self.button(
            form,
            "CLEAR FORM",
            self.clear_form,
            fg=MUTED,
            bg=CARD
        ).pack(anchor="w", padx=8, pady=(10, 0))

        budget_frame = tk.Frame(form, bg=CARD)
        budget_frame.pack(fill="x", padx=20, pady=(22, 0))

        self.label(
            budget_frame,
            "MONTHLY BUDGET",
            9,
            True,
            MUTED,
            CARD
        ).pack(anchor="w")

        budget_row = tk.Frame(budget_frame, bg=CARD)
        budget_row.pack(fill="x", pady=(6, 5))

        self.budget_entry = self.entry(
            budget_row,
            self.budget_var,
            14
        )
        self.budget_entry.pack(side="left", fill="x", expand=True)

        self.button(
            budget_row,
            "SAVE",
            self.save_budget,
            fg="#111111",
            bg=GOLD
        ).pack(side="left", padx=(6, 0))

        self.budget_progress = ttk.Progressbar(
            budget_frame,
            style="Horizontal.TProgressbar",
            maximum=100
        )
        self.budget_progress.pack(fill="x", pady=(5, 3))

        self.label(
            budget_frame,
            self.budget_status_var,
            9,
            False,
            MUTED,
            CARD
        ).pack(anchor="w")

    def build_transactions(self, parent):
        container = tk.Frame(
            parent,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        container.pack(side="left", fill="both", expand=True)

        top = tk.Frame(container, bg=CARD)
        top.pack(fill="x", padx=14, pady=14)

        self.label(
            top,
            "TRANSACTIONS",
            16,
            True,
            TEXT,
            CARD
        ).pack(side="left")

        self.button(
            top,
            "DELETE",
            self.delete_transaction,
            fg=RED,
            bg=CARD
        ).pack(side="right")

        self.button(
            top,
            "EDIT",
            self.edit_transaction,
            fg=GOLD,
            bg=CARD
        ).pack(side="right", padx=4)

        filters = tk.Frame(container, bg=CARD)
        filters.pack(fill="x", padx=14, pady=(0, 10))

        self.search_entry = self.entry(
            filters,
            self.search_var,
            24
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.insert(0, "")
        self.search_entry.bind("<KeyRelease>", lambda event: self.refresh())

        self.month_combo = ttk.Combobox(
            filters,
            textvariable=self.month_var,
            state="readonly",
            width=14
        )
        self.month_combo.pack(side="left", padx=(8, 5))
        self.month_combo.bind("<<ComboboxSelected>>", lambda event: self.refresh())

        self.type_filter = ttk.Combobox(
            filters,
            textvariable=self.filter_type_var,
            values=["All Types"] + TYPES,
            state="readonly",
            width=13
        )
        self.type_filter.pack(side="left", padx=5)
        self.type_filter.bind("<<ComboboxSelected>>", lambda event: self.refresh())

        self.category_filter = ttk.Combobox(
            filters,
            textvariable=self.filter_category_var,
            values=["All Categories"] + CATEGORIES,
            state="readonly",
            width=17
        )
        self.category_filter.pack(side="left", padx=(5, 0))
        self.category_filter.bind("<<ComboboxSelected>>", lambda event: self.refresh())

        table_frame = tk.Frame(container, bg=CARD)
        table_frame.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        columns = ("id", "date", "type", "category", "amount", "note")

        self.transaction_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        headings = {
            "id": "ID",
            "date": "DATE",
            "type": "TYPE",
            "category": "CATEGORY",
            "amount": "AMOUNT",
            "note": "NOTE"
        }

        widths = {
            "id": 0,
            "date": 110,
            "type": 90,
            "category": 130,
            "amount": 120,
            "note": 220
        }

        for column in columns:
            self.transaction_tree.heading(
                column,
                text=headings[column]
            )
            self.transaction_tree.column(
                column,
                width=widths[column],
                anchor="w"
            )

        self.transaction_tree.column("id", width=0, minwidth=0, stretch=False)
        self.transaction_tree.column("amount", anchor="e")

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.transaction_tree.yview
        )
        self.transaction_tree.configure(yscrollcommand=scrollbar.set)

        self.transaction_tree.pack(
            side="left",
            fill="both",
            expand=True
        )
        scrollbar.pack(side="right", fill="y")

        self.transaction_tree.bind(
            "<Double-1>",
            lambda event: self.edit_transaction()
        )

    def build_analytics(self, parent):
        analytics = tk.Frame(
            parent,
            bg=BG,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        analytics.pack(fill="x", padx=28, pady=(0, 22))

        self.label(
            analytics,
            "ANALYTICS",
            14,
            True,
            TEXT,
            BG
        ).pack(anchor="w", padx=18, pady=(14, 10))

        content = tk.Frame(analytics, bg=BG)
        content.pack(fill="x", padx=18, pady=(0, 18))

        self.chart_canvas = tk.Canvas(
            content,
            width=280,
            height=190,
            bg=BG,
            highlightthickness=0
        )
        self.chart_canvas.pack(side="left")

        stats = tk.Frame(content, bg=BG)
        stats.pack(side="left", fill="x", expand=True, padx=(15, 0))

        self.analytics_card(
            stats,
            "TRANSACTIONS",
            self.transaction_count_var
        ).pack(side="left", fill="both", expand=True, padx=5)

        self.analytics_card(
            stats,
            "TOP CATEGORY",
            self.top_category_var
        ).pack(side="left", fill="both", expand=True, padx=5)

        self.analytics_card(
            stats,
            "LARGEST EXPENSE",
            self.largest_expense_var
        ).pack(side="left", fill="both", expand=True, padx=5)

        self.analytics_card(
            stats,
            "AVERAGE EXPENSE",
            self.average_var
        ).pack(side="left", fill="both", expand=True, padx=5)

        self.button(
            analytics,
            "CLEAR ALL DATA",
            self.clear_all_data,
            fg=RED,
            bg=CARD
        ).pack(anchor="e", padx=18, pady=(0, 14))

    def analytics_card(self, parent, title, variable):
        card = tk.Frame(
            parent,
            bg=CARD,
            height=70,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        card.pack_propagate(False)

        self.label(
            card,
            title,
            8,
            True,
            MUTED,
            CARD
        ).pack(anchor="w", padx=12, pady=(10, 2))

        tk.Label(
            card,
            textvariable=variable,
            font=(FONT, 13, "bold"),
            fg=TEXT,
            bg=CARD
        ).place(x=12, y=29)

        return card

    def category_for_type(self, event=None):
        if self.type_var.get() == "Income":
            income_categories = ["Salary", "Freelance", "Other"]
            self.category_combo["values"] = income_categories
            if self.category_var.get() not in income_categories:
                self.category_var.set("Salary")
        else:
            expense_categories = [
                "Food", "Travel", "Shopping", "Education",
                "Bills", "Health", "Entertainment", "Other"
            ]
            self.category_combo["values"] = expense_categories
            if self.category_var.get() not in expense_categories:
                self.category_var.set("Food")

    def validate_transaction(self):
        transaction_date = self.date_var.get().strip()
        transaction_type = self.type_var.get().strip()
        category = self.category_var.get().strip()
        amount_text = self.amount_var.get().strip()

        try:
            datetime.strptime(transaction_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror(
                "Invalid Date",
                "Date must be in YYYY-MM-DD format."
            )
            return None

        if transaction_type not in TYPES:
            messagebox.showerror("Invalid Type", "Select a valid transaction type.")
            return None

        if not category:
            messagebox.showerror("Invalid Category", "Select a category.")
            return None

        try:
            amount = float(amount_text)
        except ValueError:
            messagebox.showerror("Invalid Amount", "Enter a valid amount.")
            return None

        if amount <= 0:
            messagebox.showerror("Invalid Amount", "Amount must be greater than zero.")
            return None

        return (
            transaction_date,
            transaction_type,
            category,
            amount,
            self.note_var.get().strip()
        )

    def add_transaction(self):
        data = self.validate_transaction()

        if not data:
            return

        self.conn.execute(
            """
            INSERT INTO transactions
            (date, type, category, amount, note)
            VALUES (?, ?, ?, ?, ?)
            """,
            data
        )
        self.conn.commit()

        self.clear_form()
        self.refresh()

    def edit_transaction(self):
        selected = self.transaction_tree.selection()

        if not selected:
            messagebox.showinfo(
                "Select Transaction",
                "Select a transaction first."
            )
            return

        item = self.transaction_tree.item(selected[0])
        transaction_id = item["values"][0]

        row = self.conn.execute(
            "SELECT * FROM transactions WHERE id = ?",
            (transaction_id,)
        ).fetchone()

        if not row:
            return

        self.selected_id = row["id"]
        self.date_var.set(row["date"])
        self.type_var.set(row["type"])
        self.category_for_type()
        self.category_var.set(row["category"])
        self.amount_var.set(str(row["amount"]))
        self.note_var.set(row["note"] or "")

        self.amount_entry.focus_set()

    def update_selected(self):
        if self.selected_id is None:
            return

        data = self.validate_transaction()

        if not data:
            return

        self.conn.execute(
            """
            UPDATE transactions
            SET date = ?, type = ?, category = ?, amount = ?, note = ?
            WHERE id = ?
            """,
            (*data, self.selected_id)
        )
        self.conn.commit()

        self.clear_form()
        self.refresh()

    def delete_transaction(self):
        selected = self.transaction_tree.selection()

        if not selected:
            messagebox.showinfo(
                "Select Transaction",
                "Select a transaction first."
            )
            return

        item = self.transaction_tree.item(selected[0])
        transaction_id = item["values"][0]

        confirm = messagebox.askyesno(
            "Delete Transaction",
            "Are you sure you want to delete this transaction?"
        )

        if not confirm:
            return

        self.conn.execute(
            "DELETE FROM transactions WHERE id = ?",
            (transaction_id,)
        )
        self.conn.commit()

        self.clear_form()
        self.refresh()

    def clear_form(self):
        self.selected_id = None
        self.date_var.set(date.today().isoformat())
        self.type_var.set("Expense")
        self.category_for_type()
        self.category_var.set("Food")
        self.amount_var.set("")
        self.note_var.set("")

    def get_months(self):
        rows = self.conn.execute(
            """
            SELECT DISTINCT substr(date, 1, 7) AS month
            FROM transactions
            ORDER BY month DESC
            """
        ).fetchall()

        return ["All Months"] + [row["month"] for row in rows]

    def get_where_clause(self, include_search=True):
        conditions = []
        params = []

        month = self.month_var.get()

        if month and month != "All Months":
            conditions.append("substr(date, 1, 7) = ?")
            params.append(month)

        transaction_type = self.filter_type_var.get()

        if transaction_type and transaction_type != "All Types":
            conditions.append("type = ?")
            params.append(transaction_type)

        category = self.filter_category_var.get()

        if category and category != "All Categories":
            conditions.append("category = ?")
            params.append(category)

        if include_search:
            search = self.search_var.get().strip()

            if search:
                conditions.append(
                    "(date LIKE ? OR type LIKE ? OR category LIKE ? OR note LIKE ?)"
                )
                pattern = f"%{search}%"
                params.extend([pattern, pattern, pattern, pattern])

        if conditions:
            return " WHERE " + " AND ".join(conditions), params

        return "", params

    def refresh(self):
        self.update_months()
        self.load_transactions()
        self.update_summary()
        self.update_budget_display()
        self.update_analytics()
        self.update_chart()

    def update_months(self):
        months = self.get_months()
        current = self.month_var.get()

        self.month_combo["values"] = months

        if current in months:
            self.month_var.set(current)
        else:
            self.month_var.set("All Months")

    def load_transactions(self):
        for item in self.transaction_tree.get_children():
            self.transaction_tree.delete(item)

        where, params = self.get_where_clause()

        rows = self.conn.execute(
            f"""
            SELECT id, date, type, category, amount, note
            FROM transactions
            {where}
            ORDER BY date DESC, id DESC
            """,
            params
        ).fetchall()

        for row in rows:
            amount = row["amount"]

            self.transaction_tree.insert(
                "",
                "end",
                values=(
                    row["id"],
                    row["date"],
                    row["type"],
                    row["category"],
                    f"₹{amount:,.2f}",
                    row["note"] or ""
                )
            )

        

    def get_totals(self, filtered=True):
        if filtered:
            where, params = self.get_where_clause()
        else:
            where, params = "", []

        rows = self.conn.execute(
            f"""
            SELECT type, COALESCE(SUM(amount), 0) AS total
            FROM transactions
            {where}
            GROUP BY type
            """,
            params
        ).fetchall()

        income = 0
        expense = 0

        for row in rows:
            if row["type"] == "Income":
                income = row["total"]
            elif row["type"] == "Expense":
                expense = row["total"]

        return income, expense

    def get_month_expense(self):
        month = self.month_var.get()

        if month == "All Months":
            month = date.today().strftime("%Y-%m")

        row = self.conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM transactions
            WHERE type = 'Expense'
            AND substr(date, 1, 7) = ?
            """,
            (month,)
        ).fetchone()

        return row["total"]

    def update_summary(self):
        income, expense = self.get_totals(filtered=False)
        month_expense = self.get_month_expense()

        self.income_var.set(f"₹{income:,.2f}")
        self.expense_var.set(f"₹{expense:,.2f}")
        self.balance_var.set(f"₹{income - expense:,.2f}")
        self.month_expense_var.set(f"₹{month_expense:,.2f}")

    def get_budget(self):
        row = self.conn.execute(
            "SELECT value FROM settings WHERE key = 'monthly_budget'"
        ).fetchone()

        if not row:
            return 0

        try:
            return float(row["value"])
        except ValueError:
            return 0

    def save_budget(self):
        value = self.budget_var.get().strip()

        if not value:
            self.conn.execute(
                "DELETE FROM settings WHERE key = 'monthly_budget'"
            )
            self.conn.commit()
            self.update_budget_display()
            return

        try:
            budget = float(value)
        except ValueError:
            messagebox.showerror(
                "Invalid Budget",
                "Enter a valid budget amount."
            )
            return

        if budget <= 0:
            messagebox.showerror(
                "Invalid Budget",
                "Budget must be greater than zero."
            )
            return

        self.conn.execute(
            """
            INSERT INTO settings(key, value)
            VALUES('monthly_budget', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (str(budget),)
        )
        self.conn.commit()

        self.update_budget_display()

    def update_budget_display(self):
        budget = self.get_budget()
        expense = self.get_month_expense()

        if budget <= 0:
            self.budget_progress["value"] = 0
            self.budget_status_var.set("No budget set")
            return

        percentage = min((expense / budget) * 100, 100)
        remaining = budget - expense

        self.budget_progress["value"] = percentage

        if remaining >= 0:
            self.budget_status_var.set(
                f"₹{remaining:,.2f} remaining"
            )
        else:
            self.budget_status_var.set(
                f"₹{abs(remaining):,.2f} over budget"
            )

    def update_analytics(self):
        month = self.month_var.get()

        if month == "All Months":
            month = date.today().strftime("%Y-%m")

        rows = self.conn.execute(
            """
            SELECT category, amount, note
            FROM transactions
            WHERE type = 'Expense'
            AND substr(date, 1, 7) = ?
            """,
            (month,)
        ).fetchall()

        count = len(rows)
        total = sum(row["amount"] for row in rows)

        category_totals = defaultdict(float)

        for row in rows:
            category_totals[row["category"]] += row["amount"]

        top_category = "None"

        if category_totals:
            top_category = max(
                category_totals,
                key=category_totals.get
            )

        largest = max(
            [row["amount"] for row in rows],
            default=0
        )

        average = total / count if count else 0

        self.transaction_count_var.set(str(count))
        self.top_category_var.set(top_category)
        self.largest_expense_var.set(
            f"₹{largest:,.2f}" if largest else "None"
        )
        self.average_var.set(f"₹{average:,.2f}")

    def update_chart(self):
        self.chart_canvas.delete("all")

        month = self.month_var.get()

        if month == "All Months":
            month = date.today().strftime("%Y-%m")

        rows = self.conn.execute(
            """
            SELECT category, SUM(amount) AS total
            FROM transactions
            WHERE type = 'Expense'
            AND substr(date, 1, 7) = ?
            GROUP BY category
            ORDER BY total DESC
            """,
            (month,)
        ).fetchall()

        if not rows:
            self.chart_canvas.create_text(
                140,
                95,
                text="No expense data for this month",
                fill=MUTED,
                font=(FONT, 11)
            )
            return

        total = sum(row["total"] for row in rows)

        x0, y0, x1, y1 = 20, 20, 150, 150
        start = 0

        chart_colors = [
            "#D9A441", "#6C9FC7", "#5FBA78", "#D86655",
            "#B28D5B", "#8A9A9E", "#C27BA0", "#7FA67B"
        ]

        for index, row in enumerate(rows):
            extent = (row["total"] / total) * 360
            color = chart_colors[index % len(chart_colors)]

            self.chart_canvas.create_arc(
                x0,
                y0,
                x1,
                y1,
                start=start,
                extent=extent,
                fill=color,
                outline=BG,
                width=2
            )

            start += extent

        self.chart_canvas.create_oval(
            55,
            55,
            115,
            115,
            fill=BG,
            outline=BG
        )

        self.chart_canvas.create_text(
            85,
            82,
            text=f"₹{total:,.0f}",
            fill=TEXT,
            font=(FONT, 10, "bold")
        )

        self.chart_canvas.create_text(
            85,
            98,
            text="expenses",
            fill=MUTED,
            font=(FONT, 8)
        )

        legend_x = 175
        legend_y = 35

        for index, row in enumerate(rows[:7]):
            color = chart_colors[index % len(chart_colors)]

            self.chart_canvas.create_rectangle(
                legend_x,
                legend_y,
                legend_x + 10,
                legend_y + 10,
                fill=color,
                outline=color
            )

            self.chart_canvas.create_text(
                legend_x + 18,
                legend_y + 5,
                text=f"{row['category']}  ₹{row['total']:,.0f}",
                anchor="w",
                fill=TEXT,
                font=(FONT, 9)
            )

            legend_y += 23

    def export_csv(self):
        path = filedialog.asksaveasfilename(
            title="Export Transactions",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )

        if not path:
            return

        rows = self.conn.execute(
            """
            SELECT date, type, category, amount, note
            FROM transactions
            ORDER BY date DESC, id DESC
            """
        ).fetchall()

        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)

                writer.writerow([
                    "Date",
                    "Type",
                    "Category",
                    "Amount",
                    "Note"
                ])

                for row in rows:
                    writer.writerow([
                        row["date"],
                        row["type"],
                        row["category"],
                        row["amount"],
                        row["note"] or ""
                    ])

            messagebox.showinfo(
                "Export Complete",
                "Transactions exported successfully."
            )

        except OSError as error:
            messagebox.showerror(
                "Export Error",
                str(error)
            )

    def import_csv(self):
        path = filedialog.askopenfilename(
            title="Import Transactions",
            filetypes=[("CSV files", "*.csv")]
        )

        if not path:
            return

        imported = 0
        skipped = 0

        try:
            with open(path, "r", newline="", encoding="utf-8-sig") as file:
                reader = csv.DictReader(file)

                required = {"Date", "Type", "Category", "Amount", "Note"}

                if not required.issubset(set(reader.fieldnames or [])):
                    messagebox.showerror(
                        "Invalid CSV",
                        "CSV must contain Date, Type, Category, Amount and Note columns."
                    )
                    return

                for row in reader:
                    try:
                        transaction_date = row["Date"].strip()
                        transaction_type = row["Type"].strip()
                        category = row["Category"].strip()
                        amount = float(row["Amount"])
                        note = row["Note"].strip()

                        datetime.strptime(
                            transaction_date,
                            "%Y-%m-%d"
                        )

                        if transaction_type not in TYPES or amount <= 0:
                            skipped += 1
                            continue

                        self.conn.execute(
                            """
                            INSERT INTO transactions
                            (date, type, category, amount, note)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (
                                transaction_date,
                                transaction_type,
                                category,
                                amount,
                                note
                            )
                        )

                        imported += 1

                    except (ValueError, KeyError):
                        skipped += 1

            self.conn.commit()
            self.refresh()

            messagebox.showinfo(
                "Import Complete",
                f"Imported: {imported}\nSkipped: {skipped}"
            )

        except (OSError, UnicodeError) as error:
            messagebox.showerror(
                "Import Error",
                str(error)
            )

    def clear_all_data(self):
        confirm = messagebox.askyesno(
            "Clear All Data",
            "This will permanently delete all transactions. Continue?"
        )

        if not confirm:
            return

        self.conn.execute("DELETE FROM transactions")
        self.conn.commit()

        self.clear_form()
        self.refresh()

    def focus_search(self):
        self.search_entry.focus_set()
        self.search_entry.select_range(0, tk.END)

    def close_app(self):
        try:
            self.conn.commit()
            self.conn.close()
        finally:
            self.root.destroy()


def main():
    root = tk.Tk()
    app = ExpenseTracker(root)
    root.mainloop()


if __name__ == "__main__":
    main()
