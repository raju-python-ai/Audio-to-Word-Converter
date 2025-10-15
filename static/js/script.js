document.getElementById("uploadForm").addEventListener("submit", function(e) {
    e.preventDefault();

    const statusText = document.getElementById("status");
    statusText.innerText = "Processing... Please wait.";

    const formData = new FormData();
    const file = document.getElementById("audioFile").files[0];
    formData.append("audio", file);

    fetch("/upload", {
        method: "POST",
        body: formData
    })
    .then(response => {
        if (!response.ok) throw new Error("Upload failed");
        return response.blob();
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "tamil_transcription.docx";
        document.body.appendChild(a);
        a.click();
        a.remove();
        statusText.innerText = "✅ Done! File downloaded.";
    })
    .catch(error => {
        statusText.innerText = "❌ Error: " + error.message;
    });
});
