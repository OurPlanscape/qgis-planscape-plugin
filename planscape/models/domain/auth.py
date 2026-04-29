from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class AuthErrorDetails:
    detail: str = ""
    field_errors: dict[str, List[str]] = field(default_factory=dict)

    def formatted_message(self) -> str:
        messages: List[str] = []
        if self.detail:
            messages.append(self.detail)
        for field_name, errors in self.field_errors.items():
            messages.extend(f"{field_name}: {error}" for error in errors)
        return "\n".join(messages) or "Planscape sign-in failed."
