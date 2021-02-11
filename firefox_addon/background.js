function zNotify(title, message) {
    browser.notifications.create("zNotification", {
        "type": "basic",
        "title": title,
        "message": message
    }).then();
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function getState(downloadArray) {
    theDownload = downloadArray[0];
    if (theDownload.state == "in_progress") {
        sleep(1000).then(() => { monitorDownload(theDownload.id); });
    }
    else if (theDownload.state == "complete") { zNotify("Download succeeded", theDownload.filename); }
    else { zNotify("Download failed", theDownload.filename); }
}

function monitorDownload(downloadId) {
    browser.downloads.search({"id" : downloadId}, getState);
}

function handleMessage(request, sender, sendResponse) {
    pageUrl = request.pageUrl;
    urlHost = pageUrl.split("/")[2];

    //set the filename based on what's being downloaded
    currentDateTime = new Date();
    fileTimestamp = currentDateTime.getFullYear().toString() + "-" +
        ('0' + (currentDateTime.getMonth()+1)).slice(-2) + "-" +
        ('0' + currentDateTime.getDate()).slice(-2) + "-" +
        ('0' + currentDateTime.getHours()).slice(-2) + "-" +
        ('0' + currentDateTime.getMinutes()).slice(-2) + "-" +
        ('0' + currentDateTime.getSeconds()).slice(-2);

    fileName = "z-reports_downloads\\" + fileTimestamp + "-";


    //add new sites here
    if (urlHost.endsWith("fidelity.com")) {
        if (pageUrl.includes("portfolio#/positions/Z")) {
            fileName += "fidelity";
        }
        else {
            zNotify("Download aborted", "Unable to verify fidelity portfolio positions url");
            fileName = "";
        }
    }
    else if (urlHost.endsWith("webull.com")) {
        if (pageUrl.includes("/account")) {
            fileName += "webull";
        }
        else {
            zNotify("Download aborted", "Unable to verify webull portfolio positions url");
            fileName = "";
        }
    }
    else if (urlHost.endsWith("ucbonline.com")) {
        if (pageUrl.includes("Account/Detail")) {
            fileName += "ucb";
        }
        else {
            zNotify("Download aborted", "Unable to verify ucb loan url");
            fileName = "";
        }
    }


    else {
        zNotify("Unknown host", urlHost);
        fileName = "";
    }

    if (fileName != "") {

        console.log("Downloading");
        fileName += ".htm";
        console.log(fileName);

        downloadString = request.htmlOutputString
        downloadBlob = new Blob([downloadString], {
            type : "text/plain"
        });
        objDownloadURL = URL.createObjectURL(downloadBlob);

        var startDownload = browser.downloads.download({
            url : objDownloadURL,
            filename : fileName,
            saveAs : false
        },
            monitorDownload
        );
        startDownload.then();
    }

}

browser.runtime.onStartup.addListener(function() {
    browser.runtime.onMessage.addListener(handleMessage);
    console.log("z-Extractor loaded on startup.");
});

browser.runtime.onInstalled.addListener(function() {
    browser.runtime.onMessage.addListener(handleMessage);
    console.log("z-Extractor loaded on install.");
});


browser.browserAction.onClicked.addListener((tab) => { browser.tabs.executeScript(null, {file: "content.js"}); } );
