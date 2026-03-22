import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

CATEGORY_ICONS = {
    "Sports":  "⚽",
    "Tech":    "💻",
    "Finance": "📈",
    "Science": "🔬",
    "Policy":  "🏛️",
}
 
SUBCATEGORY_ICONS = {
    "Football": "⚽", "Cricket": "🏏", "Basketball": "🏀", "Hockey": "🏒",
    "AI": "🤖", "Startups & Business": "🚀", "Mobile & Apps": "📱",
    "Cybersecurity": "🔒", "Stocks & Investing": "📊",
    "Crypto & Blockchain": "🪙", "India-Focused": "🇮🇳",
    "General Finance & Markets": "💰", "Central Banks & Policy": "🏦",
    "Biology & Medicine": "🧬", "Space & Astronomy": "🌌",
    "Physics & Chemistry": "⚗️", "General Science News": "🔭",
    "Indian Government": "🇮🇳", "USA": "🇺🇸",
    "International Policy Bodies": "🌍",
}


def build_newsletter_data(user: dict, articles: list) -> dict:
    prefs = user.get("preferences", {})
    filtered = [
        a for a in articles
        if a.get("category") in prefs
        and a.get("sub_category") in prefs.get(a.get("category", ""), [])
    ]
    grouped = defaultdict(list)
    for article in filtered:
        grouped[article["category"]].append(article)

    categories = []
    for cat_name, art_list in grouped.items():
        art_list.sort(key=lambda x: (not x.get("is_breaking", False),
                                     -x.get("score", 0)))
        categories.append({
            "id":       cat_name.lower().replace(" ", "-"),
            "name":     cat_name,
            "icon":     CATEGORY_ICONS.get(cat_name, "📰"),
            "articles": art_list[:5],   
        })

    
    hour = datetime.now().hour
    if hour < 12:
        time_of_day = "morning"
    elif hour < 17:
        time_of_day = "afternoon"
    else:
        time_of_day = "evening"

    return {
        "user_name":      user["name"],
        "user_email":     user["email"],
        "date":           datetime.now().strftime("%A, %d %B %Y"),
        "edition":        datetime.now().strftime("%Y%m%d"),
        "time_of_day":    time_of_day,
        "categories":     categories,
        "total_articles": len(filtered),
        "total_sources":  len(set(a["source"] for a in filtered)),
        "total_topics":   sum(len(v) for v in prefs.values()),
        "breaking_count": sum(1 for a in filtered if a.get("is_breaking")),
    }


def render_newsletter(data: dict, template_path: str = "src/Gmail/newsletter_template.html") -> str:
    template_dir  = os.path.dirname(os.path.abspath(template_path))
    template_file = os.path.basename(template_path)

    env      = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template_file)
    return template.render(**data)


def send_via_gmail(to_email: str, to_name: str,html_content: str, date_str: str):
    GMAIL_USER     = os.getenv("GMAIL_USER",     "")
    GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD", "")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📡 NewsFlow Digest — {date_str}"
    msg["From"]    = f"NewsFlow <{GMAIL_USER}>"
    msg["To"]      = f"{to_name} <{to_email}>"

    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USER, to_email, msg.as_string())
        print(f"  ✅ Email sent to {to_email}")
        return True
    except smtplib.SMTPAuthenticationError:
        print("  ❌ Gmail auth failed — check GMAIL_USER and GMAIL_PASSWORD")
        return False
    except Exception as e:
        print(f"  ❌ Failed to send to {to_email}: {e}")
        return False


def generate_and_send(user: dict, articles: list,template_path: str = "src/Gmail/newsletter_template.html"):

    print(f"\n📡 Generating newsletter for {user['name']}...")

    data = build_newsletter_data(user, articles)
    print(f"  Topics: {data['total_topics']} | "
          f"Articles: {data['total_articles']} | "
          f"Breaking: {data['breaking_count']}")

    if data["total_articles"] == 0:
        print("  ⚠️  No articles match user preferences — skipping.")
        return False

    html = render_newsletter(data, template_path)
    print(f"  Rendered {len(html):,} chars of HTML")

    
    return send_via_gmail(user["email"], user["name"],html, data["date"])


def send_to_all_users(users: list, articles: list):

    print(f"\n📬 Sending newsletters to {len(users)} users...")
    results = {"sent": 0, "failed": 0, "skipped": 0}

    for user in users:
        success = generate_and_send(
            user, articles
        )
        if success is True:
            results["sent"] += 1
        elif success is False:
            results["failed"] += 1
        else:
            results["skipped"] += 1

    print(f"\n✅ Done — Sent: {results['sent']} | "
          f"Failed: {results['failed']} | "
          f"Skipped: {results['skipped']}")
    return results








