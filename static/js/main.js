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


document.addEventListener("DOMContentLoaded",function(){
    const checkinBtn=document.getElementById("checkinBtn");
    const checkoutBtn=document.getElementById("checkoutBtn");
    const selfieInputGallery =document.getElementById("selfieInputGallery");
    const attendancePreview=document.getElementById("attendancePreview");
    const statusText=document.getElementById("statusText");
    const workerName=document.getElementById("workerName").value;
    const projectName=document.getElementById("projectName").value;

    let attendanceType="";

    // navigator.geolocation.getCurrentPosition(

    // function(position){

    // fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${position.coords.latitude}&lon=${position.coords.longitude}`)

    // .then(response=>response.json())

    // .then(data=>{

    // locationName=
    // data.address.suburb||
    // data.address.city||
    // data.address.town||
    // data.address.village||
    // "Unknown Location";

    // });

    // },

    // function(){

    // locationName="Location not allowed";

    // }

    // );

    checkinBtn.onclick=function(){
        attendanceType="Check In";
        selfieInputGallery.click();
    };

    checkoutBtn.onclick=function(){
        attendanceType="Check Out";
        selfieInputGallery.click();
    };

    selfieInputGallery.onchange=function(){
        const file=this.files[0];

        if(!file){
        return;
        }

    const imageUrl=URL.createObjectURL(file);
    const currentDate=new Date().toLocaleDateString();
    
    const formData=new FormData()
    formData.append("image",file);
    formData.append("type",attendanceType);
    formData.append("date",currentDate);
    formData.append("worker_name",workerName);
    formData.append("project_name",projectName);


    const card=`
        <div class="card p-3 mb-3">
            <img src="${imageUrl}" style="width:200px;border-radius:10px;" class="mb-2">
            <h5>${attendanceType}</h5>
            <p><strong>Date:</strong>${currentDate}</p>
        </div>

    `;

    attendancePreview.innerHTML=card;

    fetch("/save-attendance-checkin",{
        method:"POST",
        body:formData
    })
    .then(response=>response.json())
    .then(data=>{
        statusText.innerText=attendanceType+" Successful";
    });

    };

});



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
