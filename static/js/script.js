document.getElementById("userIdInput").style.display = "none";
document.getElementById("titleInput").style.display = "block";
document.getElementById("recommendations").style.display = "none";

function toggle(){
    let drp=document.getElementById("method");
    if (drp.value === "Content") {
        document.getElementById("userId").value = "";
        document.getElementById('title').value ="";
        document.getElementById("titleInput").style.display="block";
        document.getElementById("userIdInput").style.display="none";
    }
    else if (drp.value === "Collaborative") {
        document.getElementById("userId").value = "";
        document.getElementById('title').value ="";
        document.getElementById("titleInput").style.display="none";
        document.getElementById("userIdInput").style.display="block";
    }
    else if (drp.value === "Hybrid"){
        document.getElementById("userId").value = "";
        document.getElementById('title').value =""; 
        document.getElementById("titleInput").style.display="block";
        document.getElementById("userIdInput").style.display="block";
    }
}

document.getElementById("recommendationForm").addEventListener("submit", function (e) {
    e.preventDefault();
    const method = document.getElementById("method").value;    
    let requestBody = {method};
    if (method == "Content") {
                requestBody.title = document.getElementById("title").value;
    }
    else if (method == "Collaborative") {
        requestBody.userId = document.getElementById("userId").value;
    }
    else if (method == "Hybrid") {
        requestBody.userId = document.getElementById("userId").value;
        requestBody.title = document.getElementById("title").value;
    }


    fetch("/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("API Response:", data);
            const resultsList = document.getElementById("recommendations-list");
            resultsList.innerHTML="";
            
            if (!Array.isArray(data) || data.length === 0) {
                resultsDiv.innerHTML += "<p>No recommendations found.</p>";
                return;
            }
            document.getElementById("recommendations").style.display="block";
            data.forEach(movie => {
                console.log("Movie Data:", movie);
                const listItem = document.createElement("li")
                listItem.textContent=movie;
                resultsList.appendChild(listItem);
            });
        })
        .catch(error => console.error("Error fetching recommendations:", error));
});
