from google import genai
from config.settings import Settings
from prompts.prompt_templates import TESTCASE_PROMPT


class TestCaseAgent:

    def __init__(self):
        self.client = genai.Client(api_key=Settings.GEMINI_API_KEY)

    def generate(self, context):

        prompt = TESTCASE_PROMPT.format(context=context)

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return response.text