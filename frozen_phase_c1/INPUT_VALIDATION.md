# Input Validation Contract

## Public certificate input

```python
ReachEngine.certify(circles, r0)
```

returns `INPUT_INVALID` unless all conditions below hold before certificate arithmetic begins.

## Numeric conditions

- `r0` is an exact `Fraction` or built-in non-boolean integer;
- `r0 > 0`;
- every circle is an exact `Circle` record;
- `cx`, `cy`, and `radius` are exact `Fraction` or built-in non-boolean integers;
- every radius is strictly positive.

## Nonempty link

The empty list is not certified by this restricted reference engine:

```python
certify([], Fraction(1)) -> INPUT_INVALID
```

## Pairwise embedded/disjoint condition

For circles `i,j`, define exactly:

```text
D2 = (cx_i - cx_j)^2 + (cy_i - cy_j)^2
S2 = (R_i + R_j)^2
Q2 = (R_i - R_j)^2
```

The two circle boundaries are accepted exactly when:

```text
D2 > S2        # externally separated
```

or:

```text
D2 < Q2        # one boundary strictly nested inside the other
```

The following are rejected:

| Relation | Exact condition | Status |
|---|---|---|
| duplicate circle | same center and radius | `INPUT_INVALID` |
| external tangency | `D2 == S2` | `INPUT_INVALID` |
| internal tangency | `D2 == Q2` | `INPUT_INVALID` |
| transverse intersection | `Q2 < D2 < S2` | `INPUT_INVALID` |

Concentric circles of different radii satisfy `D2=0<Q2` and are valid nested link components.

## Why tangency is rejected

The soundness theorem assumes a finite link of pairwise-disjoint embedded circle boundaries. At tangency the union is not such a link, even if the individual circle parameterizations are smooth. The engine therefore rejects tangency explicitly instead of relying on the interval solver to return `UNKNOWN`.

## Validation order

1. validate `r0` type and positivity;
2. validate circle iterable, fields, and radii;
3. validate all unordered circle pairs;
4. construct the atlas;
5. test curvature;
6. enter exact interval pair solving.

No invalid value can reach a predicate capable of returning `VALID`.
