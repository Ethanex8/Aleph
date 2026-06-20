# Axiom of Union

The Axiom of Union states that for any set $A$, there exists a set $U$ containing all elements that
belong to at least one element of $A$. This effectively "flattens" a set of sets.

## Union Existence

```fol
axiom UnionExistence:
    ∀A ∃U ∀x (x ∈ U ⟺ ∃y (y ∈ A ∧ x ∈ y))
```

## Uniqueness

Any two union sets for $A$ are equal by the Axiom of Extensionality.

```fol
theorem UnionUniqueness:
    ∀A ∀U ∀V ((∀x (x ∈ U ⟺ ∃y (y ∈ A ∧ x ∈ y)) ∧ ∀x (x ∈ V ⟺ ∃y (y ∈ A ∧ x ∈ y))) ⟹ U = V)
proof:
    1. Let A, U, V be arbitrary [Hypothesis]
        2. Assume (∀x (x ∈ U ⟺ ∃y (y ∈ A ∧ x ∈ y)) ∧ ∀x (x ∈ V ⟺ ∃y (y ∈ A ∧ x ∈ y))) [Hypothesis]
            3. ∀x (x ∈ U ⟺ ∃y (y ∈ A ∧ x ∈ y)) [AndElim 2, Left]
            4. ∀x (x ∈ V ⟺ ∃y (y ∈ A ∧ x ∈ y)) [AndElim 2, Right]
            5. Let z be arbitrary [Hypothesis]
                6. z ∈ U ⟺ ∃y (y ∈ A ∧ z ∈ y) [UI 3, z]
                7. z ∈ V ⟺ ∃y (y ∈ A ∧ z ∈ y) [UI 4, z]
                8. z ∈ U ⟺ z ∈ V [IffTrans 6, 7]
            9. ∀z (z ∈ U ⟺ z ∈ V) [UG 8, z]
            10. U = V [Axiom Extensionality, U, V, 9]
        11. (∀x (x ∈ U ⟺ ∃y (y ∈ A ∧ x ∈ y)) ∧ ∀x (x ∈ V ⟺ ∃y (y ∈ A ∧ x ∈ y))) ⟹ U = V [ImplIntro 2, 10]
    12. ∀A ∀U ∀V ((∀x (x ∈ U ⟺ ∃y (y ∈ A ∧ x ∈ y)) ∧ ∀x (x ∈ V ⟺ ∃y (y ∈ A ∧ x ∈ y))) ⟹ U = V) [UG 11, A, U, V]
qed
```

## The Union Symbol

With existence and uniqueness proven, we define the `Union(A)` symbol.

```fol
symbol Union(A):
    ∀x (x ∈ Union(A) ⟺ ∃y (y ∈ A ∧ x ∈ y))
existence: UnionExistence
uniqueness: UnionUniqueness
```

## Binary Union

We can now define the binary union $A \\cup B$ using the `Union` and `{,}` symbols. With syntactic
sugar `set_enum` (e.g. `{A, B, C}`), the parser automatically converts multi-element sets into
binary unions under the hood: `{A, B} ∪ {C}`.

```fol
theorem BinaryUnionExistence:
    ∀A ∀B ∃C ∀x (x ∈ C ⟺ ∃y (y ∈ {A, B} ∧ x ∈ y))
proof:
    1. Let A, B be arbitrary [Hypothesis]
        2. ∀x (x ∈ Union({A, B}) ⟺ ∃y (y ∈ {A, B} ∧ x ∈ y)) [Symbol Union, {A, B}]
        3. ∃C ∀x (x ∈ C ⟺ ∃y (y ∈ {A, B} ∧ x ∈ y)) [ExistsIntro 2, Union({A, B}), C]
    4. ∀A ∀B ∃C ∀x (x ∈ C ⟺ ∃y (y ∈ {A, B} ∧ x ∈ y)) [UG 3, A, B]
qed

theorem BinaryUnionUniqueness:
    ∀A ∀B ∀C ∀D ((∀x (x ∈ C ⟺ ∃y (y ∈ {A, B} ∧ x ∈ y)) ∧ ∀x (x ∈ D ⟺ ∃y (y ∈ {A, B} ∧ x ∈ y))) ⟹ C = D)
proof:
    1. Let A, B, C, D be arbitrary [Hypothesis]
        2. Assume (∀x (x ∈ C ⟺ ∃y (y ∈ {A, B} ∧ x ∈ y)) ∧ ∀x (x ∈ D ⟺ ∃y (y ∈ {A, B} ∧ x ∈ y))) [Hypothesis]
            3. ∀x (x ∈ C ⟺ ∃y (y ∈ {A, B} ∧ x ∈ y)) [AndElim 2, Left]
            4. ∀x (x ∈ D ⟺ ∃y (y ∈ {A, B} ∧ x ∈ y)) [AndElim 2, Right]
            5. Let z be arbitrary [Hypothesis]
                6. z ∈ C ⟺ ∃y (y ∈ {A, B} ∧ z ∈ y) [UI 3, z]
                7. z ∈ D ⟺ ∃y (y ∈ {A, B} ∧ z ∈ y) [UI 4, z]
                8. z ∈ C ⟺ z ∈ D [IffTrans 6, 7]
            9. ∀z (z ∈ C ⟺ z ∈ D) [UG 8, z]
            10. C = D [Axiom Extensionality, C, D, 9]
        11. (∀x (x ∈ C ⟺ ∃y (y ∈ {A, B} ∧ x ∈ y)) ∧ ∀x (x ∈ D ⟺ ∃y (y ∈ {A, B} ∧ x ∈ y))) ⟹ C = D [ImplIntro 2, 10]
    12. ∀A ∀B ∀C ∀D ((∀x (x ∈ C ⟺ ∃y (y ∈ {A, B} ∧ x ∈ y)) ∧ ∀x (x ∈ D ⟺ ∃y (y ∈ {A, B} ∧ x ∈ y))) ⟹ C = D) [UG 11, A, B, C, D]
qed

symbol A ∪ B:
    ∀x (x ∈ A ∪ B ⟺ ∃y (y ∈ {A, B} ∧ x ∈ y))
existence: BinaryUnionExistence
uniqueness: BinaryUnionUniqueness
```

## Binary Union Member

**Theorem.** An element $x$ is in the binary union $A \\cup B$ if and only if it is in $A$ or it is
in $B$: $x \\in A \\cup B \\iff (x \\in A \\lor x \\in B)$.

```fol
theorem BinaryUnionMember:
    ∀A ∀B ∀x (x ∈ A ∪ B ⟺ (x ∈ A ∨ x ∈ B))
proof:
    1. Let A, B, x be arbitrary [Hypothesis]
        2. Assume x ∈ A ∪ B [Hypothesis]
            3. ∃y (y ∈ {A, B} ∧ x ∈ y) [Def ∪, 2]
            4. Let y be arbitrary [Hypothesis]
                5. Assume (y ∈ {A, B} ∧ x ∈ y) [Hypothesis]
                    6. y ∈ {A, B} [AndElim 5, Left]
                    7. x ∈ y [AndElim 5, Right]
                    8. y = A ∨ y = B [Def {,}, 6]
                    9. Assume y = A [Hypothesis]
                        10. x ∈ A [EqReplace 7, 9]
                        11. x ∈ A ∨ x ∈ B [OrIntro 10, Left]
                    12. Assume y = B [Hypothesis]
                        13. x ∈ B [EqReplace 7, 12]
                        14. x ∈ A ∨ x ∈ B [OrIntro 13, Right]
                    15. x ∈ A ∨ x ∈ B [OrCases 8, 11, 14]
                16. (y ∈ {A, B} ∧ x ∈ y) ⟹ (x ∈ A ∨ x ∈ B) [ImplIntro 5, 15]
            17. x ∈ A ∨ x ∈ B [ExistsElim 3, 16, y]
        18. x ∈ A ∪ B ⟹ (x ∈ A ∨ x ∈ B) [ImplIntro 2, 17]
        19. Assume (x ∈ A ∨ x ∈ B) [Hypothesis]
            20. Assume x ∈ A [Hypothesis]
                21. (A ∈ {A, B} ⟺ (A = A ∨ A = B)) [Def {,}]
                22. A = A [EqIntro]
                23. A = A ∨ A = B [OrIntro 22, Left]
                24. A ∈ {A, B} [IffMP 21, 23]
                25. (A ∈ {A, B} ∧ x ∈ A) [AndIntro 24, 20]
                26. ∃y (y ∈ {A, B} ∧ x ∈ y) [ExistsIntro 25, A, y]
            27. x ∈ A ⟹ ∃y (y ∈ {A, B} ∧ x ∈ y) [ImplIntro 20, 26]
            28. Assume x ∈ B [Hypothesis]
                29. (B ∈ {A, B} ⟺ (B = A ∨ B = B)) [Def {,}]
                30. B = B [EqIntro]
                31. B = A ∨ B = B [OrIntro 30, Right]
                32. B ∈ {A, B} [IffMP 29, 31]
                33. (B ∈ {A, B} ∧ x ∈ B) [AndIntro 32, 28]
                34. ∃y (y ∈ {A, B} ∧ x ∈ y) [ExistsIntro 33, B, y]
            35. x ∈ B ⟹ ∃y (y ∈ {A, B} ∧ x ∈ y) [ImplIntro 28, 34]
            36. ∃y (y ∈ {A, B} ∧ x ∈ y) [OrElim 19, 27, 35]
            37. x ∈ A ∪ B [Def ∪, 36]
        38. (x ∈ A ∨ x ∈ B) ⟹ x ∈ A ∪ B [ImplIntro 19, 37]
        39. (x ∈ A ∪ B ⟺ (x ∈ A ∨ x ∈ B)) [IffIntro 18, 38]
    40. ∀A ∀B ∀x (x ∈ A ∪ B ⟺ (x ∈ A ∨ x ∈ B)) [UG 39, A, B, x]
qed

```
