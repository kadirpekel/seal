from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:

    strict: Optional[bool] = False
    pragma_version: Optional[int] = 8
