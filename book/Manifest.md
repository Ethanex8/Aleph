# Aleph Table of Contents

This is the central manifest for the Aleph book. The verifier uses this manifest to understand the structure of the topological module graph, validate imports and exports, and ensure that all files in the book are accounted for.

## [SetTheory.Extensionality](SetTheory/Extensionality.md)

```yaml
sections:
  - name: SetTheory.Extensionality
    imports: []
    exports: [Extensionality, ∉, ≠]
```

## [SetTheory.Subset](SetTheory/Subset.md)

```yaml
sections:
  - name: SetTheory.Subset
    imports: [SetTheory.Extensionality.*]
    exports: [⊆, SubsetReflexivity, SubsetTransitivity, SubsetAntisymmetry, EqualityImpliesSubsets, EqualityIffSubsets]
```

## [SetTheory.EmptySet](SetTheory/EmptySet.md)

```yaml
sections:
  - name: SetTheory.EmptySet
    imports: [SetTheory.Extensionality.*, SetTheory.Subset.⊆]
    exports: [EmptySetExistence, EmptySetUniqueness, ∅, EmptySetSubset]
```

## [SetTheory.Pair](SetTheory/Pair.md)

```yaml
sections:
  - name: SetTheory.Pair
    imports: [SetTheory.Extensionality.Extensionality]
    exports: [PairExistence, PairUniqueness, "{,}", PairCommutativity, "{}", SingletonMember]
```

## [SetTheory.Union](SetTheory/Union.md)

```yaml
sections:
  - name: SetTheory.Union
    imports: [SetTheory.Extensionality.Extensionality, "SetTheory.Pair.{,}"]
    exports: [UnionExistence, UnionUniqueness, Union, BinaryUnionExistence, BinaryUnionUniqueness, ∪, BinaryUnionMember]
```
