"""
AST Transformer — base class for applying transformations to FOL formulas.

Implements the Visitor/Transformer pattern to abstract away the structural
decomposition of AST nodes, eliminating duplicated boilerplate across the verifier.
"""

from __future__ import annotations

from collections.abc import Callable

from tools.parser.ast_nodes import (
    And,
    Biconditional,
    Equality,
    Exists,
    ForAll,
    FuncApp,
    Implies,
    InfixPredicate,
    InfixTerm,
    Membership,
    Node,
    Not,
    Or,
    Predicate,
    SchemaApp,
    Variable,
)


class FormulaTransformer:
    """
    Base class for transforming AST nodes.

    By default, it traverses the AST recursively and reconstructs nodes only
    if their children have changed. Subclasses should override specific
    ``transform_NodeType`` methods to implement custom transformations.
    """

    def __init__(self, transform_func: Callable[[Node], Node | None] | None = None):
        """
        Initialize the transformer.

        Args:
            transform_func: An optional function that takes a node and returns
                a transformed node or None. If it returns None, the default
                recursive transformation is applied.
        """
        self.transform_func = transform_func

    def transform(self, formula: Node) -> Node:
        """
        Entry point for transforming a formula or term.

        Uses structural pattern matching to dispatch the node to the
        appropriate `transform_NodeType` method.

        Args:
            formula: The AST node (Formula or Term) to transform.

        Returns:
            The transformed AST node.
        """
        if self.transform_func:
            res = self.transform_func(formula)
            if res is not None:
                return res

        match formula:
            case Variable():
                return self.transform_Variable(formula)
            case FuncApp():
                return self.transform_FuncApp(formula)
            case InfixTerm():
                return self.transform_InfixTerm(formula)
            case Predicate():
                return self.transform_Predicate(formula)
            case SchemaApp():
                return self.transform_SchemaApp(formula)
            case Membership():
                return self.transform_Membership(formula)
            case InfixPredicate():
                return self.transform_InfixPredicate(formula)
            case Equality():
                return self.transform_Equality(formula)
            case Not():
                return self.transform_Not(formula)
            case And():
                return self.transform_And(formula)
            case Or():
                return self.transform_Or(formula)
            case Implies():
                return self.transform_Implies(formula)
            case Biconditional():
                return self.transform_Biconditional(formula)
            case ForAll():
                return self.transform_ForAll(formula)
            case Exists():
                return self.transform_Exists(formula)
            case _:
                # Fallback to handle any unexpected or unregistered node types
                return formula

    def transform_Variable(self, node: Variable) -> Node:
        """Transform a Variable term node (leaf node, returns as-is by default)."""
        return node

    def transform_FuncApp(self, node: FuncApp) -> Node:
        """
        Transform a FuncApp term node.

        Recursively transforms all arguments. Reconstructs the node only if
        at least one argument was modified to preserve object identity.
        """
        new_args = tuple(self.transform(arg) for arg in node.args)
        # Avoid allocating a new node if arguments haven't changed
        if new_args == node.args:
            return node
        return FuncApp(name=node.name, args=new_args)  # type: ignore[arg-type]

    def transform_InfixTerm(self, node: InfixTerm) -> Node:
        """Transform an InfixTerm term node, recursively transforming left and right children."""
        new_left = self.transform(node.left)
        new_right = self.transform(node.right)
        # Reconstruct only if children have changed
        if new_left == node.left and new_right == node.right:
            return node
        return InfixTerm(left=new_left, operator=node.operator, right=new_right)  # type: ignore[arg-type]

    def transform_Predicate(self, node: Predicate) -> Node:
        """Transform a Predicate formula node, recursively transforming all arguments."""
        new_args = tuple(self.transform(arg) for arg in node.args)
        if new_args == node.args:
            return node
        return Predicate(name=node.name, args=new_args)  # type: ignore[arg-type]

    def transform_SchemaApp(self, node: SchemaApp) -> Node:
        """Transform a SchemaApp formula node, recursively transforming all arguments."""
        new_args = tuple(self.transform(arg) for arg in node.args)
        if new_args == node.args:
            return node
        return SchemaApp(name=node.name, args=new_args)  # type: ignore[arg-type]

    def transform_Membership(self, node: Membership) -> Node:
        """Transform a Membership formula node, recursively transforming element and set terms."""
        new_element = self.transform(node.element)
        new_set = self.transform(node.set_)
        if new_element == node.element and new_set == node.set_:
            return node
        return Membership(element=new_element, set_=new_set)  # type: ignore[arg-type]

    def transform_InfixPredicate(self, node: InfixPredicate) -> Node:
        """Transform an InfixPredicate formula node, recursively transforming left and right terms."""
        new_left = self.transform(node.left)
        new_right = self.transform(node.right)
        if new_left == node.left and new_right == node.right:
            return node
        return InfixPredicate(left=new_left, operator=node.operator, right=new_right)  # type: ignore[arg-type]

    def transform_Equality(self, node: Equality) -> Node:
        """Transform an Equality formula node, recursively transforming left and right terms."""
        new_left = self.transform(node.left)
        new_right = self.transform(node.right)
        if new_left == node.left and new_right == node.right:
            return node
        return Equality(left=new_left, right=new_right)  # type: ignore[arg-type]

    def transform_Not(self, node: Not) -> Node:
        """Transform a Not negation formula node, recursively transforming the operand."""
        new_operand = self.transform(node.operand)
        if new_operand == node.operand:
            return node
        return Not(operand=new_operand)  # type: ignore[arg-type]

    def transform_And(self, node: And) -> Node:
        """Transform an And conjunction formula node, recursively transforming left and right conjuncts."""
        new_left = self.transform(node.left)
        new_right = self.transform(node.right)
        if new_left == node.left and new_right == node.right:
            return node
        return And(left=new_left, right=new_right)  # type: ignore[arg-type]

    def transform_Or(self, node: Or) -> Node:
        """Transform an Or disjunction formula node, recursively transforming left and right disjuncts."""
        new_left = self.transform(node.left)
        new_right = self.transform(node.right)
        if new_left == node.left and new_right == node.right:
            return node
        return Or(left=new_left, right=new_right)  # type: ignore[arg-type]

    def transform_Implies(self, node: Implies) -> Node:
        """Transform an Implies implication formula node, recursively transforming antecedent and consequent."""
        new_antecedent = self.transform(node.antecedent)
        new_consequent = self.transform(node.consequent)
        if new_antecedent == node.antecedent and new_consequent == node.consequent:
            return node
        return Implies(antecedent=new_antecedent, consequent=new_consequent)  # type: ignore[arg-type]

    def transform_Biconditional(self, node: Biconditional) -> Node:
        """Transform a Biconditional formula node, recursively transforming left and right formulas."""
        new_left = self.transform(node.left)
        new_right = self.transform(node.right)
        if new_left == node.left and new_right == node.right:
            return node
        return Biconditional(left=new_left, right=new_right)  # type: ignore[arg-type]

    def transform_ForAll(self, node: ForAll) -> Node:
        """Transform a ForAll universal quantifier formula node, recursively transforming the body."""
        new_body = self.transform(node.body)
        if new_body == node.body:
            return node
        return ForAll(variable=node.variable, body=new_body)  # type: ignore[arg-type]

    def transform_Exists(self, node: Exists) -> Node:
        """Transform an Exists existential quantifier formula node, recursively transforming the body."""
        new_body = self.transform(node.body)
        if new_body == node.body:
            return node
        return Exists(variable=node.variable, body=new_body)  # type: ignore[arg-type]
