from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv
import psycopg2
import os
import time
import random
from datetime import datetime, timedelta
from src.app.all_function_2 import *
from src.Gmail.send_mail import *
from apscheduler.events import EVENT_JOB_ADDED

last_call_time = 0

def rate_limited_call(workflow, payload, min_interval=6):
    global last_call_time

    now = time.time()
    elapsed = now - last_call_time

    if elapsed < min_interval:
        sleep_time = min_interval - elapsed
        print(f"⏳ Waiting {sleep_time:.2f}s to avoid rate limit", flush=True)
        time.sleep(sleep_time)

    result = safe_invoke(workflow, payload)
    last_call_time = time.time()

    return result



def safe_invoke(workflow, payload, max_retries=5):
    base_delay = 5

    for attempt in range(max_retries):
        try:
            return workflow.invoke(payload)

        except Exception as e:
            error_msg = str(e)

            if "429" in error_msg or "rate limit" in error_msg.lower():
                wait_time = base_delay * (2 ** attempt) + random.uniform(0, 2)
                print(f"⚠️ 429 Rate limit hit. Retrying in {wait_time:.2f}s...", flush=True)
                time.sleep(wait_time)
            else:
                print(f"❌ Non-retryable error: {e}", flush=True)
                raise e

    raise Exception("❌ Max retries exceeded due to rate limits")

def my_listener(event):
    job = scheduler.get_job(event.job_id)
    if job:
        print(f"⏰ Next run: {job.next_run_time}", flush=True)

def modify_data(user_data):
    new_set = []
    for item in user_data:
        for sub in item['subcategories']:
            new_set.append({
                "category": item["category"],
                "preference": sub
            })
    return new_set


def convert_data(items):
    return [
        {
            "title": item.title,
            "url": item.url,
            "source": item.source,
            "category": item.category,
            "sub_category": item.preference,
            "summary": item.summary,
            "is_breaking": item.is_breaking,
            "score": item.score
        }
        for item in items
    ]



def excute_workflow(workflow, name, email, preferences):
    print(f"👤 Processing user: {email}", flush=True)

    modified_pref = modify_data(preferences)
    all_res = []

    for item in modified_pref:
        try:
            print(f"🔄 Processing item: {item}", flush=True)

            workflow_res = rate_limited_call(
                workflow,
                {"items": [item]}   
            )

            for key in workflow_res['final_res']:
                final_re = convert_data(
                    workflow_res['final_res'][key]['final_output'].details
                )
                all_res.append(final_re[0])

            time.sleep(5)  

        except Exception as e:
            print(f"❌ Error processing item {item}: {e}", flush=True)
            continue

    print("✅ Completed Extracting Summary", flush=True)

    user_pref = {
        item['category']: item['subcategories']
        for item in preferences
    }

    user = {
        "name": name,
        "email": email,
        "preferences": user_pref
    }

    generate_and_send(
        user,
        articles=all_res,
        template_path="src/Gmail/newsletter_template.html"
    )

    print(f"📩 Email sent to: {name}\n", flush=True)


def run_pipeline():
    load_dotenv()

    passw = os.environ.get("supabase_pass", "")

    print("connection setup")

    obj = Workflow2()
    workflow = obj.build_final_workflow()

    try:
        conn = psycopg2.connect(
            f"postgresql://postgres.engepyysrjkmhxkumyit:{passw}@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres"
        )
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users_database;")
        users_data = cursor.fetchall()

        conn.close()  

        for data in users_data:
            _, name, email, preferences = data
            excute_workflow(workflow, name, email=email, preferences=preferences)

        conn = psycopg2.connect(
            f"postgresql://postgres.engepyysrjkmhxkumyit:{passw}@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres"
        )
        cursor = conn.cursor()

        cursor.execute("UPDATE scheduler_state SET last_run = NOW();")
        conn.commit()
        conn.close()

    except Exception as e:
        print("❌ Error:", e)

if __name__ == "__main__":
    print("🔥 Scheduler starting...", flush=True)

    scheduler = BlockingScheduler()

    scheduler.add_job(
        run_pipeline,
        trigger=IntervalTrigger(days=1),
        id="news_pipeline",
        replace_existing=True,
        next_run_time=datetime.now() + timedelta(seconds=10)
    )

    scheduler.add_listener(my_listener, EVENT_JOB_ADDED)

    print("🚀 Scheduler running...", flush=True)

    scheduler.start()
