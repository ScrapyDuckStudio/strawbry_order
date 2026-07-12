import io
import time
import streamlit as st
import qrcode
from database import (
    init_db, verify_user, get_all_users, change_password,
    get_full_order, get_all_full_orders,
    save_order, submit_order, reset_all_orders, reset_apt_order,
    mark_delivered, undeliver_order,
    get_token_for_apt, verify_token,
    get_available_products, set_product_available,
    ALL_PRODUCTS, APARTMENTS, PAYMENT_METHODS, TIME_SLOTS,
)

init_db()
st.set_page_config(page_title="Strawberry Orders", page_icon="🍓", layout="centered")

# ── THEME ─────────────────────────────────────────────────────────────────────
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

# ── CSS ───────────────────────────────────────────────────────────────────────
DARK_CSS = """
html, body, [data-testid="stAppViewContainer"], section[data-testid="stMain"] {
    background: linear-gradient(160deg,#1a0005 0%,#2d0010 40%,#150800 100%) fixed !important;
    color: #f0d0d5 !important;
}
[data-testid="stHeader"] {
    background: rgba(26,0,5,0.92) !important;
    border-bottom: 1px solid rgba(255,100,120,0.1);
}
::-webkit-scrollbar-track{background:#1a0005}
::-webkit-scrollbar-thumb{background:#8b1a2a}
h1,h2,h3{ color:#ff8fa3 !important }
label,[data-testid="stWidgetLabel"]{ color:#c08090 !important }
[data-testid="stCaptionContainer"] p{ color:#7a4050 !important }
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {
    background:rgba(255,100,120,0.06) !important; color:#f0d0d5 !important;
    border:1px solid rgba(255,100,120,0.2) !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus{
    border-color:#e05070 !important; box-shadow:0 0 0 3px rgba(224,80,112,0.15) !important;
}
[data-testid="stRadio"] label{ color:#d0a0a8 !important }
[data-testid="stMetricLabel"]{ color:#c08090 !important }
[data-testid="stMetricValue"]{ color:#ff8fa3 !important; font-weight:800 !important }
hr{ border-color:rgba(255,100,120,0.12) !important }
button[data-baseweb="tab"]{ color:#805060 !important }
button[data-baseweb="tab"][aria-selected="true"]{ color:#ff8fa3 !important; border-bottom:3px solid #e05070 !important }
[data-testid="stTabs"] [role="tablist"]{ border-bottom:1px solid rgba(255,100,120,0.15) !important }
details{ background:rgba(255,80,100,0.04) !important; border:1px solid rgba(255,100,120,0.12) !important }
details summary{ color:#b07080 !important }
[data-testid="stAlert"]{ border:1px solid rgba(255,100,120,0.2) !important }
button[kind="secondary"]{
    background:rgba(255,80,100,0.07) !important; color:#d0a0a8 !important;
    border:1px solid rgba(255,100,120,0.25) !important;
}
.hero{
    background:linear-gradient(135deg,rgba(139,26,42,0.3),rgba(30,5,10,0.8));
    border:1px solid rgba(255,100,120,0.15);
}
.hero p{ color:#9a6070 }
.ocard{
    background:linear-gradient(135deg,rgba(139,26,42,0.28) 0%,rgba(20,5,8,0.95) 100%);
    border:1px solid rgba(224,80,112,0.22); border-left:5px solid #e05070;
    box-shadow:0 8px 32px rgba(0,0,0,0.5);
}
.ocard.delivered{
    background:linear-gradient(135deg,rgba(20,80,40,0.28),rgba(5,15,8,0.95));
    border-color:rgba(46,204,113,0.25); border-left-color:#27ae60;
}
.ocard h3{ color:#ff8fa3 }
.ocard .ts{ color:#603040 }
.ocard .row{ color:#c0a0a8 }
.ocard .row b{ color:#f0d0d5 }
.ocard .tot{ color:#ff8fa3 }
.ocard.delivered h3{ color:#2ecc71 }
.ocard.delivered .tot{ color:#2ecc71 }
.scard{ background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.04); border-left:4px solid #2e1020 }
.scard.draft{ background:rgba(243,156,18,0.06); border-color:rgba(243,156,18,0.15); border-left-color:#f39c12 }
.scard h4{ color:#c09090 }
.scard .st{ color:#6a3040 }
.sumbox{
    background:linear-gradient(135deg,rgba(139,26,42,0.25),rgba(10,2,5,0.97));
    border:1px solid rgba(224,80,112,0.3); box-shadow:0 4px 28px rgba(139,26,42,0.25);
}
.sumbox h3{ color:#ff8fa3 }
.sumbox .row{ color:#c0a0a8 }
.sumbox .row b{ color:#f0d0d5 }
.sumbox .big{ background:linear-gradient(90deg,#ff8fa3,#e05070); -webkit-background-clip:text; -webkit-text-fill-color:transparent }
.ptog{ background:rgba(255,100,120,0.05); border:1.5px solid rgba(255,100,120,0.15) }
.ptog:hover{ background:rgba(255,100,120,0.1); border-color:rgba(255,100,120,0.3) }
.ptog.on{ background:rgba(139,26,42,0.35); border-color:rgba(224,80,112,0.5) }
.ptog .name{ color:#c0a0a8 }
.ptog.on .name{ color:#ff8fa3 }
.ptog .dot{ background:#3a1020 }
.ptog.on .dot{ background:#e05070; box-shadow:0 0 6px rgba(224,80,112,0.6) }
"""

LIGHT_CSS = """
html, body, [data-testid="stAppViewContainer"], section[data-testid="stMain"] {
    background: linear-gradient(160deg,#fff5f7 0%,#ffe8ec 50%,#fff9f0 100%) fixed !important;
    color: #2d0a10 !important;
}
[data-testid="stHeader"] {
    background: rgba(255,245,247,0.95) !important;
    border-bottom: 1px solid rgba(192,57,43,0.15);
}
::-webkit-scrollbar-track{ background:#fff5f7 }
::-webkit-scrollbar-thumb{ background:#e05070 }
h1,h2,h3{ color:#c0392b !important }
label,[data-testid="stWidgetLabel"]{ color:#7a3040 !important }
[data-testid="stCaptionContainer"] p{ color:#a06070 !important }
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {
    background:#fff !important; color:#2d0a10 !important;
    border:1px solid rgba(192,57,43,0.25) !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus{
    border-color:#c0392b !important; box-shadow:0 0 0 3px rgba(192,57,43,0.12) !important;
}
[data-testid="stRadio"] label{ color:#5a2030 !important }
[data-testid="stMetricLabel"]{ color:#a06070 !important }
[data-testid="stMetricValue"]{ color:#c0392b !important; font-weight:800 !important }
hr{ border-color:rgba(192,57,43,0.15) !important }
button[data-baseweb="tab"]{ color:#c08090 !important }
button[data-baseweb="tab"][aria-selected="true"]{ color:#c0392b !important; border-bottom:3px solid #c0392b !important }
[data-testid="stTabs"] [role="tablist"]{ border-bottom:1px solid rgba(192,57,43,0.15) !important }
details{ background:rgba(192,57,43,0.03) !important; border:1px solid rgba(192,57,43,0.12) !important }
details summary{ color:#a06070 !important }
[data-testid="stAlert"]{ border:1px solid rgba(192,57,43,0.2) !important }
button[kind="secondary"]{
    background:rgba(192,57,43,0.06) !important; color:#7a3040 !important;
    border:1px solid rgba(192,57,43,0.2) !important;
}
.hero{
    background:linear-gradient(135deg,rgba(255,200,200,0.5),rgba(255,240,235,0.8));
    border:1px solid rgba(192,57,43,0.15);
}
.hero p{ color:#a06070 }
.ocard{
    background:linear-gradient(135deg,rgba(255,220,220,0.5) 0%,rgba(255,250,248,0.98) 100%);
    border:1px solid rgba(192,57,43,0.18); border-left:5px solid #c0392b;
    box-shadow:0 4px 20px rgba(192,57,43,0.1);
}
.ocard.delivered{
    background:linear-gradient(135deg,rgba(200,255,220,0.4),rgba(248,255,250,0.98));
    border-color:rgba(39,174,96,0.25); border-left-color:#27ae60;
}
.ocard h3{ color:#c0392b }
.ocard .ts{ color:#c09090 }
.ocard .row{ color:#7a5060 }
.ocard .row b{ color:#2d0a10 }
.ocard .tot{ color:#c0392b }
.ocard.delivered h3{ color:#27ae60 }
.ocard.delivered .tot{ color:#27ae60 }
.scard{ background:rgba(255,255,255,0.6); border:1px solid rgba(192,57,43,0.08); border-left:4px solid #f0d0d5 }
.scard.draft{ background:rgba(243,156,18,0.05); border-color:rgba(243,156,18,0.15); border-left-color:#f39c12 }
.scard h4{ color:#7a4050 }
.scard .st{ color:#a08090 }
.sumbox{
    background:linear-gradient(135deg,rgba(255,200,200,0.4),rgba(255,250,248,0.97));
    border:1px solid rgba(192,57,43,0.2); box-shadow:0 4px 20px rgba(192,57,43,0.08);
}
.sumbox h3{ color:#c0392b }
.sumbox .row{ color:#7a5060 }
.sumbox .row b{ color:#2d0a10 }
.sumbox .big{ background:linear-gradient(90deg,#c0392b,#e05070); -webkit-background-clip:text; -webkit-text-fill-color:transparent }
.ptog{ background:rgba(192,57,43,0.04); border:1.5px solid rgba(192,57,43,0.12) }
.ptog:hover{ background:rgba(192,57,43,0.08); border-color:rgba(192,57,43,0.25) }
.ptog.on{ background:rgba(192,57,43,0.12); border-color:rgba(192,57,43,0.4) }
.ptog .name{ color:#7a5060 }
.ptog.on .name{ color:#c0392b }
.ptog .dot{ background:#f0d0d5 }
.ptog.on .dot{ background:#c0392b; box-shadow:0 0 6px rgba(192,57,43,0.4) }
"""

# Shared CSS (both modes)
SHARED_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html,body,[data-testid="stAppViewContainer"],section[data-testid="stMain"]{
    font-family:'Inter',sans-serif !important;
}
::-webkit-scrollbar{width:5px}
[data-testid="stHeader"]{ backdrop-filter:blur(12px) }
h1,h2,h3{ font-family:'Inter',sans-serif !important; font-weight:800 !important }
label,[data-testid="stWidgetLabel"]{ font-size:.88rem !important }
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input { border-radius:12px !important; font-size:1rem !important }
[data-testid="stRadio"] > div{ gap:.4rem !important }
hr{ margin:1.2rem 0 !important }
button[data-baseweb="tab"]{ font-weight:600 !important; background:transparent !important }
[data-testid="stTabs"] [role="tablist"]{ gap:.5rem !important }
details{ border-radius:14px !important }
[data-testid="stAlert"]{ border-radius:14px !important }
button[kind="primary"]{
    background:linear-gradient(135deg,#8b1a2a 0%,#c0392b 55%,#e05070 100%) !important;
    border:none !important; color:#fff !important; font-weight:700 !important;
    border-radius:12px !important; letter-spacing:.3px !important;
    box-shadow:0 4px 15px rgba(192,57,43,0.35) !important; transition:all .2s !important;
}
button[kind="primary"]:hover{ transform:translateY(-1px) !important; box-shadow:0 6px 20px rgba(192,57,43,0.5) !important }
button[kind="secondary"]{ border-radius:12px !important }
.hero{ text-align:center; padding:2rem 1rem 1.5rem; border-radius:24px; margin-bottom:1.5rem }
.hero h1{ font-size:2.2rem !important; margin:0 !important }
.hero p{ font-size:.95rem; margin-top:.4rem }
.ocard{ border-radius:20px; padding:1.5rem 1.8rem; margin-bottom:.6rem }
.ocard h3{ margin:0 0 .2rem; font-size:1.3rem; font-weight:800 }
.ocard .ts{ font-size:.8rem; margin-bottom:.8rem }
.ocard .row{ font-size:.95rem; margin:.35rem 0 }
.ocard .tot{ font-size:1.35rem; font-weight:800; margin-top:.9rem }
.ocard.delivered .tot{ color:#2ecc71 }
.badge-ok{ display:inline-block;
    background:linear-gradient(135deg,#145028,#27ae60);
    color:#fff; font-size:.72rem; font-weight:700; letter-spacing:1.2px;
    text-transform:uppercase; padding:.2rem .7rem; border-radius:20px; margin-bottom:.5rem }
.scard{ border-radius:14px; padding:.9rem 1.4rem; margin-bottom:.6rem }
.scard h4{ margin:0; font-size:1.05rem }
.scard .st{ font-size:.82rem; margin-top:.15rem }
.sumbox{ border-radius:20px; padding:1.5rem 2rem; margin-top:1.2rem }
.sumbox h3{ margin:0 0 .7rem; font-size:1.25rem }
.sumbox .row{ font-size:1rem; margin:.3rem 0 }
.sumbox .big{ font-size:1.9rem; font-weight:800; margin-top:.6rem;
    -webkit-background-clip:text; -webkit-text-fill-color:transparent }
.ptog-grid{ display:grid; grid-template-columns:1fr 1fr; gap:.75rem; margin-top:.5rem }
.ptog{ display:flex; align-items:center; gap:.8rem;
    border-radius:14px; padding:.85rem 1.1rem; cursor:pointer; transition:all .2s }
.ptog .ico{ font-size:1.5rem }
.ptog .name{ font-size:.95rem; font-weight:600 }
.ptog .dot{ width:10px; height:10px; border-radius:50%; margin-left:auto;
    transition:all .2s; flex-shrink:0 }

/* ── Mobile responsive ── */
@media (max-width: 768px) {
    .hero h1 { font-size:1.6rem !important }
    .ocard { padding:1.1rem 1.2rem; border-radius:16px }
    .ocard h3 { font-size:1.1rem }
    .ocard .tot { font-size:1.15rem }
    .sumbox { padding:1.2rem 1.4rem }
    .sumbox .big { font-size:1.5rem }
    .ptog-grid { grid-template-columns:1fr }
    [data-testid="stTabs"] [role="tablist"] { gap:.2rem !important; flex-wrap:wrap }
    button[data-baseweb="tab"] { font-size:.8rem !important; padding:.4rem .5rem !important }
    [data-testid="stMetricValue"] { font-size:1.4rem !important }
}
@media (max-width: 480px) {
    .hero { padding:1.5rem .8rem 1rem; border-radius:18px; margin-bottom:1rem }
    .hero h1 { font-size:1.4rem !important }
    .ocard { padding:.9rem 1rem; border-radius:14px }
    .ocard .row { font-size:.85rem }
    .scard { padding:.7rem 1rem }
    .sumbox { padding:1rem 1.2rem; border-radius:16px }
}
"""

theme_css = DARK_CSS if st.session_state.theme == "dark" else LIGHT_CSS
st.markdown(f"<style>{SHARED_CSS}{theme_css}</style>", unsafe_allow_html=True)

# Theme toggle button in top-right
def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

theme_icon = "☀️" if st.session_state.theme == "dark" else "🌙"
theme_label = "Light mode" if st.session_state.theme == "dark" else "Dark mode"
cols_theme = st.columns([8, 1])
with cols_theme[1]:
    if st.button(theme_icon, key="theme_toggle", help=theme_label):
        toggle_theme()
        st.rerun()
# ── session ───────────────────────────────────────────────────────────────────
if "user"           not in st.session_state: st.session_state.user = None
if "confirm_del"    not in st.session_state: st.session_state.confirm_del = None
if "known_orders"   not in st.session_state: st.session_state.known_orders = set()

# Notification JS — injected once, asks browser permission, exposes notifyOrder()
st.components.v1.html("""
<script>
// Request notification permission on load
if ("Notification" in window && Notification.permission === "default") {
    Notification.requestPermission();
}

// Global function called by Streamlit when a new order arrives
window.notifyNewOrder = function(aptName, total) {
    if ("Notification" in window && Notification.permission === "granted") {
        const n = new Notification("🍓 New order!", {
            body: "Apartment " + aptName + " — " + total + " NOK",
            icon: "https://em-content.zobj.net/source/twitter/376/strawberry_1f353.png",
            badge: "https://em-content.zobj.net/source/twitter/376/strawberry_1f353.png",
            tag: "order-" + aptName,
        });
        n.onclick = function() { window.focus(); };
    }
};
</script>
""", height=0)

def logout():
    st.session_state.user        = None
    st.session_state.confirm_del = None
    st.session_state.known_orders = set()
    st.query_params.clear()
    st.rerun()

def check_and_notify(orders):
    """Fire browser notifications for any newly submitted orders."""
    current = {o["apt_id"] for o in orders if o["submitted"]}
    new     = current - st.session_state.known_orders
    for apt_id in new:
        o = next(x for x in orders if x["apt_id"] == apt_id)
        st.components.v1.html(f"""
<script>
if (window.notifyNewOrder) {{
    window.notifyNewOrder("{o['apt_name']}", "{o['total_nok']:.0f}");
}}
</script>
""", height=0)
    st.session_state.known_orders = current

def get_base_url():
    try:    return st.context.url.split("?")[0].rstrip("/")
    except: return "http://localhost:8501"

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
    return any(o["lines"].get(p, {}).get("quantity", 0) > 0 for p in ALL_PRODUCTS)

# ── QR token auto-login ───────────────────────────────────────────────────────
preselect_apt = st.query_params.get("apt", "").upper()
qr_token      = st.query_params.get("token", "")
if st.session_state.user is None and qr_token:
    token_user = verify_token(qr_token)
    if token_user:
        st.session_state.user = token_user
        st.query_params.clear()

# ── shared card renderer ──────────────────────────────────────────────────────
def render_order_card(o, show_ts=True):
    qty   = sum(o["lines"].get(p, {}).get("quantity", 0) for p in ALL_PRODUCTS)
    total = o["total_nok"]
    t     = o.get("delivery_time") or "—"
    pay   = o.get("payment_method") or "—"
    css   = "ocard delivered" if o.get("delivered") else "ocard"
    ts    = f'<p class="ts">Submitted: {o["submitted_at"]}</p>' if show_ts and o.get("submitted_at") else ""
    badge = '<span class="badge-ok">&#10003; Delivered</span>' if o.get("delivered") else ""
    del_t = f'<p class="ts" style="color:#2ecc71">Delivered: {o["delivered_at"]}</p>' if o.get("delivered_at") else ""

    lines_html = ""
    for pid, info in ALL_PRODUCTS.items():
        q = o["lines"].get(pid, {}).get("quantity", 0)
        if q > 0:
            lines_html += f'<p class="row">{info["emoji"]} {info["label"]} &times; <b>{q}</b> = <b>{q*info["price"]} NOK</b></p>'

    st.markdown(f"""
<div class="{css}">
  <h3>&#127968; Apartment {o['apt_name']}</h3>
  {ts}{badge}{del_t}
  {lines_html}
  <p class="row">&#128336; <b>{t}</b> &nbsp;|&nbsp; &#128179; <b>{pay}</b></p>
  <p class="tot">Total: {total:.0f} NOK</p>
</div>""", unsafe_allow_html=True)

# ╔══════════════════════════════════════════════════════╗
# ║  LOGIN                                               ║
# ╚══════════════════════════════════════════════════════╝
def show_login():
    st.markdown("""
<div class="hero">
  <h1>&#127827; Strawberry Orders</h1>
  <p>Fresh delivery for your apartment</p>
</div>""", unsafe_allow_html=True)

    apt_usernames = list(APARTMENTS.values())
    if preselect_apt in apt_usernames:
        st.info(f"&#127968; Apartment **{preselect_apt}** — enter your PIN")

    with st.form("login_form"):
        default  = preselect_apt if preselect_apt in apt_usernames else ""
        username = st.text_input("Username", value=default, placeholder="A1  B2  C3  D4  admin")
        password = st.text_input("PIN / Password", type="password")
        ok       = st.form_submit_button("Sign in &#10132;", use_container_width=True)

    if ok:
        user = verify_user(username.strip(), password.strip())
        if user:
            st.session_state.user = user
            st.query_params.clear()
            st.rerun()
        else:
            st.error("Wrong username or password.")


# ╔══════════════════════════════════════════════════════╗
# ║  TENANT                                              ║
# ╚══════════════════════════════════════════════════════╝
def show_tenant(user):
    apt_id   = user["apt_id"]
    apt_name = APARTMENTS[apt_id]
    order    = get_full_order(apt_id)

    c1, c2 = st.columns([5, 1])
    with c1: st.markdown(f"# &#127968; Apartment {apt_name}")
    with c2:
        st.write("")
        if st.button("Log out", key="t_out"): logout()

    if order["submitted"] and not order.get("delivered"):
        st.success("Your order has been submitted!")
        render_order_card(order)
        if st.button("Edit my order", type="secondary", use_container_width=True):
            reset_apt_order(apt_id); st.rerun()
        return

    if order.get("delivered"):
        st.success(f"Delivered at **{order['delivered_at']}**. Place a new order below!")
        reset_apt_order(apt_id); st.rerun()

    st.divider()

    available = get_available_products()
    if not available:
        st.warning("No products are available today. Check back later!")
        return

    st.markdown("### &#127827; Select products")
    quantities = {}
    cols = st.columns(len(available) if len(available) <= 4 else 2)
    for idx, pid in enumerate(available):
        info = ALL_PRODUCTS[pid]
        with cols[idx % len(cols)]:
            current = order["lines"].get(pid, {}).get("quantity", 0)
            qty = st.number_input(
                f"{info['emoji']} {info['label']}\n\n*{info['price']} NOK*",
                min_value=0, max_value=50, value=current, step=1, key=f"q_{pid}"
            )
            quantities[pid] = qty

    st.divider()
    st.markdown("### &#128336; Delivery time")
    saved_time    = order.get("delivery_time") or TIME_SLOTS[0]
    slot_idx      = TIME_SLOTS.index(saved_time) if saved_time in TIME_SLOTS else 0
    delivery_time = st.radio("Slot", TIME_SLOTS, index=slot_idx, label_visibility="collapsed")

    st.divider()
    st.markdown("### &#128179; Payment method")
    saved_pay = order.get("payment_method") or PAYMENT_METHODS[0]
    pay_idx   = PAYMENT_METHODS.index(saved_pay) if saved_pay in PAYMENT_METHODS else 0
    payment   = st.radio("Pay", PAYMENT_METHODS, index=pay_idx,
                         horizontal=True, label_visibility="collapsed")

    st.divider()
    total = sum(quantities.get(p, 0) * ALL_PRODUCTS[p]["price"] for p in available)

    c_tot, c_save, c_sub = st.columns([2, 1, 1])
    with c_tot: st.metric("Total", f"{total} NOK")
    with c_save:
        if st.button("Save draft", use_container_width=True):
            save_order(apt_id, quantities, delivery_time, payment)
            st.success("Saved!"); st.rerun()
    with c_sub:
        if st.button("Submit order", type="primary", use_container_width=True):
            if total == 0: st.warning("Add at least one item.")
            else:
                save_order(apt_id, quantities, delivery_time, payment)
                submit_order(apt_id)
                st.success("Order submitted!"); st.rerun()

# ╔══════════════════════════════════════════════════════╗
# ║  ADMIN  (orders + product stock toggles)             ║
# ╚══════════════════════════════════════════════════════╝
def show_admin(user):
    c1, c2 = st.columns([5, 1])
    with c1: st.markdown("# &#127827; Today's Orders")
    with c2:
        st.write("")
        if st.button("Log out", key="a_out"): logout()

    tab_active, tab_delivered, tab_stock, tab_qr_adm = st.tabs(["🚛 To deliver", "✅ Delivered", "🛒 Stock", "📱 QR Codes"])

    @st.fragment(run_every=15)
    def orders_fragment():
        orders    = get_all_full_orders()
        check_and_notify(orders)
        submitted = [o for o in orders if o["submitted"]]
        active    = [o for o in submitted if not o.get("delivered")]
        delivered = [o for o in submitted if o.get("delivered")]
        drafts    = [o for o in orders if not o["submitted"] and order_has_items(o)]

        with tab_active:
            # refresh indicator
            st.caption(f"Auto-refreshes every 15s · Last checked: {time.strftime('%H:%M:%S')}")

            if not active and not drafts:
                st.markdown('<div class="scard"><h4 style="text-align:center;color:#6a3040;padding:.4rem 0">No orders yet</h4></div>', unsafe_allow_html=True)
            else:
                for o in active:
                    render_order_card(o)
                    if st.session_state.confirm_del == o["apt_id"]:
                        st.warning(f"Are you sure you want to mark **{o['apt_name']}** as delivered?")
                        cc1, cc2 = st.columns(2)
                        with cc1:
                            if st.button("Yes, delivered", type="primary", key=f"yes_{o['apt_id']}"):
                                mark_delivered(o["apt_id"])
                                st.session_state.confirm_del = None
                                st.rerun()
                        with cc2:
                            if st.button("Cancel", key=f"no_{o['apt_id']}"):
                                st.session_state.confirm_del = None
                                st.rerun()
                    else:
                        if st.button(f"🚚 Mark as delivered — {o['apt_name']}",
                                     key=f"dlv_{o['apt_id']}", type="primary",
                                     use_container_width=True):
                            st.session_state.confirm_del = o["apt_id"]
                            st.rerun()
                    st.write("")

                for o in drafts:
                    st.markdown(f'<div class="scard draft"><h4>&#128203; Apartment {o["apt_name"]}</h4>'
                                f'<p class="st">Draft — not submitted yet</p></div>', unsafe_allow_html=True)
                if drafts:
                    st.warning(f"{len(drafts)} apartment(s) have a draft not yet submitted.")

            if active:
                total_nok = sum(o["total_nok"] for o in active)
                st.markdown(f"""
<div class="sumbox">
  <h3>&#128230; Still to collect</h3>
  <p class="row">&#127968; <b>{len(active)}</b> apartment(s)</p>
  <p class="big">{total_nok:.0f} NOK</p>
</div>""", unsafe_allow_html=True)

        with tab_delivered:
            if not delivered:
                st.markdown('<div class="scard"><h4 style="text-align:center;color:#6a3040;padding:.4rem 0">No deliveries yet</h4></div>', unsafe_allow_html=True)
            else:
                for o in delivered:
                    render_order_card(o)
                    if st.button(f"↩ Undo delivery — {o['apt_name']}", key=f"undo_{o['apt_id']}"):
                        undeliver_order(o["apt_id"])
                        st.rerun()
                    st.write("")

                total_nok = sum(o["total_nok"] for o in delivered)
                st.markdown(f"""
<div class="sumbox">
  <h3>&#9989; Delivered today</h3>
  <p class="row">&#127968; <b>{len(delivered)}</b> apartment(s)</p>
  <p class="big">{total_nok:.0f} NOK</p>
</div>""", unsafe_allow_html=True)

    orders_fragment()

    with tab_stock:
        st.markdown("### What's available today?")
        st.caption("Toggle on the products you have in stock. Tenants will only see enabled items.")
        available = get_available_products()
        render_product_toggles(available, prefix="adm")

    with tab_qr_adm:
        st.subheader("QR Codes")
        st.caption("Scan → auto-login. No password needed. Print and stick on each door.")
        base_url = get_base_url()
        cols = st.columns(4)
        for apt_id, apt_name in APARTMENTS.items():
            token    = get_token_for_apt(apt_id)
            url      = f"{base_url}/?token={token}"
            qr_bytes = make_qr_bytes(url)
            with cols[apt_id - 1]:
                st.image(qr_bytes, caption=f"Apt {apt_name}", use_container_width=True)
                st.download_button(f"⬇ {apt_name}", data=qr_bytes,
                                   file_name=f"qr_{apt_name}.png", mime="image/png",
                                   key=f"adm_dl_{apt_id}", use_container_width=True)
        with st.expander("Direct links"):
            for apt_id, apt_name in APARTMENTS.items():
                st.code(f"{base_url}/?token={get_token_for_apt(apt_id)}")


def render_product_toggles(available: list, prefix: str):
    """Render styled product toggle grid using Streamlit checkboxes."""
    st.markdown('<div class="ptog-grid">', unsafe_allow_html=True)
    cols = st.columns(2)
    for idx, (pid, info) in enumerate(ALL_PRODUCTS.items()):
        on = pid in available
        with cols[idx % 2]:
            new_val = st.checkbox(
                f"{info['emoji']}  {info['label']}",
                value=on,
                key=f"{prefix}_tog_{pid}"
            )
            if new_val != on:
                set_product_available(pid, new_val)
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ╔══════════════════════════════════════════════════════╗
# ║  SUPERADMIN                                          ║
# ╚══════════════════════════════════════════════════════╝
def show_superadmin(user):
    c1, c2 = st.columns([5, 1])
    with c1: st.markdown("# &#9881;&#65039; Super Admin")
    with c2:
        st.write("")
        if st.button("Log out", key="sa_out"): logout()

    tab_orders, tab_stock, tab_qr, tab_pwd = st.tabs(["📋 Orders", "🛒 Stock", "📱 QR Codes", "🔑 Passwords"])

    with tab_orders:
        @st.fragment(run_every=15)
        def sa_orders_fragment():
            orders    = get_all_full_orders()
            check_and_notify(orders)
            submitted = [o for o in orders if o["submitted"]]
            active    = [o for o in submitted if not o.get("delivered")]
            delivered = [o for o in submitted if o.get("delivered")]
            drafts    = [o for o in orders if not o["submitted"] and order_has_items(o)]

            st.caption(f"Auto-refreshes every 15s · Last checked: {time.strftime('%H:%M:%S')}")

            if active:
                st.subheader("To deliver")
                for o in active:
                    render_order_card(o)
                    if st.button(f"Reset {o['apt_name']}", key=f"rsa_{o['apt_id']}"): reset_apt_order(o["apt_id"]); st.rerun()
                    st.write("")
            if delivered:
                st.subheader("Delivered")
                for o in delivered:
                    render_order_card(o)
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button(f"↩ Undo {o['apt_name']}", key=f"undo_sa_{o['apt_id']}"): undeliver_order(o["apt_id"]); st.rerun()
                    with c2:
                        if st.button(f"Reset {o['apt_name']}", key=f"rsd_{o['apt_id']}"): reset_apt_order(o["apt_id"]); st.rerun()
                    st.write("")
            if drafts:
                st.subheader("Drafts")
                for o in drafts:
                    render_order_card(o, show_ts=False)
                    if st.button(f"Reset {o['apt_name']}", key=f"rdr_{o['apt_id']}"): reset_apt_order(o["apt_id"]); st.rerun()
                    st.write("")
            if not submitted and not drafts:
                st.info("No orders yet.")

            if submitted:
                total_n = sum(o["total_nok"] for o in submitted)
                st.divider()
                c1, c2 = st.columns(2)
                c1.metric("Orders", len(submitted))
                c2.metric("Total NOK", f"{total_n:.0f}")

            st.divider()
            if st.button("🔄 Reset ALL orders", type="secondary", use_container_width=True):
                reset_all_orders(); st.success("All reset."); st.rerun()

        sa_orders_fragment()

    with tab_stock:
        st.markdown("### What's available today?")
        st.caption("Toggle on the products in stock. Shared with admin.")
        available = get_available_products()
        render_product_toggles(available, prefix="sa")

    with tab_qr:
        st.subheader("QR Codes")
        st.caption("Scan → auto-login. No password needed. Print and stick on each door.")
        base_url = get_base_url()
        cols = st.columns(4)
        for apt_id, apt_name in APARTMENTS.items():
            token    = get_token_for_apt(apt_id)
            url      = f"{base_url}/?token={token}"
            qr_bytes = make_qr_bytes(url)
            with cols[apt_id - 1]:
                st.image(qr_bytes, caption=f"Apt {apt_name}", use_container_width=True)
                st.download_button(f"⬇ {apt_name}", data=qr_bytes,
                                   file_name=f"qr_{apt_name}.png", mime="image/png",
                                   key=f"dl_{apt_id}", use_container_width=True)
        with st.expander("Direct links"):
            for apt_id, apt_name in APARTMENTS.items():
                st.code(f"{base_url}/?token={get_token_for_apt(apt_id)}")

    with tab_pwd:
        st.subheader("Change Passwords")
        users = get_all_users()
        with st.form("pwd_form"):
            st.caption("Leave blank to keep current password.")
            new_pwds = {}
            cols = st.columns(2)
            for i, u in enumerate(users):
                label = {"superadmin": "Superadmin", "admin": "Admin"}.get(u["role"], f"Apartment {u['username']}")
                with cols[i % 2]:
                    new_pwds[u["username"]] = st.text_input(label, type="password",
                                                             placeholder="New password",
                                                             key=f"np_{u['username']}")
            if st.form_submit_button("Save passwords", use_container_width=True):
                changed = sum(1 for u, p in new_pwds.items() if p.strip() and not change_password(u, p.strip()))
                st.success(f"Updated {changed} password(s).") if changed else st.warning("Nothing changed.")


# ── router ────────────────────────────────────────────────────────────────────
u = st.session_state.user
if u is None:           show_login()
elif u["role"] == "superadmin": show_superadmin(u)
elif u["role"] == "admin":      show_admin(u)
else:                           show_tenant(u)
