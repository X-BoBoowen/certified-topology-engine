from __future__ import annotations

from fractions import Fraction

from .circle_proposal import CircleProposal, CircleSpec
from .exact_types import parse_rational
from .field import PiecewisePolynomialField2D
from .polynomial import Polynomial2D


class ExactSerializationError(ValueError):
    pass


def _require_keys(value, keys, name):
    if type(value) is not dict:
        raise ExactSerializationError(f'{name} must be an object')
    if set(value) != set(keys):
        raise ExactSerializationError(f'{name} has unexpected or missing fields')


def _fraction(text, name):
    if type(text) is not str:
        raise ExactSerializationError(f'{name} must be a canonical rational string')
    try:
        value = parse_rational(text)
    except (ValueError, TypeError, ZeroDivisionError) as exc:
        raise ExactSerializationError(f'{name} is not an exact rational') from exc
    if str(value) != text:
        raise ExactSerializationError(f'{name} is not canonically encoded')
    return value


def _polynomial(record, name):
    if type(record) is not list:
        raise ExactSerializationError(f'{name} must be a coefficient list')
    coefficients = {}
    for index, term in enumerate(record):
        if type(term) is not list or len(term) != 3:
            raise ExactSerializationError(f'{name}[{index}] must be [i,j,value]')
        i, j, value = term
        if type(i) is not int or type(j) is not int or i < 0 or j < 0:
            raise ExactSerializationError(f'{name}[{index}] has invalid exponents')
        key = (i, j)
        if key in coefficients:
            raise ExactSerializationError(f'{name} has a duplicate monomial')
        coefficients[key] = _fraction(value, f'{name}[{index}].value')
    polynomial = Polynomial2D(coefficients)
    if polynomial.canonical() != record:
        raise ExactSerializationError(f'{name} is not canonical')
    return polynomial


def _cell_key(text, name):
    if type(text) is not str:
        raise ExactSerializationError(f'{name} must be a canonical cell key')
    parts = text.split(',')
    if len(parts) != 2:
        raise ExactSerializationError(f'{name} must be i,j')
    try:
        i, j = (int(part) for part in parts)
    except ValueError as exc:
        raise ExactSerializationError(f'{name} must be i,j') from exc
    if i < 0 or j < 0 or text != f'{i},{j}':
        raise ExactSerializationError(f'{name} is not canonical')
    return i, j


def _field(record):
    _require_keys(record, ('x_breaks', 'y_breaks', 'pieces', 'label'), 'field')
    if type(record['x_breaks']) is not list or type(record['y_breaks']) is not list:
        raise ExactSerializationError('field breakpoints must be lists')
    if type(record['pieces']) is not dict or type(record['label']) is not str:
        raise ExactSerializationError('field pieces/label have invalid types')
    x_breaks = tuple(
        _fraction(value, f'field.x_breaks[{index}]')
        for index, value in enumerate(record['x_breaks'])
    )
    y_breaks = tuple(
        _fraction(value, f'field.y_breaks[{index}]')
        for index, value in enumerate(record['y_breaks'])
    )
    pieces = {
        _cell_key(key, f'field.pieces[{key!r}]'): _polynomial(
            value, f'field.pieces[{key!r}]'
        )
        for key, value in record['pieces'].items()
    }
    try:
        field = PiecewisePolynomialField2D(
            x_breaks, y_breaks, pieces, record['label']
        )
    except (TypeError, ValueError) as exc:
        raise ExactSerializationError('serialized field is invalid') from exc
    if field.canonical() != record:
        raise ExactSerializationError('serialized field is not canonical')
    return field


def _proposal(record):
    _require_keys(record, ('circles', 'multipliers'), 'proposal')
    if type(record['circles']) is not list or type(record['multipliers']) is not dict:
        raise ExactSerializationError('proposal members have invalid types')
    circles = []
    for index, circle in enumerate(record['circles']):
        if type(circle) is not list or len(circle) != 3:
            raise ExactSerializationError(
                f'proposal.circles[{index}] must contain cx, cy, radius'
            )
        try:
            circles.append(
                CircleSpec(
                    _fraction(circle[0], f'proposal.circles[{index}].cx'),
                    _fraction(circle[1], f'proposal.circles[{index}].cy'),
                    _fraction(circle[2], f'proposal.circles[{index}].radius'),
                )
            )
        except (TypeError, ValueError) as exc:
            raise ExactSerializationError('serialized circle is invalid') from exc
    multipliers = {
        _cell_key(key, f'proposal.multipliers[{key!r}]'): _polynomial(
            value, f'proposal.multipliers[{key!r}]'
        )
        for key, value in record['multipliers'].items()
    }
    try:
        proposal = CircleProposal(tuple(circles), multipliers)
    except (TypeError, ValueError) as exc:
        raise ExactSerializationError('serialized proposal is invalid') from exc
    if proposal.canonical() != record:
        raise ExactSerializationError('serialized proposal is not canonical')
    return proposal


def serialize_exact_input(field, proposal, r0):
    if not isinstance(field, PiecewisePolynomialField2D):
        raise ExactSerializationError('field has invalid type')
    if not isinstance(proposal, CircleProposal):
        raise ExactSerializationError('proposal has invalid type')
    if type(r0) is int and type(r0) is not bool:
        exact_r0 = Fraction(r0)
    elif type(r0) is Fraction:
        exact_r0 = r0
    else:
        raise ExactSerializationError('r0 must be an exact built-in rational')
    return {
        'schema': 'phase-c2b-exact-input-v1',
        'r0': str(exact_r0),
        'field': field.canonical(),
        'proposal': proposal.canonical(),
        'field_hash': field.field_hash(),
        'proposal_hash': proposal.proposal_hash(),
    }


def deserialize_exact_input(record):
    _require_keys(
        record,
        ('schema', 'r0', 'field', 'proposal', 'field_hash', 'proposal_hash'),
        'exact_input',
    )
    if record['schema'] != 'phase-c2b-exact-input-v1':
        raise ExactSerializationError('unsupported exact-input schema')
    r0 = _fraction(record['r0'], 'exact_input.r0')
    field = _field(record['field'])
    proposal = _proposal(record['proposal'])
    if type(record['field_hash']) is not str or field.field_hash() != record['field_hash']:
        raise ExactSerializationError('field hash mismatch')
    if (
        type(record['proposal_hash']) is not str
        or proposal.proposal_hash() != record['proposal_hash']
    ):
        raise ExactSerializationError('proposal hash mismatch')
    if serialize_exact_input(field, proposal, r0) != record:
        raise ExactSerializationError('exact input is not canonical')
    return field, proposal, r0
