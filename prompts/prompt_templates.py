TESTCASE_PROMPT = """
You are a senior QA engineer.

Generate comprehensive manual test cases from the requirement.

Include:
- positive scenarios
- negative scenarios
- edge cases
- boundary tests

Return structured format:

Test Case ID
Scenario
Steps
Expected Result

Requirement:
{context}
"""