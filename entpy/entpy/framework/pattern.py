from entpy.framework.descriptor import Descriptor


class Pattern(Descriptor):
    def get_example_subclass_name(self) -> str | None:
        """Return the name of a concrete implementation of this pattern to be
        used in the example generation. If `None`, EntPy will randomly select
        one of the available concrete implementations.

        Use the class name. For example, for `EntTestSchema`, return `EntTest`."""
        return None
