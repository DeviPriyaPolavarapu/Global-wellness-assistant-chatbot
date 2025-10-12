# translator.py
from transformers import MarianMTModel, MarianTokenizer

# --- Machine translation models (English <-> Hindi) ---
# Make sure these models are downloaded locally or via Hugging Face
en_hi_model_name = "Helsinki-NLP/opus-mt-en-hi"
hi_en_model_name = "Helsinki-NLP/opus-mt-hi-en"

en_hi_tokenizer = MarianTokenizer.from_pretrained(en_hi_model_name)
en_hi_model = MarianMTModel.from_pretrained(en_hi_model_name)

hi_en_tokenizer = MarianTokenizer.from_pretrained(hi_en_model_name)
hi_en_model = MarianMTModel.from_pretrained(hi_en_model_name)

def translate_en_to_hi(text):
    if not text:
        return ""
    translated = en_hi_model.generate(**en_hi_tokenizer(text, return_tensors="pt", padding=True))
    return en_hi_tokenizer.decode(translated[0], skip_special_tokens=True)

def translate_hi_to_en(text):
    if not text:
        return ""
    translated = hi_en_model.generate(**hi_en_tokenizer(text, return_tensors="pt", padding=True))
    return hi_en_tokenizer.decode(translated[0], skip_special_tokens=True)

def ui_texts(language=None):
    """
    Returns a dictionary of UI texts based on language.
    Defaults to English if None or unknown value.
    """
    language = (language or "English").lower()

    texts_en = {
        "you_label": "You",
        "bot_label": "WellBot",
        "profile_subheader": "Your Profile",
        "account_created": "Account created on: {val}",
        "last_login": "Last login: {val}",
        "last_profile_update": "Last profile update: {val}",
        "age_label": "Age",
        "gender_label": "Gender",
        "gender_male": "Male",
        "gender_female": "Female",
        "gender_others": "Others",
        "preferred_language_label": "Preferred Language",
        "lang_english": "English",
        "lang_hindi": "Hindi",
        "update_profile_btn": "Update Profile",
        "delete_account_btn": "Delete Account",
        "chat_header": "Chat with WellBot",
        "select_chat_language": "Select Chat Language",
        "send_btn": "Send",
        "logout_btn": "Logout",
        "feedback_thanks": "Thanks for your feedback!",
        "feedback_recorded": "Feedback recorded.",
        "comment_optional": "Add a comment (optional)",
        "comment_saved": "Comment saved successfully!"
    }

    texts_hi = {
        "you_label": "आप",
        "bot_label": "वेलबॉट",
        "profile_subheader": "आपकी प्रोफ़ाइल",
        "account_created": "खाता बनाया गया: {val}",
        "last_login": "अंतिम लॉगिन: {val}",
        "last_profile_update": "अंतिम प्रोफ़ाइल अपडेट: {val}",
        "age_label": "उम्र",
        "gender_label": "लिंग",
        "gender_male": "पुरुष",
        "gender_female": "महिला",
        "gender_others": "अन्य",
        "preferred_language_label": "पसंदीदा भाषा",
        "lang_english": "अंग्रेज़ी",
        "lang_hindi": "हिंदी",
        "update_profile_btn": "प्रोफ़ाइल अपडेट करें",
        "delete_account_btn": "खाता हटाएँ",
        "chat_header": "वेलबॉट से चैट करें",
        "select_chat_language": "चैट भाषा चुनें",
        "send_btn": "भेजें",
        "logout_btn": "लॉगआउट",
        "feedback_thanks": "आपके फीडबैक के लिए धन्यवाद!",
        "feedback_recorded": "फीडबैक दर्ज किया गया।",
        "comment_optional": "टिप्पणी जोड़ें (वैकल्पिक)",
        "comment_saved": "टिप्पणी सफलतापूर्वक सहेजी गई!"
    }

    if language == "hindi":
        return texts_hi
    else:
        return texts_en
