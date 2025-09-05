import streamlit as st
from db import init_db, register_user, login_user, get_user, update_user, delete_user, reset_password
from jose import jwt, JWTError
from datetime import datetime, timedelta

# ------------------- Initialize DB -------------------              
init_db()

# ------------------- JWT Config -------------------
SECRET_KEY = "supersecretkey"  
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(username: str, expires_delta: timedelta = None):
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None

# ------------------- Session State -------------------
if "page" not in st.session_state:
    st.session_state.page = "Login"
if "username" not in st.session_state:
    st.session_state.username = None
if "token" not in st.session_state:
    st.session_state.token = None

st.title("🌍 Global Wellness Chatbot ")

# ------------------- Navigation -------------------
if st.session_state.page not in ["Profile", "Reset Password"]:
    action = st.radio("Select Action:", ["Login", "Register"])
    st.session_state.page = action

# ------------------- Login Page -------------------
if st.session_state.page == "Login":
    st.subheader("🔑 Login")
    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")

    if st.button("Login"):
        user = login_user(username, password)
        if user:
            # Generate JWT
            token = create_access_token(username, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
            st.session_state.username = username
            st.session_state.token = token
            st.session_state.page = "Profile"
            st.success("✅ Logged in successfully!")
        else:
            st.error("❌ Invalid username or password")
           

    if st.button("Forgot Password"):
        st.session_state.page = "Reset Password"

# ------------------- Register Page -------------------
elif st.session_state.page == "Register":
    st.subheader("📝 Register")
    new_user = st.text_input("Username", key="reg_user")
    new_pass = st.text_input("Password", type="password", key="reg_pass")
    confirm_pass = st.text_input("Confirm Password", type="password", key="reg_confirm")

    if st.button("Register"):
        if new_pass != confirm_pass:
            st.error("Passwords do not match!")
        else:
            if register_user(new_user, new_pass):
                st.success("✅ Registration successful! Please login.")
                st.session_state.page = "Login"
            else:
                st.error("❌ Username already exists!")

# ------------------- Reset Password Page -------------------
elif st.session_state.page == "Reset Password":
    st.subheader("🔄 Reset Password")
    uname = st.text_input("Enter Username", key="reset_user")
    new_pass = st.text_input("New Password", type="password", key="reset_pass")
    if st.button("Reset Now"):
        reset_password(uname, new_pass)
        st.success("Password reset successful! Please login.")
        st.session_state.page = "Login"

# ------------------- Profile Management Page -------------------
elif st.session_state.page == "Profile":
    # ✅ Verify token before allowing access
    if not st.session_state.token or not verify_token(st.session_state.token):
        st.error("⚠️ Session expired or invalid. Please login again.")
        st.session_state.page = "Login"
    else:
        st.subheader("👤 Profile Management")
        username = st.session_state.username
        profile = get_user(username)
        age, gender, language, account_created, last_login, last_profile_update = profile if profile else (18, "Male", "English", "-", "-", "-")

        st.markdown(f"**Account Created:** {account_created if account_created else '-'}")
        st.markdown(f"**Last Login:** {last_login if last_login else '-'}")
        st.markdown(f"**Last Profile Update:** {last_profile_update if last_profile_update else '-'}")

        # Handle None values
        if gender not in ["Male", "Female", "Others"]:
            gender = "Male"
        if language not in ["English", "Hindi"]:
            language = "English"

        new_age = st.number_input("Age", min_value=1, max_value=120, value=age, step=1)
        new_gender = st.radio("Gender", ["Male", "Female", "Others"], index=["Male","Female","Others"].index(gender))
        new_language = st.radio("Language Preference", ["English", "Hindi"], index=["English","Hindi"].index(language))

        if st.button("Update Profile"):
            update_user(username, new_age, new_gender, new_language)
            st.success("✅ Profile updated successfully!")

        if st.button("Logout"):
            st.session_state.username = None
            st.session_state.token = None
            st.session_state.page = "Login"
            st.success("✅ Logged out successfully!")

        if st.button("Delete My Account"):
            delete_user(username)
            st.session_state.username = None
            st.session_state.token = None
            st.session_state.page = "Login"
            st.success("Account deleted successfully!")
