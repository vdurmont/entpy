from entpy.framework.descriptor import Descriptor


class Pattern(Descriptor):
    def get_example_subclass_name(self) -> str | None:
        """Return the name of a concrete implementation of this pattern to be
        used in the example generation. If `None`, EntPy will randomly select
        one of the available concrete implementations.

        Use the class name. For example, for `EntTestSchema`, return `EntTest`."""
        return None

    def is_queryable(self) -> bool:
        """Whether this pattern can be queried across its implementations.

        A queryable pattern gets a database view unioning every implementing
        table, and an `I<Name>.query()` returning an `EntPatternQuery` over it.
        That view has to be rebuilt whenever an implementation is added or its
        columns change, which is a real cost for a pattern nobody queries
        polymorphically.

        Return `False` to skip both. The pattern still contributes its fields,
        privacy rules and mutator surface to its implementations; only the
        cross-implementation query goes away, so callers reach the ents through
        the concrete schemas instead."""
        return True
