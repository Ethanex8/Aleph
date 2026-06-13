# Subset

The subset relation is a foundational concept in set theory. A set $A$ is a
**subset** of $B$ — written $A ⊆ B$ — if every element of $A$ is also
an element of $B$.

## Definition

```fol
definition A ⊆ B:
    ∀x (x ∈ A ⟹ x ∈ B)
```

## Reflexivity of Subset

**Theorem.** Every set is a subset of itself: $A \subseteq A$.

To prove this, we just need to apply the definition of a subset. For any arbitrary set $A$, we must show that any element $x \in A$ implies $x \in A$. This is trivially true, and generalizing this over all $x$ gives us $A \subseteq A$.

```fol
theorem SubsetReflexivity:
    ∀A (A ⊆ A)
proof:
    1. Let A be arbitrary [Hypothesis]
        2. Let x be arbitrary [Hypothesis]
            3. Assume x ∈ A [Hypothesis]
            4. x ∈ A ⟹ x ∈ A [ImplIntro 3, 3]
        5. ∀x (x ∈ A ⟹ x ∈ A) [UG 4, x]
        6. A ⊆ A [Def ⊆, 5]
    7. ∀A (A ⊆ A) [UG 6, A]
qed
```

## Transitivity of Subset

**Theorem.** If $A ⊆ B$ and $B ⊆ C$, then $A ⊆ C$.

The proof proceeds by assuming both inclusions, then introducing an arbitrary
element $w$ and tracing it from $A$ through $B$ into $C$ using the definition
of subset and two applications of Modus Ponens.

```fol
theorem SubsetTransitivity:
    ∀A ∀B ∀C ((A ⊆ B ∧ B ⊆ C) ⟹ A ⊆ C)
proof:
    1. Let A, B, C be arbitrary [Hypothesis]
        2. Assume (A ⊆ B ∧ B ⊆ C) [Hypothesis]
            3. A ⊆ B [AndElim 2, Left]
            4. B ⊆ C [AndElim 2, Right]
            5. ∀x (x ∈ A ⟹ x ∈ B) [Def ⊆, 3]
            6. ∀x (x ∈ B ⟹ x ∈ C) [Def ⊆, 4]
            7. Let w be arbitrary [Hypothesis]
                8. Assume w ∈ A [Hypothesis]
                    9. w ∈ A ⟹ w ∈ B [UI 5, w]
                    10. w ∈ B [MP 9, 8]
                    11. w ∈ B ⟹ w ∈ C [UI 6, w]
                    12. w ∈ C [MP 11, 10]
                13. w ∈ A ⟹ w ∈ C [ImplIntro 8, 12]
            14. ∀w (w ∈ A ⟹ w ∈ C) [UG 13, w]
            15. A ⊆ C [Def ⊆, 14]
        16. (A ⊆ B ∧ B ⊆ C) ⟹ A ⊆ C [ImplIntro 2, 15]
    17. ∀A ∀B ∀C ((A ⊆ B ∧ B ⊆ C) ⟹ A ⊆ C) [UG 16, A, B, C]
qed
```

## Antisymmetry of Subset

**Theorem.** Two sets are equal if and only if they are subsets of each other. In this theorem we establish the forward direction (SubsetAntisymmetry): if $A \subseteq B$ and $B \subseteq A$, then $A = B$.

```fol
theorem SubsetAntisymmetry:
    ∀A ∀B ((A ⊆ B ∧ B ⊆ A) ⟹ A = B)
proof:
    1. Let A, B be arbitrary [Hypothesis]
        2. Assume (A ⊆ B ∧ B ⊆ A) [Hypothesis]
            3. A ⊆ B [AndElim 2, Left]
            4. B ⊆ A [AndElim 2, Right]
            5. ∀x (x ∈ A ⟹ x ∈ B) [Def ⊆, 3]
            6. ∀x (x ∈ B ⟹ x ∈ A) [Def ⊆, 4]
            7. Let z be arbitrary [Hypothesis]
                8. z ∈ A ⟹ z ∈ B [UI 5, z]
                9. z ∈ B ⟹ z ∈ A [UI 6, z]
                10. (z ∈ A ⟺ z ∈ B) [IffIntro 8, 9]
            11. ∀z (z ∈ A ⟺ z ∈ B) [UG 10, z]
            12. A = B [Axiom Extensionality, A, B, 11]
        13. ((A ⊆ B ∧ B ⊆ A) ⟹ A = B) [ImplIntro 2, 12]
    14. ∀A ∀B ((A ⊆ B ∧ B ⊆ A) ⟹ A = B) [UG 13, A, B]
qed
```

## Equality Implies Subset

**Theorem.** If $A = B$, then $A$ is a subset of $B$ and $B$ is a subset of $A$.

This proof leverages the reflexivity of the subset relation. Since $A \subseteq A$ for any set $A$, if $A = B$, we can simply replace occurrences of $A$ with $B$ to show that $A \subseteq B$ and $B \subseteq A$.

```fol
theorem EqualityImpliesSubsets:
    ∀A ∀B (A = B ⟹ (A ⊆ B ∧ B ⊆ A))
proof:
    1. Let A, B be arbitrary [Hypothesis]
        2. Assume A = B [Hypothesis]
            3. A ⊆ A [Theorem SubsetReflexivity, A]
            4. A ⊆ B [EqReplace 3, 2]
            5. B ⊆ A [EqReplace 3, 2]
            6. (A ⊆ B ∧ B ⊆ A) [AndIntro 4, 5]
        7. (A = B ⟹ (A ⊆ B ∧ B ⊆ A)) [ImplIntro 2, 6]
    8. ∀A ∀B (A = B ⟹ (A ⊆ B ∧ B ⊆ A)) [UG 7, A, B]
qed
```

## Equality Iff Subset

**Theorem.** Two sets are equal if and only if they are subsets of each other.

Combining our results from antisymmetry and equality, we can establish the full biconditional. By citing our previous theorems directly with composite universal instantiation, we arrive at the result concisely.

```fol
theorem EqualityIffSubsets:
    ∀A ∀B (A = B ⟺ (A ⊆ B ∧ B ⊆ A))
proof:
    1. Let A, B be arbitrary [Hypothesis]
        2. (A = B ⟹ (A ⊆ B ∧ B ⊆ A)) [Theorem EqualityImpliesSubsets, A, B]
        3. ((A ⊆ B ∧ B ⊆ A) ⟹ A = B) [Theorem SubsetAntisymmetry, A, B]
        4. (A = B ⟺ (A ⊆ B ∧ B ⊆ A)) [IffIntro 2, 3]
    5. ∀A ∀B (A = B ⟺ (A ⊆ B ∧ B ⊆ A)) [UG 4, A, B]
qed
```
