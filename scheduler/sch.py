from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv
import psycopg2
from src.app.all_function_2 import *
from src.Gmail.send_mail import *
from apscheduler.events import EVENT_JOB_ADDED


def my_listener(event):
    job = scheduler.get_job(event.job_id)
    if job:
        print(f"⏰ Next run calculated: {job.next_run_time}")

def modify_data(user_data):
    new_set=[]
    for item in user_data:
        no_items = len(item['subcategories'])
        for i in range(no_items):
            rs=dict({"category":item["category"],"preference":item["subcategories"][i]})
            new_set.append(rs)
    return new_set

def convert_data(items):
    return [
    {"title":item.title , "url": item.url ,"source":item.source, "category":item.category,"sub_category":item.preference,"summary":item.summary,"is_breaking":item.is_breaking,"score":item.score}
    for item in items ]



def excute_workflow(workflow,name,email,preferences):
    modified_pref=modify_data(preferences)
    workflow_res=workflow.invoke({"items":modified_pref})
    print("Completed Extracting Summary")
    print()

    all_res=[]
    for all in workflow_res['final_res']:
        final_re=convert_data(workflow_res['final_res'][all]['final_output'].details)
        all_res.append(final_re[0])

    print("Completed converting articles")
    
    user_pref={}
    for item in preferences:
        user_pref[item['category']]=item['subcategories']

    print("Modified user preferences")

    user={
        "name":name,
        "email":email,
        "preferences":user_pref
    }

    articles=all_res

    generate_and_send(user,articles=articles,template_path="src/Gmail/newsletter_template.html")
    print("Completed for user",name)
    print()

def run_pipeline():
    load_dotenv() 

    passw=os.environ.get("supabase_pass","")
    conn = psycopg2.connect("postgresql://postgres:{}@db.engepyysrjkmhxkumyit.supabase.co:5432/postgres".format(passw))
    cursor = conn.cursor()

    print("connection setup")

    obj = Workflow2()
    workflow = obj.build_final_workflow()
    try:
        cursor.execute("SELECT * FROM users_database;")
        users_data= cursor.fetchall()

        for data in users_data:
            _,name,email,preferences=data 
            excute_workflow(workflow,name,email=email,preferences=preferences)

    except Exception as e:
        print("Error:",e)
        print("rolling back...")
        conn.rollback()
        cursor.execute("SELECT * FROM users_database;")
        users_data= cursor.fetchall()

        for data in users_data:
            _,name,email,preferences=data 
            excute_workflow(workflow,name,email=email,preferences=preferences)


if __name__=="__main__":
    print("✅ Scheduler running. Press Ctrl+C to stop.")

    try:
        scheduler = BlockingScheduler()
        scheduler.add_job(run_pipeline,trigger=IntervalTrigger(minutes=3),id="news_pipeline",name="News Aggregator Pipeline",replace_existing=True)

        scheduler.add_listener(my_listener, EVENT_JOB_ADDED)
        scheduler.start()
    except KeyboardInterrupt:
        print("Scheduler stopped.")
