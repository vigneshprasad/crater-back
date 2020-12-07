import requests
from urllib.parse import urlencode

class TinyurlService:
    URL = "http://tinyurl.com/api-create.php"

    def shorten(self, url_long):
        url = self.URL + "?" + urlencode({"url": url_long})
        res = requests.get(url)
        return res.text

tiny_url_service = TinyurlService()