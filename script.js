document.addEventListener("DOMContentLoaded", function () {
    console.log("JavaScript Loaded!");

    // Function to update the resume preview
    function generateResume() {
        console.log("Generate Resume button clicked!"); // ✅ Debug log

        let name = document.getElementById("name").value.trim();
        let email = document.getElementById("email").value.trim();
        let phone = document.getElementById("phone").value.trim();

        if (!name || !email || !phone) {
            alert("Please fill out all fields!");
            return;
        }

        document.getElementById("r-name").innerText = document.getElementById("name").value;
        document.getElementById("r-email").innerText = document.getElementById("email").value;
        document.getElementById("r-phone").innerText = document.getElementById("phone").value;
        document.getElementById("r-linkedin").innerText = document.getElementById("linkedin").value;
        document.getElementById("r-education").innerText = document.getElementById("education").value;
        document.getElementById("r-experience").innerText = document.getElementById("experience").value;
        document.getElementById("r-skills").innerText = document.getElementById("skills").value;
        document.getElementById("r-projects").innerText = document.getElementById("projects").value;

        console.log("Resume Updated!"); // 
    }

    // Attach the event listener properly
    document.getElementById("generate-btn").addEventListener("click", generateResume);
});


     // Function to download resume as PDF
     function downloadResume() {
        console.log("Download PDF button clicked!"); // 

        if (!window.jsPDF) {
            console.error("jsPDF library is missing!");
            alert("Error: PDF generation library (jsPDF) is not loaded.");
            return;
        }

        const doc = new jsPDF();
        doc.setFont("helvetica", "bold");
        doc.text("Resume", 105, 20, null, null, "center");

        let resumeContent = `
Name: ${document.getElementById("name").value || "Your Name"}
Email: ${document.getElementById("email").value || "your.email@example.com"}
Phone: ${document.getElementById("phone").value || "123-456-7890"}
LinkedIn: ${document.getElementById("linkedin").value || "linkedin.com/in/your-profile"}

Education:
${document.getElementById("education").value || "Your education details..."}

Experience:
${document.getElementById("experience").value || "Your experience details..."}

Skills:
${document.getElementById("skills").value || "Your skills..."}

Projects:
${document.getElementById("projects").value || "Your project details..."}
`;


        doc.setFont("times", "normal");
        doc.setFontSize(12);
        doc.text(resumeContent, 10, 30);

        doc.save("Resume.pdf");
        console.log("PDF Downloaded!"); // 
    }

    // Attach event listener to Download PDF button
    document.getElementById("download-btn").addEventListener("click", downloadResume);


    document.getElementById("generate-btn").addEventListener("click", generateResume);
    document.getElementById("download-btn").addEventListener("click", downloadResume);
    
    let uploadButton = document.getElementById("upload-btn");
    if (uploadButton) {
        uploadButton.addEventListener("click", uploadResume);
    }
