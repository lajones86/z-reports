function sendPage(htmlOutput, pageUrl) {
    browser.runtime.sendMessage({ htmlOutputString : htmlOutput, pageUrl : pageUrl }).then();
}

htmlOutput = new XMLSerializer().serializeToString(document)
pageUrl = location.href;

sendPage(htmlOutput, pageUrl);
