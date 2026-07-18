"""
schemas.py
Pydantic models defining the exact structure a generated test case must
have. Used to validate the LLM's JSON output -- if the model returns
something malformed or missing a field, this raises immediately instead of
silently passing bad data downstream.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class TestCaseCategory(str, Enum):
    HAPPY_PATH = "happy_path"
    EDGE_CASE = "edge_case"
    NEGATIVE = "negative"


class TestCase(BaseModel):
    title: str
    category: TestCaseCategory
    preconditions: list[str]
    steps: list[str]
    expected_result: str
    source_section: str = Field(description="PRD section this test case is grounded in")


class TestCaseSet(BaseModel):
    feature: str
    test_cases: list[TestCase]