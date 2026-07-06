from app.schemas import Fix, Issue

STACK_GENERATORS: dict[str, object] = {}


def _load_generators() -> None:
    if STACK_GENERATORS:
        return

    from app.fixes import nextjs_13, plain_html, react_spa

    STACK_GENERATORS["nextjs-13"] = nextjs_13.generate_nextjs_13_fix
    STACK_GENERATORS["react-spa"] = react_spa.generate_react_spa_fix
    STACK_GENERATORS["plain-html"] = plain_html.generate_plain_html_fix


def generate_fixes(issues: list[Issue], target_stack: str) -> list[Fix]:
    _load_generators()
    generator = STACK_GENERATORS.get(target_stack)
    if generator is None:
        return []

    fixes: list[Fix] = []
    for issue in issues:
        fix = generator(issue.id)  # type: ignore[operator]
        if fix is not None:
            fixes.append(fix)
    return fixes
