"""OneRead: a compiler for technical English.

Parse technical prose, type-check it against ASD-STE100 Issue 9 mechanical
rules, lower it to OneRead IR (ORIR), and emit it to the surfaces a team
already ships.

This package is unofficial. It is not affiliated with ASD or STEMG. No tool
can guarantee ASD-STE100 compliance. See NOTICE.
"""

from .lint import lint, format_report, LIMITS
from .ir import to_ir
from .compile import compile_text
from .emit import emit

__version__ = "1.0.0"
__all__ = ["lint", "format_report", "LIMITS", "to_ir", "compile_text", "emit"]
