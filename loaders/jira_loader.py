import requests

class JiraLoader:

    def load(self, jira_url):

        response = requests.get(jira_url)

        return response.text