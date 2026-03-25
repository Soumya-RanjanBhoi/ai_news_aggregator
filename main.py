import streamlit as st
import json
import re
import requests
from src.datasource import rss_category_feeds

API_BASE = "http://api:8000/"


st.set_page_config(
    page_title="NewsFlow — Personalized News",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

CATEGORY_ICONS = {
    "Sports": "⚽",
    "Tech": "💻",
    "Finance": "📈",
    "Science": "🔬",
    "Policy": "🏛️"
}

SUBCATEGORY_ICONS = {
    "Football": "⚽", "Cricket": "🏏", "Basketball": "🏀", "Hockey": "🏒",
    "AI": "🤖", "Startups & Business": "🚀", "Mobile & Apps": "📱", "Cybersecurity": "🔒",
    "Stocks & Investing": "📊", "Crypto & Blockchain": "🪙", "India-Focused": "🇮🇳",
    "General Finance & Markets": "💰", "Central Banks & Policy": "🏦",
    "Biology & Medicine": "🧬", "Space & Astronomy": "🚀", "Physics & Chemistry": "⚗️",
    "General Science News": "🔭",
    "Indian Government": "🇮🇳", "USA": "🇺🇸", "International Policy Bodies": "🌍"
}


def api_get_user(email: str):
    try:
        resp = requests.get(
            f"{API_BASE}/get_user",
            params={"email": email},
            timeout=5
        )

        if resp.status_code == 200:
            return resp.json()

        elif resp.status_code == 404:
            return None

        else:
            try:
                error_detail = resp.json().get("detail", "Unknown error")
            except Exception:
                error_detail = resp.text  # fallback

            raise RuntimeError(f"API Error ({resp.status_code}): {error_detail}")

    except requests.exceptions.ConnectionError:
        raise RuntimeError("Cannot reach API server")

def api_create_user(name: str, email: str, preferences: list):
    try:
        resp = requests.post(
            f"{API_BASE}/create_user",
            json={"name": name, "email": email, "preferences": preferences},
            timeout=5,
        )
        if resp.status_code == 200:
            return resp.json()
        else:
            raise RuntimeError(resp.json().get("detail", "Failed to create user."))
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Cannot reach the API. Make sure the server is running on http://127.0.0.1:8000")


def api_update_preferences(email: str, preferences: list):
    try:
        resp = requests.put(
            f"{API_BASE}/user/{email}",
            json={"preferences": preferences},
            timeout=5,
        )
        if resp.status_code == 200:
            return resp.json()
        else:
            raise RuntimeError(resp.json().get("detail", "Failed to update preferences."))
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Cannot reach the API. Make sure the server is running on http://127.0.0.1:8000")


def build_preferences_payload(preferences_dict: dict) -> list:
    return [
        {"category": cat, "subcategories": subs}
        for cat, subs in preferences_dict.items()
    ]


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
.block-container { padding-top: 2rem; padding-bottom: 4rem; max-width: 1100px; }

.hero {
    background: linear-gradient(135deg, #0a0a0f 0%, #0d1b2a 50%, #0a0a0f 100%);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 24px;
    padding: 56px 48px;
    text-align: center;
    margin-bottom: 48px;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -60px; left: 50%; transform: translateX(-50%);
    width: 400px; height: 200px;
    background: radial-gradient(ellipse, rgba(99,179,237,0.12) 0%, transparent 70%);
    pointer-events: none;
}
.hero-eyebrow {
    font-family: 'DM Sans', sans-serif;
    font-size: 11px; font-weight: 600; letter-spacing: 3px;
    text-transform: uppercase; color: #63b3ed; margin-bottom: 16px;
}
.hero-title {
    font-family: 'Playfair Display', serif;
    font-size: clamp(38px, 6vw, 64px); font-weight: 900;
    color: #f7fafc; line-height: 1.1; margin-bottom: 16px;
}
.hero-title span { color: #63b3ed; }
.hero-subtitle {
    font-size: 16px; color: rgba(255,255,255,0.45);
    font-weight: 300; max-width: 480px; margin: 0 auto; line-height: 1.7;
}

.step-indicator { display: flex; justify-content: center; gap: 0; margin-bottom: 40px; }
.step-item {
    display: flex; align-items: center; gap: 10px;
    font-size: 13px; font-weight: 500; color: rgba(255,255,255,0.3);
    padding: 10px 20px; border-radius: 40px;
}
.step-item.active {
    background: rgba(99,179,237,0.1); color: #63b3ed;
    border: 1px solid rgba(99,179,237,0.25);
}
.step-item.done { color: rgba(255,255,255,0.5); }
.step-num {
    width: 24px; height: 24px; border-radius: 50%;
    background: rgba(255,255,255,0.08);
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 11px; font-weight: 700;
}
.step-item.active .step-num { background: #63b3ed; color: #0a0a0f; }
.step-item.done .step-num { background: rgba(72,187,120,0.3); color: #48bb78; }

.section-card {
    background: #0d1117; border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px; padding: 32px; margin-bottom: 24px;
}
.section-label {
    font-size: 10px; font-weight: 700; letter-spacing: 2.5px;
    text-transform: uppercase; color: #63b3ed; margin-bottom: 6px;
}
.section-title {
    font-family: 'Playfair Display', serif;
    font-size: 22px; font-weight: 700; color: #f7fafc; margin-bottom: 6px;
}
.section-desc {
    font-size: 14px; color: rgba(255,255,255,0.38);
    margin-bottom: 28px; line-height: 1.6;
}

div[data-testid="stTextInput"] > label,
div[data-testid="stSelectbox"] > label {
    font-size: 12px !important; font-weight: 600 !important;
    letter-spacing: 1.5px !important; text-transform: uppercase !important;
    color: rgba(255,255,255,0.45) !important; margin-bottom: 6px !important;
}
div[data-testid="stTextInput"] input {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important; color: #f7fafc !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 15px !important; padding: 14px 16px !important;
    transition: border-color 0.2s !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: rgba(99,179,237,0.5) !important;
    box-shadow: 0 0 0 3px rgba(99,179,237,0.08) !important;
}

.category-header {
    display: flex; align-items: center; gap: 10px;
    padding: 14px 18px; background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px; margin-bottom: 12px; cursor: default;
}
.category-icon { font-size: 20px; }
.category-name { font-size: 14px; font-weight: 600; color: #e2e8f0; }
.category-count {
    margin-left: auto; font-size: 11px; color: rgba(255,255,255,0.3);
    background: rgba(255,255,255,0.06); padding: 2px 8px; border-radius: 20px;
}

div[data-testid="stCheckbox"] {
    background: rgba(255,255,255,0.025); border: 1px solid rgba(255,255,255,0.06);
    border-radius: 8px; padding: 10px 14px; margin-bottom: 6px;
    transition: background 0.15s, border-color 0.15s;
}
div[data-testid="stCheckbox"]:hover {
    background: rgba(99,179,237,0.05); border-color: rgba(99,179,237,0.2);
}
div[data-testid="stCheckbox"] label {
    font-size: 13px !important; font-weight: 400 !important;
    color: rgba(255,255,255,0.7) !important; cursor: pointer !important;
}

.pill-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 16px; }
.pill {
    background: rgba(99,179,237,0.1); border: 1px solid rgba(99,179,237,0.22);
    color: #90cdf4; font-size: 12px; font-weight: 500;
    padding: 4px 12px; border-radius: 20px;
}
.pill.green {
    background: rgba(72,187,120,0.1); border-color: rgba(72,187,120,0.22); color: #9ae6b4;
}

div[data-testid="stButton"] > button {
    width: 100%; background: #63b3ed !important; color: #0a0a0f !important;
    font-family: 'DM Sans', sans-serif !important; font-size: 15px !important;
    font-weight: 700 !important; letter-spacing: 0.5px !important;
    padding: 16px 32px !important; border: none !important;
    border-radius: 12px !important; cursor: pointer !important;
    transition: all 0.2s !important;
}
div[data-testid="stButton"] > button:hover {
    background: #90cdf4 !important; transform: translateY(-1px);
}

.success-card {
    background: linear-gradient(135deg, #0d2818 0%, #0a1f10 100%);
    border: 1px solid rgba(72,187,120,0.25);
    border-radius: 20px; padding: 40px; text-align: center;
}
.success-icon { font-size: 48px; margin-bottom: 16px; }
.success-title {
    font-family: 'Playfair Display', serif; font-size: 28px;
    font-weight: 700; color: #9ae6b4; margin-bottom: 8px;
}
.success-subtitle { font-size: 14px; color: rgba(255,255,255,0.4); line-height: 1.7; }

.summary-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 14px;
}
.summary-row:last-child { border-bottom: none; }
.summary-key { color: rgba(255,255,255,0.4); font-weight: 400; }
.summary-val { color: #e2e8f0; font-weight: 500; }

.feed-count {
    display: inline-block; background: rgba(99,179,237,0.12); color: #90cdf4;
    font-size: 11px; font-weight: 600; padding: 2px 8px;
    border-radius: 10px; margin-left: 6px;
}

.styled-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
    margin: 32px 0;
}

.stApp { background: #06080d; }
section[data-testid="stSidebar"] { background: #0d1117; }
</style>
""", unsafe_allow_html=True)


if "step" not in st.session_state:
    st.session_state.step = 1
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "user_data" not in st.session_state:
    st.session_state.user_data = {}
if "is_returning_user" not in st.session_state:
    st.session_state.is_returning_user = False


st.markdown("""
<div class="hero">
    <div class="hero-eyebrow">📡 Intelligent News Aggregator</div>
    <div class="hero-title">Your feed,<br><span>your rules</span></div>
    <div class="hero-subtitle">Get AI-curated news from 50+ sources across sports, tech, finance, science and policy — personalised exactly to you.</div>
</div>
""", unsafe_allow_html=True)


if st.session_state.submitted:
    ud = st.session_state.user_data
    total_feeds = sum(
        len(urls)
        for cat, subs in rss_category_feeds.items()
        for sub, urls in subs.items()
        if cat in ud.get("preferences", {}) and sub in ud["preferences"][cat]
    )

    st.markdown(f"""
    <div class="success-card">
        <div class="success-icon">🎉</div>
        <div class="success-title">You're all set, {ud['name'].split()[0]}!</div>
        <div class="success-subtitle">
            Your personalised feed is ready.<br>
            We'll deliver curated news straight to your inbox at
            <strong style="color:#9ae6b4">{ud['email']}</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='styled-divider'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    
    with col1:
        st.markdown(f"""
        <div class="section-card">
            <div class="section-label">Your profile</div>
            <div class="summary-row">
                <span class="summary-key">Name</span>
                <span class="summary-val">{ud['name']}</span>
            </div>
            <div class="summary-row">
                <span class="summary-key">Email</span>
                <span class="summary-val">{ud['email']}</span>
            </div>
            <div class="summary-row">
                <span class="summary-key">Active feeds</span>
                <span class="summary-val">{total_feeds} RSS sources</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    
    with col2:
        pill_html = "".join([
            f"<span class='pill'>{SUBCATEGORY_ICONS.get(sub, '•')} {sub}</span>"
            for cat, subs in ud.get("preferences", {}).items()
            for sub in subs
        ])
        st.markdown(f"""
        <div class="section-card">
            <div class="section-label">Selected topics</div>
            <div class="pill-row">{pill_html}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    with st.expander("🔗 View your active RSS feed URLs"):
        for cat, subs in ud.get("preferences", {}).items():
            for sub in subs:
                feeds = rss_category_feeds.get(cat, {}).get(sub, [])
                if feeds:
                    st.markdown(f"**{CATEGORY_ICONS.get(cat,'')} {cat} → {sub}**")
                    for f in feeds:
                        st.code(f, language=None)

    export_data = {
        "user": {"name": ud["name"], "email": ud["email"]},
        "preferences": {
            cat: {
                sub: rss_category_feeds[cat][sub]
                for sub in subs
                if sub in rss_category_feeds.get(cat, {})
            }
            for cat, subs in ud.get("preferences", {}).items()
        }
    }
    st.download_button(
        label="⬇️  Download preferences as JSON",
        data=json.dumps(export_data, indent=2),
        file_name="newsflow_preferences.json",
        mime="application/json"
    )

    if st.button("✏️  Edit preferences"):
        st.session_state.submitted = False
        st.session_state.step = 1
        st.rerun()

    st.stop()


step = st.session_state.step
s1 = "active" if step == 1 else "done" if step > 1 else ""
s2 = "active" if step == 2 else "done" if step > 2 else ""
s3 = "active" if step == 3 else ""

st.markdown(f"""
<div class="step-indicator">
    <div class="step-item {s1}">
        <span class="step-num">{'✓' if step > 1 else '1'}</span> Your details
    </div>
    <span style="color:rgba(255,255,255,0.15);padding:0 4px;align-self:center">——</span>
    <div class="step-item {s2}">
        <span class="step-num">{'✓' if step > 2 else '2'}</span> Pick topics
    </div>
    <span style="color:rgba(255,255,255,0.15);padding:0 4px;align-self:center">——</span>
    <div class="step-item {s3}">
        <span class="step-num">3</span> Confirm
    </div>
</div>
""", unsafe_allow_html=True)


if step == 1:
    st.markdown("""
    <div class="section-card">
        <div class="section-label">Step 1 of 3</div>
        <div class="section-title">Tell us about you</div>
        <div class="section-desc">We'll use this to personalise your daily news digest and deliver it to your inbox.</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name", placeholder="e.g. Arjun Sharma",
                             value=st.session_state.user_data.get("name", ""))
    with col2:
        email = st.text_input("Email Address", placeholder="e.g. arjun@example.com",
                              value=st.session_state.user_data.get("email", ""))

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Continue to Topics →"):
        if not name.strip():
            st.error("Please enter your name.")
        elif not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email.strip()):
            st.error("Please enter a valid email address.")
        else:
            with st.spinner("Checking your account..."):
                try:
                    existing_user = api_get_user(email.strip())

                    st.session_state.user_data["name"] = name.strip()
                    st.session_state.user_data["email"] = email.strip()

                    if existing_user:
                        st.session_state.is_returning_user = True
                        saved_prefs = {}
                        for item in existing_user.get("preferences", []):
                            saved_prefs[item["category"]] = item["subcategories"]
                        st.session_state.user_data["preferences"] = saved_prefs
                        st.info("Welcome back! Your previous preferences have been loaded.")
                    else:
                        st.session_state.is_returning_user = False

                    st.session_state.step = 2
                    st.rerun()

                except RuntimeError as e:
                    st.error(str(e))


elif step == 2:
    st.markdown(f"""
    <div class="section-card">
        <div class="section-label">Step 2 of 3</div>
        <div class="section-title">Choose your topics</div>
        <div class="section-desc">Select the categories you care about. You can pick as many as you like — we'll pull from {sum(len(urls) for cat in rss_category_feeds.values() for urls in cat.values())}+ RSS sources.</div>
    </div>
    """, unsafe_allow_html=True)

    selected_prefs = {}
    prev_prefs = st.session_state.user_data.get("preferences", {})

    for category, subcategories in rss_category_feeds.items():
        cat_icon = CATEGORY_ICONS.get(category, "•")
        total_subs = len(subcategories)

        st.markdown(f"""
        <div class="category-header">
            <span class="category-icon">{cat_icon}</span>
            <span class="category-name">{category}</span>
            <span class="category-count">{total_subs} topics</span>
        </div>
        """, unsafe_allow_html=True)

        cols = st.columns(2)
        selected_subs = []
        for i, (subcat, feeds) in enumerate(subcategories.items()):
            sub_icon = SUBCATEGORY_ICONS.get(subcat, "•")
            label = f"{sub_icon}  {subcat}  ·  {len(feeds)} feeds"
            default = subcat in prev_prefs.get(category, [])
            with cols[i % 2]:
                checked = st.checkbox(label, value=default, key=f"chk_{category}_{subcat}")
                if checked:
                    selected_subs.append(subcat)

        if selected_subs:
            selected_prefs[category] = selected_subs

        st.markdown("<div class='styled-divider'></div>", unsafe_allow_html=True)

    total_selected = sum(len(v) for v in selected_prefs.values())
    total_feeds_selected = sum(
        len(rss_category_feeds[cat][sub])
        for cat, subs in selected_prefs.items()
        for sub in subs
    )

    if total_selected > 0:
        pill_html = "".join([
            f"<span class='pill'>{SUBCATEGORY_ICONS.get(sub, '•')} {sub}</span>"
            for cat, subs in selected_prefs.items()
            for sub in subs
        ])
        st.markdown(f"""
        <div class="section-card" style="border-color:rgba(99,179,237,0.15)">
            <div class="section-label">Your selection — {total_selected} topics · {total_feeds_selected} RSS feeds</div>
            <div class="pill-row">{pill_html}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("← Back"):
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button("Review & Confirm →"):
            if not selected_prefs:
                st.error("Please select at least one topic.")
            else:
                st.session_state.user_data["preferences"] = selected_prefs
                st.session_state.step = 3
                st.rerun()


elif step == 3:
    ud = st.session_state.user_data
    prefs = ud.get("preferences", {})

    st.markdown("""
    <div class="section-card">
        <div class="section-label">Step 3 of 3</div>
        <div class="section-title">Review your profile</div>
        <div class="section-desc">Everything look right? Hit confirm to activate your feed.</div>
    </div>
    """, unsafe_allow_html=True)

    total_feeds_selected = sum(
        len(rss_category_feeds[cat][sub])
        for cat, subs in prefs.items()
        for sub in subs
    )
    total_topics = sum(len(v) for v in prefs.values())

    col1, col2 = st.columns([1, 1])


    with col1:
        st.markdown(f"""
        <div class="section-card">
            <div class="section-label">Profile</div>
            <div class="summary-row">
                <span class="summary-key">Name</span>
                <span class="summary-val">{ud['name']}</span>
            </div>
            <div class="summary-row">
                <span class="summary-key">Email</span>
                <span class="summary-val">{ud['email']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


    with col2:
        st.markdown(f"""
        <div class="section-card">
            <div class="section-label">Feed summary</div>
            <div class="summary-row">
                <span class="summary-key">Topics selected</span>
                <span class="summary-val">{total_topics}</span>
            </div>
            <div class="summary-row">
                <span class="summary-key">Active RSS feeds</span>
                <span class="summary-val">{total_feeds_selected}</span>
            </div>
            <div class="summary-row">
                <span class="summary-key">Categories</span>
                <span class="summary-val">{', '.join(prefs.keys())}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

  
    breakdown_rows = "".join([
        f"""<div class="summary-row">
            <span class="summary-key">{CATEGORY_ICONS.get(cat, '•')} {cat}</span>
            <span class="summary-val">
                {"  ".join([f'<span class="feed-count">{SUBCATEGORY_ICONS.get(s, "")}&nbsp;{s}</span>' for s in subs])}
                &nbsp;·&nbsp; {sum(len(rss_category_feeds[cat][sub]) for sub in subs)} feeds
            </span>
        </div>"""
        for cat, subs in prefs.items()
    ])
    st.markdown(f"""
    <div class="section-card">
        <div class="section-label">Topic breakdown</div>
        {breakdown_rows}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("← Edit topics"):
            st.session_state.step = 2
            st.rerun()
    with col2:
        if st.button("🚀  Activate my NewsFlow feed"):
            preferences_payload = build_preferences_payload(prefs)
            with st.spinner("Saving your preferences..."):
                try:
                    if st.session_state.is_returning_user:
                        api_update_preferences(ud["email"], preferences_payload)
                    else:
                        api_create_user(ud["name"], ud["email"], preferences_payload)
                    st.session_state.submitted = True
                    st.rerun()
                except RuntimeError as e:
                    st.error(f"Could not save your profile: {str(e)}")