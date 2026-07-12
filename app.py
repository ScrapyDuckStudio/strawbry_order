import re
import io
import streamlit as st
import qrcode
from database import (
    init_db, verify_user, get_all_users, change_password,
    get_full_order, get_all_full_orders,
    save_order, submit_order, reset_all_orders, reset_apt_order,
    mark_delivered, get_token_for_apt, verify_token,
    PRODUCTS, APARTMENTS, PAYMENT_METHODS, TIME_SLOTS,
    DELIVERY_START, DELIVERY_END,
)

init_db()

st.set_page_config(page_title="Strawberry Orders", page_icon="🍓", layout="centered")

# ── GLOBAL CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* background */
[data-testid="stAppViewContainer"], section[data-testid="stMain"] {
    background: linear-gradient(160deg, #1a0005 0%, #2d0010 35%, #1a0a00 70%, #0d0000 100%) fixed !important;
    color: #f0d0d5 !important;
}
[data-testid="stHeader"] {
    background: rgba(26,0,5,0.9) !important;
    backdrop-filter: blur(10px);
}

/* scrollbar */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #1a0005; }
::-webkit-scrollbar-thumb { background: #8b1a2a; border-radius: 4px; }

/* headings */
h1, h2, h3 { color: #ff8fa3 !important; }

/* inputs */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {
    background: rgba(255,100,120,0.07) !important;
    color: #f0d0d5 !important;
    border: 1px solid rgba(255,100,120,0.25) !important;
    border-radius: 10px !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus {
    border-color: #e05070 !important;
    box-shadow: 0 0 0 2px rgba(224,80,112,0.2) !important;
}

/* labels */
label, [data-testid="stWidgetLabel"] { color: #d0a0a8 !important; }

/* radio */
[data-testid="stRadio"] label { color: #d0a0a8 !important; }

/* metrics */
[data-testid="stMetricLabel"] { color: #c08090 !important; }
[data-testid="stMetricValue"] { color: #ff8fa3 !important; }

/* divider */
hr { border-color: rgba(255,100,120,0.15) !important; }

/* tabs */
button[data-baseweb="tab"] { color: #906070 !important; background: transparent !important; }
button[data-baseweb="tab"][aria-selected="true"] {
    color: #ff8fa3 !important;
    border-bottom: 2px solid #e05070 !important;
}
[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1px solid rgba(255,100,120,0.2) !important;
}

/* expander */
details {
    background: rgba(255,80,100,0.05) !important;
    border: 1px solid rgba(255,100,120,0.15) !important;
    border-radius: 12px !important;
}
details summary { color: #c08090 !important; }
details summary:hover { color: #ff8fa3 !important; }

/* caption */
[data-testid="stCaptionContainer"] p { color: #906070 !important; }

/* primary button */
[data-testid="stButton"] button[kind="primary"] {
    background: linear-gradient(135deg, #8b1a2a 0%, #c0392b 50%, #e05070 100%) !important;
    border: none !important;
    color: #fff !important;
    font-weight: 700 !important;
    border-radius: 12px !important;
    letter-spacing: .4px;
}
[data-testid="stButton"] button[kind="primary"]:hover {
    background: linear-gradient(135deg, #a02030 0%, #d04040 100%) !important;
}

/* secondary button */
[data-testid="stButton"] button[kind="secondary"] {
    background: rgba(255,80,100,0.08) !important;
    border: 1px solid rgba(255,100,120,0.3) !important;
    color: #d0a0a8 !important;
    border-radius: 12px !important;
}

/* alerts */
[data-testid="stAlert"] {
    background: rgba(255,80,100,0.08) !important;
    border: 1px solid rgba(255,100,120,0.2) !important;
    border-radius: 12px !important;
}

/* markdown tables */
table { color: #d0a0a8 !important; }
th { color: #ff8fa3 !important; border-bottom: 1px solid rgba(255,100,120,0.3) !important; }
td { border-bottom: 1px solid rgba(255,100,120,0.1) !important; }

/* code */
code { background: rgba(255,80,100,0.12) !important; color: #ffb0c0 !important; border-radius: 4px !important; }

/* ── ORDER CARD ── */
.ocard {
    background: linear-gradient(135deg, rgba(139,26,42,0.35) 0%, rgba(30,5,10,0.95) 100%);
    border-radius: 18px;
    padding: 1.5rem 1.8rem 1.2rem 1.8rem;
    border: 1px solid rgba(224,80,112,0.3);
    border-left: 5px solid #e05070;
    box-shadow: 0 6px 32px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,150,170,0.08);
    margin-bottom: .5rem;
}
.ocard.delivered {
    background: linear-gradient(135deg, rgba(20,80,40,0.35) 0%, rgba(5,20,10,0.95) 100%);
    border-color: rgba(46,204,113,0.3);
    border-left-color: #27ae60;
}
.ocard h3 {
    margin: 0 0 .15rem 0;
    font-size: 1.35rem;
    color: #ff8fa3;
    font-weight: 700;
}
.ocard.delivered h3 { color: #2ecc71; }
.ocard .ts { font-size: .82rem; color: #704050; margin-bottom: .9rem; }
.ocard .row { font-size: 1rem; margin: .4rem 0; color: #d0a0a8; }
.ocard .row b { color: #f0d0d5; }
.ocard .tot {
    font-size: 1.35rem; font-weight: 800;
    color: #ff8fa3; margin-top: .9rem;
}
.ocard.delivered .tot { color: #2ecc71; }
.badge-delivered {
    display: inline-block;
    background: linear-gradient(135deg, #145028, #27ae60);
    color: #fff; font-size: .75rem; font-weight: 700;
    letter-spacing: 1.5px; text-transform: uppercase;
    padding: .2rem .7rem; border-radius: 20px; margin-bottom: .6rem;
}

/* ── STATUS CARD (admin empty/draft) ── */
.scard {
    border-radius: 14px;
    padding: 1rem 1.5rem;
    margin-bottom: .6rem;
    border-left: 5px solid #555;
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.05);
    border-left: 5px solid #3a2030;
}
.scard.draft {
    background: rgba(243,156,18,0.07);
    border-color: rgba(243,156,18,0.15);
    border-left-color: #f39c12;
}
.scard h4 { margin: 0; font-size: 1.1rem; color: #d0a0a8; }
.scard .st { font-size: .85rem; color: #705060; margin-top: .15rem; }

/* ── SUMMARY BOX ── */
.sumbox {
    background: linear-gradient(135deg, rgba(139,26,42,0.3), rgba(10,2,5,0.97));
    border-radius: 18px;
    padding: 1.5rem 2rem;
    margin-top: 1.4rem;
    border: 1px solid rgba(224,80,112,0.35);
    box-shadow: 0 4px 28px rgba(139,26,42,0.3);
}
.sumbox h3 { margin: 0 0 .7rem 0; color: #ff8fa3; font-size: 1.3rem; }
.sumbox .srow { font-size: 1.05rem; color: #d0a0a8; margin: .3rem 0; }
.sumbox .srow b { color: #f0d0d5; }
.sumbox .stot {
    font-size: 2rem; font-weight: 800; margin-top: .8rem;
    background: linear-gradient(90deg, #ff8fa3, #e05070);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
</style>
""", unsafe_allow_html=True)

# ── SESSION ───────────────────────────────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None

# ── HELPERS ───────────────────────────────────────────────────────────────────
def logout():
    st.session_state.user = None
    st.query_params.clear()
    st.rerun()

def get_base_url():
    try:
        return st.context.url.split("?")[0].rstrip("/")
    except Exception:
        return "http://localhost:8501"

def make_qr_bytes(url):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H,
                       box_size=8, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#8b1a2a", back_color="#fff5f5")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def order_has_items(o):
    return any(o["lines"][p]["quantity"] > 0 for p in PRODUCTS)

def validate_time(raw):
    """Returns (time_str, error_str). One of them is None."""
    raw = raw.strip()
    if not re.fullmatch(r"\d{1,2}:\d{2}", raw):
        return None, "Use HH:MM format, e.g. 09:15"
    h, m = map(int, raw.split(":"))
    if not (DELIVERY_START <= h <= DELIVERY_END and 0 <= m <= 59):
        return None, f"Must be between {DELIVERY_START:02d}:00 and {DELIVERY_END:02d}:00"
    if h == DELIVERY_END and m > 0:
        return None, f"Latest delivery is {DELIVERY_END:02d}:00"
    return f"{h:02d}:{m:02d}", None

preselect_apt = st.query_params.get("apt", "").upper()
qr_token      = st.query_params.get("token", "")

# Auto-login via QR token — no password needed
if st.session_state.user is None and qr_token:
    token_user = verify_token(qr_token)
    if token_user:
        st.session_state.user = token_user
        st.query_params.clear()


# ╔══════════════════════════════════════════════════════════════╗
# ║  SHARED ORDER CARD                                           ║
# ╚══════════════════════════════════════════════════════════════╝
def render_order_card(o, show_ts=True):
    qty   = o["lines"]["strawberries"]["quantity"]
    total = o["total_nok"]
    t     = o["delivery_time"] or "—"
    pay   = o["payment_method"] or "—"

    css   = "ocard delivered" if o.get("delivered") else "ocard"
    ts    = ""
    if show_ts and o.get("submitted_at"):
        ts = f'<p class="ts">Submitted: {o["submitted_at"]}</p>'
    badge = '<span class="badge-delivered">&#10003; Delivered</span>' if o.get("delivered") else ""
    del_ts = f'<p class="ts">Delivered: {o["delivered_at"]}</p>' if o.get("delivered_at") else ""

    st.markdown(f"""
<div class="{css}">
  <h3>&#127968; Apartment {o['apt_name']}</h3>
  {ts}{badge}{del_ts}
  <p class="row">&#127827; Strawberries 400g &nbsp;&times;&nbsp; <b>{qty}</b></p>
  <p class="row">&#128336; Delivery: <b>{t}</b></p>
  <p class="row">&#128179; Payment: <b>{pay}</b></p>
  <p class="tot">Total: {total:.0f} NOK</p>
</div>
""", unsafe_allow_html=True)


# ╔══════════════════════════════════════════════════════════════╗
# ║  LOGIN                                                       ║
# ╚══════════════════════════════════════════════════════════════╝
def show_login():
    st.markdown("# &#127827; Strawberry Orders")
    st.caption("Sign in to place or view orders")
    st.write("")

    apt_usernames = list(APARTMENTS.values())
    if preselect_apt in apt_usernames:
        st.info(f"&#127968; Apartment **{preselect_apt}** — enter your PIN below")

    with st.form("login_form"):
        default  = preselect_apt if preselect_apt in apt_usernames else ""
        username = st.text_input("Username", value=default,
                                  placeholder="A1  B2  C3  D4  admin")
        password = st.text_input("PIN / Password", type="password")
        ok = st.form_submit_button("Sign in", use_container_width=True)

    if ok:
        user = verify_user(username.strip(), password.strip())
        if user:
            st.session_state.user = user
            st.query_params.clear()
            st.rerun()
        else:
            st.error("Wrong username or password.")

    with st.expander("Default accounts"):
        st.markdown("""
| Username | Password | Role |
|---|---|---|
| `superadmin` | `superadmin123` | Full control |
| `admin` | `admin123` | View orders |
| `A1` | `1111` | Apartment A1 |
| `B2` | `2222` | Apartment B2 |
| `C3` | `3333` | Apartment C3 |
| `D4` | `4444` | Apartment D4 |
""")


# ╔══════════════════════════════════════════════════════════════╗
# ║  TENANT                                                      ║
# ╚══════════════════════════════════════════════════════════════╝
def show_tenant(user):
    apt_id   = user["apt_id"]
    apt_name = APARTMENTS[apt_id]
    order    = get_full_order(apt_id)

    c1, c2 = st.columns([5, 1])
    with c1:
        st.markdown(f"# &#127968; Apartment {apt_name}")
    with c2:
        st.write("")
        if st.button("Log out", key="t_logout"):
            logout()

    # Already submitted
    if order["submitted"]:
        # If already delivered → let them place a new order right away
        if order.get("delivered"):
            st.success(f"Your previous order was delivered at **{order.get('delivered_at', '')}**. You can place a new one below.")
            reset_apt_order(apt_id)
            st.rerun()

        st.success("Your order has been submitted!")
        render_order_card(order)
        st.write("")
        if st.button("Edit my order", type="secondary", use_container_width=True):
            reset_apt_order(apt_id)
            st.rerun()
        return

    st.divider()

    # Quantity
    st.markdown("### &#127827; Strawberries 400g — 60 NOK each")
    c_qty, c_price = st.columns([1, 2])
    with c_qty:
        qty = st.number_input("Baskets", min_value=0, max_value=50,
                              value=order["lines"]["strawberries"]["quantity"],
                              step=1, label_visibility="collapsed")
    with c_price:
        if qty > 0:
            st.markdown(
                f"<p style='padding-top:.5rem;font-size:1.1rem;color:#d0a0a8'>"
                f"<b style='color:#f0d0d5'>{qty}</b> &times; 60 = "
                f"<b style='color:#ff8fa3;font-size:1.2rem'>{qty*60} NOK</b></p>",
                unsafe_allow_html=True
            )

    st.divider()

    # Delivery time — slot picker
    st.markdown("### &#128336; Delivery time")
    saved_time    = order["delivery_time"] or TIME_SLOTS[0]
    slot_idx      = TIME_SLOTS.index(saved_time) if saved_time in TIME_SLOTS else 0
    delivery_time = st.radio(
        "Delivery slot", options=TIME_SLOTS, index=slot_idx,
        label_visibility="collapsed"
    )
    time_err = None

    st.divider()

    # Payment
    st.markdown("### &#128179; Payment method")
    saved_pay = order["payment_method"] or PAYMENT_METHODS[0]
    pay_idx   = PAYMENT_METHODS.index(saved_pay) if saved_pay in PAYMENT_METHODS else 0
    payment   = st.radio("Pay", PAYMENT_METHODS, index=pay_idx,
                         horizontal=True, label_visibility="collapsed")

    st.divider()

    # Total + actions
    c_tot, c_save, c_sub = st.columns([2, 1, 1])
    with c_tot:
        st.metric("Total", f"{qty * 60} NOK")
    with c_save:
        if st.button("Save draft", use_container_width=True):
            if time_err:
                st.warning("Fix the time first.")
            else:
                save_order(apt_id, {"strawberries": qty}, delivery_time, payment)
                st.success("Saved!")
                st.rerun()
    with c_sub:
        if st.button("Submit order", type="primary", use_container_width=True):
            if qty == 0:
                st.warning("Add at least 1 basket.")
            elif time_err:
                st.warning("Fix the time first.")
            else:
                save_order(apt_id, {"strawberries": qty}, delivery_time, payment)
                submit_order(apt_id)
                st.success("Order submitted!")
                st.rerun()


# ╔══════════════════════════════════════════════════════════════╗
# ║  ADMIN  (read-only + mark delivered)                         ║
# ╚══════════════════════════════════════════════════════════════╝
def show_admin(user):
    c1, c2 = st.columns([5, 1])
    with c1:
        st.markdown("# &#127827; Today's Orders")
    with c2:
        st.write("")
        if st.button("Log out", key="a_logout"):
            logout()

    orders    = get_all_full_orders()
    submitted = [o for o in orders if o["submitted"]]
    delivered = [o for o in submitted if o.get("delivered")]
    active    = [o for o in submitted if not o.get("delivered")]
    drafts    = [o for o in orders if not o["submitted"] and order_has_items(o)]
    empty     = [o for o in orders if not o["submitted"] and not order_has_items(o)]

    # tab badge counts
    active_label    = f"&#128666; To deliver ({len(active)})" if active else "&#128666; To deliver"
    delivered_label = f"&#9989; Delivered ({len(delivered)})" if delivered else "&#9989; Delivered"

    tab_active, tab_delivered = st.tabs([active_label, delivered_label])

    # ── TAB 1: active (submitted, not yet delivered) ───────────────────────
    with tab_active:
        if active:
            for o in active:
                render_order_card(o)
                if st.button(f"Mark as delivered — {o['apt_name']}",
                             key=f"dlv_{o['apt_id']}", type="primary",
                             use_container_width=True):
                    mark_delivered(o["apt_id"])
                    st.rerun()
                st.write("")
        else:
            st.markdown(
                '<div class="scard"><h4 style="color:#704050;text-align:center;padding:.5rem 0">No orders yet</h4></div>',
                unsafe_allow_html=True
            )

        # drafts below active orders
        for o in drafts:
            st.markdown(
                f'<div class="scard draft">'
                f'<h4>&#128203; Apartment {o["apt_name"]}</h4>'
                f'<p class="st">Draft — not submitted yet</p></div>',
                unsafe_allow_html=True
            )
        if drafts:
            st.warning(f"{len(drafts)} apartment(s) saved a draft but haven't submitted.")

        # summary for active tab
        if active:
            total_baskets = sum(o["lines"]["strawberries"]["quantity"] for o in active)
            total_nok     = sum(o["total_nok"] for o in active)
            total_g       = total_baskets * 400
            st.markdown(f"""
<div class="sumbox">
  <h3>&#129534; Still to collect</h3>
  <p class="srow">&#127827; <b>{total_baskets} baskets</b> &nbsp;&mdash;&nbsp; {total_g} g</p>
  <p class="stot">{total_nok:.0f} NOK</p>
  <p style="color:#704050;font-size:.85rem">from {len(active)} apartment(s)</p>
</div>
""", unsafe_allow_html=True)

    # ── TAB 2: delivered ───────────────────────────────────────────────────
    with tab_delivered:
        if delivered:
            for o in delivered:
                render_order_card(o)
                st.write("")

            total_baskets = sum(o["lines"]["strawberries"]["quantity"] for o in delivered)
            total_nok     = sum(o["total_nok"] for o in delivered)
            total_g       = total_baskets * 400
            st.markdown(f"""
<div class="sumbox">
  <h3>&#9989; Delivered today</h3>
  <p class="srow">&#127827; <b>{total_baskets} baskets</b> &nbsp;&mdash;&nbsp; {total_g} g</p>
  <p class="stot">{total_nok:.0f} NOK</p>
  <p style="color:#704050;font-size:.85rem">from {len(delivered)} apartment(s)</p>
</div>
""", unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="scard"><h4 style="color:#704050;text-align:center;padding:.5rem 0">No deliveries yet</h4></div>',
                unsafe_allow_html=True
            )


# ╔══════════════════════════════════════════════════════════════╗
# ║  SUPERADMIN                                                  ║
# ╚══════════════════════════════════════════════════════════════╝
def show_superadmin(user):
    c1, c2 = st.columns([5, 1])
    with c1:
        st.markdown("# &#9881;&#65039; Super Admin")
    with c2:
        st.write("")
        if st.button("Log out", key="sa_logout"):
            logout()

    tab_orders, tab_qr, tab_pwd = st.tabs(["Orders", "QR Codes", "Passwords"])

    with tab_orders:
        orders    = get_all_full_orders()
        submitted = [o for o in orders if o["submitted"]]
        drafts    = [o for o in orders if not o["submitted"] and order_has_items(o)]

        if submitted:
            st.subheader("Submitted")
            for o in submitted:
                render_order_card(o)
                if st.button(f"Reset {o['apt_name']}", key=f"rs_{o['apt_id']}"):
                    reset_apt_order(o["apt_id"])
                    st.rerun()
                st.write("")

        if drafts:
            st.subheader("Drafts")
            for o in drafts:
                render_order_card(o, show_ts=False)
                if st.button(f"Reset {o['apt_name']}", key=f"rd_{o['apt_id']}"):
                    reset_apt_order(o["apt_id"])
                    st.rerun()
                st.write("")

        if not submitted and not drafts:
            st.info("No orders yet.")

        if submitted:
            total_b = sum(o["lines"]["strawberries"]["quantity"] for o in submitted)
            total_n = sum(o["total_nok"] for o in submitted)
            st.divider()
            col1, col2 = st.columns(2)
            col1.metric("Total baskets", total_b)
            col2.metric("Total NOK", f"{total_n:.0f}")

        st.divider()
        if st.button("Reset ALL orders", type="secondary", use_container_width=True):
            reset_all_orders()
            st.success("All orders reset.")
            st.rerun()

    with tab_qr:
        st.subheader("QR Codes")
        st.caption("Scan → logged in automatically. No password needed. Print and stick on each door.")
        base_url = get_base_url()
        cols = st.columns(4)
        for apt_id, apt_name in APARTMENTS.items():
            token    = get_token_for_apt(apt_id)
            url      = f"{base_url}/?token={token}"
            qr_bytes = make_qr_bytes(url)
            with cols[apt_id - 1]:
                st.image(qr_bytes, caption=f"Apt {apt_name}", use_container_width=True)
                st.download_button(f"Download {apt_name}", data=qr_bytes,
                                   file_name=f"qr_{apt_name}.png", mime="image/png",
                                   key=f"dl_{apt_id}", use_container_width=True)
        with st.expander("Direct links"):
            for apt_id, apt_name in APARTMENTS.items():
                token = get_token_for_apt(apt_id)
                st.code(f"{base_url}/?token={token}")

    with tab_pwd:
        st.subheader("Change Passwords")
        users = get_all_users()
        with st.form("pwd_form"):
            st.caption("Leave blank to keep current password.")
            new_pwds = {}
            cols = st.columns(2)
            for i, u in enumerate(users):
                label = {"superadmin": "Superadmin", "admin": "Admin (viewer)"}.get(
                    u["role"], f"Apartment {u['username']}"
                )
                with cols[i % 2]:
                    new_pwds[u["username"]] = st.text_input(
                        label, type="password", placeholder="New password",
                        key=f"npwd_{u['username']}"
                    )
            if st.form_submit_button("Save passwords", use_container_width=True):
                changed = sum(1 for u, p in new_pwds.items()
                              if p.strip() and not change_password(u, p.strip()))
                if changed:
                    st.success(f"Updated {changed} password(s).")
                else:
                    st.warning("Nothing changed — all fields blank.")


# ── ROUTER ────────────────────────────────────────────────────────────────────
u = st.session_state.user
if u is None:
    show_login()
elif u["role"] == "superadmin":
    show_superadmin(u)
elif u["role"] == "admin":
    show_admin(u)
else:
    show_tenant(u)
