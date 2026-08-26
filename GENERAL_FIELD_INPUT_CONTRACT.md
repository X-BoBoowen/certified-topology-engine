# Exact General-Field Input Contract

The reference implementation uses a finite exact rational tensor-product rectangular cell complex. Every cell carries a rational bivariate polynomial. The validator checks the entire grid is present, all breakpoints are exact and strictly ordered, all polynomial coefficients are exact, and value/gradient/Hessian restrictions agree identically on every shared edge.

The outer-domain zero-free certificate is an exact one-dimensional certificate: each cell polynomial is restricted to each outer boundary segment and a rational Sturm sequence proves that no real zero lies in the closed segment. Endpoint zeros are rejected explicitly. No boundary samples are used.
