from urllib.parse import quote_plus

class DeepLinkService():
    FIREBASE_URL = "https://worknetwork.page.link/?link={}&apn=com.wurknet.mobile&ibi=com.wurknet.ios"
    
    def make_firebase_deep_link(self, url):
        encoded_url = quote_plus(url)
        deep_link = self.FIREBASE_URL.format(encoded_url)
        return deep_link


deep_link_service = DeepLinkService()
