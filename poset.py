## This is a placeholder file
## RD is currently developing code which will handle posets
##    (partially-ordered sets)

## Currently, the plan is to develop a class (in the Pythonic
##     sense of an object type) which includes a set of sets.
## Said object type will implement various things, such as:
##     standard set operations (subset, intersect, difference)
##     intersective closure (see below)
##     intersective closure with complementation
##     tools to shift representations (poset <-> matrix <-> DAG)
##     a parent-daughter function (see below)

## The intersective closure of a set-of-sets is defined as follows:
## Let SIGMA be the segmental alphabet, and CLASSES be a subset of
##     the powerset of SIGMA, i.e. a set of sets of segments.
## The intersective closure of CLASSES is defined recursively:
##     if class[i] is in CLASSES, it is in the intersective closure
##     if class[i] and class[j] are in the intersective closure,
##         then their intersection is in the intersective closure

## There is a deep equivalence between square matrices and
##     directed graphs. For example, when A[i,j] indicates
##     the number of paths (or cost of traveling) from j to i,
##     then (A^n)[i,j] indicates the number of paths (or cost)
##     from j to i of exactly n steps.
## Posets have properties that make for relatively efficient
##     computation. In particular, the intersective closure
##     could in principle be an O(2^n) computation. But
##     if y is a subset of x, then intersect(x,y)=y. Thus,
##     the algorithm for intersective closure need only
##     consider pairs of sets that are not in a subset-superset
##     relationship. This can be done using a modified version
##     of the shortest-path algorithm.
## Intersective closure with complementation is defined as follows.
##     Set x is a parent of y if y is a subset of x, and there is
##     no other z in CLASSES such that y is a subset of z, and
##     z is a subset of x.
##     If x is in CLASSES, then x is in the intersective closure
##     with complementation.
##     If x and y are in the intersective closure with complementation,
##     then so is their intersection.
##     Furthermore, if x is a parent of y, then x\y (the complement
##     of y with respect to x) is in the intersective closure with
##     complementation.
##     Note that this does not imply that every complement of x,
##     SIGMA\x, will be in the intersective closure. For example,
##     suppose that SIGMA is a parent to CORONALS, and CORONALS
##     is a parent to STRIDENTS. Then CORONAL\STRIDENTS (non-
##     strident coronals) will be in the intersective closure with
##     complementation, but SIGMA\STRIDENTS (non-stridents) need
##     not be.

## Finally, I plan to implement code which will represent the natural
##     class lattice as a DAG in the DOT language, which can be
##     rendered using GraphViz
