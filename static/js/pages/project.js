const newObjective = document.querySelector("#add-objective");
const checkboxes = document.querySelectorAll(".checkbox");
const deletebtns = document.querySelectorAll(".delete-objective");
const deleteBtn = document.querySelector("#delete-project");
const shareBtn = document.querySelector("#share");
const downloadBtn = document.querySelector("#download");

const showToolBtn = document.querySelector("#toolbar-btn");
const showToolIcon = document.querySelector("#toolbar-btn .show");
const hideToolIcon = document.querySelector("#toolbar-btn .hide");
const toolbar = document.querySelector(".ui-toolbar");

const projectId = document.querySelector("#project-id").innerHTML;
const userId = document.querySelector("#userid").innerHTML;
const adminId = document.querySelector("#admin-id").innerHTML;
const teamId = document.querySelector("#team-id") ? document.querySelector("#team-id").innerHTML : '0';

const objectives = document.querySelectorAll(".objective");
const chartElem = document.querySelector("#contribution-chart");
const chartArea = chartElem ? chartElem.getContext('2d') : null;
const chartColor = document.body.dataset.chartColor;
const chartType = document.body.dataset.chartType;

const sharePopup = document.querySelector("#share-popup");
const downloadPopup = document.querySelector("#download-popup");

const colorScheme = {
    timelineBg: ["#4C8EFF", "#FFFFFF00"],
    timelineHover: ["#C0D8FF", "#808080"],
    taskBg: ["#93FF93", "#FF9393"],
    taskHover: ["#CCFFCC", "#FFCCCC"],
    contributionBg: "#CCFFCC",
    contributionBorder: "#93FF93"
};

const classic = {
    blue: { ...colorScheme },
    green: { ...colorScheme },
    red: { ...colorScheme },
    yellow: { ...colorScheme }
};

const modern = {
    blue: {
        timelineBg: ["#7CACFF", "#FFFFFF00"],
        timelineHover: ["#C0D8FF", "#808080"],
        taskBg: ["#4C8EFF", "#7CACFF"],
        taskHover: ["#89B4FF", "#9BC0FF"],
        contributionBg: "#9BC0FF",
        contributionBorder: "#89B4FF",
    },
    green: {
        timelineBg: ["#7CFFAC", "#FFFFFF00"],
        timelineHover: ["#C0FFD8", "#808080"],
        taskBg: ["#36C76B", "#7CFFAC"],
        taskHover: ["#89FFC4", "#9BFFD5"],
        contributionBg: "#9BFFD5",
        contributionBorder: "#89FFC4",
    },
    red: {
        timelineBg: ["#FF7CAC", "#FFFFFF00"],
        timelineHover: ["#FFC0D8", "#808080"],
        taskBg: ["#FF4C8E", "#FF7CAC"],
        taskHover: ["#FF8989", "#FF9B9B"],
        contributionBg: "#FF9B9B",
        contributionBorder: "#FF8989",
    },
    yellow: {
        timelineBg: ["#F0F084", "#FFFFFF00"],
        timelineHover: ["#FFFFD0", "#808080"],
        taskBg: ["#DBDB53", "#F0F084"],
        taskHover: ["#FDFF89", "#FFF09B"],
        contributionBg: "#FFF09B",
        contributionBorder: "#FDFF89",
    },
};

const currentScheme = (chartColor == 'classic') ? classic : modern;
const currentAccent = document.body.dataset.accent;

// * Function to export project
function export_project() {
    // | Export canvas
    const timelineImage = document.querySelector("#timeline-chart").toDataURL('image/png', 1.0);
    const taskImage = document.querySelector("#task-chart").toDataURL('image/png', 1.0);

    // | Export objectives
    objective_text = [];
    const objectives = document.querySelectorAll(".objective");
    objectives.forEach((objective) => {
        objective_text.push(objective.querySelector(".text").innerHTML);
    });

    // | Export tags
    const tags = document.querySelectorAll(".tags .tag");
    let tag_text = [];
    tags.forEach((tag) => {
        tag_text.push(tag.innerHTML);
    });

    // | Export urls
    const urls = document.querySelectorAll('.re-url');
    let url_text = [];
    urls.forEach((url) => {
        url_text.push(url.innerHTML);
    })

    // | Export images
    const images = document.querySelectorAll(".img-group .img");
    let image_urls = [];
    images.forEach((img) => {
        image_urls.push(img.src);
    });

    // | Export documents
    const docs = document.querySelectorAll(".docs-overview .link");
    let doc_urls = [];
    docs.forEach((doc) => {
        doc_urls.push(doc.href);
    });    

    // | Emit to server
    socket.emit('export_project', {
        'charts': {
            'timeline': timelineImage,
            'task': taskImage
        },
        'objectives': objective_text,
        'images': image_urls,
        'urls': url_text,
        'tags': tag_text,
        'docs': doc_urls,
        'project': {
            'title': document.querySelector("#project-title").innerHTML,
            'desc': document.querySelector("#project-desc").innerHTML
        }
    });
}

// * function to show objectives 
function showObjectives(index=0) {
    if (index >= objectives.length) {return;}

    objectives[index].classList.add('show');

    setTimeout(() => {
        showObjectives(index+1);
    }, 100);
}

// * function to send socket msg to server
function transmit(namespace, data) {
    socket.emit(namespace, {
        'obj_id': data,
        'team_id': parseInt(teamId),
        'user_id': parseInt(userId),
        'admin_id': parseInt(adminId),
        'route': parseInt(projectId),
    })
}

async function rednerContributionChart() {
    if (teamId != '0') {
        const response = await fetch(`/api/team/members/contribution?team_id=${teamId}`);
        const data = await response.json();

        const contributionChart = new Chart(chartArea, {
            type: 'bar',
            data: {
                labels: data.members,
                datasets: [{
                    label: "Contribution",
                    data: data.contribution,
                    backgroundColor: currentScheme[currentAccent].contributionBg,
                    borderColor: currentScheme[currentAccent].contributionChart,
                    borderWidth: 1,
                    hoverBackgroundColor: currentScheme[currentAccent].contributionBg,
                    hoverBorderColor: currentScheme[currentAccent].contributionChart,
                    indexAxis: 'y',
                    barThickness: 75
                }]
            }
        });
    }
}

async function renderTimelineChart() {
    const response = await fetch(`/api/projects/${projectId}/time-data?userid=${adminId}&teamid=${teamId}`);
    const data = await response.json();

    if (data.left_time !== undefined && data.spent_time !== undefined) {
        const timeline_chart = new Chart(
            document.querySelector("#timeline-chart").getContext('2d'), {
            type: chartType,
            data: {
                labels: ["Left time", "Spent time"],
                datasets: [{
                    label: "Timeline",
                    data: [data.left_time, data.spent_time],
                    backgroundColor: currentScheme[currentAccent].timelineBg,
                    hoverBackgroundColor: currentScheme[currentAccent].timelineHover,
                    hoverOffset: 5,
                    borderColor: "#00000000",
                }]
            }
        });
    }
}

async function renderTaskChart() {
    const response = await fetch(`/api/projects/${projectId}/task-data?userid=${adminId}&teamid=${teamId}`)
    const data = await response.json();

    if (data.completed !== undefined && data.incomplete !== undefined) {
        const task_chart = new Chart(
            document.querySelector("#task-chart").getContext('2d'), {
            type: chartType,
            data: {
                labels: ["Completed", "Incomplete"],
                datasets: [{
                    label: "Tasks",
                    data: [data.completed, data.incomplete],
                    backgroundColor: currentScheme[currentAccent].taskBg,
                    hoverBackgroundColor: currentScheme[currentAccent].taskHover,
                    hoverOffset: 5,
                    borderColor: "#00000000",
                }]
            }
        });
    }
}

// | socket listener for marking objectives
socket.on('mark-obj-callback', (data) => {
    if (data.status == 200) {
        window.location.reload();
    } else {
        alert("Something went wrong.")
    }
})

// | socket listener for delete objectives
socket.on('del-obj-callback', (data) => {
    if (data.status == 200) {
        window.location.reload();
    } else {
        alert("Something went wrong.")
    }
})

// & Event listerner for add-objective button
if (newObjective) {
    newObjective.addEventListener('click', () => {
        openPopup(objectivePopup);
    })
}

// & Event listener to close popup
if (backBtn) {
    backBtn[1].addEventListener('click', () => {
        closePopup();
    })
}

// & Event listener for checkbox markings
if (checkboxes) {
    checkboxes.forEach((checkbox) => {
        checkbox.addEventListener('click', (event) => {
            transmit('mark-obj', event.currentTarget.dataset.objId);
        });
    });
}

// & Event listener for delete button clicks
if (deletebtns) {
    deletebtns.forEach((btn) => {
        btn.addEventListener('click', (event) => {
            transmit('delete-obj', event.currentTarget.dataset.objId);
        })
    })
}

// & Event listener for delete-project
if (deleteBtn) {
    deleteBtn.addEventListener('click', () => {
        confirmation = confirm("Are you sure to delete this project?");

        if (confirmation) {
            window.open(`/projects/delete?project-id=${projectId}`)
        }
    })
}

// * Function to show toolbar
function showToolbar() {
    toolbar.classList.toggle('show');
    showToolIcon.style.display = "inline";
    hideToolIcon.style.display = "none";
}

// * Function to hide toolbar
function hideToolbar() {
    toolbar.classList.toggle('show');
    showToolIcon.style.display = "none";
    hideToolIcon.style.display = "inline";
}

// & Event listener for show/hide toolbar btn
showToolBtn.addEventListener('click', () => {
    if (toolbar.classList.contains("show")) {hideToolbar();}
    else {showToolbar()}
})

// & Event listener for share button
shareBtn.addEventListener('click', () => {
    sharePopup.style.display = "flex";
    document.body.classList.add('no-scroll');

    setTimeout(() => {
        sharePopup.style.opacity = "1";
    }, 100);
})

// & Event listener for download button
downloadBtn.addEventListener('click', () => {
    export_project();
    downloadPopup.style.display = "flex";
    document.body.classList.add('no-scroll');

    setTimeout(() => {
        downloadPopup.style.opacity = "1";
    }, 100);
})

renderTimelineChart();
renderTaskChart();
rednerContributionChart();
showObjectives();