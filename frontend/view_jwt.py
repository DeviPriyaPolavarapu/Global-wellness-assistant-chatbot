import streamlit as st
from jose import jwt, JWTError

# Must match app.py settings
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"

st.title("🔍 JWT Viewer & Verifier")

token = st.text_area("Paste your JWT token here:")

if st.button("Decode & Verify"):
    if not token.strip():
        st.error("⚠️ Please enter a token.")
    else:
        try:
            # Decode with verification
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            st.success("✅ Token is valid!")
            st.json(payload)
        except JWTError as e:
            st.error(f"❌ Invalid or expired token: {str(e)}")

if st.button("Decode Without Verification (Unsafe)"):
    if not token.strip():
        st.error("⚠️ Please enter a token.")
    else:
        try:
            # Decode without signature check
            payload = jwt.get_unverified_claims(token)
            st.warning("⚠️ Signature NOT verified! (for debugging only)")
            st.json(payload)
        except Exception as e:
            st.error(f"❌ Failed to decode: {str(e)}")
