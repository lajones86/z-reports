browser.browserAction.onClicked.addListener((tab) => {

    function logIt(string) {
        console.log(string);
    }

    function zNotify(title, message) {
        browser.notifications.create({
            "type": "basic",
            "title": title,
            "message": message
        }).then();
    }

    function handleMessage(request, sender, sendResponse) {

        downloadString = request.htmlOutputString

        downloadBlob = new Blob([downloadString], {
            type : "text/plain"
        });

        //maybe use window.URL here
        //more likely need to make content wait for response
        objDownloadURL = URL.createObjectURL(downloadBlob);

        currentDateTime = new Date();
        fileTimestamp = currentDateTime.getFullYear().toString() + "-" +
            ('0' + (currentDateTime.getMonth()+1)).slice(-2) + "-" +
            ('0' + currentDateTime.getDate()).slice(-2) + "-" +
            ('0' + currentDateTime.getHours()).slice(-2) + "-" +
            ('0' + currentDateTime.getMinutes()).slice(-2) + "-" +
            ('0' + currentDateTime.getSeconds()).slice(-2);

        fileName = "z-reports_downloads\\" + fileTimestamp + "-fidelity.htm";

        var startDownload = browser.downloads.download({
            url : objDownloadURL,
            filename : fileName,
            saveAs : false

        });

        startDownload.then(zNotify("Downloading", fileName));
    }

    currentUrl = tab.url;
    currentTitle = tab.title;

    browser.runtime.onMessage.addListener(handleMessage);

    browser.tabs.executeScript(null, {file: "content.js"});

});

