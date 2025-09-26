#!/usr/bin/env python3

from gencode.ent_generator import Config, EntGenerator

if __name__ == "__main__":
    generator = EntGenerator(
        config=Config(
            schemas_directory="./examples",
            output_directory="./examples/generated",
            base_import="from examples.database import Base",
        )
    )
    generator.run()
