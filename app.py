import streamlit as st
import sqlite3, hashlib, random, smtplib
from email.message import EmailMessage
import tensorflow as tf
import numpy as np
from PIL import Image

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="Paddy Leaf Disease Detection",
    page_icon="🌾",
    layout="centered"
)

# ===============================
# CONFIG
# ===============================
ADMIN_EMAIL = "siteprojectbatch4@gmail.com"
ADMIN_PASSWORD = "sitebatch@4"

MODEL_PATH = "paddy_disease_model.h5"
IMG_SIZE = 224

SENDER_EMAIL = "siteprojectbatch4@gmail.com"
SENDER_PASSWORD = "toojcwqjqtusatpn"  # Gmail App Password

CLASS_NAMES = [
    "Bacterial Leaf Blight",
    "Brown Spot",
    "Leaf Smut"
]

PESTICIDE_INFO = {
    "Bacterial Leaf Blight": "Spray Streptomycin or Copper Oxychloride",
    "Brown Spot": "Spray Mancozeb fungicide",
    "Leaf Smut": "Spray Carbendazim fungicide"
}

# ===============================
# DATABASE
# ===============================
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    email TEXT PRIMARY KEY,
    password TEXT
)
""")
conn.commit()

# ===============================
# HELPERS
# ===============================
def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def send_otp(email):
    otp = str(random.randint(100000, 999999))
    st.session_state.otp = otp
    st.session_state.otp_email = email

    msg = EmailMessage()
    msg.set_content(f"Your OTP is: {otp}")
    msg["Subject"] = "OTP Verification"
    msg["From"] = SENDER_EMAIL
    msg["To"] = email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)

def register_user(email, password):
    try:
        c.execute(
            "INSERT INTO users VALUES (?, ?)",
            (email.lower(), hash_password(password))
        )
        conn.commit()
        return True
    except:
        return False

def login_user(email, password):
    c.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (email.lower(), hash_password(password))
    )
    return c.fetchone()

def reset_password(email, password):
    c.execute(
        "UPDATE users SET password=? WHERE email=?",
        (hash_password(password), email.lower())
    )
    conn.commit()

# ===============================
# LOAD MODEL
# ===============================
@st.cache_resource
def load_model():
    return tf.keras.models.load_model(MODEL_PATH, compile=False)

model = load_model()

# ===============================
# SESSION STATE INIT
# ===============================
if "page" not in st.session_state:
    st.session_state.page = "login"

if "otp_stage" not in st.session_state:
    st.session_state.otp_stage = False

def reset_otp_state():
    st.session_state.otp_stage = False
    st.session_state.pop("otp", None)
    st.session_state.pop("otp_email", None)
    st.session_state.pop("temp_pass", None)

def go(page):
    reset_otp_state()
    st.session_state.page = page
    st.rerun()

# ===============================
# LOGIN PAGE
# ===============================
if st.session_state.page == "login":
    st.title("🔐 Login")

    email = st.text_input("📧 Email")
    password = st.text_input("🔑 Password", type="password")

    if st.button("Login", use_container_width=True):
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            go("admin")
        elif login_user(email, password):
            go("user")
        else:
            st.error("Invalid email or password")

    st.markdown("---")
    st.button("📝 Register", on_click=go, args=("register",), use_container_width=True)
    st.button("🔁 Forgot Password", on_click=go, args=("forgot",), use_container_width=True)

# ===============================
# REGISTER PAGE
# ===============================
elif st.session_state.page == "register":
    st.title("📝 Register")

    email = st.text_input("📧 Email")
    password = st.text_input("🔑 Password", type="password")
    confirm = st.text_input("🔑 Confirm Password", type="password")

    if not st.session_state.otp_stage:
        if st.button("Send OTP", use_container_width=True):
            if password != confirm:
                st.error("Passwords do not match")
            else:
                send_otp(email)
                st.session_state.temp_pass = password
                st.session_state.otp_stage = True
                st.success("OTP sent to email 📩")

    if st.session_state.otp_stage:
        otp = st.text_input("Enter OTP")
        if st.button("Verify & Register", use_container_width=True):
            if otp == st.session_state.otp:
                if register_user(email, st.session_state.temp_pass):
                    st.success("Registration successful ✅")
                    go("login")
                else:
                    st.error("User already exists")
            else:
                st.error("Invalid OTP")

    st.button("⬅ Back", on_click=go, args=("login",), use_container_width=True)

# ===============================
# FORGOT PASSWORD
# ===============================
elif st.session_state.page == "forgot":
    st.title("🔁 Forgot Password")

    email = st.text_input("📧 Registered Email")

    if not st.session_state.otp_stage:
        if st.button("Send OTP", use_container_width=True):
            send_otp(email)
            st.session_state.otp_stage = True
            st.success("OTP sent 📩")

    if st.session_state.otp_stage:
        otp = st.text_input("Enter OTP")
        new_pass = st.text_input("New Password", type="password")

        if st.button("Reset Password", use_container_width=True):
            if otp == st.session_state.otp:
                reset_password(email, new_pass)
                st.success("Password reset successful ✅")
                go("login")
            else:
                st.error("Invalid OTP")

    st.button("⬅ Back", on_click=go, args=("login",), use_container_width=True)

# ===============================
# ADMIN PANEL
# ===============================
elif st.session_state.page == "admin":
    st.title("👑 Admin Panel")

    if st.button("Logout", use_container_width=True):
        go("login")

    c.execute("SELECT email FROM users")
    users = c.fetchall()

    st.subheader("Registered Users")
    for u in users:
        st.write("📧", u[0])

# ===============================
# USER + ML PAGE
# ===============================
elif st.session_state.page == "user":
    st.title("🌾 Paddy Leaf Disease Detection")

    if st.button("Logout", use_container_width=True):
        go("login")

    file = st.file_uploader(
        "Upload Paddy Leaf Image",
        type=["jpg", "png", "jpeg"]
    )

    if file:
        img = Image.open(file).convert("RGB")
        st.image(img, use_container_width=True)

        img = img.resize((IMG_SIZE, IMG_SIZE))
        arr = np.array(img) / 255.0
        arr = np.expand_dims(arr, axis=0)

        with st.spinner("Analyzing image..."):
            pred = model.predict(arr)[0]

        idx = int(np.argmax(pred))
        disease = CLASS_NAMES[idx]
        confidence = float(np.max(pred)) * 100
        pesticide = PESTICIDE_INFO[disease]

        st.success(f"🌿 Disease: {disease}")
        st.info(f"🎯 Confidence: {confidence:.2f}%")
        st.warning(f"🧪 Pesticide: {pesticide}")

    st.markdown("---")
    st.caption("🌾 Paddy Leaf Disease Detection | AI Powered")
