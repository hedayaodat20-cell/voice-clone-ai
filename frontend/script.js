// ========================================
// Voice Clone AI - Frontend
// ========================================

const API_URL = "https://voice-clone-ai-gvoo.onrender.com";


// -------------------------------
// HTML Elements
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


// -------------------------------
// File Selection
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
// Remove File
// -------------------------------

removeFile.addEventListener("click", function () {

    voiceFile.value = "";

    selectedFile.hidden = true;
    uploadArea.style.display = "flex";

});


// -------------------------------
// File Size
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

    characterCount.textContent =
        textInput.value.length;

});


// -------------------------------
// Generate / Upload
// -------------------------------

generateButton.addEventListener("click", async function () {

    const file = voiceFile.files[0];
    const text = textInput.value.trim();


    // Check file

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


    // Loading

    generateButton.classList.add("loading");

    generateButton.innerHTML = `
        <span>⏳</span>
        Uploading...
    `;


    try {

        const formData = new FormData();

        formData.append("file", file);


        const response = await fetch(
            `${API_URL}/upload`,
            {
                method: "POST",
                body: formData
            }
        );


        if (!response.ok) {

            throw new Error(
                "Upload failed"
            );

        }


        const data = await response.json();


        console.log(
            "Backend response:",
            data
        );


        alert(
            "🎉 Voice sample uploaded successfully!"
        );


    } catch (error) {

        console.error(error);

        alert(
            "❌ Could not connect to the Voice Clone server."
        );


    } finally {

        generateButton.classList.remove("loading");

        generateButton.innerHTML = `
            <span class="button-icon">✨</span>
            Generate Voice
        `;

    }

});
