from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:

    pragma_version: Optional[int] = 8
