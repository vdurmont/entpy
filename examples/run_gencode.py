#!/usr/bin/env python3

from entpy.gencode.generator import ImportedObject, run

if __name__ == "__main__":
    run(
        schemas_directory=".",
        output_directory="./generated",
        base_model_import="from database import Base",
        session_getter=ImportedObject(module="database", name="get_session"),
        vc=ImportedObject(module="evc", name="ExampleViewerContext"),
    )
