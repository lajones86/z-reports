import requests
import zr_io as Io

def make_api_request(api_request):
    response = requests.get(api_request)
    status = str(response.status_code)
    if status.startswith("2"):
        return(response.json())
    else:
        Io.error("Api request %s returned %s error" % (api_request, status))
