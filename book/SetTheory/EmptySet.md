# Axiom of the Empty Set

This axiom posits the existence of a set containing no elements. We also establish its uniqueness
using the Axiom of Extensionality.

## Empty Set

The Axiom of the Empty Set asserts the existence of a set with no elements.

```fol
axiom EmptySetExistence:
    ∃x ∀y (y ∉ x)
```

## Uniqueness of the Empty Set

Any two sets that contain no elements are equal. We can prove this by contradiction. Suppose we have
two arbitrary empty sets, $A$ and $B$. If they are not equal, then they must not have the same
elements. That means there exists some element $z$ that is in one but not the other. But since they
are both empty, neither can contain $z$. This allows us to establish the biconditional $z \\in A
\\iff z \\in B$ vacuously, and by the Axiom of Extensionality, $A = B$.

```fol
theorem EmptySetUniqueness:
    ∀A ∀B ((∀x (x ∉ A) ∧ ∀y (y ∉ B)) ⟹ A = B)
proof:
    1. Let A, B be arbitrary [Hypothesis]
        2. Assume (∀x (x ∉ A) ∧ ∀y (y ∉ B)) [Hypothesis]
            3. ∀x (x ∉ A) [AndElim 2, Left]
            4. ∀y (y ∉ B) [AndElim 2, Right]
            5. Let z be arbitrary [Hypothesis]
                6. z ∉ A [UI 3, z]
                7. ¬(z ∈ A) [Def ∉, 6]
                8. z ∈ A ⟹ z ∈ B [Vacuous 7]
                9. z ∉ B [UI 4, z]
                10. ¬(z ∈ B) [Def ∉, 9]
                11. z ∈ B ⟹ z ∈ A [Vacuous 10]
                12. z ∈ A ⟺ z ∈ B [IffIntro 8, 11]
            13. ∀z (z ∈ A ⟺ z ∈ B) [UG 12, z]
            14. A = B [Axiom Extensionality, A, B, 13]
        15. (∀x (x ∉ A) ∧ ∀y (y ∉ B)) ⟹ A = B [ImplIntro 2, 14]
    16. ∀A ∀B ((∀x (x ∉ A) ∧ ∀y (y ∉ B)) ⟹ A = B) [UG 15, A, B]
qed
```

## The Empty Set Symbol

Now that we have proven that an empty set exists and that it is unique, we can formally introduce a
symbol for it: $\emptyset$.

```fol
symbol ∅:
    ∀x (x ∉ ∅)
existence: EmptySetExistence
uniqueness: EmptySetUniqueness
```

## Empty Set is a Subset of Every Set

**Theorem.** The empty set $\\emptyset$ is a subset of every set $B$.

This relies on the principle of vacuous truth. Since $\\emptyset$ has no elements, the statement "if
$z \\in \\emptyset$ then $z \\in B$" is true for any $B$ and any $z$, because the antecedent $z \\in
\\emptyset$ is always false. We use the `Vacuous` inference rule to establish this implication
directly from the definition of the empty set.

```fol
theorem EmptySetSubset:
    ∀B (∅ ⊆ B)
proof:
    1. Let B be arbitrary [Hypothesis]
        2. Let z be arbitrary [Hypothesis]
            3. z ∉ ∅ [Symbol ∅, z]
            4. ¬(z ∈ ∅) [Def ∉, 3]
            5. z ∈ ∅ ⟹ z ∈ B [Vacuous 4]
        6. ∀z (z ∈ ∅ ⟹ z ∈ B) [UG 5, z]
        7. ∅ ⊆ B [Def ⊆, 6]
    8. ∀B (∅ ⊆ B) [UG 7, B]
qed
```
