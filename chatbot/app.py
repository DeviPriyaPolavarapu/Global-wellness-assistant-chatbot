# app.py
import streamlit as st
import json
from datetime import datetime
import pandas as pd

from db import (
    init_db, register_user, login_user, get_user, get_all_users,
    update_user, delete_user, reset_password,
    add_kb_entry, edit_kb_entry, delete_kb_entry, get_all_kb_entries, get_kb_entry,
    total_queries_count, count_queries_per_day
)
from chat_history import save_chat, get_all_chats, get_user_chat_history
from feedback import save_feedback, get_all_feedback, feedback_stats
from translator import translate_en_to_hi, translate_hi_to_en, ui_texts

# Initialize DB
init_db()

def reload_kb():
    entries = get_all_kb_entries() or []
    mapping = {}
    for row in entries:
        cond = (row[0] or "").strip()
        desc = row[1] or ""
        symptoms = (row[2] or "").split("|") if row[2] else []
        first_aid = (row[3] or "").split("|") if row[3] else []
        prevention = (row[4] or "").split("|") if row[4] else []
        disclaimer = row[5] or ""
        mapping[cond.lower()] = {
            "description": desc,
            "symptoms": symptoms,
            "first_aid": first_aid,
            "prevention": prevention,
            "disclaimer": disclaimer
        }
    return mapping

health_kb_lower = reload_kb()

def format_kb_response(key: str, info: dict) -> str:
    resp = f"**{key.title()}**\n\n"
    resp += f"**Description:** {info.get('description','N/A')}\n\n"
    if info.get('symptoms'):
        resp += f"**Symptoms:** {', '.join(info.get('symptoms', []))}\n\n"
    if info.get('first_aid'):
        resp += f"**First Aid:** {', '.join(info.get('first_aid', []))}\n\n"
    if info.get('prevention'):
        resp += f"**Prevention:** {', '.join(info.get('prevention', []))}\n\n"
    resp += f"{info.get('disclaimer','')}"
    return resp

def find_condition_in_text(text: str):
    words = set([w.strip(".,!?()[]\"'") for w in text.split()])
    for cond in list(health_kb_lower.keys()):
        if cond in text:
            return cond
    for cond in list(health_kb_lower.keys()):
        cond_tokens = cond.split()
        if all(tok in words for tok in cond_tokens):
            return cond
    return None

# canned replies
GREETINGS = ["hi", "hello", "hey", "good morning", "good evening", "namaste"]
GREETING_REPLY = "Hello! I'm WellBot — how can I help you today?"
THANKS = ["thanks", "thank you", "thx"]
THANKS_REPLY = "You're welcome! If you have more questions, ask away."

# session defaults
if "page" not in st.session_state:
    st.session_state.page = "Login"
if "username" not in st.session_state:
    st.session_state.username = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.set_page_config(page_title="Global Wellness Chatbot", layout="wide")
st.title("🌍 Global Wellness Chatbot")

# Navigation
if st.session_state.page not in ["Profile", "Reset Password", "Admin Dashboard"]:
    action = st.radio("Select Action:", ["Login", "Register"], key="nav_radio")
    st.session_state.page = action

# --- Login ---
if st.session_state.page == "Login":
    st.subheader("🔑 Login")
    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")

    if st.button("Login", key="login_btn"):
        user = login_user(username, password)
        if user:
            st.session_state.username = username
            st.session_state.page = "Admin Dashboard" if username.lower() == "admin" else "Profile"
            st.success(f"Logged in as {username}")
            st.rerun()
        else:
            st.error("Invalid username or password")

    if st.button("Forgot Password", key="forgot_btn"):
        st.session_state.page = "Reset Password"
        st.rerun()

# --- Register ---
elif st.session_state.page == "Register":
    st.subheader("📝 Register")
    new_user = st.text_input("Username", key="reg_user")
    new_pass = st.text_input("Password", type="password", key="reg_pass")
    confirm_pass = st.text_input("Confirm Password", type="password", key="reg_confirm")

    if st.button("Register", key="register_btn"):
        if new_pass != confirm_pass:
            st.error("Passwords do not match!")
        else:
            if register_user(new_user, new_pass):
                st.success("Registration successful! Please login.")
                st.session_state.page = "Login"
                st.rerun()
            else:
                st.error("Username already exists!")

# --- Reset Password ---
elif st.session_state.page == "Reset Password":
    st.subheader("🔄 Reset Password")
    uname = st.text_input("Enter Username", key="reset_user")
    new_pass = st.text_input("New Password", type="password", key="reset_pass")
    if st.button("Reset Now", key="reset_now"):
        reset_password(uname, new_pass)
        st.success("Password reset successful! Please login.")
        st.session_state.page = "Login"
        st.rerun()

# --- Profile + Chatbot ---
elif st.session_state.page == "Profile" and st.session_state.username:
    username = st.session_state.username
    profile = get_user(username)
    age, gender, language_pref, account_created, last_login, last_profile_update = profile if profile else (18, "Male", "English", "-", "-", "-")
    texts = ui_texts(language_pref)

    st.sidebar.markdown(f"**{texts['you_label']} {username}**")
    if st.sidebar.button(texts['logout_btn'], key="logout_sidebar"):
        st.session_state.username = None
        st.session_state.page = "Login"
        st.success("Logged out successfully!")
        st.rerun()

    st.subheader(texts["profile_subheader"])
    st.markdown(texts["account_created"].format(val=account_created))
    st.markdown(texts["last_login"].format(val=last_login))
    st.markdown(texts["last_profile_update"].format(val=last_profile_update))

    col1, col2 = st.columns(2)
    with col1:
        new_age = st.number_input(texts["age_label"], min_value=1, max_value=120, value=age, step=1)
        gender_options = [texts["gender_male"], texts["gender_female"], texts["gender_others"]]
        default_gender = gender if gender in ["Male", "Female", "Others"] else "Male"
        default_gender_trans = texts[f"gender_{default_gender.lower()}"]
        new_gender = st.radio(texts["gender_label"], gender_options, index=gender_options.index(default_gender_trans))
    with col2:
        language_options = [texts["lang_english"], texts["lang_hindi"]]
        default_language = language_pref if language_pref in ["English", "Hindi"] else "English"
        new_language = st.radio(texts["preferred_language_label"], language_options, index=language_options.index(texts[f"lang_{default_language.lower()}"]))

    if st.button(texts["update_profile_btn"], key="update_profile_btn"):
        stored_gender = ["Male","Female","Others"][gender_options.index(new_gender)]
        stored_language = ["English","Hindi"][language_options.index(new_language)]
        update_user(username, new_age, stored_gender, stored_language)
        st.success("Profile updated successfully!")

    if st.button(texts["delete_account_btn"], key="delete_account_btn"):
        delete_user(username)
        st.session_state.username = None
        st.session_state.page = "Login"
        st.success("Account deleted successfully!")
        st.rerun()

    # --- Chatbot Section (fixed) ---
    st.subheader(texts["chat_header"])
    lang_option = st.radio(texts["select_chat_language"], ["English", "Hindi"], horizontal=True, key="chat_lang_radio")

    chat_container = st.container()
    with chat_container:
        hist = st.session_state.chat_history
        for entry in hist:  # chronological order (user first then bot)
            sender = entry[0] if len(entry) > 0 else ""
            text = entry[1] if len(entry) > 1 else ""
            chat_id = entry[2] if len(entry) > 2 else None
            ts = entry[3] if len(entry) > 3 else ""

            if sender == "You":
                st.markdown(f"**{texts['you_label']}** {text}")
            else:
                st.markdown(f"**{texts['bot_label']}** {text}")

                # Feedback controls only for bot messages
                key_base = f"{chat_id}_{abs(hash(text))}"
                cols = st.columns([1,1,6])
                with cols[0]:
                    if st.button("👍", key=f"thumb_up_{key_base}"):
                        save_feedback(chat_id, st.session_state.username, 1, "")
                        st.success(texts["feedback_thanks"])
                with cols[1]:
                    if st.button("👎", key=f"thumb_down_{key_base}"):
                        save_feedback(chat_id, st.session_state.username, 0, "")
                        st.info(texts["feedback_recorded"])
                with cols[2]:
                    comment = st.text_input(texts["comment_optional"], key=f"comment_{key_base}")
                    if st.button("Submit", key=f"submit_comment_{key_base}"):
                        save_feedback(chat_id, st.session_state.username, None, comment)
                        st.success(texts["comment_saved"])

    # Input for new message
    user_query = st.text_input(texts["you_label"], key="chat_input")
    if st.button(texts["send_btn"], key="send_btn"):
        if not user_query.strip():
            st.warning("Please enter a message.")
        else:
            original = user_query.strip()
            query_to_send = translate_hi_to_en(original) if lang_option == "Hindi" else original

            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.chat_history.append(("You", original, None, ts))

            qlow = query_to_send.lower() if query_to_send else ""
            bot_text = None
            condition = None
            if any(g in qlow for g in GREETINGS):
                bot_text = GREETING_REPLY
            elif any(t in qlow for t in THANKS):
                bot_text = THANKS_REPLY
            else:
                condition = find_condition_in_text(query_to_send.lower())
                if condition:
                    info = health_kb_lower.get(condition)
                    if info:
                        bot_text = format_kb_response(condition, info)
                    else:
                        db_entry = get_kb_entry(condition.title())
                        if db_entry:
                            cond_name = db_entry[0]
                            desc = db_entry[1] if len(db_entry) > 1 else ""
                            symptoms = db_entry[2] if len(db_entry) > 2 else ""
                            first_aid = db_entry[3] if len(db_entry) > 3 else ""
                            prevention = db_entry[4] if len(db_entry) > 4 else ""
                            disclaimer = db_entry[5] if len(db_entry) > 5 else ""
                            info = {"description": desc, "symptoms": symptoms.split("|") if symptoms else [], "first_aid": first_aid.split("|") if first_aid else [], "prevention": prevention.split("|") if prevention else [], "disclaimer": disclaimer}
                            bot_text = format_kb_response(cond_name, info)
                        else:
                            bot_text = "Sorry, I don't have information on that condition."
                else:
                    bot_text = "I don't have a direct match. Can you specify the main symptom or condition?"

            bot_text_display = translate_en_to_hi(bot_text) if lang_option == "Hindi" else bot_text
            chat_id = save_chat(st.session_state.username, original, "local_kb" if condition else "no_kb", bot_text or "")
            st.session_state.chat_history.append(("WellBot", bot_text_display, chat_id, ts))

            st.rerun()

# --- Admin Dashboard ---
elif st.session_state.page == "Admin Dashboard" and st.session_state.username:
    if st.session_state.username.lower() != "admin":
        st.error("Admin access only.")
    else:
        st.sidebar.markdown("### Admin")
        if st.sidebar.button("Logout Admin", key="admin_logout"):
            st.session_state.username = None
            st.session_state.page = "Login"
            st.rerun()

        st.title("🛠️ Admin Dashboard")

        users = get_all_users() or []
        total_users = len(users)
        try:
            total_queries = total_queries_count()
            trend_rows = count_queries_per_day()
        except Exception:
            total_queries = 0
            trend_rows = []

        fb_stats = feedback_stats()
        pos = fb_stats.get("pos", 0)
        neg = fb_stats.get("neg", 0)
        total_fb = fb_stats.get("total", 0)
        pos_pct = round((pos / total_fb * 100), 1) if total_fb else 0
        neg_pct = round((neg / total_fb * 100), 1) if total_fb else 0

        c1, c2, c3, c4 = st.columns([2,2,2,2])
        c1.metric("Total Users", total_users)
        c2.metric("Queries handled", total_queries)
        c3.metric("Positive feedback %", f"{pos_pct}%")
        c4.metric("Negative feedback %", f"{neg_pct}%")

        st.markdown("---")
        st.subheader("📈 Query Trends")
        if trend_rows:
            df = pd.DataFrame(trend_rows, columns=["day", "count"])
            df["day"] = pd.to_datetime(df["day"])
            df = df.set_index("day")
            st.line_chart(df)
        else:
            st.info("No query trend data yet.")

        st.subheader("📊 Top Query Categories")
        all_chats = get_all_chats() or []
        cond_counts = {}
        for row in all_chats:
            q_text = str(row[2]).lower() if len(row) > 2 else ""
            for cond in health_kb_lower.keys():
                if cond in q_text:
                    cond_counts[cond] = cond_counts.get(cond, 0) + 1
        if cond_counts:
            top = sorted(cond_counts.items(), key=lambda x: x[1], reverse=True)[:20]
            top_df = pd.DataFrame(top, columns=["condition", "count"])
            st.table(top_df)
        else:
            st.info("No categorized queries yet.")

        st.markdown("---")
        st.subheader("🛢️ Knowledge Base Management")

        kb_tabs = st.tabs(["View KB", "Add Entry", "Edit Entry", "Delete Entry"])

        # View DB KB (immediate from DB)
        with kb_tabs[0]:
            entries_db = get_all_kb_entries() or []
            if entries_db:
                st.markdown("**KB entries (A → Z)**")
                for row in entries_db:
                    cond = row[0]
                    desc = row[1] if len(row) > 1 else ""
                    symptoms = row[2] if len(row) > 2 else ""
                    fa = row[3] if len(row) > 3 else ""
                    prev = row[4] if len(row) > 4 else ""
                    dis = row[5] if len(row) > 5 else ""
                    st.markdown(f"**{cond}**")
                    st.markdown(f"- Description: {desc}")
                    st.markdown(f"- Symptoms: {symptoms}")
                    st.markdown(f"- First Aid: {fa}")
                    st.markdown(f"- Prevention: {prev}")
                    st.markdown(f"- Disclaimer: {dis}")
                    st.markdown("---")
            else:
                st.info("No DB KB entries yet.")

        # Add Entry (DB)
        with kb_tabs[1]:
            st.markdown("Add a new KB entry")
            new_cond = st.text_input("Condition", key="add_cond")
            new_desc = st.text_area("Description", key="add_desc")
            new_sym = st.text_input("Symptoms (pipe-separated | ) e.g. fever|headache", key="add_sym")
            new_fa = st.text_input("First aid (pipe-separated)", key="add_fa")
            new_prev = st.text_input("Prevention (pipe-separated)", key="add_prev")
            new_dis = st.text_input("Disclaimer", key="add_dis")
            if st.button("Add Entry", key="add_entry_btn"):
                if not new_cond.strip():
                    st.error("Condition name required.")
                else:
                    ok = add_kb_entry(new_cond.strip(), new_desc, new_sym, new_fa, new_prev, new_dis)
                    if ok:
                        st.success("Entry added to DB.")
                        # reload in-memory cache immediately
                        health_kb_lower.clear()
                        health_kb_lower.update(reload_kb())
                    else:
                        st.error("Condition likely exists in DB or an error occurred.")

        # Edit Entry (DB)
        with kb_tabs[2]:
            st.markdown("Edit DB entry")
            edit_cond = st.text_input("Condition to edit (exact DB condition)", key="edit_cond")
            if st.button("Load DB entry", key="load_db_entry"):
                e = get_kb_entry(edit_cond)
                if e:
                    st.session_state._edit_entry = e
                    st.success("Loaded DB entry. Modify fields and save.")
                else:
                    st.error("DB entry not found. Use Add Entry to create it.")

            if "_edit_entry" in st.session_state:
                loaded = st.session_state._edit_entry
                cond_name = loaded[0]
                desc = loaded[1] if len(loaded) > 1 else ""
                sym = loaded[2] if len(loaded) > 2 else ""
                fa = loaded[3] if len(loaded) > 3 else ""
                prev = loaded[4] if len(loaded) > 4 else ""
                dis = loaded[5] if len(loaded) > 5 else ""
                new_desc2 = st.text_area("Description", value=desc, key=f"edit_desc_{cond_name}")
                new_sym2 = st.text_input("Symptoms (pipe-separated)", value=sym, key=f"edit_sym_{cond_name}")
                new_fa2 = st.text_input("First aid (pipe-separated)", value=fa, key=f"edit_fa_{cond_name}")
                new_prev2 = st.text_input("Prevention (pipe-separated)", value=prev, key=f"edit_prev_{cond_name}")
                new_dis2 = st.text_input("Disclaimer", value=dis, key=f"edit_dis_{cond_name}")
                if st.button("Save Edit", key=f"save_edit_db_{cond_name}"):
                    ok = edit_kb_entry(cond_name, new_desc2, new_sym2, new_fa2, new_prev2, new_dis2)
                    if ok:
                        st.success("DB entry updated.")
                        # reload immediately
                        health_kb_lower.clear()
                        health_kb_lower.update(reload_kb())
                    else:
                        st.error("Update failed (entry not found).")
                    del st.session_state._edit_entry

        # Delete entry (DB)
        with kb_tabs[3]:
            st.markdown("Delete DB entry")
            del_cond = st.text_input("DB condition to delete (exact DB condition)", key="del_cond")
            if st.button("Delete from DB", key="delete_cond_btn"):
                if not del_cond.strip():
                    st.error("Please enter a condition to delete.")
                else:
                    deleted = delete_kb_entry(del_cond)
                    if deleted:
                        st.success("Deleted from DB (if existed).")
                    else:
                        st.info("No matching condition found in DB.")
                    # reload immediately
                    health_kb_lower.clear()
                    health_kb_lower.update(reload_kb())

        st.markdown("---")
        st.subheader("👥 User Management")
        if not users:
            st.info("No users available.")
            users_df = pd.DataFrame(columns=["id", "username", "age", "gender", "language", "account_created", "last_login"])
            st.dataframe(users_df)
        else:
            sample_len = len(users[0])
            if sample_len == 7:
                col_names = ["id", "username", "age", "gender", "language", "account_created", "last_login"]
                users_df = pd.DataFrame(users, columns=col_names)
            else:
                users_df = pd.DataFrame(users)
            st.dataframe(users_df)

        col_a, col_b = st.columns(2)
        with col_a:
            del_user = st.text_input("Username to delete", key="del_user_input")
            if st.button("Delete User", key="delete_user_btn"):
                delete_user(del_user)
                st.success("Deleted user (if existed).")
        with col_b:
            if "show_chat_history" not in st.session_state:
                st.session_state.show_chat_history = False
            if st.button("Chat History", key="toggle_chat_history_btn"):
                st.session_state.show_chat_history = not st.session_state.show_chat_history

        if st.session_state.get("show_chat_history"):
            st.subheader("💬 Chat History with feedback per chat")
            chats = get_all_chats() or []
            all_fb = get_all_feedback() or []
            fb_by_chat = {}
            for fb in all_fb:
                if len(fb) >= 6:
                    _, c_id, uname_fb, thumbs_up, comment, ts = fb
                else:
                    continue
                fb_by_chat.setdefault(c_id, []).append({"user": uname_fb, "thumbs": thumbs_up, "comment": comment, "ts": ts})

            for row in chats:  # get_all_chats already returns latest-first
                if len(row) >= 6:
                    cid, uname, query, intent, response, ts = row[0], row[1], row[2], row[3], row[4], row[5]
                else:
                    continue
                st.markdown(f"[{ts}] **{uname}** → {query} ({intent})")
                st.markdown(f"Bot → {response}")
                if cid in fb_by_chat:
                    st.markdown("Feedback:")
                    for fb in fb_by_chat[cid]:
                        icon = "👍" if fb["thumbs"] == 1 else ("👎" if fb["thumbs"] == 0 else "✏️")
                        comment_text = f" — {fb['comment']}" if fb.get("comment") else ""
                        st.markdown(f"- [{fb['ts']}] {fb['user']} | {icon}{comment_text}")
                else:
                    st.markdown("_No feedback for this chat yet._")
                st.markdown("---")

        st.markdown("---")
        st.subheader("📝 Recent Feedback")
        all_fb = get_all_feedback() or []
        if all_fb:
            for fb in all_fb[:200]:
                if len(fb) >= 6:
                    fid, chat_id, uname_fb, thumbs_up, comment, ts = fb[0], fb[1], fb[2], fb[3], fb[4], fb[5]
                else:
                    continue
                icon = "👍" if thumbs_up == 1 else ("👎" if thumbs_up == 0 else "✏️")
                st.markdown(f"[{ts}] **{uname_fb}** → Chat {chat_id} | {icon}")
                if comment:
                    st.markdown(f"> {comment}")
                st.markdown("---")
        else:
            st.info("No feedback yet.")
