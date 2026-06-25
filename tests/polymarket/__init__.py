"""Polymarket engine tests.

`unittest discover -s tests` imports this directory as the top-level
``polymarket`` package. Include the production package directory in this
package's search path so the mandated test layout does not shadow the code it
tests.
"""

from pathlib import Path

_PRODUCTION_PACKAGE = Path(__file__).resolve().parents[2] / "polymarket"
__path__.append(str(_PRODUCTION_PACKAGE))
