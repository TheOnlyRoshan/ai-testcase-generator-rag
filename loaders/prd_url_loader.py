import requests
from bs4 import BeautifulSoup

class PRDUrlLoader:

    def load(self, url):

        response = requests.get(url)

        soup = BeautifulSoup(response.text, "html.parser")

        text = soup.get_text(separator="\n")

        return text