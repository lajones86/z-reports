//document.body.style.border = "5px solid red";

function sendPage(htmlOutput) {
    browser.runtime.sendMessage({ htmlOutputString: htmlOutput }).then();
}

htmlOutput = new XMLSerializer().serializeToString(document)

sendPage(htmlOutput);
