"""Phase C.2a proposal-assisted exact general-field reference engine."""
from .exact_types import ExactInputError, parse_rational, require_fraction
from .polynomial import Polynomial2D
from .field import PiecewisePolynomialField2D, FieldStatus, FieldValidation
from .circle_proposal import CircleSpec, CircleProposal
from .exact_serialization import (
    ExactSerializationError,
    deserialize_exact_input,
    serialize_exact_input,
)
from .engine import GeneralReachEngine, EngineStatus, EngineResult
from .version import PACKAGE_VERSION as __version__

__all__ = [
    "ExactInputError", "parse_rational", "require_fraction",
    "Polynomial2D", "PiecewisePolynomialField2D", "FieldStatus", "FieldValidation",
    "CircleSpec", "CircleProposal", "GeneralReachEngine", "EngineStatus", "EngineResult",
    "ExactSerializationError", "deserialize_exact_input", "serialize_exact_input",
    "__version__",
]
