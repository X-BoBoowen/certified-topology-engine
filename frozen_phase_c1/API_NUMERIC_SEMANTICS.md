# Certified API Numeric Semantics

## Principle

No ambiguous approximate number is permitted to influence a predicate that can lead to `VALID`.

The certificate core admits exactly:

1. `fractions.Fraction` with exact built-in type;
2. non-boolean built-in `int`, explicitly converted to `Fraction`.

The implementation deliberately rejects subclasses as well as unrelated `numbers.Rational` implementations, because a subclass or custom numeric type may override arithmetic or comparison semantics.

## Accepted values

```python
Fraction(7, 10)
Fraction(-3, 4)
0
7
-2
```

Coordinates may be negative. `r0` and radii must additionally be strictly positive.

## Rejected values

- Python `float`, including finite values, `NaN`, and infinities;
- `decimal.Decimal`;
- `bool`;
- strings passed directly to `certify()`;
- NumPy scalar integers/floats;
- subclasses of `int` or `Fraction`;
- custom numeric objects.

A rejected public call returns `Status.INPUT_INVALID` before atlas construction and before any interval arithmetic.

## Exact text adapter

Use:

```python
parse_rational("0.7") == Fraction(7, 10)
parse_rational("14/20") == Fraction(7, 10)
```

`parse_rational()` is separate from `certify()` so the caller explicitly chooses decimal-text semantics. The engine never silently chooses between:

- decimal `0.7 = 7/10`;
- the exact binary value represented by the Python float `0.7`.

To intentionally certify against the latter, the caller must explicitly write:

```python
Fraction.from_float(0.7)
```

## Exact threshold

The distance threshold is computed as:

```python
two_r0 = Fraction(2) * r0
threshold2 = two_r0 * two_r0
```

For `r0 = Fraction(7, 10)`:

```python
threshold2 == Fraction(49, 25)
```

The implementation asserts that this value has exact built-in `Fraction` type.

## Exact arithmetic audit

After input validation, the following certificate quantities use `Fraction` interval endpoints throughout:

- curvature-radius comparisons;
- rational patch parameters;
- interval midpoints;
- circle positions;
- circle tangents;
- chord components;
- squared distance enclosure;
- `G1` and `G2` orthogonality enclosures;
- subdivision endpoints;
- the distance-pruning threshold.

The only floating-point value in `ReachResult` is `runtime_seconds`, obtained from the system clock. It is never used by a pruning predicate or status decision.

## Defensive interval boundary

`Interval`, `Interval.point()`, and `as_interval()` repeat exact-type validation. This defense-in-depth prevents a future internal refactor from reintroducing a float through an interval operand.
