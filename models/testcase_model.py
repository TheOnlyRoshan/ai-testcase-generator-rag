from dataclasses import dataclass

@dataclass
class TestCase:

    id: str
    scenario: str
    steps: str
    expected_result: str