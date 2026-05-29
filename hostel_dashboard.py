"""
Hostel Management System – Dashboard (Tkinter)
=============================================
Features
--------
• Role-based login  (Admin / Staff / Student)
• Dynamic navigation per role
• Room management with 3-state status toggle
• Weekly mess-menu display
• Input validation   (utils.validators)
• Data integrity checks (duplicate rooms/students, room-before-assign)
• Hover effects, styled ttk tables, proper resizing
• Robust error handling everywhere
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime

from db_connection import DatabaseConnection
from utils.validators import (
    validate_name, validate_phone, validate_amount,
    validate_reg_no, validate_room_number, validate_required
)
from utils.constants import (
    COLORS, FONTS, ROLE_NAV,
    ROOM_STATUSES, ROOM_STATUS_CYCLE, ROOM_CAPACITY,
    DAY_ORDER, MEAL_ORDER
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def add_hover(widget, normal_bg: str, hover_bg: str):
    """Attach mouse-enter / mouse-leave colour-change to a Button."""
    widget.bind("<Enter>", lambda _: widget.config(bg=hover_bg))
    widget.bind("<Leave>", lambda _: widget.config(bg=normal_bg))


def make_button(parent, text, command, bg=None, fg="white", **kw):
    """Create a styled, hover-enabled flat Button.
    
    ipadx / ipady are silently converted to padx / pady because they are
    geometry-manager options and are not accepted by tk.Button().
    """
    bg = bg or COLORS["accent"]
    hover = _darken(bg)
    # ipadx/ipady are pack/grid options, not Button options – remap them
    kw.setdefault("padx", kw.pop("ipadx", 10))
    kw.setdefault("pady", kw.pop("ipady", 6))
    btn = tk.Button(
        parent, text=text, command=command,
        font=FONTS["button"], bg=bg, fg=fg,
        activebackground=hover, activeforeground=fg,
        cursor="hand2", relief=tk.FLAT, bd=0, **kw
    )
    add_hover(btn, bg, hover)
    return btn


def _darken(hex_color: str) -> str:
    """Return a slightly darker version of a hex colour."""
    hex_color = hex_color.lstrip('#')
    r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    r, g, b = max(0, r - 30), max(0, g - 30), max(0, b - 30)
    return f'#{r:02x}{g:02x}{b:02x}'


# ── Main Application ──────────────────────────────────────────────────────────

class HostelDashboard(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Hostel Management System")
        self.geometry("1300x800")
        self.minsize(1000, 650)
        self.resizable(True, True)
        self.configure(bg=COLORS["light"])

        # State
        self.current_user = None
        self.current_role = "admin"
        self._nav_buttons = []

        # DB
        self.db = DatabaseConnection(
            host='localhost',
            user='root',
            password='ziyan@123',
            database='hostel_db'
        )
        if not self.db.connect():
            messagebox.showerror(
                "Database Error",
                "Failed to connect to MySQL.\n\n"
                "Ensure MySQL is running and the database exists."
            )
            self.destroy()
            return

        self.db.create_tables()
        self._configure_ttk_styles()
        self.create_login_page()

    # ── TTK Styles ────────────────────────────────────────────────────────────

    def _configure_ttk_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure(
            'Treeview',
            background='white', foreground='black',
            rowheight=32, fieldbackground='white',
            font=FONTS["table_row"]
        )
        style.map('Treeview', background=[('selected', COLORS["accent"])])
        style.configure(
            'Treeview.Heading',
            background=COLORS["secondary"], foreground='white',
            font=FONTS["table_hdr"], relief='flat'
        )
        style.map('Treeview.Heading',
                  background=[('active', COLORS["primary"])])

    # ── Login Page ────────────────────────────────────────────────────────────

    def create_login_page(self):
        self.login_frame = tk.Frame(self, bg=COLORS["primary"])
        self.login_frame.pack(fill='both', expand=True)

        box = tk.Frame(self.login_frame, bg='white', relief=tk.FLAT)
        box.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=460, height=420)

        # Header band
        hdr = tk.Frame(box, bg=COLORS["accent"], height=85)
        hdr.pack(fill='x')
        tk.Label(hdr, text="🏢  Hostel Management",
                 font=("Segoe UI", 22, "bold"),
                 fg='white', bg=COLORS["accent"]).pack(pady=22)

        form = tk.Frame(box, bg='white')
        form.pack(pady=30, padx=45, fill='both', expand=True)

        for label_text, attr, show in [
            ("Username", "username_var", ""),
            ("Password", "password_var", "●"),
        ]:
            tk.Label(form, text=label_text, font=FONTS["body"],
                     bg='white', fg=COLORS["text_dark"]).pack(anchor='w', pady=(0, 4))
            var = tk.StringVar()
            setattr(self, attr, var)
            ent = tk.Entry(form, textvariable=var, font=("Segoe UI", 13),
                           show=show, relief=tk.SOLID, bd=1)
            ent.pack(fill='x', ipady=9, pady=(0, 14))
            if label_text == "Password":
                ent.bind('<Return>', lambda _: self._check_login())

        self._login_err = tk.Label(form, text="", fg=COLORS["danger"],
                                   bg='white', font=FONTS["small"])
        self._login_err.pack(pady=3)

        btn = make_button(form, "LOG IN", self._check_login,
                          bg=COLORS["accent"], ipadx=10, ipady=10)
        btn.pack(fill='x', pady=(12, 0))

        tk.Label(box, text="Default: admin / admin123",
                 font=FONTS["small"], bg='white',
                 fg=COLORS["text_muted"]).pack(pady=8)

    def _check_login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        if not username or not password:
            self._login_err.config(text="⚠  Please enter username and password.")
            return
        try:
            user = self.db.verify_user(username, password)
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
            return

        if user:
            self.current_user = user
            self.current_role = user.get('role', 'student').lower()
            self.login_frame.destroy()
            self.create_dashboard()
        else:
            self._login_err.config(text="❌  Invalid username or password.")
            self.password_var.set("")

    # ── Dashboard Shell ───────────────────────────────────────────────────────

    def create_dashboard(self):
        self.dash_frame = tk.Frame(self, bg=COLORS["light"])
        self.dash_frame.pack(fill='both', expand=True)

        # Top header bar
        top = tk.Frame(self.dash_frame, bg=COLORS["primary"], height=70)
        top.pack(fill='x')
        top.pack_propagate(False)

        role_label = (self.current_role or "user").capitalize()
        username = self.current_user.get('username', '') if self.current_user else ''
        tk.Label(
            top, text="🏢  Hostel Management System",
            font=("Segoe UI", 22, "bold"), fg='white', bg=COLORS["primary"]
        ).pack(side='left', padx=28, pady=14)

        tk.Label(
            top, text=f"👤  {username}  [{role_label}]",
            font=FONTS["body"], fg='#bdc3c7', bg=COLORS["primary"]
        ).pack(side='right', padx=120, pady=14)

        logout_btn = tk.Button(
            top, text="🚪  Logout", font=FONTS["button"],
            bg=COLORS["danger"], fg='white', cursor='hand2',
            relief=tk.FLAT, bd=0, command=self._logout
        )
        add_hover(logout_btn, COLORS["danger"], _darken(COLORS["danger"]))
        logout_btn.pack(side='right', padx=28, pady=14, ipadx=14, ipady=5)

        # Left nav
        nav = tk.Frame(self.dash_frame, bg=COLORS["secondary"], width=210)
        nav.pack(side='left', fill='y')
        nav.pack_propagate(False)

        tk.Label(nav, text="Navigation", font=FONTS["subheading"],
                 bg=COLORS["secondary"], fg='white').pack(pady=18)

        ttk.Separator(nav, orient='horizontal').pack(fill='x', padx=15)

        self._nav_buttons = []
        nav_items = ROLE_NAV.get(self.current_role, ROLE_NAV['admin'])
        for label, section_key in nav_items:
            btn = tk.Button(
                nav, text=label, font=("Segoe UI", 12),
                bg=COLORS["secondary"], fg='white',
                activebackground=COLORS["primary"],
                activeforeground='white',
                cursor='hand2', bd=0, anchor='w', padx=18,
                command=lambda k=section_key: self._show_section(k)
            )
            btn.pack(fill='x', ipady=13, pady=1)
            add_hover(btn, COLORS["secondary"], COLORS["primary"])
            self._nav_buttons.append((section_key, btn))

        # Content area
        self.content = tk.Frame(self.dash_frame, bg=COLORS["light"])
        self.content.pack(side='left', fill='both', expand=True,
                          padx=18, pady=18)

        # Build all permitted sections
        self.sections = {}
        builders = {
            "Rooms":      self._build_rooms,
            "Mess":       self._build_mess,
            "Payment":    self._build_payments,
            "Staff":      self._build_staff,
            "Students":   self._build_students,
            "Visitors":   self._build_visitors,
            "Complaints": self._build_complaints,
        }
        allowed = {k for _, k in nav_items}
        for key, builder in builders.items():
            if key in allowed:
                self.sections[key] = builder()

        # Show first available section
        first_key = nav_items[0][1] if nav_items else None
        if first_key:
            self._show_section(first_key)

    def _show_section(self, name):
        for f in self.sections.values():
            f.pack_forget()
        if name in self.sections:
            self.sections[name].pack(fill='both', expand=True)

    def _logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.current_user = None
            self.current_role = "admin"
            # clear widget references that may be stale after re-login
            for attr in ('_room_combo', '_room_status_filter_var', 'room_tree',
                         'student_tree', 'mess_tree', 'pay_tree',
                         'staff_tree', 'visitor_tree', 'complaint_tree'):
                if hasattr(self, attr):
                    delattr(self, attr)
            self.dash_frame.destroy()
            self.create_login_page()

    # ── Shared Widgets ────────────────────────────────────────────────────────

    def _section_header(self, parent, icon, title):
        hdr = tk.Frame(parent, bg='white')
        hdr.pack(fill='x', pady=(0, 14))
        tk.Label(hdr, text=f"{icon}  {title}",
                 font=FONTS["heading"], bg='white',
                 fg=COLORS["text_dark"]).pack(side='left', padx=20, pady=14)

    def _make_table(self, parent, columns, col_widths=None, height=14):
        """Create scrollable, styled Treeview."""
        wrapper = tk.Frame(parent, bg='white')
        wrapper.pack(fill='both', expand=True, padx=8, pady=8)

        vsb = ttk.Scrollbar(wrapper, orient='vertical')
        vsb.pack(side='right', fill='y')
        hsb = ttk.Scrollbar(wrapper, orient='horizontal')
        hsb.pack(side='bottom', fill='x')

        tree = ttk.Treeview(
            wrapper, columns=columns, show='headings',
            yscrollcommand=vsb.set, xscrollcommand=hsb.set,
            height=height
        )
        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)

        for i, col in enumerate(columns):
            w = (col_widths[i] if col_widths and i < len(col_widths) else 150)
            tree.heading(col, text=col)
            tree.column(col, anchor='center', width=w, minwidth=60)

        tree.pack(side='left', fill='both', expand=True)
        tree.tag_configure('odd',  background='#f9f9f9')
        tree.tag_configure('even', background='white')
        return tree

    def _form_box(self, parent):
        f = tk.Frame(parent, bg='white', relief=tk.FLAT)
        f.pack(fill='x', pady=(0, 12), padx=4)
        return f

    def _lbl_entry(self, parent, text, var, width=14):
        tk.Label(parent, text=text, font=FONTS["body"],
                 bg='white', fg=COLORS["text_dark"]).pack(side='left', padx=(8, 3))
        tk.Entry(parent, textvariable=var, font=("Segoe UI", 11),
                 width=width, relief=tk.SOLID, bd=1).pack(
                     side='left', padx=(0, 10), ipady=5)

    # ── Rooms Section ─────────────────────────────────────────────────────────

    def _build_rooms(self):
        frame = tk.Frame(self.content, bg=COLORS["light"])
        self._section_header(frame, "🏠", "Room Management")

        # Add-room form — admin only
        if self.current_role == 'admin':
            form_box = self._form_box(frame)
            inner = tk.Frame(form_box, bg='white')
            inner.pack(pady=16, padx=16, fill='x')

            room_var = tk.StringVar()
            self._lbl_entry(inner, "Room Number:", room_var, 12)

            make_button(inner, "➕  Add Room",
                        lambda: self._add_room(room_var),
                        bg=COLORS["success"],
                        ipadx=12, ipady=5).pack(side='left', padx=5)

            status_filter_var = tk.StringVar(value="All")
            tk.Label(inner, text="Filter:", font=FONTS["body"],
                     bg='white').pack(side='left', padx=(20, 4))
            filter_cb = ttk.Combobox(
                inner, textvariable=status_filter_var,
                values=["All"] + ROOM_STATUSES, width=12, state='readonly'
            )
            filter_cb.pack(side='left')
            filter_cb.bind('<<ComboboxSelected>>',
                           lambda _: self._refresh_rooms(status_filter_var.get()))

            tk.Label(form_box,
                     text="Double-click a room to cycle its status  →  "
                          "Available ▶ Occupied ▶ Maintenance ▶ Available",
                     font=FONTS["small"], bg='white',
                     fg=COLORS["text_muted"]).pack(pady=(0, 8))
        else:
            # staff: filter only, no add
            form_box = self._form_box(frame)
            inner = tk.Frame(form_box, bg='white')
            inner.pack(pady=16, padx=16, fill='x')
            status_filter_var = tk.StringVar(value="All")
            tk.Label(inner, text="Filter:", font=FONTS["body"],
                     bg='white').pack(side='left', padx=(0, 4))
            filter_cb = ttk.Combobox(
                inner, textvariable=status_filter_var,
                values=["All"] + ROOM_STATUSES, width=12, state='readonly'
            )
            filter_cb.pack(side='left')
            filter_cb.bind('<<ComboboxSelected>>',
                           lambda _: self._refresh_rooms(status_filter_var.get()))

        tbl_frame = tk.Frame(frame, bg='white')
        tbl_frame.pack(fill='both', expand=True, padx=4)

        cols = ["Room Number", "Status", f"Students ({ROOM_CAPACITY} = Full)"]
        widths = [160, 140, 180]
        self.room_tree = self._make_table(tbl_frame, cols, widths)
        if self.current_role == 'admin':
            self.room_tree.bind('<Double-Button-1>',
                                lambda e: self._room_double_click())

        self._refresh_rooms()
        self._room_status_filter_var = status_filter_var

        if self.current_role == 'admin':
            btn_row = tk.Frame(frame, bg=COLORS["light"])
            btn_row.pack(fill='x', padx=4, pady=(6, 0))
            make_button(btn_row, "🗑  Delete Selected Room",
                        self._delete_room,
                        bg=COLORS["danger"],
                        ipadx=12, ipady=5).pack(side='left', padx=4)

        return frame

    def _refresh_rooms(self, status_filter="All"):
        try:
            rooms = self.db.get_all_rooms()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
            return
        self.room_tree.delete(*self.room_tree.get_children())
        for r in rooms:
            s = r.get('status', 'Available')
            if status_filter != "All" and s != status_filter:
                continue
            try:
                count = self.db.get_room_student_count(r['room_no'])
            except Exception:
                count = 0
            tag_colour = {
                'Available':   'avail',
                'Occupied':    'occup',
                'Maintenance': 'maint',
            }.get(s, 'even')
            self.room_tree.insert('', 'end', iid=r['room_no'],
                                  values=(r['room_no'], s,
                                          f"{count}/{ROOM_CAPACITY}"),
                                  tags=(tag_colour,))
        self.room_tree.tag_configure('avail', foreground=COLORS["available"])
        self.room_tree.tag_configure('occup', foreground=COLORS["occupied"])
        self.room_tree.tag_configure('maint', foreground=COLORS["warning"])
        # keep available-rooms combobox in student form in sync
        if hasattr(self, '_room_combo'):
            try:
                if self._room_combo.winfo_exists():
                    avail = self.db.get_available_rooms()
                    self._room_combo['values'] = avail
                else:
                    del self._room_combo
            except Exception:
                pass

    def _add_room(self, room_var):
        val = room_var.get().strip()
        ok, msg = validate_room_number(val)
        if not ok:
            messagebox.showwarning("Validation Error", msg)
            return
        try:
            self.db.add_room(val)
            room_var.set("")
            self._refresh_rooms(
                getattr(self, '_room_status_filter_var', tk.StringVar()).get() or "All"
            )
            messagebox.showinfo("Success", f"Room {val} added.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _room_double_click(self):
        sel = self.room_tree.selection()
        if not sel:
            return
        room_no = sel[0]
        current_status = self.room_tree.item(room_no, 'values')[1]
        next_status = ROOM_STATUS_CYCLE.get(current_status, 'Available')
        if messagebox.askyesno(
            "Toggle Status",
            f"Room {room_no}  current: {current_status}\nChange to: {next_status}?"
        ):
            try:
                self.db.update_room_status(room_no, next_status)
                self._refresh_rooms(
                    getattr(self, '_room_status_filter_var', tk.StringVar()).get() or "All"
                )
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _delete_room(self):
        sel = self.room_tree.selection()
        if not sel:
            messagebox.showwarning("Select Room", "Please select a room first.")
            return
        room_no = sel[0]
        if messagebox.askyesno("Confirm Delete", f"Delete room {room_no}?"):
            try:
                self.db.delete_room(room_no)
                self._refresh_rooms(
                    getattr(self, '_room_status_filter_var', tk.StringVar()).get() or "All"
                )
            except Exception as e:
                messagebox.showerror("Error", str(e))

    # ── Mess Section ──────────────────────────────────────────────────────────

    def _build_mess(self):
        frame = tk.Frame(self.content, bg=COLORS["light"])
        self._section_header(frame, "🍽️", "Weekly Mess Menu")

        if self.current_role == 'admin':
            form_box = self._form_box(frame)
            inner = tk.Frame(form_box, bg='white')
            inner.pack(pady=14, padx=14, fill='x')

            day_var   = tk.StringVar(value='Monday')
            meal_var  = tk.StringVar(value='Breakfast')
            items_var = tk.StringVar()

            tk.Label(inner, text="Day:", font=FONTS["body"],
                     bg='white').pack(side='left', padx=(4, 2))
            ttk.Combobox(inner, textvariable=day_var,
                         values=DAY_ORDER, width=11,
                         state='readonly').pack(side='left', padx=(0, 10))

            tk.Label(inner, text="Meal:", font=FONTS["body"],
                     bg='white').pack(side='left', padx=(4, 2))
            ttk.Combobox(inner, textvariable=meal_var,
                         values=MEAL_ORDER, width=10,
                         state='readonly').pack(side='left', padx=(0, 10))

            self._lbl_entry(inner, "Items:", items_var, 30)
            make_button(inner, "➕  Add",
                        lambda: self._add_mess_item(day_var, meal_var, items_var),
                        bg=COLORS["success"],
                        ipadx=10, ipady=5).pack(side='left', padx=5)

        tbl_frame = tk.Frame(frame, bg='white')
        tbl_frame.pack(fill='both', expand=True, padx=4)
        cols   = ["Day", "Meal", "Menu Items"]
        widths = [130, 110, 550]
        self.mess_tree = self._make_table(tbl_frame, cols, widths, height=16)
        self._refresh_mess()

        if self.current_role == 'admin':
            btn_row = tk.Frame(frame, bg=COLORS["light"])
            btn_row.pack(fill='x', padx=4, pady=(6, 0))
            make_button(btn_row, "🗑  Delete Selected Row",
                        self._delete_mess_item,
                        bg=COLORS["danger"],
                        ipadx=12, ipady=5).pack(side='left', padx=4)
            make_button(btn_row, "🔄  Reset to Default Menu",
                        self._reset_mess_menu,
                        bg=COLORS["warning"],
                        ipadx=12, ipady=5).pack(side='left', padx=4)

        return frame

    def _refresh_mess(self):
        try:
            rows_raw = self.db.get_all_mess_menu()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
            return
        self.mess_tree.delete(*self.mess_tree.get_children())
        for i, r in enumerate(rows_raw):
            tag = 'odd' if i % 2 else 'even'
            self.mess_tree.insert('', 'end', iid=str(r['id']),
                                  values=(r['day'], r['meal'], r['items']),
                                  tags=(tag,))

    def _add_mess_item(self, day_var, meal_var, items_var):
        day   = day_var.get()
        meal  = meal_var.get()
        items = items_var.get().strip()
        ok, msg = validate_required(items, "Menu Items")
        if not ok:
            messagebox.showwarning("Validation", msg)
            return
        try:
            self.db.add_mess_menu_item(day, meal, items)
            items_var.set("")
            self._refresh_mess()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _delete_mess_item(self):
        sel = self.mess_tree.selection()
        if not sel:
            messagebox.showwarning("Select Row", "Please select a menu row.")
            return
        if messagebox.askyesno("Confirm", "Delete this menu entry?"):
            try:
                self.db.delete_mess_menu_item(int(sel[0]))
                self._refresh_mess()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _reset_mess_menu(self):
        if not messagebox.askyesno(
            "Reset Menu",
            "This will delete ALL current entries and reload the default weekly menu.\nContinue?"
        ):
            return
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("DELETE FROM mess_menu")
            self.db.seed_default_mess_menu()
            self._refresh_mess()
            messagebox.showinfo("Reset", "Default weekly menu restored.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ── Payments Section ──────────────────────────────────────────────────────

    def _build_payments(self):
        frame = tk.Frame(self.content, bg=COLORS["light"])
        self._section_header(frame, "💰", "Payment Records")

        if self.current_role != 'student':
            form_box = self._form_box(frame)
            inner = tk.Frame(form_box, bg='white')
            inner.pack(pady=14, padx=14, fill='x')

            name_var = tk.StringVar()
            amt_var  = tk.StringVar()

            self._lbl_entry(inner, "Student Name:", name_var, 18)
            self._lbl_entry(inner, "Amount (Rs.):", amt_var, 10)

            status_var = tk.StringVar(value='Paid')
            tk.Label(inner, text="Status:", bg='white',
                     font=FONTS["body"]).pack(side='left', padx=(10, 4))
            ttk.Combobox(inner, textvariable=status_var,
                         values=['Paid', 'Failed'], state='readonly',
                         width=10).pack(side='left', padx=(0, 10))

            make_button(inner, "➕  Add Payment",
                        lambda: self._add_payment(name_var, amt_var, status_var),
                        bg=COLORS["success"],
                        ipadx=12, ipady=5).pack(side='left', padx=5)

        tbl_frame = tk.Frame(frame, bg='white')
        tbl_frame.pack(fill='both', expand=True, padx=4)
        cols   = ["ID", "Student", "Amount (Rs.)", "Date", "Status"]
        widths = [60, 200, 140, 140, 100]
        self.pay_tree = self._make_table(tbl_frame, cols, widths)
        self.pay_tree.tag_configure('paid',   foreground=COLORS["available"])
        self.pay_tree.tag_configure('failed', foreground=COLORS["danger"])
        self._refresh_payments()

        if self.current_role != 'student':
            btn_row = tk.Frame(frame, bg=COLORS["light"])
            btn_row.pack(fill='x', padx=4, pady=(6, 0))
            make_button(btn_row, "🗑  Delete Selected",
                        self._delete_payment,
                        bg=COLORS["danger"],
                        ipadx=12, ipady=5).pack(side='left', padx=4)

        return frame

    def _refresh_payments(self):
        try:
            payments = self.db.get_all_payments()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
            return
        self.pay_tree.delete(*self.pay_tree.get_children())
        for p in payments:
            status = p.get('status', 'Paid')
            color_tag = 'paid' if status == 'Paid' else 'failed'
            self.pay_tree.insert('', 'end', iid=str(p['id']),
                                 values=(p['id'], p['student'],
                                         f"Rs.{p['amount']}", p['date'],
                                         status),
                                 tags=(color_tag,))

    def _add_payment(self, name_var, amt_var, status_var=None):
        name   = name_var.get().strip()
        amt    = amt_var.get().strip()
        status = status_var.get() if status_var else 'Paid'

        ok, msg = validate_required(name, "Student Name")
        if not ok:
            messagebox.showwarning("Validation", msg)
            return
        ok, err = validate_amount(amt)
        if not ok:
            messagebox.showwarning("Validation", err)
            return

        try:
            self.db.add_payment(name, float(amt), status)
            name_var.set("")
            amt_var.set("")
            if status_var:
                status_var.set('Paid')
            self._refresh_payments()
            messagebox.showinfo("Success", "Payment recorded.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _delete_payment(self):
        sel = self.pay_tree.selection()
        if not sel:
            messagebox.showwarning("Select Row", "Please select a payment record.")
            return
        if messagebox.askyesno("Confirm", "Delete this payment record?"):
            try:
                self.db.delete_payment(int(sel[0]))
                self._refresh_payments()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    # ── Staff Section ─────────────────────────────────────────────────────────

    def _build_staff(self):
        frame = tk.Frame(self.content, bg=COLORS["light"])
        self._section_header(frame, "👥", "Staff Management")

        form_box = self._form_box(frame)
        inner = tk.Frame(form_box, bg='white')
        inner.pack(pady=14, padx=14, fill='x')

        name_v    = tk.StringVar()
        role_v    = tk.StringVar()
        contact_v = tk.StringVar()

        self._lbl_entry(inner, "Name:", name_v, 18)
        self._lbl_entry(inner, "Role:", role_v, 14)
        self._lbl_entry(inner, "Contact:", contact_v, 12)

        make_button(inner, "➕  Add Staff",
                    lambda: self._add_staff(name_v, role_v, contact_v),
                    bg=COLORS["success"],
                    ipadx=12, ipady=5).pack(side='left', padx=5)

        tbl_frame = tk.Frame(frame, bg='white')
        tbl_frame.pack(fill='both', expand=True, padx=4)
        cols   = ["ID", "Name", "Role", "Contact"]
        widths = [60, 230, 190, 170]
        self.staff_tree = self._make_table(tbl_frame, cols, widths)
        self._refresh_staff()

        btn_row = tk.Frame(frame, bg=COLORS["light"])
        btn_row.pack(fill='x', padx=4, pady=(6, 0))
        make_button(btn_row, "🗑  Delete Selected Staff",
                    self._delete_staff,
                    bg=COLORS["danger"],
                    ipadx=12, ipady=5).pack(side='left', padx=4)

        return frame

    def _refresh_staff(self):
        try:
            staff = self.db.get_all_staff()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
            return
        self.staff_tree.delete(*self.staff_tree.get_children())
        for i, s in enumerate(staff):
            tag = 'odd' if i % 2 else 'even'
            self.staff_tree.insert('', 'end', iid=str(s['id']),
                                   values=(s['id'], s['name'],
                                           s['role'], s['contact']),
                                   tags=(tag,))

    def _add_staff(self, name_v, role_v, contact_v):
        name    = name_v.get().strip()
        role    = role_v.get().strip()
        contact = contact_v.get().strip()

        ok1, m1 = validate_name(name)
        ok2, m2 = validate_required(role, "Role")
        ok3, m3 = validate_phone(contact)
        for ok, msg in [(ok1, m1), (ok2, m2), (ok3, m3)]:
            if not ok:
                messagebox.showwarning("Validation", msg)
                return

        try:
            self.db.add_staff(name, role, contact)
            name_v.set(""); role_v.set(""); contact_v.set("")
            self._refresh_staff()
            messagebox.showinfo("Success", f"Staff member '{name}' added.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _delete_staff(self):
        sel = self.staff_tree.selection()
        if not sel:
            messagebox.showwarning("Select Row", "Please select a staff member.")
            return
        if messagebox.askyesno("Confirm", "Remove this staff member?"):
            try:
                self.db.delete_staff(int(sel[0]))
                self._refresh_staff()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    # ── Students Section ──────────────────────────────────────────────────────

    def _build_students(self):
        frame = tk.Frame(self.content, bg=COLORS["light"])
        self._section_header(frame, "🎓", "Student Management")

        form_box = self._form_box(frame)
        inner = tk.Frame(form_box, bg='white')
        inner.pack(pady=14, padx=14, fill='x')

        reg_v     = tk.StringVar()
        name_v    = tk.StringVar()
        addr_v    = tk.StringVar()
        contact_v = tk.StringVar()
        room_v    = tk.StringVar()

        for label, var, w in [
            ("Reg No:", reg_v, 10),
            ("Name:", name_v, 14),
            ("Address:", addr_v, 16),
            ("Contact:", contact_v, 12),
        ]:
            self._lbl_entry(inner, label, var, w)

        # Available-rooms combobox
        tk.Label(inner, text="Room (available):", font=FONTS["body"],
                 bg='white', fg=COLORS["text_dark"]).pack(side='left', padx=(8, 3))
        try:
            avail_rooms = self.db.get_available_rooms()
        except Exception:
            avail_rooms = []
        self._room_combo = ttk.Combobox(
            inner, textvariable=room_v,
            values=avail_rooms, width=10, state='readonly'
        )
        self._room_combo.pack(side='left', padx=(0, 10), ipady=4)
        # refresh list every time the user opens the dropdown
        self._room_combo.bind('<ButtonPress-1>',
            lambda _: self._room_combo.config(
                values=self.db.get_available_rooms() if hasattr(self, 'db') else []
            )
        )

        make_button(inner, "➕  Add Student",
                    lambda: self._add_student(
                        reg_v, name_v, addr_v, contact_v, room_v),
                    bg=COLORS["success"],
                    ipadx=12, ipady=5).pack(side='left', padx=5)

        tk.Label(form_box,
                 text="Double-click a row: change room (Yes) or delete student (No)",
                 font=FONTS["small"], bg='white',
                 fg=COLORS["text_muted"]).pack(pady=(0, 6))

        tbl_frame = tk.Frame(frame, bg='white')
        tbl_frame.pack(fill='both', expand=True, padx=4)
        cols   = ["Reg No", "Name", "Address", "Contact", "Room No"]
        widths = [110, 180, 220, 130, 100]
        self.student_tree = self._make_table(tbl_frame, cols, widths)
        self.student_tree.bind('<Double-Button-1>',
                               lambda _: self._student_action())
        self._refresh_students()

        return frame

    def _refresh_students(self):
        try:
            students = self.db.get_all_students()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
            return
        self.student_tree.delete(*self.student_tree.get_children())
        for i, s in enumerate(students):
            tag = 'odd' if i % 2 else 'even'
            self.student_tree.insert(
                '', 'end', iid=s['reg_no'],
                values=(s['reg_no'], s['name'], s['address'],
                        s['contact'], s.get('room_no', '')),
                tags=(tag,)
            )

    def _add_student(self, reg_v, name_v, addr_v, contact_v, room_v):
        reg     = reg_v.get().strip()
        name    = name_v.get().strip()
        addr    = addr_v.get().strip()
        contact = contact_v.get().strip()
        room    = room_v.get().strip()

        ok1, m1 = validate_reg_no(reg)
        ok2, m2 = validate_name(name)
        ok3, m3 = validate_required(addr, "Address")
        ok4, m4 = validate_phone(contact)
        ok5, m5 = validate_room_number(room)
        for ok, msg in [(ok1, m1), (ok2, m2), (ok3, m3), (ok4, m4), (ok5, m5)]:
            if not ok:
                messagebox.showwarning("Validation Error", msg)
                return

        try:
            self.db.add_student(reg, name, addr, contact, room)
            for v in (reg_v, name_v, addr_v, contact_v, room_v):
                v.set("")
            self._refresh_students()
            # sync room table and combobox
            if hasattr(self, 'room_tree'):
                self._refresh_rooms()
            elif hasattr(self, '_room_combo'):
                try:
                    self._room_combo['values'] = self.db.get_available_rooms()
                except Exception:
                    pass
            messagebox.showinfo("Success", f"Student '{name}' added to room {room}.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _student_action(self):
        sel = self.student_tree.selection()
        if not sel:
            return
        reg_no = sel[0]
        values = self.student_tree.item(reg_no, 'values')

        action = messagebox.askquestion(
            "Student Action",
            f"Student: {values[1]}  |  Room: {values[4]}\n\n"
            "Yes  Change Room\nNo   Delete Student",
            icon='question'
        )
        if action == 'yes':
            new_room = simpledialog.askstring(
                "Change Room", "Enter new Room Number:")
            if new_room:
                ok, msg = validate_room_number(new_room)
                if not ok:
                    messagebox.showwarning("Validation", msg)
                    return
                if not self.db.check_room_exists(new_room):
                    messagebox.showerror(
                        "Room Not Found",
                        f"Room '{new_room}' does not exist.\n"
                        "Please add the room first."
                    )
                    return
                try:
                    old_room = values[4]
                    self.db.update_student(reg_no, room_no=new_room)
                    self.db.update_room_status(new_room, 'Occupied')
                    if old_room and not self.db.check_room_has_students(old_room):
                        self.db.update_room_status(old_room, 'Available')
                    self._refresh_students()
                    if hasattr(self, 'room_tree'):
                        self._refresh_rooms()
                    messagebox.showinfo("Updated", f"Room changed to {new_room}.")
                except Exception as e:
                    messagebox.showerror("Error", str(e))
        else:
            if messagebox.askyesno("Confirm Delete",
                                   f"Delete student {values[1]} ({reg_no})?"):
                try:
                    self.db.delete_student(reg_no)
                    self._refresh_students()
                    if hasattr(self, 'room_tree'):
                        self._refresh_rooms()
                    messagebox.showinfo("Deleted", "Student record removed.")
                except Exception as e:
                    messagebox.showerror("Error", str(e))

    # ── Visitors Section ──────────────────────────────────────────────────────

    def _build_visitors(self):
        frame = tk.Frame(self.content, bg=COLORS["light"])
        self._section_header(frame, "👤", "Visitor Management")

        form_box = self._form_box(frame)
        inner = tk.Frame(form_box, bg='white')
        inner.pack(pady=14, padx=14, fill='x')

        name_v    = tk.StringVar()
        contact_v = tk.StringVar()
        date_v    = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        purpose_v = tk.StringVar()

        for label, var, w in [
            ("Name:", name_v, 16),
            ("Contact:", contact_v, 12),
            ("Date (YYYY-MM-DD):", date_v, 13),
            ("Purpose:", purpose_v, 20),
        ]:
            self._lbl_entry(inner, label, var, w)

        make_button(inner, "➕  Add Visitor",
                    lambda: self._add_visitor(
                        name_v, contact_v, date_v, purpose_v),
                    bg=COLORS["success"],
                    ipadx=12, ipady=5).pack(side='left', padx=5)

        tbl_frame = tk.Frame(frame, bg='white')
        tbl_frame.pack(fill='both', expand=True, padx=4)
        cols   = ["ID", "Name", "Contact", "Date", "Purpose"]
        widths = [60, 200, 140, 130, 270]
        self.visitor_tree = self._make_table(tbl_frame, cols, widths)
        self._refresh_visitors()

        btn_row = tk.Frame(frame, bg=COLORS["light"])
        btn_row.pack(fill='x', padx=4, pady=(6, 0))
        make_button(btn_row, "🗑  Delete Selected Visitor",
                    self._delete_visitor,
                    bg=COLORS["danger"],
                    ipadx=12, ipady=5).pack(side='left', padx=4)

        return frame

    def _refresh_visitors(self):
        try:
            visitors = self.db.get_all_visitors()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
            return
        self.visitor_tree.delete(*self.visitor_tree.get_children())
        for i, v in enumerate(visitors):
            tag = 'odd' if i % 2 else 'even'
            self.visitor_tree.insert(
                '', 'end', iid=str(v['id']),
                values=(v['id'], v['name'], v['contact'],
                        str(v['date']), v['purpose']),
                tags=(tag,)
            )

    def _add_visitor(self, name_v, contact_v, date_v, purpose_v):
        name    = name_v.get().strip()
        contact = contact_v.get().strip()
        date    = date_v.get().strip()
        purpose = purpose_v.get().strip()

        ok1, m1 = validate_name(name)
        ok2, m2 = validate_phone(contact)
        ok3, m3 = validate_required(date, "Date")
        ok4, m4 = validate_required(purpose, "Purpose")
        for ok, msg in [(ok1, m1), (ok2, m2), (ok3, m3), (ok4, m4)]:
            if not ok:
                messagebox.showwarning("Validation", msg)
                return

        try:
            from datetime import datetime as dt
            date_obj = dt.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            messagebox.showwarning("Validation",
                                   "Date must be in YYYY-MM-DD format.")
            return

        try:
            self.db.add_visitor(name, contact, date_obj, purpose)
            name_v.set(""); contact_v.set("")
            date_v.set(datetime.now().strftime("%Y-%m-%d"))
            purpose_v.set("")
            self._refresh_visitors()
            messagebox.showinfo("Success", f"Visitor '{name}' registered.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _delete_visitor(self):
        sel = self.visitor_tree.selection()
        if not sel:
            messagebox.showwarning("Select Row", "Please select a visitor.")
            return
        if messagebox.askyesno("Confirm", "Remove this visitor record?"):
            try:
                self.db.delete_visitor(int(sel[0]))
                self._refresh_visitors()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    # ── Complaints Section ────────────────────────────────────────────────────

    def _build_complaints(self):
        frame = tk.Frame(self.content, bg=COLORS["light"])
        self._section_header(frame, "📝", "Complaint Management")

        form_box = self._form_box(frame)
        inner = tk.Frame(form_box, bg='white')
        inner.pack(pady=14, padx=14, fill='x')

        student_v   = tk.StringVar()
        room_v      = tk.StringVar()
        complaint_v = tk.StringVar()

        for label, var, w in [
            ("Student:", student_v, 14),
            ("Room:", room_v, 8),
            ("Complaint:", complaint_v, 32),
        ]:
            self._lbl_entry(inner, label, var, w)

        make_button(inner, "➕  Submit",
                    lambda: self._add_complaint(
                        student_v, room_v, complaint_v),
                    bg=COLORS["success"],
                    ipadx=12, ipady=5).pack(side='left', padx=5)

        if self.current_role in ('admin', 'staff'):
            tk.Label(form_box,
                     text="Double-click a row: toggle status (Pending / Resolved) or delete",
                     font=FONTS["small"], bg='white',
                     fg=COLORS["text_muted"]).pack(pady=(0, 6))

        tbl_frame = tk.Frame(frame, bg='white')
        tbl_frame.pack(fill='both', expand=True, padx=4)
        cols   = ["ID", "Student", "Room", "Complaint", "Date", "Status"]
        widths = [50, 160, 80, 310, 110, 100]
        self.complaint_tree = self._make_table(tbl_frame, cols, widths)

        if self.current_role in ('admin', 'staff'):
            self.complaint_tree.bind(
                '<Double-Button-1>',
                lambda _: self._complaint_action()
            )

        self._refresh_complaints()
        return frame

    def _refresh_complaints(self):
        try:
            complaints = self.db.get_all_complaints()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
            return
        self.complaint_tree.delete(*self.complaint_tree.get_children())
        for i, c in enumerate(complaints):
            tag = 'odd' if i % 2 else 'even'
            text = c['complaint']
            display = text if len(text) <= 45 else text[:42] + '...'
            self.complaint_tree.insert(
                '', 'end', iid=str(c['id']),
                values=(c['id'], c['student'], c['room_no'],
                        display, str(c['date']), c['status']),
                tags=(tag,)
            )

    def _add_complaint(self, student_v, room_v, complaint_v):
        student   = student_v.get().strip()
        room      = room_v.get().strip()
        complaint = complaint_v.get().strip()

        ok1, m1 = validate_required(student, "Student")
        ok2, m2 = validate_room_number(room)
        ok3, m3 = validate_required(complaint, "Complaint")
        for ok, msg in [(ok1, m1), (ok2, m2), (ok3, m3)]:
            if not ok:
                messagebox.showwarning("Validation", msg)
                return

        try:
            self.db.add_complaint(student, room, complaint)
            student_v.set(""); room_v.set(""); complaint_v.set("")
            self._refresh_complaints()
            messagebox.showinfo("Submitted", "Complaint registered.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _complaint_action(self):
        sel = self.complaint_tree.selection()
        if not sel:
            return
        cid    = int(sel[0])
        values = self.complaint_tree.item(sel[0], 'values')
        status = values[5]

        action = messagebox.askquestion(
            "Complaint Action",
            f"Complaint ID: {cid}\nCurrent status: {status}\n\n"
            "Yes  Toggle status\nNo   Delete complaint",
            icon='question'
        )
        if action == 'yes':
            new_status = "Resolved" if status == "Pending" else "Pending"
            try:
                self.db.update_complaint_status(cid, new_status)
                self._refresh_complaints()
                messagebox.showinfo("Updated",
                                    f"Status changed to {new_status}.")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        else:
            if messagebox.askyesno("Confirm Delete",
                                   f"Delete complaint #{cid}?"):
                try:
                    self.db.delete_complaint(cid)
                    self._refresh_complaints()
                except Exception as e:
                    messagebox.showerror("Error", str(e))


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = HostelDashboard()
    app.mainloop()
