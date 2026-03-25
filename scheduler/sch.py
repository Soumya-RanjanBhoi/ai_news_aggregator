
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv
import psycopg2
import os
import time
from datetime import datetime, timedelta
from src.app.all_function_2 import *
from src.Gmail.send_mail import *
from apscheduler.events import EVENT_JOB_ADDED


def my_listener(event):
    job = scheduler.get_job(event.job_id)
    if job:
        print(f"⏰ Next run calculated: {job.next_run_time}")


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
    modified_pref = modify_data(preferences)

    workflow_res = workflow.invoke({"items": modified_pref})
    print("✅ Completed Extracting Summary")

    all_res = []
    for key in workflow_res['final_res']:
        final_re = convert_data(
            workflow_res['final_res'][key]['final_output'].details
        )
        all_res.append(final_re[0])

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

    print(f"📩 Completed for user: {name}\n")



def run_pipeline():
    load_dotenv()

    passw = os.environ.get("supabase_pass", "")

    conn = psycopg2.connect(
        f"postgresql://postgres.engepyysrjkmhxkumyit:{passw}@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres"
    )
    cursor = conn.cursor()

    print("🔌 DB connection setup")

    cursor.execute("SELECT last_run FROM scheduler_state ORDER BY id DESC LIMIT 1;")
    last_run = cursor.fetchone()[0]

    now = datetime.now()

    if last_run and (now - last_run) < timedelta(days=3):
        print("⏳ Skipping run (last run < 3 days ago)")
        return

    print("🚀 Running pipeline...")

    obj = Workflow2()
    workflow = obj.build_final_workflow()

    try:
        cursor.execute("SELECT * FROM users_database;")
        users_data = cursor.fetchall()

        for data in users_data:
            try:
                _, name, email, preferences = data
                print(f"➡️ Processing: {email}")

                excute_workflow(
                    workflow,
                    name,
                    email=email,
                    preferences=preferences
                )

                time.sleep(5)  

            except Exception as e:
                print(f"❌ Error for {data}: {e}")
                continue

        cursor.execute("UPDATE scheduler_state SET last_run = NOW();")
        conn.commit()

        print("✅ Pipeline completed successfully\n")

    except Exception as e:
        print("❌ Pipeline failed:", e)
        conn.rollback()


if __name__ == "__main__":
    print("✅ Scheduler running")

    scheduler = BlockingScheduler()

    scheduler.add_job(
        run_pipeline,
        trigger=IntervalTrigger(days=3),
        id="news_pipeline",
        name="News Aggregator Pipeline",
        replace_existing=True,
        next_run_time=datetime.now() + timedelta(seconds=10) 
    )

    scheduler.add_listener(my_listener, EVENT_JOB_ADDED)

    scheduler.start()