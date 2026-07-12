import sqlite3
import hashlib
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "strawberry.db")

# All possible products — admin toggles which are available today
ALL_PRODUCTS = {
    "strawberries": {"label": "Strawberries 400g", "emoji": "🍓", "price": 60},
    "apples":       {"label": "Apples 1kg",         "emoji": "🍎", "price": 60},
    "honey":        {"label": "Honey 500g",          "emoji": "🍯", "price": 60},
    "juice":        {"label": "Juice 1L",            "emoji": "🧃", "price": 60},
}

# Legacy alias — code that imports PRODUCTS still works
PRODUCTS = ALL_PRODUCTS

APARTMENTS = {1: "A1", 2: "B2", 3: "C3", 4: "D4"}

PAYMENT_METHODS = ["Cash", "Vipps", "Card"]

TIME_SLOTS = [
    "ASAP",
    "06:00 – 08:00",
    "08:00 – 10:00",
    "10:00 – 12:00",
    "12:00 – 14:00",
    "14:00 – 16:00",
    "16:00 – 18:00",
    "18:00 – 20:00",
]

DELIVERY_START = 6
DELIVERY_END   = 20


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    conn = get_conn()
    cur  = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    UNIQUE NOT NULL,
            password TEXT    NOT NULL,
            role     TEXT    NOT NULL CHECK(role IN ('superadmin','admin','tenant')),
            apt_id   INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS order_headers (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            apt_id         INTEGER NOT NULL,
            apt_name       TEXT    NOT NULL,
            delivery_time  TEXT,
            payment_method TEXT,
            submitted      INTEGER NOT NULL DEFAULT 0,
            submitted_at   TEXT,
            delivered      INTEGER NOT NULL DEFAULT 0,
            delivered_at   TEXT,
            total_nok      REAL    NOT NULL DEFAULT 0,
            UNIQUE(apt_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS order_lines (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            header_id  INTEGER NOT NULL REFERENCES order_headers(id) ON DELETE CASCADE,
            product    TEXT    NOT NULL,
            quantity   INTEGER NOT NULL DEFAULT 0,
            price_each REAL    NOT NULL DEFAULT 60,
            UNIQUE(header_id, product)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS qr_tokens (
            token  TEXT    PRIMARY KEY,
            apt_id INTEGER NOT NULL UNIQUE
        )
    """)

    # available_products: which products admin has toggled ON today
    cur.execute("""
        CREATE TABLE IF NOT EXISTS available_products (
            product  TEXT PRIMARY KEY,
            enabled  INTEGER NOT NULL DEFAULT 0
        )
    """)

    # Migrations
    existing = [r[1] for r in cur.execute("PRAGMA table_info(order_headers)").fetchall()]
    if "delivered"    not in existing:
        cur.execute("ALTER TABLE order_headers ADD COLUMN delivered INTEGER NOT NULL DEFAULT 0")
    if "delivered_at" not in existing:
        cur.execute("ALTER TABLE order_headers ADD COLUMN delivered_at TEXT")

    # Seed users
    for username, pwd, role, apt_id in [
        ("superadmin", hash_password("superadmin123"), "superadmin", None),
        ("admin",      hash_password("admin123"),      "admin",      None),
        ("A1",         hash_password("1111"),           "tenant",     1),
        ("B2",         hash_password("2222"),           "tenant",     2),
        ("C3",         hash_password("3333"),           "tenant",     3),
        ("D4",         hash_password("4444"),           "tenant",     4),
    ]:
        cur.execute(
            "INSERT OR IGNORE INTO users (username,password,role,apt_id) VALUES(?,?,?,?)",
            (username, pwd, role, apt_id)
        )

    # Seed order headers + lines for all products
    for apt_id, apt_name in APARTMENTS.items():
        cur.execute("INSERT OR IGNORE INTO order_headers (apt_id,apt_name) VALUES(?,?)", (apt_id, apt_name))
        cur.execute("SELECT id FROM order_headers WHERE apt_id=?", (apt_id,))
        hid = cur.fetchone()["id"]
        for pid, info in ALL_PRODUCTS.items():
            cur.execute(
                "INSERT OR IGNORE INTO order_lines (header_id,product,quantity,price_each) VALUES(?,?,0,?)",
                (hid, pid, info["price"])
            )

    # Seed available_products (strawberries on by default)
    for pid in ALL_PRODUCTS:
        default_on = 1 if pid == "strawberries" else 0
        cur.execute(
            "INSERT OR IGNORE INTO available_products (product,enabled) VALUES(?,?)",
            (pid, default_on)
        )

    # Seed QR tokens
    import secrets
    for apt_id in APARTMENTS:
        cur.execute("SELECT token FROM qr_tokens WHERE apt_id=?", (apt_id,))
        if not cur.fetchone():
            cur.execute("INSERT INTO qr_tokens (token,apt_id) VALUES(?,?)",
                        (secrets.token_urlsafe(32), apt_id))

    conn.commit()
    conn.close()


# ── Auth ──────────────────────────────────────────────────────────────────────

def verify_user(username: str, password: str):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cur.fetchone()
    conn.close()
    if user and user["password"] == hash_password(password):
        return dict(user)
    return None


def get_all_users():
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT id,username,role,apt_id FROM users ORDER BY id")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def change_password(username: str, new_password: str):
    conn = get_conn()
    conn.execute("UPDATE users SET password=? WHERE username=?",
                 (hash_password(new_password), username))
    conn.commit()
    conn.close()


# ── Available products ────────────────────────────────────────────────────────

def get_available_products() -> list:
    """Return list of enabled product ids."""
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT product FROM available_products WHERE enabled=1")
    rows = [r["product"] for r in cur.fetchall()]
    conn.close()
    return rows


def set_product_available(product: str, enabled: bool):
    conn = get_conn()
    conn.execute("UPDATE available_products SET enabled=? WHERE product=?",
                 (1 if enabled else 0, product))
    conn.commit()
    conn.close()


# ── Orders ────────────────────────────────────────────────────────────────────

def _attach_lines(cur, headers) -> list:
    result = []
    for h in headers:
        h = dict(h)
        cur.execute("SELECT * FROM order_lines WHERE header_id=?", (h["id"],))
        h["lines"] = {r["product"]: dict(r) for r in cur.fetchall()}
        result.append(h)
    return result


def get_full_order(apt_id: int) -> dict:
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM order_headers WHERE apt_id=?", (apt_id,))
    header = cur.fetchone()
    if not header:
        conn.close()
        return None
    result = _attach_lines(cur, [header])[0]
    conn.close()
    return result


def get_all_full_orders() -> list:
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM order_headers ORDER BY apt_id")
    result = _attach_lines(cur, cur.fetchall())
    conn.close()
    return result


def save_order(apt_id: int, lines: dict, delivery_time: str, payment_method: str):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT id FROM order_headers WHERE apt_id=?", (apt_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return
    hid   = row["id"]
    total = 0.0
    for product, qty in lines.items():
        price  = ALL_PRODUCTS[product]["price"]
        total += qty * price
        cur.execute(
            "UPDATE order_lines SET quantity=?,price_each=? WHERE header_id=? AND product=?",
            (qty, price, hid, product)
        )
    cur.execute(
        "UPDATE order_headers SET delivery_time=?,payment_method=?,total_nok=?,submitted=0 WHERE id=?",
        (delivery_time, payment_method, total, hid)
    )
    conn.commit()
    conn.close()


def submit_order(apt_id: int):
    import datetime
    conn = get_conn()
    conn.execute(
        "UPDATE order_headers SET submitted=1,submitted_at=? WHERE apt_id=?",
        (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), apt_id)
    )
    conn.commit()
    conn.close()


def undeliver_order(apt_id: int):
    """Move a delivered order back to active (undo delivery)."""
    conn = get_conn()
    conn.execute(
        "UPDATE order_headers SET delivered=0,delivered_at=NULL WHERE apt_id=?",
        (apt_id,)
    )
    conn.commit()
    conn.close()


def reset_apt_order(apt_id: int):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT id FROM order_headers WHERE apt_id=?", (apt_id,))
    h = cur.fetchone()
    if h:
        cur.execute("UPDATE order_lines SET quantity=0 WHERE header_id=?", (h["id"],))
        cur.execute("""UPDATE order_headers
                       SET delivery_time=NULL,payment_method=NULL,
                           submitted=0,submitted_at=NULL,
                           delivered=0,delivered_at=NULL,total_nok=0
                       WHERE id=?""", (h["id"],))
    conn.commit()
    conn.close()


def reset_all_orders():
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("UPDATE order_lines SET quantity=0")
    cur.execute("""UPDATE order_headers
                   SET delivery_time=NULL,payment_method=NULL,
                       submitted=0,submitted_at=NULL,
                       delivered=0,delivered_at=NULL,total_nok=0""")
    conn.commit()
    conn.close()


def mark_delivered(apt_id: int):
    import datetime
    conn = get_conn()
    conn.execute(
        "UPDATE order_headers SET delivered=1,delivered_at=? WHERE apt_id=?",
        (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), apt_id)
    )
    conn.commit()
    conn.close()


# ── QR tokens ─────────────────────────────────────────────────────────────────

def get_token_for_apt(apt_id: int) -> str:
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT token FROM qr_tokens WHERE apt_id=?", (apt_id,))
    row = cur.fetchone()
    conn.close()
    return row["token"] if row else None


def verify_token(token: str):
    if not token:
        return None
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT apt_id FROM qr_tokens WHERE token=?", (token,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    conn2 = get_conn()
    cur2  = conn2.cursor()
    cur2.execute("SELECT * FROM users WHERE apt_id=? AND role='tenant'", (row["apt_id"],))
    user = cur2.fetchone()
    conn2.close()
    return dict(user) if user else None
