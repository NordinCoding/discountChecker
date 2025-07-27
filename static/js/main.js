function remove_row(button) {
    var row = button.closest('tr')
    var rowData = { name: row.querySelector('.product-name').innerText }
    fetch(`${window.urlPrefix}/remove_row`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(rowData)
    });
    row.remove();

    // Check if table is empty after removing row, if so, add the empty table message row
    const { totalRows, tableBody } = checkRows();
    if (totalRows === 0) {
        emptyTableMessage(tableBody);
    }
};

window.remove_row = remove_row



function fadeOut(messageDiv, submitButton) {
    submitButton.disabled = true;

    setTimeout(() => {
        messageDiv.style.opacity = '0';
        setTimeout(() => {
            messageDiv.innerHTML = "";
            messageDiv.removeAttribute("class");
            messageDiv.removeAttribute("style");
            submitButton.disabled = false;
        }, 1000);
     }, 3000); //3 seconds
};

window.fadeOut = fadeOut



function updateProductTable(product_data, tableBody){
    if (product_data["URL"].includes("mediamarkt")){
        var mediamarktBool = true
    }
    else {
        var mediamarktBool = false
    }

    // Create new row in productTable to show the newly gathered data
    var newRow = document.createElement("tr");
    newRow.setAttribute("id", `product-${product_data["id"]}`);
    newRow.setAttribute("class", "product-row");
    tableBody.appendChild(newRow);

    // Create name cell
    var nameCell = document.createElement("td");
    nameCell.setAttribute("class", "product-name-td");
    
    // Create span element for the websites URL to store in nameCell
    var strongName = document.createElement("strong");

    // Change website name based on previously set boolean
    if (mediamarktBool === true) {
        strongName.appendChild(document.createTextNode("[MediaMarkt]"))
    }
    else{
        strongName.appendChild(document.createTextNode("[Bol.com]"))
    }

    // Create hyperlink element for the website href
    var websiteLink = document.createElement("a");
    websiteLink.setAttribute("target", "_blank");

    if (mediamarktBool === true){
        websiteLink.setAttribute("href", "https://www.mediamarkt.nl/nl/")
    }
    else{
        websiteLink.setAttribute("href", "https://www.bol.com/nl/nl/")     
    }

    // Create span element for the website name/link
    var websiteSpan = document.createElement("span");
    websiteSpan.setAttribute("class", "website-name")

    websiteLink.appendChild(strongName)
    websiteSpan.appendChild(websiteLink)
    nameCell.appendChild(websiteSpan)


    // Create hyperlink element for the products URL to store in nameCell
    var urlCell = document.createElement("a");
    urlCell.appendChild(document.createTextNode(product_data["name"]));
    urlCell.setAttribute("target", "_blank");
    urlCell.setAttribute("class", "product-name");
    urlCell.setAttribute("id", `name-${product_data["id"]}`);
    urlCell.setAttribute("href", product_data["URL"]);
    nameCell.appendChild(urlCell);

    // Create button element for the remove row button to store in nameCell
    var buttonCell = document.createElement("button");
    buttonCell.appendChild(document.createTextNode("Remove"));
    buttonCell.setAttribute("class", "button remove-btn");
    buttonCell.setAttribute("onclick", "remove_row(this)");
    nameCell.appendChild(buttonCell);
    newRow.appendChild(nameCell);
    
    // Create currentPrice cell
    var currentPriceCell = document.createElement("td");
    if (product_data["currentPrice"] > 0 ) {
        currentPriceCell.appendChild(document.createTextNode(`€${Number(product_data["currentPrice"]).toFixed(2)}`));
    } 
    else {
        currentPriceCell.appendChild(document.createTextNode("N/A"));
    }

    currentPriceCell.setAttribute("class", "current-price");
    currentPriceCell.setAttribute("id", `current-price-${product_data["id"]}`);
    newRow.appendChild(currentPriceCell);

    // Create ogPrice cell
    var ogPriceCell = document.createElement("td");

    if (product_data["ogPrice"] > 0 ) {
        ogPriceCell.appendChild(document.createTextNode(`€${Number(product_data["ogPrice"]).toFixed(2)}`));
    }
    else {
        ogPriceCell.appendChild(document.createTextNode("N/A"));
    }

    ogPriceCell.setAttribute("class", "og-price");
    ogPriceCell.setAttribute("id", `og-price-${product_data["id"]}`);
    newRow.appendChild(ogPriceCell);

    // Create savings Cell
    var savingsCell = document.createElement("td");
    var savings = product_data["ogPrice"] - product_data["currentPrice"]
    savingsCell.appendChild(document.createTextNode(`€${savings.toFixed(2)}`));
    if (savings > 0) {
        savingsCell.setAttribute("class", "savings-up");
    }
    else {
        savingsCell.setAttribute("class", "savings-down");
    }
    
    savingsCell.setAttribute("id", `savings-${product_data["id"]}`);
    newRow.appendChild(savingsCell);
};

window.updateProductTable = updateProductTable



function checkRows() {
    // Get table body and return the amount of rows inside the tables body
    const tableBody = document.getElementById('product-table-body');
    const totalRows = tableBody.rows.length;
    return { totalRows, tableBody }
}

window.checkRows = checkRows



function emptyTableMessage(tableBody) {
    // Create new table row
    var emptyTableRow = document.createElement("tr");
    emptyTableRow.setAttribute("id", "empty-table-row")

    // Create new table cell
    var emptyTableCell = document.createElement("td");
    emptyTableCell.setAttribute("id", "empty-table-Cell")
    emptyTableCell.setAttribute("colspan", "4")

    // Populate table body with the new row and cell that includes a message
    emptyTableCell.appendChild(document.createTextNode("This table is empty. Add a product by giving the text box above a URL"));
    emptyTableRow.appendChild(emptyTableCell);
    tableBody.appendChild(emptyTableRow);
}

window.emptyTableMessage = emptyTableMessage