# Frozen Theorem Ledger

## Status and authority

This file is the compact engineering interface to the frozen mathematical work. The full source ledger remains in:

`../aaa/Transition Phase A：Frozen Theorem Ledger and Final Novelty Audit.md`

Phase C.2b may consume these results but must not silently strengthen them.

## Setting

Let `R_r` contain the empty set and compact regular-closed planar regions whose boundary is a compact embedded `C^{1,1}` one-manifold without boundary and has reach at least `r > 0`. Multiple components, holes, and nesting are permitted.

For `A, B in R_r`, define the geometric discrepancy by the symmetric-difference area

`Delta(A,B) = |A triangle B|`.

The certified topology quantities are the planar Betti numbers `beta_0` and `beta_1`.

## Frozen constants

```text
s* = 4 - 2 sqrt(3)

Phi(s) = 2 pi - 2 arccos(s/2) + (s/2) sqrt(4-s^2)

Lambda* = Phi(s*)

Lambda_maj = (3/2) Lambda* - pi/2

epsilon_VI = 3 (s*)^4 / 2^20

Lambda_VI = 4.7298374690403929848538049521...
```

## Accepted results

1. Each connected component `C` has a nonempty compact connected core `K_C` with `C = K_C + closed_ball(r)`.
2. Distinct connected components are separated by at least `2r`.
3. A discrepancy in `beta_0` admits an open radius-`r` witness contained in the symmetric difference.
4. Complement duality exchanges the planar `beta_0` and `beta_1` defect types while preserving symmetric-difference area.
5. The exact one-error constants are `c_0* = c_1* = pi`.
6. Grade-0 certificate:

   `Delta(A,B) < pi r^2` implies `beta_0(A)=beta_0(B)` and `beta_1(A)=beta_1(B)`.

7. Rounded-Y gives a `3 versus 1` component counterexample with area `(8 sqrt(3) - 2 pi) r^2` and witness-center diameter below `2r`. Independent witness-ball packing is therefore invalid.
8. Interaction clusters and a degree-three reduction replace independent-ball counting in the defect-two analysis.
9. The three-witness majority-overlap argument yields `Lambda_maj`.
10. Phase VI supplies the strict positive gap `epsilon_VI` and the global bound

    `F_r(2) >= Lambda_VI r^2`.

11. The known upper bound remains `F_r(2) <= 2 pi r^2`.
12. Grade-1 certificate:

    `Delta(A,B) < Lambda_VI r^2` implies

    `|beta_0(A)-beta_0(B)| <= 1` and `|beta_1(A)-beta_1(B)| <= 1`.

13. The Grade-1 statement bounds each Betti discrepancy separately; it does not bound their sum by one.
14. The pure `3-to-1` penetration-cap theorem, symmetric-family exclusion, and the `beta_1` defect-two dual statement are accepted only in the scope recorded by the full ledger.

## Open problems

- The exact value of `F_r(2)`.
- Whether `F_r(2) = 2 pi r^2`.
- General `F_r(m)`.
- Exact connector surcharge and exact finite-dimensional `Lambda_3`.
- A theorem guaranteeing full homeomorphism or ambient isotopy from the present area thresholds.
- An unconditional bridge from raw digital-mask topology to the certified continuous region.

## Prohibited claims

- Do not claim full topology, homeomorphism, or isotopy from Grade-0 or Grade-1.
- Do not claim `F_r(2) = 2 pi r^2`.
- Do not use independent witness-ball packing after Rounded-Y.
- Do not claim that Grade-1 bounds the sum of Betti errors by one.
- Do not apply the theorem directly to raw pixels without a separately defined and certified continuous regularization.
- Do not present the base one-error theorem alone as a major novelty claim. The stronger novelty lies in the defect-two chain and its use in a visual certification method.
