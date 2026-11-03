from generated.ent_child import EntChild


async def gen_child_shout(child: EntChild) -> str:
    return child.name.upper()
