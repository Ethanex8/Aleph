# Axiom of Pair

The Axiom of Pair states that for any two sets $A$ and $B$, there exists a set $C$ that contains
exactly $A$ and $B$ as its elements.

## Pair Existence

```fol
axiom PairExistence:
    ∀A ∀B ∃C ∀x (x ∈ C ⟺ (x = A ∨ x = B))
```

## Uniqueness

Any two sets that contain exactly $A$ and $B$ are equal by the Axiom of Extensionality.

```fol
theorem PairUniqueness:
    ∀A ∀B ∀C ∀D ((∀x (x ∈ C ⟺ (x = A ∨ x = B)) ∧ ∀x (x ∈ D ⟺ (x = A ∨ x = B))) ⟹ C = D)
proof:
    1. Let A, B, C, D be arbitrary [Hypothesis]
        2. Assume (∀x (x ∈ C ⟺ (x = A ∨ x = B)) ∧ ∀x (x ∈ D ⟺ (x = A ∨ x = B))) [Hypothesis]
            3. ∀x (x ∈ C ⟺ (x = A ∨ x = B)) [AndElim 2, Left]
            4. ∀x (x ∈ D ⟺ (x = A ∨ x = B)) [AndElim 2, Right]
            5. Let z be arbitrary [Hypothesis]
                6. z ∈ C ⟺ (z = A ∨ z = B) [UI 3, z]
                7. z ∈ D ⟺ (z = A ∨ z = B) [UI 4, z]
                8. z ∈ C ⟺ z ∈ D [IffTrans 6, 7]
            9. ∀z (z ∈ C ⟺ z ∈ D) [UG 8, z]
            10. C = D [Axiom Extensionality, C, D, 9]
        11. (∀x (x ∈ C ⟺ (x = A ∨ x = B)) ∧ ∀x (x ∈ D ⟺ (x = A ∨ x = B))) ⟹ C = D [ImplIntro 2, 10]
    12. ∀A ∀B ∀C ∀D ((∀x (x ∈ C ⟺ (x = A ∨ x = B)) ∧ ∀x (x ∈ D ⟺ (x = A ∨ x = B))) ⟹ C = D) [UG 11, A, B, C, D]
qed
```

## The Pair Operation

Now that we have proven existence and uniqueness, we can introduce the pair operation `{A, B}`
directly.

```fol
operation {A, B}:
    ∀x (x ∈ {A, B} ⟺ (x = A ∨ x = B))
existence: PairExistence
uniqueness: PairUniqueness
```

## Pair Commutativity

The pair operation is commutative, meaning that the order of the elements in the pair does not
affect the set itself: ${A, B} = {B, A}$.

```fol
theorem PairCommutativity:
    ∀A ∀B ({A, B} = {B, A})
proof:
    1. Let A, B be arbitrary [Hypothesis]
        2. Let C, D be arbitrary [Hypothesis]
            3. Let z be arbitrary [Hypothesis]
                4. z ∈ {C, D} ⟺ (z = C ∨ z = D) [Operation {,}, C, D, z]
                5. z ∈ {D, C} ⟺ (z = D ∨ z = C) [Operation {,}, D, C, z]
                6. Assume z ∈ {C, D} [Hypothesis]
                    7. z = C ∨ z = D [IffMP 4, 6]
                    8. Assume z = C [Hypothesis]
                        9. z = D ∨ z = C [OrIntro 8, Right]
                    10. z = C ⟹ (z = D ∨ z = C) [ImplIntro 8, 9]
                    11. Assume z = D [Hypothesis]
                        12. z = D ∨ z = C [OrIntro 11, Left]
                    13. z = D ⟹ (z = D ∨ z = C) [ImplIntro 11, 12]
                    14. z = D ∨ z = C [OrElim 7, 10, 13]
                    15. z ∈ {D, C} [IffMP 5, 14]
                16. z ∈ {C, D} ⟹ z ∈ {D, C} [ImplIntro 6, 15]
                17. Assume z ∈ {D, C} [Hypothesis]
                    18. z = D ∨ z = C [IffMP 5, 17]
                    19. Assume z = D [Hypothesis]
                        20. z = C ∨ z = D [OrIntro 19, Right]
                    21. z = D ⟹ (z = C ∨ z = D) [ImplIntro 19, 20]
                    22. Assume z = C [Hypothesis]
                        23. z = C ∨ z = D [OrIntro 22, Left]
                    24. z = C ⟹ (z = C ∨ z = D) [ImplIntro 22, 23]
                    25. z = C ∨ z = D [OrElim 18, 21, 24]
                    26. z ∈ {C, D} [IffMP 4, 25]
                27. z ∈ {D, C} ⟹ z ∈ {C, D} [ImplIntro 17, 26]
                28. z ∈ {C, D} ⟺ z ∈ {D, C} [IffIntro 16, 27]
            29. ∀z (z ∈ {C, D} ⟺ z ∈ {D, C}) [UG 28, z]
            30. {C, D} = {D, C} [Axiom Extensionality, {C, D}, {D, C}, 29]
        31. ∀C ∀D ({C, D} = {D, C}) [UG 30, C, D]
        32. {A, B} = {B, A} [UI 31, A, B]
    33. ∀A ∀B ({A, B} = {B, A}) [UG 32, A, B]
qed
```

## The Singleton Definition

We define the singleton set ${A}$ directly as the pair containing $A$ twice.

```fol
definition {A} = {A, A}
```

## Singleton Member

```fol
theorem SingletonMember:
    ∀A ∀x (x ∈ {A} ⟺ x = A)
proof:
    1. Let A, x be arbitrary [Hypothesis]
        2. {A} = {A, A} [Def {}]
        3. (x ∈ {A, A} ⟺ (x = A ∨ x = A)) [Operation {,}, A, A, x]
        4. Assume x ∈ {A} [Hypothesis]
            5. x ∈ {A, A} [EqReplace 4, 2]
            6. x = A ∨ x = A [IffMP 3, 5]
            7. x = A [OrIdem 6]
        8. (x ∈ {A} ⟹ x = A) [ImplIntro 4, 7]
        9. Assume x = A [Hypothesis]
            10. (x = A ∨ x = A) [OrIntro 9, Left]
            11. x ∈ {A, A} [IffMP 3, 10]
            12. x ∈ {A} [EqReplace 11, 2]
        13. (x = A ⟹ x ∈ {A}) [ImplIntro 9, 12]
        14. (x ∈ {A} ⟺ x = A) [IffIntro 8, 13]
    15. ∀A ∀x (x ∈ {A} ⟺ x = A) [UG 14, A, x]
qed
```
