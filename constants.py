"""
Hostel Management System - Constants
Centralised constants for colours, fonts, roles, and default data.
"""

# ── Colour Palette ────────────────────────────────────────────────────────────
COLORS = {
    "primary":       "#2c3e50",
    "secondary":     "#34495e",
    "accent":        "#3498db",
    "success":       "#27ae60",
    "danger":        "#e74c3c",
    "warning":       "#f39c12",
    "light":         "#ecf0f1",
    "white":         "#ffffff",
    "text_dark":     "#2c3e50",
    "text_muted":    "#7f8c8d",
    "occupied":      "#e74c3c",
    "available":     "#27ae60",
    "maintenance":   "#f39c12",
}

# ── Fonts ─────────────────────────────────────────────────────────────────────
FONTS = {
    "heading":   ("Segoe UI", 22, "bold"),
    "subheading":("Segoe UI", 14, "bold"),
    "body":      ("Segoe UI", 11),
    "small":     ("Segoe UI", 9),
    "button":    ("Segoe UI", 11, "bold"),
    "table_hdr": ("Segoe UI", 11, "bold"),
    "table_row": ("Segoe UI", 10),
}

# ── Roles ─────────────────────────────────────────────────────────────────────
ROLES = {
    "admin":   "Admin",
    "staff":   "Staff",
    "student": "Student",
}

# Navigation items per role: (label, section_key)
ROLE_NAV = {
    "admin": [
        ("🏠  Rooms",      "Rooms"),
        ("🍽️  Mess Menu",  "Mess"),
        ("💰  Payments",   "Payment"),
        ("👥  Staff",      "Staff"),
        ("🎓  Students",   "Students"),
        ("👤  Visitors",   "Visitors"),
        ("📝  Complaints", "Complaints"),
    ],
    "staff": [
        ("🏠  Rooms",      "Rooms"),
        ("�️  Mess Menu",  "Mess"),
        ("�🎓  Students",   "Students"),
        ("👤  Visitors",   "Visitors"),
        ("📝  Complaints", "Complaints"),
    ],
    "student": [
        ("🍽️  Mess Menu",  "Mess"),
        ("📝  Complaints", "Complaints"),
        ("💰  Payments",   "Payment"),
    ],
}

# ── Room Statuses ─────────────────────────────────────────────────────────────
ROOM_CAPACITY = 4  # number of students that fills a room
ROOM_STATUSES = ["Available", "Occupied", "Maintenance"]
ROOM_STATUS_CYCLE = {
    "Available":   "Occupied",
    "Occupied":    "Maintenance",
    "Maintenance": "Available",
}

# ── Default Weekly Mess Menu ──────────────────────────────────────────────────
DEFAULT_MESS_MENU = [
    ("Monday",    "Breakfast", "Idli, Sambar, Coconut Chutney"),
    ("Monday",    "Lunch",     "Rice, Sambar, Thoran, Papad"),
    ("Monday",    "Dinner",    "Chapati, Dal Curry, Salad"),

    ("Tuesday",   "Breakfast", "Dosa, Sambar, Tomato Chutney"),
    ("Tuesday",   "Lunch",     "Rice, Fish Curry, Pickle"),
    ("Tuesday",   "Dinner",    "Chapati, Paneer Curry"),

    ("Wednesday", "Breakfast", "Puttu, Kadala Curry"),
    ("Wednesday", "Lunch",     "Rice, Egg Curry, Rasam"),
    ("Wednesday", "Dinner",    "Chapati, Mixed Vegetable Curry"),

    ("Thursday",  "Breakfast", "Idiyappam, Coconut Milk"),
    ("Thursday",  "Lunch",     "Rice, Chicken Curry, Salad"),
    ("Thursday",  "Dinner",    "Paratha, Dal Makhani"),

    ("Friday",    "Breakfast", "Appam, Vegetable Stew"),
    ("Friday",    "Lunch",     "Rice, Fish Fry, Sambar"),
    ("Friday",    "Dinner",    "Chapati, Palak Paneer"),

    ("Saturday",  "Breakfast", "Poha, Banana"),
    ("Saturday",  "Lunch",     "Biryani, Raita, Papad"),
    ("Saturday",  "Dinner",    "Chapati, Mutton Curry"),

    ("Sunday",    "Breakfast", "Bread, Butter, Omelette, Juice"),
    ("Sunday",    "Lunch",     "Rice, Chicken Roast, Payasam"),
    ("Sunday",    "Dinner",    "Fried Rice, Manchurian, Soup"),
]

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MEAL_ORDER = ["Breakfast", "Lunch", "Dinner"]
