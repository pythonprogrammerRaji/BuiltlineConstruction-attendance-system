function togglePassword() {

    let passwordField =
        document.getElementById("password");

    if(passwordField.type === "password"){
        passwordField.type = "text";
    }else{
        passwordField.type = "password";
    }
}

let projects = [];

function toggleForm(){

    let form =document.getElementById("projectForm");

        form.classList.toggle("hidden");
}

function addProject(){
    let name = document.getElementById("projectName").value;

    let engineer =document.getElementById("engineerName").value;

    let project = {
        name:name,
        engineer:engineer,
        status:"Ongoing"
    };

    projects.push(project);

    renderProjects();

    document.getElementById("projectForm").classList.add("hidden");
}


    function renderProjects(){

        let container =
            document.getElementById(
                "projectContainer"
            );

        container.innerHTML = "";

        projects.forEach(project => {

            container.innerHTML += `

            <div class="col-md-4 mb-4">

                <div class="card shadow p-4 project-card">

                    <h4>
                        ${project.name}
                    </h4>

                    <p>
                        <strong>
                            Engineer:
                        </strong>

                        ${project.engineer}
                    </p>

                    <p>

                        <strong>
                            Status:
                        </strong>

                        <span
                        class="badge bg-success">

                        ${project.status}

                        </span>

                    </p>

                    <button
                        class="btn btn-primary">

                        Open Project

                    </button>

                </div>

            </div>

            `;
        });
    }

    function showAlert(){
        const engineer=document.querySelector('[name="assigned_engineer"]').value;
        alert("Task assigned to "+ engineer);
    }

    
// project_page js



function showSection(section){

    document.getElementById("attendanceSection").style.display = "none";
    document.getElementById("checkinSection").style.display = "none";
    document.getElementById("tasksSection").style.display = "none";


    if(section === "attendance"){
        document.getElementById("attendanceSection").style.display = "block";
    }
    else if(section === "checkin"){
        document.getElementById("checkinSection").style.display = "block";
    }
    else{
        document.getElementById("tasksSection").style.display = "block";
    }

}

function calculateTotal(select){
        let row=select.closest("tr");
        let selects=row.querySelectorAll(".attendance-select");
        let total=0;
        selects.forEach(item=>{total+=parseFloat(item.value)||0;});
        row.querySelector(".total-days").innerText=total;
}



function calculateTotal(select){
    let row=select.closest("tr");
    let selects=row.querySelectorAll(".attendance-select");
    let total=0;

    selects.forEach(item=>{
        if(item.value=="1d")total+=1;
        if(item.value=="0.5d")total+=0.5;
        if(item.value=="1.5d")total+=1.5;
        if(item.value=="2d")total+=2;
        if(item.value=="2.5d")total+=2.5;
    });

    row.querySelector(".total-days").innerText=total+" d";
      let salary = parseFloat(row.querySelector('input[name="salary"]').value) || 0;
    // Total Amount
    let amount = salary * total;
    row.querySelector('[id^="sal-total-"]').innerText = "₹" + amount;
    }

    window.onload=function(){
        document.querySelectorAll(".attendance-select").forEach(select=>{
        calculateTotal(select);
    });
}

function calcWorkerSalary(workerId){
    let salary = parseFloat(document.getElementById("salary-" + workerId).value) || 0;

    let total = parseFloat(
        document.getElementById("total-days-" + workerId).innerText
    ) || 0;

    document.getElementById("sal-total-" + workerId).innerText =
        "₹" + (salary * total);
}

function saveAttendance(select,day,workerId,workerName){
calculateTotal(select);
const projectName =
    document.getElementById("projectName").value;

fetch("/save-attendance",{
    method:"POST",
    headers:{
    "Content-Type":"application/x-www-form-urlencoded"
    },
   body:"worker_id="+workerId+
    "&worker_name="+encodeURIComponent(workerName)+
    "&project_name="+encodeURIComponent(projectName)+
    "&day_name="+day+
    "&value="+select.value
    })


.then(res=>res.json())
.then(data=>{console.log(data); calcWorkerSalary(workerId)});

}


// document.addEventListener("DOMContentLoaded",function(){
//     const checkinBtn=document.getElementById("checkinBtn");
//     const checkoutBtn=document.getElementById("checkoutBtn");
//     const selfieInputGallery =document.getElementById("selfieInputGallery");
//     const attendancePreview=document.getElementById("attendancePreview");
//     const statusText=document.getElementById("statusText");
//     const workerName=document.getElementById("workerName").value;
//     const projectName=document.getElementById("projectName").value;

//     let attendanceType="";

//     // navigator.geolocation.getCurrentPosition(

//     // function(position){

//     // fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${position.coords.latitude}&lon=${position.coords.longitude}`)

//     // .then(response=>response.json())

//     // .then(data=>{

//     // locationName=
//     // data.address.suburb||
//     // data.address.city||
//     // data.address.town||
//     // data.address.village||
//     // "Unknown Location";

//     // });

//     // },

//     // function(){

//     // locationName="Location not allowed";

//     // }

//     // );

//     checkinBtn.onclick=function(){
//         attendanceType="Check In";
//         selfieInputGallery.click();
//     };

//     checkoutBtn.onclick=function(){
//         attendanceType="Check Out";
//         selfieInputGallery.click();
//     };

//     selfieInputGallery.onchange=function(){
//         const file=this.files[0];

//         if(!file){
//         return;
//         }

//     const imageUrl=URL.createObjectURL(file);
//     const currentDate=new Date().toLocaleDateString();
    
//     const formData=new FormData()
//     formData.append("image",file);
//     formData.append("type",attendanceType);
//     formData.append("date",currentDate);
//     formData.append("worker_name",workerName);
//     formData.append("project_name",projectName);


//     const card=`
//         <div class="card p-3 mb-3">
//             <img src="${imageUrl}" style="width:200px;border-radius:10px;" class="mb-2">
//             <h5>${attendanceType}</h5>
//             <p><strong>Date:</strong>${currentDate}</p>
//         </div>

//     `;

//     attendancePreview.innerHTML=card;

//     fetch("/save-attendance-checkin",{
//         method:"POST",
//         body:formData
//     })
//     .then(response=>response.json())
//     .then(data=>{
//         statusText.innerText=attendanceType+" Successful";
//     });

//     };

// });


// selfieInputGallery.onchange = function(){
//     const file = this.files[0];

//     if(!file){ return; }

//     const imageUrl = URL.createObjectURL(file);

//     // consistent date format — same on every phone
//     const now         = new Date();
//     const currentDate = now.getFullYear() + "-" +
//         String(now.getMonth() + 1).padStart(2, "0") + "-" +
//         String(now.getDate()).padStart(2, "0");

//     const formData = new FormData();
//     formData.append("image",        file);
//     formData.append("type",         attendanceType);
//     formData.append("date",         currentDate);
//     formData.append("worker_name",  workerName);
//     formData.append("project_name", projectName);

//     // show preview with uploading status
//     attendancePreview.innerHTML = `
//         <div class="card p-3 mb-3">
//             <img src="${imageUrl}" style="width:200px;border-radius:10px;" class="mb-2">
//             <h5>${attendanceType}</h5>
//             <p><strong>Date:</strong> ${currentDate}</p>
//             <p id="upload-status" style="color:orange;font-weight:600;">
//                 ⏳ Uploading... please wait
//             </p>
//         </div>
//     `;

//     // try upload — retry up to 3 times if fails
//     uploadWithRetry(formData, 3);
// };

// tries upload — if fails waits 2 seconds and tries again
// stops after 3 attempts and shows error

document.addEventListener("DOMContentLoaded", function(){

    const checkinBtn         = document.getElementById("checkinBtn");
    const checkoutBtn        = document.getElementById("checkoutBtn");
    const selfieInputGallery = document.getElementById("selfieInputGallery");
    const attendancePreview  = document.getElementById("attendancePreview");
    const statusText         = document.getElementById("statusText");
    const workerName         = document.getElementById("workerName").value;
    const projectName        = document.getElementById("projectName").value;

    let attendanceType = "";

    // check all elements exist before adding listeners
    if (!checkinBtn || !checkoutBtn || !selfieInputGallery) {
        console.error("Checkin elements not found");
        return;
    }

    checkinBtn.onclick = function(){
        attendanceType = "Check In";
        selfieInputGallery.click();
    };

    checkoutBtn.onclick = function(){
        attendanceType = "Check Out";
        selfieInputGallery.click();
    };

    selfieInputGallery.onchange = function(){

        const file = this.files[0];
        if (!file) { return; }

        const imageUrl = URL.createObjectURL(file);

        // consistent date on every phone
        const now         = new Date();
        const currentDate = now.getFullYear() + "-" +
            String(now.getMonth() + 1).padStart(2, "0") + "-" +
            String(now.getDate()).padStart(2, "0");

        const formData = new FormData();
        formData.append("image",        file);
        formData.append("type",         attendanceType);
        formData.append("date",         currentDate);
        formData.append("worker_name",  workerName);
        formData.append("project_name", projectName);

        // show preview with uploading status
        attendancePreview.innerHTML = `
            <div class="card p-3 mb-3">
                <img src="${imageUrl}"
                     style="width:200px;border-radius:10px;"
                     class="mb-2">
                <h5>${attendanceType}</h5>
                <p><strong>Date:</strong> ${currentDate}</p>
                <p id="upload-status"
                   style="color:orange;font-weight:600;">
                    ⏳ Uploading... please wait
                </p>
            </div>
        `;

        // start upload with 3 retries
        doUpload(formData, attendanceType, statusText, 3);
    };

});

// defined outside DOMContentLoaded so it is always reachable
function doUpload(formData, attendanceType, statusText, attemptsLeft) {

    fetch("/save-attendance-checkin", {
        method: "POST",
        body:   formData
    })
    .then(function(response) {
        if (!response.ok) {
            throw new Error("Server error " + response.status);
        }
        return response.json();
    })
    .then(function(data) {
        if (data.success) {
            statusText.innerText = attendanceType + " Successful ✅";
            const status = document.getElementById("upload-status");
            if (status) {
                status.textContent = "✅ Saved successfully";
                status.style.color = "green";
            }
        } else {
            throw new Error(data.error || "Upload failed");
        }
    })
    .catch(function(error) {
        console.error("Upload error:", error);

        if (attemptsLeft > 1) {
            const status = document.getElementById("upload-status");
            if (status) {
                status.textContent = "⚠️ Retrying... (" + (attemptsLeft - 1) + " attempts left)";
                status.style.color = "orange";
            }
            // wait 2 seconds then retry
            setTimeout(function() {
                doUpload(formData, attendanceType, statusText, attemptsLeft - 1);
            }, 2000);

        } else {
            const status = document.getElementById("upload-status");
            if (status) {
                status.textContent = "❌ Upload failed. Check internet and try again.";
                status.style.color = "red";
            }
            alert("Upload failed after 3 attempts. Please check internet and try again.");
        }
    });
}


function uploadWithRetry(formData, attemptsLeft) {

    fetch("/save-attendance-checkin", {
        method: "POST",
        body:   formData
    })
    .then(response => {
        if (!response.ok) throw new Error("Server error " + response.status);
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // update status to success
            statusText.innerText = attendanceType + " Successful ✅";
            const status = document.getElementById("upload-status");
            if (status) {
                status.textContent = "✅ Saved successfully";
                status.style.color = "green";
            }
        } else {
            throw new Error(data.error || "Upload failed");
        }
    })
    .catch(error => {
        console.error("Upload failed:", error);

        if (attemptsLeft > 1) {
            // show retry message and try again after 2 seconds
            const status = document.getElementById("upload-status");
            if (status) {
                status.textContent = "⚠️ Retrying... (" + (attemptsLeft - 1) + " left)";
                status.style.color = "orange";
            }
            setTimeout(() => uploadWithRetry(formData, attemptsLeft - 1), 2000);

        } else {
            // all 3 attempts failed
            const status = document.getElementById("upload-status");
            if (status) {
                status.textContent = "❌ Upload failed. Check internet and try again.";
                status.style.color = "red";
            }
            alert("Upload failed after 3 attempts. Please check internet and try again.");
        }
    });
}

const taskCheckboxes = document.querySelectorAll(".taskCheckbox");

taskCheckboxes.forEach(box => {

  box.addEventListener("change", function() {

    const taskId      = this.dataset.id;
    const isCompleted = this.checked;
    // get engineer name from checkbox data attribute
    // so we update only that engineer's progress bar
    const engineer    = this.dataset.engineer;

    fetch("/update-task", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        task_id:      taskId,
        is_completed: isCompleted
      })
    })
    .then(response => response.json())
    .then(data => {

      // update progress bar for this specific engineer card
      // not all cards — only the one that changed
      const bar   = document.getElementById("taskProgressBar-" + engineer);
      const text  = document.getElementById("progressText-"    + engineer);

      if (bar)  bar.style.width  = data.progress + "%";
      if (text) text.innerText   = data.completed + " of " + data.total + " tasks — " + data.progress + "%";

    });

  });

});
