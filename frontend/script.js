// ========================================
// Voice Clone - Frontend JavaScript
// ========================================

// -------------------------------
// Get HTML Elements
// -------------------------------

const voiceFile = document.getElementById("voiceFile");
const uploadArea = document.getElementById("uploadArea");
const selectedFile = document.getElementById("selectedFile");
const fileName = document.getElementById("fileName");
const fileSize = document.getElementById("fileSize");
const removeFile = document.getElementById("removeFile");

const textInput = document.getElementById("textInput");
const characterCount = document.getElementById("characterCount");

const generateButton = document.getElementById("generateButton");

const audioPlayer = document.getElementById("audioPlayer");
const audioPlaceholder = document.getElementById("audioPlaceholder");


// -------------------------------
// File Upload
// -------------------------------

voiceFile.addEventListener("change", function () {

    const file = voiceFile.files[0];

    if (!file) {
        return;
    }

    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);

    selectedFile.hidden = false;
    uploadArea.style.display = "none";
});


// -------------------------------
// Remove Selected File
// -------------------------------

removeFile.addEventListener("click", function () {

    voiceFile.value = "";

    selectedFile.hidden = true;
    uploadArea.style.display = "flex";
});


// -------------------------------
// Format File Size
// -------------------------------

function formatFileSize(bytes) {

    if (bytes === 0) {
        return "0 Bytes";
    }

    const units = [
        "Bytes",
        "KB",
        "MB",
        "GB"
    ];

    const index = Math.floor(
        Math.log(bytes) / Math.log(1024)
    );

    return (
        parseFloat(
            (bytes / Math.pow(1024, index)).toFixed(2)
        )
        + " "
        + units[index]
    );
}


// -------------------------------
// Character Counter
// -------------------------------

textInput.addEventListener("input", function () {

    const length = textInput.value.length;

    characterCount.textContent = length;
});


// -------------------------------
// Generate Button
// -------------------------------

generateButton.addEventListener("click", async function () {

    const file = voiceFile.files[0];
    const text = textInput.value.trim();

    // Check voice file

    if (!file) {

        alert(
            "Please upload an authorized voice sample first."
        );

        return;
    }


    // Check text

    if (!text) {

        alert(
            "Please write some text first."
        );

        textInput.focus();

        return;
    }


    // Loading state

    generateButton.classList.add("loading");

    generateButton.innerHTML = `
        <span>⏳</span>
        Uploading...
    `;


    try {

        // Create form data

        const formData = new FormData();

        formData.append("file", file);


        // Send audio to FastAPI

        const response = await fetch("/upload", {
            method: "POST",
            body: formData
        });


        // Check response

        if (!response.ok) {
            throw new Error("Upload failed");
        }


        const result = await response.json();


        console.log(result);


        // Success

        generateButton.classList.remove("loading");

        generateButton.innerHTML = `
            <span class="button-icon">✅</span>
            Uploaded Successfully
        `;


        alert(
            "تم رفع الملف الصوتي بنجاح! 🎙️"
        );


    } catch (error) {

        console.error(error);


        generateButton.classList.remove("loading");

        generateButton.innerHTML = `
            <span class="button-icon">✨</span>
            Generate Voice
        `;


        alert(
            "حدث خطأ أثناء رفع الملف الصوتي."
        );
    }

});
