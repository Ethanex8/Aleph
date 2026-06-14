# Axiom of Extensionality

The Axiom of Extensionality is a foundational concept in set theory, asserting that two sets are
equal if and only if they have the exact same elements.

```fol
axiom Extensionality:
    ∀x ∀y (∀z (z ∈ x ⟺ z ∈ y) ⟹ x = y)
```

## Non-Membership

We formally define the non-membership relation, denoted by $x \\notin y$, which holds if and only if
$x$ is not an element of $y$.

```fol
definition x ∉ y:
    ¬(x ∈ y)
```

## Inequality

We formally define the inequality relation, denoted by $x \\neq y$, which holds if and only if $x$
and $y$ are not equal.

```fol
definition x ≠ y:
    ¬(x = y)
```
