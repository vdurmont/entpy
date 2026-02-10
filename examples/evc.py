from entpy import ViewerContext


class ExampleViewerContext(ViewerContext):
    def __repr__(self) -> str:
        return self.__class__.__name__


class ExampleTestViewerContext(ExampleViewerContext):
    pass


class ExampleOmniscientViewerContext(ExampleViewerContext):
    pass
