"""Phase C.2a proposal-assisted exact general-field reference engine."""
from .exact_types import ExactInputError, parse_rational, require_fraction
from .polynomial import Polynomial2D
from .field import PiecewisePolynomialField2D, FieldStatus, FieldValidation
from .circle_proposal import CircleSpec, CircleProposal
from .engine import GeneralReachEngine, EngineStatus, EngineResult

__all__ = [
    "ExactInputError", "parse_rational", "require_fraction",
    "Polynomial2D", "PiecewisePolynomialField2D", "FieldStatus", "FieldValidation",
    "CircleSpec", "CircleProposal", "GeneralReachEngine", "EngineStatus", "EngineResult",
]
