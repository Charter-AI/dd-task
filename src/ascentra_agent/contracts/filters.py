"""Boolean expression AST for filter definitions (minimal, happy-path)."""
from __future__ import annotations
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field


# Predicates (leaf nodes)


class PredicateEq(BaseModel):
    kind: Literal["eq"] = "eq"
    question_id: str
    value: str | int


class PredicateIn(BaseModel):
    kind: Literal["in"] = "in"
    question_id: str
    values: list[str | int]


class PredicateRange(BaseModel):
    kind: Literal["range"] = "range"
    question_id: str
    min: float | int
    max: float | int
    inclusive: bool = True


class PredicateContainsAny(BaseModel):
    kind: Literal["contains_any"] = "contains_any"
    question_id: str
    values: list[str | int]


class PredicateGt(BaseModel):
    kind: Literal["gt"] = "gt"
    question_id: str
    value: float | int


class PredicateGte(BaseModel):
    kind: Literal["gte"] = "gte"
    question_id: str
    value: float | int


class PredicateLt(BaseModel):
    kind: Literal["lt"] = "lt"
    question_id: str
    value: float | int


class PredicateLte(BaseModel):
    kind: Literal["lte"] = "lte"
    question_id: str
    value: float | int


Predicate = Union[
    PredicateEq,
    PredicateIn,
    PredicateRange,
    PredicateContainsAny,
    PredicateGt,
    PredicateGte,
    PredicateLt,
    PredicateLte,
]


# Logical operators (composite nodes)


class And(BaseModel):
    kind: Literal["and"] = "and"
    children: list[FilterExpr]


class Or(BaseModel):
    kind: Literal["or"] = "or"
    children: list[FilterExpr]


class Not(BaseModel):
    kind: Literal["not"] = "not"
    child: FilterExpr


FilterExpr = Annotated[
    Union[
        PredicateEq,
        PredicateIn,
        PredicateRange,
        PredicateContainsAny,
        PredicateGt,
        PredicateGte,
        PredicateLt,
        PredicateLte,
        And,
        Or,
        Not,
    ],
    Field(discriminator="kind"),
]


And.model_rebuild()
Or.model_rebuild()
Not.model_rebuild()


