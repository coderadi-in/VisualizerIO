const exportBtn = document.querySelector("#download-btn");
let socketRecv = false;

// & Socket listener for download button callback
socket.on('export_project_callback', (data) => {
    document.querySelector(".mini").innerHTML = data.size

    if (data.status == 200) {
        socketRecv = true;
        console.log("Done");        
        document.querySelector('#status').innerHTML = "Your download is ready.";
        let btn = document.querySelector("#download-btn");
        btn.style.backgroundColor = "var(--primary)";
        btn.style.cursor = "pointer";
        btn.href = data.file
        btn.download = data.file

    } else {
        document.querySelector('#status').innerHTML = "Sorry! We're unable to prepare your download now.";
    }
})

// * Timeout for better UX
setTimeout(() => {
    if (!socketRecv) {
        document.querySelector('#status').innerHTML = "Sorry! We're unable to prepare your download now.";
        document.querySelector(".mini").innerHTML = "Can't fetch!"
    }
}, 10000);

// // & Event listener for export button
// exportBtn.addEventListener('click', () => {
//     if (socketRecv) {
//         const projectTitle = document.querySelector("#project-title").innerHTML;
//         socket.emit('delete_zip', {
//             title: projectTitle
//         });
//     }
// })