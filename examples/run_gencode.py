#!/usr/bin/env python3

from entpy import Action
from entpy.gencode.generator import ImportedObject, PrivacyRuleImport, run

if __name__ == "__main__":
    run(
        schemas_directory=".",
        output_directory="./generated",
        base_model_import="from database import Base",
        session_getter=ImportedObject(module="database", name="get_session"),
        vc=ImportedObject(module="evc", name="ExampleViewerContext"),
        prepended_rules=[
            PrivacyRuleImport(
                rule=ImportedObject(module="rules", name="AllowIfTestViewerContext"),
                actions=[Action.CREATE, Action.DELETE, Action.READ, Action.UPDATE],
            ),
            PrivacyRuleImport(
                rule=ImportedObject(
                    module="rules", name="AllowIfOmniscientViewerContext"
                ),
                actions=[Action.READ],
            ),
        ],
    )
