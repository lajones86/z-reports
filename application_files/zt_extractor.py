#a shim to work with files extracted by the firefox addon

import os
import re

def get_extractor_download_dirs():
    download_dirs = []
    firefox_profiles = os.path.join((os.environ["AppData"]), r"Mozilla\Firefox\Profiles")
    for root, dirs, files in os.walk(firefox_profiles):
        for f in files:
            if f == "prefs.js":
                with open(os.path.join(root, f), "r") as f:
                    for line in f:
                        if "browser.download.dir" in line:
                            download_dir = ""
                            for char in line[::-1]:
                                if char == ",":
                                    break
                                else:
                                    download_dir += char
                            if download_dir:
                                download_dir = (download_dir[::-1]).lstrip(" \"").rstrip(" \");\n").replace(r"\\", "\\")
                                download_dirs.append(os.path.join(download_dir, "z-reports_downloads"))
    return(download_dirs)

def get_extractor_file(identifier, download_dirs = None):
    if not download_dirs:
        download_dirs = get_extractor_download_dirs()
    extractor_files = []
    extractor_timestamps = []
    re_extractor_file = re.compile("[0-9]{4}\-[0-9]{2}\-[0-9]{2}\-[0-9]{2}\-[0-9]{2}\-[0-9]{2}\-%s\(?[0-9]*\)?.htm" % identifier)
    for download_dir in download_dirs:
        for f in os.listdir(download_dir):
            if re_extractor_file.match(f):
                extractor_files.append(os.path.join(download_dir, f))
                extractor_timestamps.append(f[:19])
    extractor_timestamps.sort()
    last_timestamp = extractor_timestamps[-1]
    for extractor_file in extractor_files:
        if last_timestamp in extractor_file:
            return(extractor_file)
    return(None)
