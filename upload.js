// static/upload.js
document.getElementById("file-input").addEventListener("change", function () {
    const fileName = this.files[0]?.name || "";
    const fileDisplay = document.getElementById("file-name");
    const successMsg = document.getElementById("success-message");

    if (fileName) {
        fileDisplay.textContent = `✅ Selected: ${fileName}`;
        fileDisplay.classList.remove("hidden");
        successMsg.classList.add("hidden");
    }
});
