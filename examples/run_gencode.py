#!/usr/bin/env python3

from entpy.gencode.generator import run

if __name__ == "__main__":
    run(
        schemas_directory=".",
        output_directory="./generated",
        base_import="from database import Base",
        session_getter_import="from database import get_session",
        session_getter_fn_name="get_session",
    )
