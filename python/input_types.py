from __future__ import annotations
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import List

@dataclass_json
@dataclass
class Operation:
    name: str
    duration: int
    deps: List[str]
    job: str

@dataclass_json
@dataclass
class Employee:
    name: str
