#!/usr/bin/env python3

from gencode.ent_generator import run

if __name__ == "__main__":
    run(
        schemas_directory="./examples",
        output_directory="./examples/generated",
        base_import="from examples.database import Base",
    )
