import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager


class DatabaseConnection:
    """
    Handle MySQL database connections and CRUD operations for the
    Hostel Management System.

    Schema assumptions
    ------------------
    students  : reg_no, name, address, contact, room_no
    rooms     : room_no, status  (Available | Occupied | Maintenance)
    staff     : id, name, role, contact
    mess      : id, item
    mess_menu : id, day, meal, items   ← managed by this class
    payments  : id, student, amount, date
    visitors  : id, name, contact, date, purpose
    complaints: id, student, room_no, complaint, date, status
    users     : id, username, password, role, created_at
    """

    def __init__(self, host='localhost', user='root',
                 password='ziyan@123', database='hostel_db'):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

    # ── Connection helpers ────────────────────────────────────────────────────

    def connect(self) -> bool:
        """Establish connection to MySQL database."""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            print("✓ Database connection successful!")
            return True
        except Error as e:
            print(f"✗ Connection failed: {e}")
            return False

    def disconnect(self):
        """Close database connection."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("✓ Database connection closed")

    @contextmanager
    def get_cursor(self):
        """Context manager that yields a dictionary cursor and auto-commits."""
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            yield cursor
            self.connection.commit()
        except Error as e:
            print(f"Database error: {e}")
            if self.connection:
                self.connection.rollback()
            raise
        finally:
            if cursor:
                cursor.close()

    # ── Table creation / seeding ──────────────────────────────────────────────

    def create_tables(self):
        """
        Ensure required tables exist and seed default data.
        Only the 'users' and 'mess_menu' tables are created here;
        all other tables are assumed to already exist in hostel_db.
        """
        with self.get_cursor() as cursor:
            # users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id         INT AUTO_INCREMENT PRIMARY KEY,
                    username   VARCHAR(50)  UNIQUE NOT NULL,
                    password   VARCHAR(255) NOT NULL,
                    role       VARCHAR(20)  NOT NULL DEFAULT 'student',
                    created_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # mess_menu table (weekly schedule)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mess_menu (
                    id    INT AUTO_INCREMENT PRIMARY KEY,
                    day   VARCHAR(15)  NOT NULL,
                    meal  VARCHAR(15)  NOT NULL,
                    items TEXT         NOT NULL
                )
            """)
            print("✓ Tables 'users' and 'mess_menu' ensured")

            # Add status column to payments if it doesn't exist yet
            cursor.execute("""
                SELECT COUNT(*) AS cnt FROM information_schema.columns
                WHERE table_schema = DATABASE()
                  AND table_name   = 'payments'
                  AND column_name  = 'status'
            """)
            if cursor.fetchone()['cnt'] == 0:
                cursor.execute("""
                    ALTER TABLE payments
                    ADD COLUMN status ENUM('Paid','Failed') NOT NULL DEFAULT 'Paid'
                """)
                print("✓ 'status' column added to 'payments'")

        # Seed default admin account if users table is empty
        self._seed_default_admin()
        # Seed weekly mess menu if mess_menu table is empty
        self.seed_default_mess_menu()

    def _seed_default_admin(self):
        """Insert default admin, staff, and student accounts if no users exist yet."""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS cnt FROM users")
            if cursor.fetchone()['cnt'] == 0:
                default_users = [
                    ('admin',    'admin123',   'admin'),
                    ('staff1',   'staff123',   'staff'),
                    ('student1', 'student123', 'student'),
                ]
                cursor.executemany(
                    "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                    default_users
                )
                print("✓ Default users created:")
                print("    admin    / admin123   [admin]")
                print("    staff1   / staff123   [staff]")
                print("    student1 / student123 [student]")

    def seed_default_mess_menu(self):
        """Populate mess_menu with a default weekly schedule if it is currently empty."""
        from utils.constants import DEFAULT_MESS_MENU
        with self.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS cnt FROM mess_menu")
            if cursor.fetchone()['cnt'] > 0:
                return  # already seeded
            cursor.executemany(
                "INSERT INTO mess_menu (day, meal, items) VALUES (%s, %s, %s)",
                DEFAULT_MESS_MENU
            )
            print("✓ Default weekly mess menu seeded")

    # ── Mess Menu (weekly schedule) ──────────────────────────────────────────

    def get_all_mess_menu(self):
        """Return all mess_menu rows ordered by canonical day/meal."""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, day, meal, items
                FROM mess_menu
                ORDER BY
                  FIELD(day,'Monday','Tuesday','Wednesday',
                            'Thursday','Friday','Saturday','Sunday'),
                  FIELD(meal,'Breakfast','Lunch','Dinner')
            """)
            return cursor.fetchall()

    def add_mess_menu_item(self, day: str, meal: str, items: str):
        """Add a single entry to the weekly mess menu."""
        with self.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO mess_menu (day, meal, items) VALUES (%s, %s, %s)",
                (day, meal, items)
            )

    def delete_mess_menu_item(self, item_id: int):
        """Delete a mess_menu entry by id."""
        with self.get_cursor() as cursor:
            cursor.execute("DELETE FROM mess_menu WHERE id = %s", (item_id,))

    # ── Data-integrity helpers ────────────────────────────────────────────────

    def check_room_exists(self, room_no: str) -> bool:
        """Return True if room_no is in the rooms table."""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT 1 FROM rooms WHERE room_no = %s", (room_no,))
            return cursor.fetchone() is not None

    def check_student_exists(self, reg_no: str) -> bool:
        """Return True if a student with this reg_no already exists."""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT 1 FROM students WHERE reg_no = %s", (reg_no,))
            return cursor.fetchone() is not None

    def check_room_has_students(self, room_no: str) -> bool:
        """Return True if any student is assigned to room_no."""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM students WHERE room_no = %s LIMIT 1", (room_no,)
            )
            return cursor.fetchone() is not None

    def get_room_student_count(self, room_no: str) -> int:
        """Return the number of students currently assigned to room_no."""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) AS cnt FROM students WHERE room_no = %s",
                (room_no,)
            )
            return cursor.fetchone()['cnt']

    def get_available_rooms(self):
        """Return all rooms whose status is 'Available' (not full, not maintenance)."""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT room_no FROM rooms WHERE status = 'Available' ORDER BY room_no"
            )
            return [r['room_no'] for r in cursor.fetchall()]

    # ── Student operations (Schema: reg_no, name, address, contact, room_no) ──

    def add_student(self, reg_no, name, address, contact, room_no):
        """
        Add a new student.
        - Raises ValueError for duplicate reg_no or non-existent room.
        - Raises ValueError if the room is under Maintenance.
        - Raises ValueError if the room is already at full capacity (4 students).
        - Automatically marks the room 'Occupied' when the 4th student is added.
        """
        from utils.constants import ROOM_CAPACITY
        if self.check_student_exists(reg_no):
            raise ValueError(f"Student with reg_no '{reg_no}' already exists.")
        if not self.check_room_exists(room_no):
            raise ValueError(f"Room '{room_no}' does not exist. Please add the room first.")
        # block Maintenance rooms
        room_status = self.get_room_status(room_no)
        if room_status and room_status.get('status') == 'Maintenance':
            raise ValueError(f"Room '{room_no}' is under Maintenance and cannot accept students.")
        # check capacity
        current_count = self.get_room_student_count(room_no)
        if current_count >= ROOM_CAPACITY:
            raise ValueError(
                f"Room '{room_no}' is already full ({ROOM_CAPACITY}/{ROOM_CAPACITY} students)."
            )
        with self.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO students (reg_no, name, address, contact, room_no) "
                "VALUES (%s, %s, %s, %s, %s)",
                (reg_no, name, address, contact, room_no)
            )
            row_id = cursor.lastrowid
        # mark Occupied when room reaches capacity
        if current_count + 1 >= ROOM_CAPACITY:
            self.update_room_status(room_no, 'Occupied')
        return row_id

    def get_all_students(self):
        """Retrieve all students"""
        with self.get_cursor() as cursor:
            query = "SELECT * FROM students ORDER BY name"
            cursor.execute(query)
            return cursor.fetchall()

    def get_student_by_reg_no(self, reg_no):
        """Get student by registration number"""
        with self.get_cursor() as cursor:
            query = "SELECT * FROM students WHERE reg_no = %s"
            cursor.execute(query, (reg_no,))
            return cursor.fetchone()

    def update_student(self, reg_no, **kwargs):
        """Update student details"""
        with self.get_cursor() as cursor:
            allowed_fields = ['name', 'address', 'contact', 'room_no']
            updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not updates:
                return False
            
            set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
            query = f"UPDATE students SET {set_clause} WHERE reg_no = %s"
            cursor.execute(query, list(updates.values()) + [reg_no])
            return cursor.rowcount > 0

    def delete_student(self, reg_no):
        """
        Delete a student.
        - Reverts room to 'Available' when count drops below capacity.
        - Reverts room to 'Available' when no students remain.
        """
        from utils.constants import ROOM_CAPACITY
        student = self.get_student_by_reg_no(reg_no)
        with self.get_cursor() as cursor:
            cursor.execute("DELETE FROM students WHERE reg_no = %s", (reg_no,))
            deleted = cursor.rowcount > 0
        if deleted and student:
            room_no = student.get('room_no')
            if room_no:
                remaining = self.get_room_student_count(room_no)
                if remaining < ROOM_CAPACITY:
                    self.update_room_status(room_no, 'Available')
        return deleted

    # ── Room operations (Schema: room_no, status) ─────────────────────────────

    def add_room(self, room_no):
        """Add new room – raises ValueError if room_no already exists."""
        if self.check_room_exists(room_no):
            raise ValueError(f"Room '{room_no}' already exists.")
        with self.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO rooms (room_no, status) VALUES (%s, 'Available')",
                (room_no,)
            )

    def get_all_rooms(self):
        """Retrieve all rooms"""
        with self.get_cursor() as cursor:
            query = "SELECT * FROM rooms ORDER BY room_no"
            cursor.execute(query)
            return cursor.fetchall()

    def get_room_status(self, room_no):
        """Get room status"""
        with self.get_cursor() as cursor:
            query = "SELECT status FROM rooms WHERE room_no = %s"
            cursor.execute(query, (room_no,))
            return cursor.fetchone()

    def update_room_status(self, room_no, status):
        """Update room status"""
        with self.get_cursor() as cursor:
            query = "UPDATE rooms SET status = %s WHERE room_no = %s"
            cursor.execute(query, (status, room_no))

    def delete_room(self, room_no):
        """Delete room – raises ValueError if students are still assigned."""
        if self.check_room_has_students(room_no):
            raise ValueError(
                f"Cannot delete room '{room_no}': students are still assigned to it."
            )
        with self.get_cursor() as cursor:
            cursor.execute("DELETE FROM rooms WHERE room_no = %s", (room_no,))

    # Staff operations (Schema: id, name, role, contact)
    def add_staff(self, name, role, contact):
        """Add new staff member"""
        with self.get_cursor() as cursor:
            query = """
                INSERT INTO staff (name, role, contact)
                VALUES (%s, %s, %s)
            """
            cursor.execute(query, (name, role, contact))

    def get_all_staff(self):
        """Retrieve all staff"""
        with self.get_cursor() as cursor:
            query = "SELECT * FROM staff ORDER BY name"
            cursor.execute(query)
            return cursor.fetchall()

    def update_staff(self, staff_id, **kwargs):
        """Update staff details"""
        with self.get_cursor() as cursor:
            allowed_fields = ['name', 'role', 'contact']
            updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not updates:
                return False
            
            set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
            query = f"UPDATE staff SET {set_clause} WHERE id = %s"
            cursor.execute(query, list(updates.values()) + [staff_id])
            return cursor.rowcount > 0

    def delete_staff(self, staff_id):
        """Delete staff member"""
        with self.get_cursor() as cursor:
            query = "DELETE FROM staff WHERE id = %s"
            cursor.execute(query, (staff_id,))

    # Mess operations (Schema: id, item)
    def add_mess_item(self, item):
        """Add mess item"""
        with self.get_cursor() as cursor:
            query = """
                INSERT INTO mess (item)
                VALUES (%s)
            """
            cursor.execute(query, (item,))

    def get_all_mess_items(self):
        """Retrieve all mess items"""
        with self.get_cursor() as cursor:
            query = "SELECT * FROM mess ORDER BY item"
            cursor.execute(query)
            return cursor.fetchall()

    def delete_mess_item(self, item_id):
        """Delete mess item"""
        with self.get_cursor() as cursor:
            query = "DELETE FROM mess WHERE id = %s"
            cursor.execute(query, (item_id,))

    # Payment operations (Schema: id, student, amount, date, status)
    def add_payment(self, student, amount, status='Paid'):
        """Add payment record"""
        if status not in ('Paid', 'Failed'):
            raise ValueError("status must be 'Paid' or 'Failed'")
        with self.get_cursor() as cursor:
            query = """
                INSERT INTO payments (student, amount, date, status)
                VALUES (%s, %s, CURDATE(), %s)
            """
            cursor.execute(query, (student, amount, status))

    def get_all_payments(self):
        """Retrieve all payments"""
        with self.get_cursor() as cursor:
            query = """
                SELECT * FROM payments 
                ORDER BY date DESC
            """
            cursor.execute(query)
            return cursor.fetchall()

    def get_student_payments(self, student):
        """Get payments for specific student"""
        with self.get_cursor() as cursor:
            query = """
                SELECT * FROM payments 
                WHERE student = %s 
                ORDER BY date DESC
            """
            cursor.execute(query, (student,))
            return cursor.fetchall()

    def delete_payment(self, payment_id):
        """Delete payment record"""
        with self.get_cursor() as cursor:
            query = "DELETE FROM payments WHERE id = %s"
            cursor.execute(query, (payment_id,))

    # Visitor operations (Schema: id, name, contact, date, purpose)
    def add_visitor(self, name, contact, date, purpose):
        """Add visitor record"""
        with self.get_cursor() as cursor:
            query = """
                INSERT INTO visitors (name, contact, date, purpose)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (name, contact, date, purpose))

    def get_all_visitors(self):
        """Retrieve all visitors"""
        with self.get_cursor() as cursor:
            query = """
                SELECT * FROM visitors 
                ORDER BY date DESC
            """
            cursor.execute(query)
            return cursor.fetchall()

    def delete_visitor(self, visitor_id):
        """Delete visitor record"""
        with self.get_cursor() as cursor:
            query = "DELETE FROM visitors WHERE id = %s"
            cursor.execute(query, (visitor_id,))

    # Complaint operations (Schema: id, student, room_no, complaint, date, status)
    def add_complaint(self, student, room_no, complaint):
        """Add complaint"""
        with self.get_cursor() as cursor:
            query = """
                INSERT INTO complaints (student, room_no, complaint, date, status)
                VALUES (%s, %s, %s, CURDATE(), 'Pending')
            """
            cursor.execute(query, (student, room_no, complaint))

    def get_all_complaints(self):
        """Retrieve all complaints"""
        with self.get_cursor() as cursor:
            query = """
                SELECT * FROM complaints 
                ORDER BY date DESC
            """
            cursor.execute(query)
            return cursor.fetchall()

    def update_complaint_status(self, complaint_id, status):
        """Update complaint status"""
        with self.get_cursor() as cursor:
            query = """
                UPDATE complaints 
                SET status = %s 
                WHERE id = %s
            """
            cursor.execute(query, (status, complaint_id))

    def delete_complaint(self, complaint_id):
        """Delete complaint"""
        with self.get_cursor() as cursor:
            query = "DELETE FROM complaints WHERE id = %s"
            cursor.execute(query, (complaint_id,))

    # User authentication
    def add_user(self, username, password, role='user'):
        """Add user account"""
        with self.get_cursor() as cursor:
            query = """
                INSERT INTO users (username, password, role)
                VALUES (%s, %s, %s)
            """
            cursor.execute(query, (username, password, role))

    def verify_user(self, username, password):
        """Verify user credentials"""
        with self.get_cursor() as cursor:
            query = "SELECT * FROM users WHERE username = %s AND password = %s"
            cursor.execute(query, (username, password))
            return cursor.fetchone()

    def get_user_by_username(self, username):
        """Get user by username"""
        with self.get_cursor() as cursor:
            query = "SELECT * FROM users WHERE username = %s"
            cursor.execute(query, (username,))
            return cursor.fetchone()
