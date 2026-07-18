"""
judge_schemas.py
Pydantic models for the faithfulness judge's output -- same validate-or-
fail principle as src/schemas.py, applied to the judge's response instead
of the generator's.

Named judge_schemas.py, not schemas.py, deliberately -- this eval script
adds src/ to sys.path, and a same-named file here would silently shadow
or be shadowed by src/schemas.py depending on import order. Caught this
exact collision while verifying the script; distinct names avoid it
entirely rather than relying on import order.
"""

from __future__ import annotations

from pydantic import BaseModel


class ClaimJudgement(BaseModel):
    claim: str
    supported: bool
    reasoning: str


class FaithfulnessJudgement(BaseModel):
    claims: list[ClaimJudgement]

    @property
    def score(self) -> float:
        if not self.claims:
            return 0.0
        return sum(1 for c in self.claims if c.supported) / len(self.claims)