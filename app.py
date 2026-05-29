from flask import Flask, render_template, request, redirect, jsonify, session
from datetime import datetime, timedelta
from openpyxl import Workbook
import time
from config import (
    supabase,
    SECRET_KEY,
    ADMIN_SECRET
)

app = Flask(__name__)
app.secret_key = SECRET_KEY
    

@app.route("/")
def home():
    return render_template("register.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        full_name = request.form.get("full_name")
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
                    if(db_role == "Admin" and admin_key ==  ADMIN_SECRET):
                        return redirect("/admin-dashboard")
                
                    return "Invalid Admin Key"


                elif role == "engineer":
                    if db_role == "Site Engineer":
                        return redirect("/engineer_page")
                    
                    
                elif role == "office":
                    if db_role == "Office Staff":
                        session["worker_name"]=user.data[0]["full_name"]
                        return redirect("/office-dashboard")
                        
                   
                    
                return "Invalid Email or Password"
        
        except Exception as e:
            return f"Error: {str(e)}"

    return render_template("login.html")


# project assigned
@app.route("/add-project", methods=["POST"])
def add_project():

    project_name = request.form.get(
        "project_name"
    )

    engineer_name = request.form.get(
        "engineer_name"
    )

    try:

        supabase.table(
            "project_assignments"
        ).insert({

            "project_name":
            project_name,

            "assigned_engineer":
            engineer_name,

            "status":
            "Ongoing"

        }).execute()

        return redirect(
            "/admin-dashboard"
        )

    except Exception as e:

        return f"Error: {str(e)}"
    
from datetime import datetime


#admin dashboard
@app.route("/admin-dashboard")
def admin_dashboard():

    today=datetime.now().strftime("%m/%d/%Y")

    engineers = supabase.table(
        "users"
    ).select("*")\
    .eq("role",
        "Site Engineer")\
    .execute()

    projects = supabase.table(
        "project_assignments"
    ).select("*")\
    .execute()



    attendance=supabase.table(
        "attendance_checkin"
    ).select("*").order(
        "id",
        desc=True
    ).execute()

    tasks=supabase.table(
        "task"
    ).select("*").execute()
    
    return render_template("admin_dashboard.html", engineers=engineers.data, projects=projects.data, attendance=attendance.data, tasks=tasks.data)

# All previous data visible here
@app.route("/history")
def history():
    attendance=supabase.table("attendance_checkin").select("*").execute()
    history=supabase.table("attendance_history").select("*").execute()
    return render_template("history.html",attendance=attendance.data, history=history.data)
    
# Photos showing here
@app.route("/photos")
def photos():
    photos=supabase.table("attendance_checkin").select("*").execute()
    return render_template("photos.html",photos=photos.data)

# Engineer page redirect 
@app.route("/engineer_page")
def engineer_page():
    projects = supabase.table(
        "project_assignments"
    ).select("*").execute();
    return render_template("engineer_home.html", projects=projects.data)
    

@app.route("/office-dashboard")
def office_dashboard(): 
    worker_name=session.get("worker_name")
    print(worker_name)
    return render_template("office_dashboard.html", worker_name=worker_name)
    
@app.route("/project/<project_name>")
def project_page(project_name):

    workers=supabase.table("workers").select("*").eq("project_name",project_name).execute()

    attendance=supabase.table("attendance").select("*").eq("project_name",project_name).execute()

    project=supabase.table("project_assignments").select("*").eq("project_name",project_name).execute()

    tasks=supabase.table("task").select("*").eq("project_name",project_name).execute()

    

    attendance_map={}

    # for item in attendance.data:
    #     attendance_map[f"{item['worker_id']}_{item['day_name']}"]=item["value"]

    for item in attendance.data:
        key = f"{item['worker_id']}_{item['day_name']}"
        attendance_map[key] = item["value"]

    site_engineer=project.data[0]["assigned_engineer"]

    print("ATTENDANCE DATA:", attendance.data)
    print("ATTENDANCE MAP:", attendance_map)


    return render_template(
        "project_page.html",
        project_name=project_name,
        workers=workers.data,
        attendance_map=attendance_map,
        worker_name=site_engineer,
        tasks=tasks.data
    )


@app.route("/add-worker", methods=["POST"])
def add_worker():

    worker_name = request.form.get("worker_name")
    project_name = request.form.get("project_name")

    supabase.table("workers").insert({
        "name": worker_name,
        "project_name": project_name
    }).execute()

    return redirect(f"/project/{project_name}")


# @app.route("/save-attendance",methods=["POST"])
# def save_attendance():
#     worker_id=request.form.get("worker_id")
#     worker_name=request.form.get("worker_name")
#     project_name=request.form.get("project_name")
#     day_name=request.form.get("day_name")
#     value=request.form.get("value")

#     old=supabase.table("attendance").select("*").eq("worker_id",worker_id).eq("day_name",day_name).execute()

#     if old.data:
#         supabase.table("attendance").update({"value":value}).eq("worker_id",worker_id).eq("day_name",day_name).execute()
#     else:
#         supabase.table("attendance").insert({"worker_id":worker_id,"worker_name":worker_name,"project_name":project_name,"day_name":day_name,"value":value}).execute()

#     return {"success":True}

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
        supabase.table("attendance") \
            .update({"value": value}) \
            .eq("worker_id", worker_id) \
            .eq("project_name", project_name) \
            .eq("day_name", day_name) \
            .execute()

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

    supabase.table("workers").delete().eq("id",worker_id).execute()

    return redirect(f"/project/{project_name}")

import time

@app.route("/save-attendance-checkin",methods=["POST"])
def save_attendance_checkin():

    try:
        print("Route working")
        worker_name=request.form.get("worker_name")
        project_name=request.form.get("project_name")
        image=request.files.get("image")
        attendance_type=request.form.get("type")
        date=request.form.get("date")
        current_time=request.form.get("time")
        location=request.form.get("location")

        print(image)
        print(attendance_type)
        print(date)
        print(current_time)
        print(location)

        if image is None:
            return jsonify({
                "success":False,
                "error":"No image received"
            })

        filename=str(int(time.time()))+"_"+image.filename

        image_bytes=image.read()

        upload=supabase.storage.from_("attendance-images").upload(
            path=filename,
            file=image_bytes,
            file_options={
                "content-type":image.content_type
            }
        )

        print("Image uploaded")

        image_url=supabase.storage.from_("attendance-images").get_public_url(filename)

        save=supabase.table("attendance_checkin").insert({

            "worker_name":worker_name,
            "project_name":project_name,
            "type":attendance_type,
            "image_url":image_url,
            "date":date,
            "time":current_time,
            "location":location

        }).execute()

        print("DB Saved")

        return jsonify({
            "success":True
        })

    except Exception as e:

        print("ERROR:",e)

        return jsonify({
            "success":False,
            "error":str(e)
        })
    

@app.route("/assign-task",methods=["POST"])
def assign_task():

    assigned_engineer=request.form.get("assigned_engineer")
    project_name=request.form.get("project_name")
    task_name=request.form.get("task_name")

    supabase.table("task").insert({

        "assigned_engineer":assigned_engineer,
        "project_name":project_name,
        "task_name":task_name,
        "is_completed":False,
        "progress":0

    }).execute()

    return redirect("/admin-dashboard")

@app.route("/update-task",methods=["POST"])
def update_task():

    data=request.get_json()

    task_id=data.get("task_id")
    is_completed=data.get("is_completed")

    supabase.table("task").update({

        "is_completed":is_completed

    }).eq("id",task_id).execute()

    current_task=supabase.table(
        "task"
    ).select("*").eq(
        "id",
        task_id
    ).execute()

    project_name=current_task.data[0]["project_name"]

    tasks=supabase.table(
        "task"
    ).select("*").eq(
        "project_name",
        project_name
    ).execute()

    completed=len([
        task for task in tasks.data
        if task["is_completed"]
    ])

    progress=completed*20

    return jsonify({
        "progress":progress
    })

# delete the task card in admin page
@app.route("/delete-engineer-task/<engineer>/<project_name>")
def delete_engineer_task(engineer,project_name):

    supabase.table("task").delete().eq("assigned_engineer",engineer).eq("project_name",project_name).execute()

    return redirect("/admin-dashboard")


# Attendance reset


from datetime import datetime
import csv
import os

# @app.route("/restart-attendance")
# def restart_attendance():

#     today=datetime.now().strftime("%A")

#     if today!="Tuesday":

#         return """
#         <script>
#         alert('Attendance reset only available on Tuesday');
#         window.location.href='/admin-dashboard';
#         </script>
#         """

#     projects=supabase.table(
#         "project_assignments"
#     ).select("*").execute()

#     os.makedirs(
#         "history",
#         exist_ok=True
#     )

#     week_name=datetime.now().strftime(
#         "%d-%m-%Y"
#     )

#     for project in projects.data:

#         project_name=project["project_name"]

#         engineer=project["assigned_engineer"]

#         attendance=supabase.table(
#             "attendance"
#         ).select("*").eq(
#             "project_name",
#             project_name
#         ).execute()

#         file_name=f"history/{project_name}_{week_name}.csv"

#         with open(
#             file_name,
#             "w",
#             newline=""
#         ) as file:

#             writer=csv.writer(file)

#             writer.writerow([
#                 "Worker Name",
#                 "Project Name",
#                 "Day",
#                 "Attendance"
#             ])

#             for item in attendance.data:

#                 writer.writerow([
#                     item["worker_name"],
#                     item["project_name"],
#                     item["day_name"],
#                     item["value"]
#                 ])

#         supabase.table(
#             "attendance_history"
#         ).insert({

#             "project_name":
#             project_name,

#             "assigned_engineer":
#             engineer,

#             "week_name":
#             week_name,

#             "file_name":
#             file_name

#         }).execute()

#     supabase.table("attendance").delete().not_.is_("project_name","null").execute()

#     return """
#     <script>
#     alert(
#     'Attendance Reset Success');
#     window.location.href=
#     '/admin-dashboard';
#     </script>
#     """


from datetime import datetime
import csv
import os

# @app.route("/restart-attendance")
# # def restart_attendance():

#     today=datetime.now().strftime("%A")

#     # Change Tuesday to Monday later
#     if today!="Wednesday":

#         return """
#         <script>
#         alert(
#         'Attendance reset only available on Tuesday');
#         window.location.href=
#         '/admin-dashboard';
#         </script>
#         """

#     projects=supabase.table(
#         "project_assignments"
#     ).select("*").execute()

#     os.makedirs(
#         "history",
#         exist_ok=True
#     )

#     week_name=datetime.now().strftime(
#         "%d-%m-%Y"
#     )

#     for project in projects.data:

#         project_name=project["project_name"]

#         engineer=project["assigned_engineer"]

#         attendance=supabase.table(
#             "attendance"
#         ).select("*").eq(
#             "project_name",
#             project_name
#         ).execute()

#         workers=supabase.table(
#             "workers"
#         ).select("*").eq(
#             "project_name",
#             project_name
#         ).execute()

#         file_name=f"history/{project_name}_{week_name}.xlsx"

#         wb=Workbook()

#         ws=wb.active

#         ws.title="Attendance"

#         ws.append([
#             "Worker Name",
#             "Mon",
#             "Tue",
#             "Wed",
#             "Thu",
#             "Fri",
#             "Sat",
#             "Sun",
#             "Total Day"
#         ])

#         days = [
#         "Monday",
#         "Tuesday",
#         "Wednesday",
#         "Thursday",
#         "Friday",
#         "Saturday",
#         "Sunday"
#     ]

#     print(attendance.data)

#     for worker in workers.data:

#         row = [worker["name"]]   # change name if column different

#         total_day = 0

#         for day in days:

#             attendance_value = "--"

#             for item in attendance.data:

#                 if (
#                     str(item["worker_id"]) == str(worker["id"])
#                     and
#                     item["day_name"] == day
#                 ):

#                     attendance_value = item["value"]

#                     if attendance_value == "1d":
#                         total_day += 1

#                     elif attendance_value == "0.5d":
#                         total_day += 0.5

#                     break

#             row.append(attendance_value)

#             row.append(f"{total_day} d")

#         ws.append(row)
#                 # Save in history table
                
#         supabase.table("attendance_history").insert({"project_name":project_name,"assigned_engineer":engineer,"week_name":week_name,"file_name":file_name}).execute()

#                 # Reset attendance after save
#         supabase.table(
#                     "attendance"
#                 ).delete().not_.is_(
#                     "project_name",
#                     "null"
#                 ).execute()

#         return """<script>alert('Attendance Reset Success');window.location.href='/admin-dashboard';</script>"""

@app.route("/restart-attendance")
def restart_attendance():

    today = datetime.now().strftime("%A")

    # Allow only Wednesday
    if today != "Thursday":
        return """
        <script>
        alert('Attendance reset only available on Wednesday');
        window.location.href='/admin-dashboard';
        </script>
        """

    # Get all projects
    projects = supabase.table(
        "project_assignment"
    ).select("*").execute()

    # Project base folder
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # Create history folder automatically
    history_folder = os.path.join(
        BASE_DIR,
        "history"
    )

    os.makedirs(
        history_folder,
        exist_ok=True
    )

    # Week date
    # week_name = datetime.now().strftime("%d-%m-%Y")

    today = datetime.now()

    # Monday date
    start_date = today - timedelta(days=today.weekday())

    # Sunday date
    end_date = start_date + timedelta(days=6)

    week_name = (
        start_date.strftime("%d-%m-%Y")
        + " to " +
        end_date.strftime("%d-%m-%Y")
    )

    today = datetime.now()

    # Monday date
    start_date = today - timedelta(days=today.weekday())

    # Sunday date
    end_date = start_date + timedelta(days=6)

    week_name = (
        start_date.strftime("%d-%m-%Y")
        + " to " +
        end_date.strftime("%d-%m-%Y")
    )

    # Loop through all projects
    for project in projects.data:

        project_name = project["project_name"].strip()
        engineer = project["assigned_engineer"]

        file_name = os.path.join(
            history_folder,
            f"{project_name}_{week_name}.xlsx"
        )

        # Get attendance
        attendance = supabase.table(
            "attendance"
        ).select("*").eq(
            "project_name",
            project_name
        ).execute()

        # Get workers
        workers = supabase.table(
            "workers"
        ).select("*").eq(
            "project_name",
            project_name
        ).execute()


        # Create workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Attendance"

        # Excel Header
        ws.append([
            "Worker Name",
            "Mon",
            "Tue",
            "Wed",
            "Thu",
            "Fri",
            "Sat",
            "Sun",
            "Total Day"
        ])

        days = [
            "Mon",
            "Tue",
            "Wed",
            "Thu",
            "Fri",
            "Sat",
            "Sun"
        ]

        # One worker = One row
        for worker in workers.data:

            row = [worker["name"]]
            total_day = 0

            for day in days:

                attendance_value = "--"

                for item in attendance.data:

                    if (
                        str(item["worker_id"]) == str(worker["id"])
                        and item["day_name"] == day
                    ):

                        attendance_value = item["value"]

                        # Calculate total
                        if attendance_value == "1d":
                            total_day += 1
                        elif attendance_value == "0.5d":
                            total_day += 0.5
                        elif attendance_value == "1.5d":
                            total_day += 1.5
                        elif attendance_value == "2d":
                            total_day += 2
                        elif attendance_value == "2.5d":
                            total_day += 2.5

                        break

                row.append(attendance_value)

            # Add total
            row.append(f"{total_day} d")

            # Add row to Excel
            ws.append(row)

        # Save Excel file
        try:
            wb.save(file_name)
            print("FILE EXISTS:", os.path.exists(file_name))
            print("FILE NAME:", file_name)

        except Exception as e:
            print("SAVE ERROR:", e)

        # Save history in DB
        supabase.table(
            "attendance_history"
        ).insert({
            "project_name": project_name,
            "assigned_engineer": engineer,
            "week_name": week_name,
            "file_name": file_name
        }).execute()

    # Reset attendance
    supabase.table(
        "attendance"
    ).delete().not_.is_(
        "project_name",
        "null"
    ).execute()

    return """
    <script>
    alert('Attendance Reset Success');
    window.location.href='/admin-dashboard';
    </script>
    """

from flask import send_file

@app.route("/download/<path:file_name>")
def download_file(file_name):
     

    print("DOWNLOADING:", file_name)

    return send_file(
        file_name,
        as_attachment=True
    )


# logout
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)