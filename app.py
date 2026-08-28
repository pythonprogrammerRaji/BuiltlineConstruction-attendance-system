from flask import Flask, render_template, request, redirect, jsonify, session, flash
from datetime import datetime, timedelta, date
from openpyxl import Workbook
import time
import os
import cloudinary
import cloudinary.uploader

from config import (
    supabase,
    SECRET_KEY,
    ADMIN_SECRET
)

app = Flask(__name__)
app.secret_key = SECRET_KEY

@app.after_request
def add_no_cache(response):
    # tell browser never to cache files
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"]        = "no-cache"
    response.headers["Expires"]       = "0"
    return response

@app.route("/")
def home():
    return render_template("register.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        full_name = request.form.get("full_name").strip()
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")
        try:
            # insert user in database
            supabase.table("users").insert({
                "full_name": full_name,
                "email": email,
                "password": password,
                "role": role
            }).execute()

            return redirect("/login")

        except Exception as e:
            return f"Error: {str(e)}"

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form.get("role")
        email = request.form.get("email")
        password = request.form.get("password")
        admin_key = request.form.get("admin_key")

        try:
            user = supabase.table("users")\
                .select("*")\
                .eq("email", email)\
                .eq("password", password)\
                .execute()
            
            if user.data:
                db_role = user.data[0]["role"]
                if role == "admin":
                    if db_role == "Admin" and admin_key == ADMIN_SECRET:
                        session["worker_name"] = user.data[0]["full_name"]
                        session["role"]        = "admin"
                        print("SESSION ROLE SAVED:", session.get("role"))
                        return redirect("/admin-dashboard")

                elif role == "Site Engineer":
                    if db_role == "Site Engineer":
                        session["worker_name"] = user.data[0]["full_name"]
                        session["role"]        = "engineer"
                        return redirect("/engineer_page")

                elif role == "office":
                    if db_role == "Supervisor":
                        session["worker_name"] = user.data[0]["full_name"]
                        session["role"]        = "office"
                        return redirect("/office-dashboard")
                        
                return "Invalid Email or Password"
        
        except Exception as e:
            return f"Error: {str(e)}"

    return render_template("login.html")


# project assigned
@app.route("/add-project", methods=["POST"])
def add_project():
    project_name = request.form.get("project_name")
    engineer_name = request.form.get("engineer_name")
    try:
        supabase.table("project_assignments").insert({"project_name":project_name,
        "assigned_engineer": engineer_name,"status":"Ongoing"}).execute()
        return redirect("/admin-dashboard")

    except Exception as e:
        return f"Error: {str(e)}"
    
from datetime import datetime


#admin dashboard
@app.route("/admin-dashboard")
def admin_dashboard():

    # today in multiple formats
    today_date  = date.today().isoformat()                          # 2026-06-25
    today_str1  = datetime.now().strftime("%m/%d/%Y")                # 06/25/2026
    today_str2  = str(datetime.now().month) + "/" + datetime.now().strftime("%d/%Y")

    today_str3  = datetime.now().strftime("%d/%m/%Y")                 # 25/06/2026
    today_str4  = str(datetime.now().day) + "/" + str(datetime.now().month) + "/" + str(datetime.now().year)  # 25/6/2026

    # get all engineers
    engineers = supabase.table("users")\
        .select("*")\
        .eq("role", "Site Engineer")\
        .execute()

    # get all projects
    projects = supabase.table("project_assignments").select("*").eq("is_deleted", False).execute()

    
    # get all checkin records
    all_attendance = supabase.table("attendance_checkin")\
        .select("*")\
        .order("id", desc=True)\
        .execute()

    print("TOTAL RECORDS:", len(all_attendance.data))
    if all_attendance.data:
        print("LATEST RECORD DATE:", all_attendance.data[0].get("date"))
    print("TODAY DATE FORMATS:", today_date, today_str1, today_str2)

    all_total     = len(projects.data)
    all_ongoing   = len([p for p in projects.data if p["status"] == "Ongoing"])
    all_completed = len([p for p in projects.data if p["status"] == "Completed"])
    all_engineers  = len(set(p["assigned_engineer"] for p in projects.data))
    

    # different devices save date differently
    attendance_today = [
        item for item in all_attendance.data
        if str(item.get("date", "")).strip() == today_str1
        or str(item.get("date", "")).strip() == today_str2
        or str(item.get("date", "")).strip() == today_str3
        or str(item.get("date", "")).strip() == today_str4
        or str(item.get("date", "")).strip() == today_date
    ]

    print("FILTERED TODAY COUNT:", len(attendance_today))

    # get this month tasks only
    # tasks stay for one month then go to history
    # one_month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    tasks = supabase.table("task").select("*").eq("is_deleted", False).execute()


    return render_template(
        "admin_dashboard.html",
        engineers  = engineers.data,
        projects   = projects.data,
        attendance = attendance_today,
        tasks      = tasks.data,
        today      = today_date,
        all_total =  all_total,
        all_ongoing = all_ongoing,
        all_completed = all_completed, all_engineers = all_engineers

    )

@app.route("/history")
def history():
    today = date.today().isoformat()
    # past checkin — before today
    attendance = supabase.table("attendance_checkin")\
        .select("*")\
        .lt("date", today)\
        .order("id", desc=True)\
        .execute()

    # past tasks — older than one week
    today_dt = datetime.now()
    monday   = today_dt - timedelta(days=today_dt.weekday())

    past_tasks = supabase.table("task")\
        .select("*")\
        .lt("created_at", monday.strftime("%Y-%m-%d"))\
        .order("created_at", desc=True)\
        .execute()

    # weekly attendance history records
    history = supabase.table("attendance_history")\
        .select("*")\
        .execute()

    try:
        return render_template(
            "history.html",
            attendance = attendance.data,
            past_tasks = past_tasks.data,
            history    = history.data
        )
    except Exception as e:
        print("HISTORY ERROR:", str(e))
        return redirect("/admin-dashboard")

@app.route("/photos")
def photos():
    # delete photos older than 15 days first
    # then show remaining photos

    cutoff = (datetime.now() - timedelta(days=15)).strftime("%m/%d/%Y")
    cutoff_date = datetime.now() - timedelta(days=15)

    # get all photos
    all_photos = supabase.table("attendance_checkin")\
        .select("*")\
        .order("id", desc=True)\
        .execute()

    # separate old and recent photos
    recent_photos = []
    old_photos    = []

    for item in all_photos.data:
        date_str = str(item.get("date", "")).strip()
        try:
            # try to parse the date
            if "/" in date_str:
                item_date = datetime.strptime(date_str, "%m/%d/%Y")
            else:
                item_date = datetime.strptime(date_str, "%Y-%m-%d")

            # if older than 15 days add to old list
            if item_date < cutoff_date:
                old_photos.append(item)
            else:
                recent_photos.append(item)

        except:
            # if date cannot be parsed keep the photo
            recent_photos.append(item)

    # delete old photos from storage and database
    for record in old_photos:
        # delete image file from supabase storage
        if record.get("image_url"):
            try:
                filename = record["image_url"].split("/")[-1]
                supabase.storage.from_("attendance-images")\
                    .remove([filename])
            except:
                pass

        # delete record from database
        supabase.table("attendance_checkin")\
            .delete()\
            .eq("id", record["id"])\
            .execute()

    print("DELETED OLD PHOTOS:", len(old_photos))
    print("SHOWING RECENT PHOTOS:", len(recent_photos))

    return render_template(
        "photos.html",
        photos = recent_photos
    )

@app.route("/engineer_page")
def engineer_page():

    worker_name = session.get("worker_name")
    role        = session.get("role")

    if not worker_name:
        return redirect("/login")

    all_projects = supabase.table("project_assignments").select("*").eq("is_deleted", False).execute()

    # get all projects for counts
    my_projects = supabase.table("project_assignments").select("*").eq("assigned_engineer", worker_name).eq("is_deleted", False).execute()
    my_total     = len(my_projects.data)
    my_ongoing   = len([p for p in my_projects.data if p["status"] == "Ongoing"])
    my_completed = len([p for p in my_projects.data if p["status"] == "Completed"])

    if role == "admin":
        projects = all_projects.data
        total_projects = len(all_projects.data)
        ongoing_count   = len([p for p in all_projects.data if p["status"] == "Ongoing"])
        completed_count = len([p for p in all_projects.data if p["status"] == "Completed"])
        engineer_count  = len(set(p["assigned_engineer"] for p in all_projects.data))
    else:
        projects = my_projects.data
        total_projects = my_total
        ongoing_count = my_ongoing
        completed_count = my_completed
        engineer_count = 1

    return render_template(
        "engineer_home.html",
        projects        = projects,
        total_projects  = total_projects,
        ongoing_count   = ongoing_count,
        completed_count = completed_count,
        engineer_name   = worker_name, 
        engineer_count = engineer_count,
        role = role
    )

@app.route("/office-dashboard")
def office_dashboard(): 
    worker_name=session.get("worker_name")
    print(worker_name)
    return render_template("office_dashboard.html", worker_name=worker_name)
    
@app.route("/project/<project_name>")
def project_page(project_name):
    engineer_name = session.get("worker_name")
    workers=supabase.table("workers").select("*").eq("project_name",project_name).execute()
    attendance=supabase.table("attendance").select("*").eq("project_name",project_name).execute()
    project=supabase.table("project_assignments").select("*").eq("project_name",project_name).execute() 
    tasks = supabase.table("task").select("*").eq("project_name", project_name).eq("is_deleted", False).execute()
    workers = supabase.table("workers").select("*").eq("project_name", project_name).eq("is_deleted", False).execute()

    for worker in workers.data:
        print("WORKER:", worker["name"], "ID:", worker["id"])

    attendance_map={}

    for item in attendance.data:
        key = f"{item['worker_id']}_{item['day_name']}"
        attendance_map[key] = item["value"]

    site_engineer=project.data[0]["assigned_engineer"]
   

    return render_template(
        "project_page.html",
        project_name=project_name,
        workers=workers.data,
        attendance_map=attendance_map,
        worker_name=site_engineer,
        tasks=tasks.data
    )

# change the engineer name in assigned project
@app.route("/change-project-engineer", methods=["POST"])
def change_project_engineer():

    project_name = request.form.get("project_name")
    new_engineer = request.form.get("new_engineer")

    supabase.table("project_assignments")\
        .update({"assigned_engineer": new_engineer})\
        .eq("project_name", project_name)\
        .execute()

    return redirect("/admin-dashboard")

@app.route("/add-worker", methods=["POST"])
def add_worker():

    worker_name = request.form.get("worker_name")
    project_name = request.form.get("project_name")

    worker_type  = request.form.get("worker_type", "")

    if not worker_name:
        flash("Worker name cannot be empty.", "danger")
        return redirect(f"/project/{project_name}")

    supabase.table("workers").insert({
        "name": worker_name,
        "project_name": project_name,
        "worker_type":  worker_type,
        "is_active":    True,
        "is_deleted":   False
    }).execute()

    return redirect(f"/project/{project_name}")

# project status
@app.route("/change-project-status", methods=["POST"])
def change_project_status():

    project_name = request.form.get("project_name")
    new_status   = request.form.get("status")

    supabase.table("project_assignments")\
        .update({"status": new_status})\
        .eq("project_name", project_name)\
        .execute()

    return redirect("/admin-dashboard")


@app.route("/save-attendance", methods=["POST"])
def save_attendance():

    worker_id = request.form.get("worker_id")
    worker_name = request.form.get("worker_name")
    project_name = request.form.get("project_name")
    day_name = request.form.get("day_name")
    value = request.form.get("value")

    # Check existing attendance
    old = supabase.table("attendance") \
        .select("*") \
        .eq("worker_id", worker_id) \
        .eq("project_name", project_name) \
        .eq("day_name", day_name) \
        .execute()

    # Update if already exists
    if old.data:
        print("UPDATING - old value:", old.data[0]["value"], "new value:", value)
        result = supabase.table("attendance") \
            .update({"value": value, "worker_name": worker_name}) \
            .eq("worker_id", worker_id) \
            .eq("project_name", project_name) \
            .eq("day_name", day_name) \
            .execute()
        print("UPDATE RESULT:", result.data)
        print("DB ROW:", old.data[0])
        print("SENDING - worker_id:", worker_id, "project:", project_name, "day:", day_name)

    # Insert new attendance
    else:
        supabase.table("attendance").insert({
            "worker_id": worker_id,
            "worker_name": worker_name,
            "project_name": project_name,
            "day_name": day_name,
            "value": value
        }).execute()

    return {"success": True}

# delete the workers
@app.route("/delete-worker/<worker_id>/<project_name>")
def delete_worker(worker_id,project_name):

    supabase.table("attendance").delete().eq("worker_id",worker_id).execute()
    supabase.table("workers").delete().eq("id", worker_id).execute()
    return redirect(f"/project/{project_name}")

# Workers OT
@app.route("/add-overtime", methods=["POST"])
def add_overtime():

    worker_id    = request.form.get("worker_id")
    worker_name  = request.form.get("worker_name")
    project_name = request.form.get("project_name")
    date         = request.form.get("date")
    start_time   = request.form.get("start_time")
    end_time     = request.form.get("end_time")
    ot_hours     = request.form.get("ot_hours")

    print("WORKER ID:",    worker_id)
    print("WORKER NAME:",  worker_name)
    print("PROJECT:",      project_name)
    print("DATE:",         date)
    print("START:",        start_time)
    print("END:",          end_time)
    print("OT HOURS:",     ot_hours)

    try:
        result = supabase.table("overtime").insert({
            "worker_id":    worker_id,
            "worker_name":  worker_name,
            "project_name": project_name,
            "date":         date,
            "start_time":   start_time,
            "end_time":     end_time,
            "ot_hours":     ot_hours
        }).execute()

        print("INSERT RESULT:", result.data)

        return jsonify({"success": True})

    except Exception as e:
        print("ERROR SAVING OT:", str(e))
        return jsonify({"success": False, "error": str(e)})


# this route is called when site engineer clicks "OT Details" button
# it returns all OT records for that specific worker
@app.route("/get-overtime/<worker_id>")
def get_overtime(worker_id):

    # fetch all OT rows for this worker, newest first
    records = supabase.table("overtime")\
        .select("*")\
        .eq("worker_id", worker_id)\
        .order("date", desc=True)\
        .execute()

    # send back as JSON so JS can display it in the popup
    return jsonify({"records": records.data})

import time

# @app.route("/save-attendance-checkin",methods=["POST"])
# def save_attendance_checkin():
#     try:
#         print("Route working")
#         worker_name=request.form.get("worker_name")
#         project_name=request.form.get("project_name")
#         image=request.files.get("image")
#         attendance_type=request.form.get("type")
#         date=request.form.get("date")


#         print(image)
#         print(attendance_type)
#         print(date)

#         if image is None:
#             return jsonify({"success":False,"error":"No image received" })
        
#         date = datetime.now().strftime("%Y-%m-%d") 

#         filename=str(int(time.time()))+"_"+image.filename

#         image_bytes=image.read()
#         # current_time = datetime.now().strftime("%I:%M:%S %p")

#         upload=supabase.storage.from_("attendance-images").upload(
#             path=filename,
#             file=image_bytes,
#             file_options={
#                 "content-type":image.content_type
#             }
#         )

#         print("Image uploaded")

#         image_url=supabase.storage.from_("attendance-images").get_public_url(filename)

#         save=supabase.table("attendance_checkin").insert({

#             "worker_name":worker_name,
#             "project_name":project_name,
#             "type":attendance_type,
#             "image_url":image_url,
#             "date":date,
#             # "time":current_time,
#             # "location":""

#         }).execute()

#         print("DB Saved")

#         return jsonify({
#             "success":True
#         })

#     except Exception as e:
#         print("ERROR:",e)

#         return jsonify({"success":False, "error":str(e) })
    
@app.route("/save-attendance-checkin", methods=["POST"])
def save_attendance_checkin():
    try:
        worker_name     = request.form.get("worker_name")
        project_name    = request.form.get("project_name")
        image           = request.files.get("image")
        attendance_type = request.form.get("type")

        if not image:
            return jsonify({"success": False, "error": "No image received"})

        # always use server date — never trust phone date
        date = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%Y-%m-%d")

        # read image bytes
        # image_bytes = image.read()

        # # fix 2 — always unique filename using timestamp + worker name
        # # prevents duplicate filename rejection from Supabase
        # safe_name = worker_name.replace(" ", "_") if worker_name else "unknown"
        # filename  = f"{date}_{safe_name}_{attendance_type.replace(' ', '_')}_{int(time.time())}.jpg"

        # # fix 3 — upsert=true means even if same file exists, overwrite it
        # supabase.storage.from_("attendance-images").upload(
        #     path         = filename,
        #     file         = image_bytes,
        #     file_options = {
        #         "content-type": "image/jpeg",
        #         "upsert":        "true"
        #     }
        # )

        # image_url = supabase.storage.from_("attendance-images").get_public_url(filename)


        cloudinary.config(
            cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"),
            api_key    = os.getenv("CLOUDINARY_API_KEY"),
            api_secret = os.getenv("CLOUDINARY_API_SECRET")
        )

        image_bytes = image.read()

        upload_result = cloudinary.uploader.upload(
            image_bytes,
            folder = "attendance-checkins"
        )

        image_url = upload_result["secure_url"]
        supabase.table("attendance_checkin").insert({
            "worker_name":  worker_name,
            "project_name": project_name,
            "type":         attendance_type,
            "image_url":    image_url,
            "date":         date
        }).execute()

        print("SUCCESS:", worker_name, attendance_type, date)
        return jsonify({"success": True})

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"success": False, "error": str(e)})


@app.route("/assign-task", methods=["POST"])
def assign_task():

    assigned_engineer = request.form.get("assigned_engineer")
    project_name      = request.form.get("project_name")
    task_input        = request.form.get("task_name")

    # split by comma — "task1, task2, task3" becomes a list
    # strip() removes extra spaces around each task
    tasks = [t.strip() for t in task_input.split(",") if t.strip()]

    # save each task separately in database
    for task in tasks:
        supabase.table("task").insert({
            "assigned_engineer": assigned_engineer,
            "project_name":      project_name,
            "task_name":         task,
            "is_completed":      False,
            "progress":          0
        }).execute()

    return redirect("/admin-dashboard")


@app.route("/update-task", methods=["POST"])
def update_task():

    data         = request.get_json()
    task_id      = data.get("task_id")
    is_completed = data.get("is_completed")
    worker_name  = session.get("worker_name")

    # update task status
    supabase.table("task")\
        .update({"is_completed": is_completed})\
        .eq("id", task_id)\
        .execute()

    # get task details
    task = supabase.table("task")\
    .select("*").eq("id", task_id).execute()
    
    task_data    = task.data[0]
    task_name    = task_data["task_name"]
    project_name = task_data["project_name"]
    engineer     = task_data["assigned_engineer"]

    # calculate progress
    all_tasks = supabase.table("task")\
        .select("*")\
        .eq("project_name", project_name)\
        .eq("assigned_engineer", engineer)\
        .eq("is_deleted", False)\
        .execute()

    total     = len(all_tasks.data)
    completed = len([t for t in all_tasks.data if t["is_completed"]])
    progress  = round((completed / total * 100)) if total > 0 else 0

    if is_completed:
    # only save notification when task is completed
    # not for pending
        result =  supabase.table("notifications").insert({
        "message":  f"{engineer} completed '{task_name}' in {project_name}",
        "type":     "task_completed",
        "for_role": "admin",
        "is_read":  False
    }).execute()

        print("ADMIN NOTIFICATION INSERT RESULT:", result.data)

    else:
        # engineer unticked a task
        supabase.table("notifications").insert({
            "message":  f"{engineer} marked '{task_name}' as pending in {project_name}",
            "type":     "task_pending",
            "for_role": "admin",
            "is_read":  False
        }).execute()

    return jsonify({
        "progress":  progress,
        "completed": completed,
        "total":     total
    })



# delete the task card in admin page
@app.route("/delete-engineer-task/<engineer>/<project_name>")
def delete_engineer_task(engineer,project_name):

    supabase.table("task").delete().eq("assigned_engineer", engineer).eq("project_name", project_name).execute()

    return redirect("/admin-dashboard")

import io
from flask import send_file


# Attendance reset
from datetime import datetime
import io   

import threading
import pytz

@app.route("/restart-attendance")
def restart_attendance():

    # use India time — Render server runs on UTC
    ist   = pytz.timezone("Asia/Kolkata")
    today = datetime.now(ist).strftime("%A")

    if today != "Monday":
        return """
        <script>
        alert('Attendance reset only available on Monday');
        window.location.href='/admin-dashboard';
        </script>
        """

    # start the heavy work in background
    # so Flask returns immediately and Render does not timeout
    thread = threading.Thread(target=do_attendance_reset)
    thread.daemon = True
    thread.start()

    # return instantly — admin sees this message right away
    return """
    <script>
    alert('Reset started! Excel files will be ready in 1-2 minutes. Check History page.');
    window.location.href='/admin-dashboard';
    </script>
    """


def do_attendance_reset():
    """
    All the heavy work happens here in a background thread.
    Flask already returned to the browser — this runs quietly
    in the background without any timeout risk.
    """
    try:
        import pytz
        ist      = pytz.timezone("Asia/Kolkata")
        today_dt = datetime.now(ist)

        # last week Monday and Sunday
        # when reset runs on Monday, we archive LAST week not current week
        last_monday = today_dt - timedelta(days=today_dt.weekday() + 7)
        last_sunday = last_monday + timedelta(days=6)

        week_name = (
            last_monday.strftime("%d-%m-%Y")
            + " to " +
            last_sunday.strftime("%d-%m-%Y")
        )

        # get all projects
        projects = supabase.table("project_assignments")\
            .select("*").execute()

        for project in projects.data:

            project_name = project["project_name"].strip()
            engineer     = project["assigned_engineer"]

            # get attendance and workers for this project
            attendance = supabase.table("attendance")\
                .select("*")\
                .eq("project_name", project_name)\
                .execute()

            workers = supabase.table("workers")\
                .select("*")\
                .eq("project_name", project_name)\
                .execute()

            # build Excel
            wb = Workbook()
            ws = wb.active
            ws.title = "Attendance"
            ws.append([
                "Worker Name", "Type", "Salary",
                "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun",
                "Total Day","Total Amount", "OT Hours", "OT Details"
            ])

            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

            for worker in workers.data:

                row = [worker["name"], worker.get("worker_type", "--"), worker.get("salary", "0")]
                total_day = 0

                for day in days:
                    attendance_value = "--"
                    for item in attendance.data:
                        if (
                            str(item["worker_id"]) == str(worker["id"])
                            and item["day_name"] == day
                        ):
                            attendance_value = item["value"]
                            if attendance_value == "1d":    total_day += 1
                            elif attendance_value == "0.5d": total_day += 0.5
                            elif attendance_value == "1.5d": total_day += 1.5
                            elif attendance_value == "2d":   total_day += 2
                            elif attendance_value == "2.5d": total_day += 2.5
                            break
                    row.append(attendance_value)

                row.append(f"{total_day} d")

                salary       = float(worker.get("salary") or 0)
                total_amount = salary * total_day
                row.append(f"₹{total_amount:,.0f}")


                # get OT for this worker
                worker_ot = supabase.table("overtime")\
                    .select("*")\
                    .eq("worker_id", worker["id"])\
                    .execute()

                if worker_ot.data:
                    total_ot = sum(float(r.get("ot_hours", 0)) for r in worker_ot.data)
                    ot_parts = [
                        f"{r.get('date','')} {r.get('start_time','')} - {r.get('end_time','')} ({r.get('ot_hours','')} hrs)"
                        for r in worker_ot.data
                    ]
                    row.append(f"{total_ot} hrs")
                    row.append(" | ".join(ot_parts))
                else:
                    row.append("0 hrs")
                    row.append("No OT")

                ws.append(row)

            # save Excel to memory and upload to Supabase Storage
            excel_buffer = io.BytesIO()
            wb.save(excel_buffer)
            excel_buffer.seek(0)

            storage_path = f"history/{project_name}_{week_name}.xlsx"

            supabase.storage.from_("attendance-images").upload(
                path         = storage_path,
                file         = excel_buffer.getvalue(),
                file_options = {
                    "content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "upsert":        "true"
                }
            )

            excel_url = supabase.storage.from_("attendance-images")\
                .get_public_url(storage_path)

            supabase.table("attendance_history").insert({
                "project_name":      project_name,
                "assigned_engineer": engineer,
                "week_name":         week_name,
                "file_name":         excel_url
            }).execute()

        # reset attendance table for new week
        supabase.table("attendance")\
            .delete()\
            .not_.is_("project_name", "null")\
            .execute()

        # move old tasks to history
        monday    = today_dt - timedelta(days=today_dt.weekday())
        old_tasks = supabase.table("task")\
            .select("*")\
            .lt("created_at", monday.strftime("%Y-%m-%d"))\
            .execute()

        for task in old_tasks.data:
            supabase.table("task_history").insert({
                "assigned_engineer": task["assigned_engineer"],
                "project_name":      task["project_name"],
                "task_name":         task["task_name"],
                "is_completed":      task["is_completed"],
                "created_at":        task["created_at"]
            }).execute()

        supabase.table("task")\
            .delete()\
            .lt("created_at", monday.strftime("%Y-%m-%d"))\
            .execute()

        # delete checkin photos older than 15 days
        cutoff = (datetime.now(ist) - timedelta(days=15)).strftime("%Y-%m-%d")

        old_photos = supabase.table("attendance_checkin")\
            .select("*")\
            .lt("date", cutoff)\
            .execute()

        for record in old_photos.data:
            if record.get("image_url"):
                try:
                    filename = record["image_url"].split("/")[-1]
                    supabase.storage.from_("attendance-images").remove([filename])
                except:
                    pass

        supabase.table("attendance_checkin")\
            .delete()\
            .lt("date", cutoff)\
            .execute()

        print("RESET COMPLETE")

    except Exception as e:
        import traceback
        print("RESET ERROR:", str(e))
        traceback.print_exc()


#delete the history stored attendance card
@app.route("/delete-history", methods=["POST"])
def delete_history():

    # get list of selected record ids from the form
    # getlist gets all checked checkboxes values at once
    selected_ids = request.form.getlist("selected_ids")

    if not selected_ids:
        flash("No records selected.", "warning")
        return redirect("/history")

    for record_id in selected_ids:

        # first get the record to find the excel file url
        record = supabase.table("attendance_history")\
            .select("*")\
            .eq("id", record_id)\
            .execute()

        if record.data:
            file_url = record.data[0].get("file_name", "")

            # delete the excel file from Supabase Storage too
            if file_url:
                try:
                    storage_path = file_url.split("/object/public/attendance-images/", 1)[-1]
                    storage_path = storage_path.split("?", 1)[0]

                    print("DELETING STORAGE FILE:", repr(storage_path))

                    result = supabase.storage.from_("attendance-images").remove([storage_path])

                    print("STORAGE DELETE RESULT:", result)

                except Exception as e:
                    print("DELETE STORAGE ERROR:", str(e))        

            

            
        # delete the record from database
        supabase.table("attendance_history")\
            .delete()\
            .eq("id", record_id)\
            .execute()

    flash("Selected records deleted.", "success")
    return redirect("/history")




@app.route("/delete-checkin-history", methods=["POST"])
def delete_checkin_history():

    selected_ids = request.form.getlist("selected_ids")

    if not selected_ids:
        flash("No records selected.", "warning")
        return redirect("/history")

    for record_id in selected_ids:

        # get record to find image url
        record = supabase.table("attendance_checkin")\
            .select("*")\
            .eq("id", record_id)\
            .execute()

        if record.data:
            image_url = record.data[0].get("image_url", "")

            # delete image from Supabase Storage
            # if image_url and "supabase" in image_url:
            if "cloudinary" in image_url:
                try:
                    public_id = "attendance-checkin/" + image_url.split("/")[-1].split(".")[0] 
                    cloudinary.uploader.destroy(public_id)
            
                except Exception as e:
                    print("STORAGE DELETE ERROR:", str(e))

        # delete record from database
        supabase.table("attendance_checkin")\
            .delete()\
            .eq("id", record_id)\
            .execute()

    flash("Selected records deleted.", "success")
    return redirect("/history")


# this route now responds to a quiet background fetch() call,
# not a full page form submission — so we return a simple JSON
# response instead of redirecting to a new page
@app.route("/update-worker-name", methods=["POST"])
def update_worker_name():

    worker_id   = request.form.get("worker_id")
    new_name    = request.form.get("worker_name")

    supabase.table("workers")\
        .update({"name": new_name})\
        .eq("id", worker_id)\
        .execute()

    # just confirm success — no redirect, no page reload
    return jsonify({"success": True})


@app.route("/update-salary", methods=["POST"])
def update_salary():

    worker_id = request.form.get("worker_id")
    salary    = request.form.get("salary")

    result=supabase.table("workers")\
        .update({"salary": salary})\
        .eq("id", worker_id)\
        .execute()

    check = supabase.table("workers")\
        .select("id, name, salary")\
        .eq("id", worker_id)\
        .execute()

    print("SALARY UPDATE:", worker_id, salary)
    print("UPDATED ROW:", check.data)

    return jsonify({"success": True})

# this route saves the worker type whenever engineer changes the dropdown
@app.route("/update-worker-type", methods=["POST"])
def update_worker_type():

    worker_id    = request.form.get("worker_id")
    worker_type  = request.form.get("worker_type")
    project_name = request.form.get("project_name")

    # update only the worker_type column for this worker
    supabase.table("workers")\
        .update({"worker_type": worker_type})\
        .eq("id", worker_id)\
        .execute()

    return redirect(f"/project/{project_name}")

from flask import send_file

# @app.route("/download/<path:file_name>")
# def download_file(file_name):
     

#     print("DOWNLOADING:", file_name)

#     return send_file(
#         file_name,
#         as_attachment=True
#     )

#profile .
# engineer sees their own profile
@app.route("/profile")
def profile():

    worker_name = session.get("worker_name").strip()
    role        = session.get("role")

    if not worker_name:
        return redirect("/login")

    # get this person's details
    user = supabase.table("users")\
        .select("*")\
        .eq("full_name", worker_name)\
        .execute()

    check = supabase.table("users")\
    .select("full_name,profile_photo")\
    .eq("full_name", worker_name)\
    .execute()

    print("AFTER UPLOAD DB:", check.data)

    user_data = user.data[0] if user.data else {}

    print("PROFILE USER DATA:", user_data)
    print("PROFILE PHOTO FROM DB:", user_data.get("profile_photo"))

    # get their projects
    my_projects = supabase.table("project_assignments")\
        .select("*")\
        .eq("assigned_engineer", worker_name)\
        .eq("is_deleted", False)\
        .execute()

    ongoing   = [p for p in my_projects.data if p["status"] == "Ongoing"]
    completed = [p for p in my_projects.data if p["status"] == "Completed"]

    return render_template(
        "profile.html",
        user      = user_data,
        ongoing   = ongoing,
        completed = completed,
        role      = role
    )


# admin sees all engineers as cards
@app.route("/all-profiles")
def all_profiles():

    role = session.get("role")

    if role != "admin":
        return redirect("/login")

    # get all engineers
    engineers = supabase.table("users")\
        .select("*")\
        .eq("role", "Site Engineer")\
        .execute()

    return render_template(
        "all_profiles.html",
        engineers = engineers.data
    )


# admin clicks one engineer card — see their profile
@app.route("/engineer-profile/<engineer_name>")
def engineer_profile(engineer_name):

    role = session.get("role")

    if not session.get("worker_name"):
        return redirect("/login")

    # get that engineer's details
    user = supabase.table("users")\
        .select("*")\
        .eq("full_name", engineer_name)\
        .execute()

    user_data = user.data[0] if user.data else {}

    # get their projects
    my_projects = supabase.table("project_assignments")\
        .select("*")\
        .eq("assigned_engineer", engineer_name)\
        .eq("is_deleted", False)\
        .execute()

    ongoing   = [p for p in my_projects.data if p["status"] == "Ongoing"]
    completed = [p for p in my_projects.data if p["status"] == "Completed"]

    return render_template(
        "profile.html",
        user      = user_data,
        ongoing   = ongoing,
        completed = completed,
        role      = role
    )


# upload profile photo
@app.route("/upload-profile-photo", methods=["POST"])
def upload_profile_photo():

    worker_name = session.get("worker_name")
    photo       = request.files.get("photo")

    if not photo or not worker_name:
        return redirect("/profile")

    filename    = f"profile_{worker_name.replace(' ', '_')}.jpg"
    image_bytes = photo.read()

    supabase.storage.from_("attendance-images").upload(
        path         = f"profiles/{filename}",
        file         = image_bytes,
        file_options = {
            "content-type": photo.content_type,
            "upsert":       "true"
        }
    )

    # photo_url = supabase.storage.from_("attendance-images")\
    #     .get_public_url(f"profiles/{filename}")

    photo_url = f"https://xtnxzhtzopxrhxmichsq.supabase.co/storage/v1/object/public/attendance-images/profiles/{filename}"

    print("PROFILE PHOTO URL:", photo_url)

    supabase.table("users")\
        .update({"profile_photo": photo_url})\
        .eq("full_name", worker_name)\
        .execute()

    return redirect("/profile")


@app.route("/edit-profile", methods=["POST"])
def edit_profile():

    worker_name = session.get("worker_name")
    phone       = request.form.get("phone")
    address     = request.form.get("address")

    supabase.table("users")\
        .update({
            "phone":   phone,
            "address": address
        })\
        .eq("full_name", worker_name)\
        .execute()

    return redirect("/profile")

# notification
@app.route("/get-notifications")
def get_notifications():

    role        = session.get("role")
    worker_name = session.get("worker_name")


    notifs = supabase.table("notifications")\
        .select("*")\
        .eq("for_role", "admin")\
        .eq("is_read", False)\
        .order("created_at", desc=True)\
        .limit(10)\
        .execute()


    return jsonify({"notifications": notifs.data})

   


# this route is called by engineer page JS
# it counts how many tasks this engineer has not completed
# returns the count as JSON so JS can show it on bell icon
@app.route("/get-pending-reminders")
def get_pending_reminders():

    # get logged in engineer name from session
    worker_name = session.get("worker_name")
    role        = session.get("role")

    if not worker_name:
        # if not logged in return 0
        return jsonify({"my_pending": 0})

    if role == "admin":
        # admin sees all engineers pending tasks
        engineers = supabase.table("users")\
            .select("*")\
            .eq("role", "Site Engineer")\
            .execute()

        reminders = []
        for eng in engineers.data:
            # count pending tasks for each engineer
            pending = supabase.table("task")\
                .select("*")\
                .eq("assigned_engineer", eng["full_name"])\
                .eq("is_completed", False)\
                .eq("is_deleted", False)\
                .execute()

            if pending.data:
                reminders.append({
                    "engineer": eng["full_name"],
                    "count":    len(pending.data)
                })

        return jsonify({"reminders": reminders, "my_pending": 0})

    else:
        # engineer sees only their own pending tasks
        # count tasks where is_completed is False
        pending = supabase.table("task")\
            .select("*")\
            .eq("assigned_engineer", worker_name)\
            .eq("is_completed", False)\
            .eq("is_deleted", False)\
            .execute()

        print("PENDING TASKS:", len(pending.data))

        # return count as JSON
        # JS reads data.my_pending to show on bell badge
        return jsonify({
            "my_pending": len(pending.data),
            "reminders":  []
        })
    

# logout
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)