async function generateChecklist() {
    let name = document.getElementById("name").value;
    let age = parseInt(document.getElementById("age").value);
    let allergy = document.getElementById("allergy").value;
    let medications = document.getElementById("medications").value;
    let procedure = document.getElementById("procedure").value;

    let resultDiv = document.getElementById("result");
    resultDiv.innerHTML = "⏳ Generating checklist...";

    try {
        let response = await fetch("http://127.0.0.1:5000/generate_checklist", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({name, age, allergy, medications, procedure})
        });

        let data = await response.json();
        let checklist = data.checklist;
        let warnings = data.warnings;

        resultDiv.innerHTML = "";

        checklist.forEach((item, index) => {
            let div = document.createElement("div");
            div.className = "checklist-item";

            let checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            checkbox.id = "item-" + index;

            let label = document.createElement("label");
            label.htmlFor = "item-" + index;
            label.innerText = item;

            div.appendChild(checkbox);
            div.appendChild(label);
            resultDiv.appendChild(div);
        });

        warnings.forEach(w => {
            let warn = document.createElement("div");
            warn.className = "warning";
            warn.innerText = w;
            resultDiv.appendChild(warn);
        });

        let submitBtn = document.createElement("button");
        submitBtn.className = "submit-btn";
        submitBtn.innerText = "Submit Checklist";
        submitBtn.onclick = function() {
            let incomplete = [];
            checklist.forEach((_, index) => {
                if(!document.getElementById("item-" + index).checked){
                    incomplete.push(checklist[index]);
                }
            });

            if(incomplete.length > 0){
                let message = "⚠ Checklist incomplete!\n";
                incomplete.forEach((step, i) => { message += `${i+1}. ${step}\n`; });
                if(warnings.length > 0){
                    message += "\nWarnings:\n";
                    warnings.forEach((w, i) => { message += `${i+1}. ${w}\n`; });
                }
                alert(message);
            } else {
                alert("✅ Checklist completed successfully!");
            }
        };
        resultDiv.appendChild(submitBtn);

    } catch (err) {
        resultDiv.innerHTML = "❌ Failed to generate checklist. Make sure backend is running.";
        console.error(err);
    }
}

async function askAssistant() {
    let query = document.getElementById("assistant-query").value;
    let resultDiv = document.getElementById("assistant-result");
    
    if (!query) {
        alert("Please enter a query.");
        return;
    }

    resultDiv.innerHTML = "⏳ Thinking...";
    resultDiv.style.display = "block";

    try {
        let response = await fetch("http://127.0.0.1:5000/query_assistant", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({query: query})
        });

        let data = await response.json();
        
        // Use marked.js or just display as paragraph if line breaks exist
        let text = data.response.replace(/\n/g, "<br>");
        resultDiv.innerHTML = `<p>${text}</p>`;
    } catch (err) {
        resultDiv.innerHTML = "❌ Failed to reach the assistant. Make sure backend is running.";
        console.error(err);
    }
}