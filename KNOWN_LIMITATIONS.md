# Known Limitations

This system remains **proposal-assisted**. A caller must supply an exact disjoint
analytic circle-link proposal and exact cellwise multipliers. Candidate-free calls
return `UNKNOWN`; the package does not discover loops from a field.

- The `VALID` path is restricted to fields whose exact zero set is certified equal
  to the supplied circle-link proposal.
- There is no field-only loop discovery or automatic owner/guard atlas for
  arbitrary loops.
- There is no certified BVH, complete XOR-area engine, conformal calibration, or
  model-training component.
- Raw pixel masks and medical images are not certified inputs, and no real-image
  evaluation is included.
- The result certifies only the frozen Grade-0/Grade-1 Betti bounds; it does not
  establish full topology, homeomorphism, or ambient isotopy.
