

# -- create blocks, sections lines for terminal output --
def div_blocks(number: int, divider: str = "= ") -> str:
    """Generates a repeating block of characters."""
    count = number if number > 0 else 5
    return (divider * count).strip()



def div_section_line(message: str = "", level: int = 1) -> str:
    """Creates a centered section line with consistent padding."""
    match level:

        # heading 1 style
        case 1:
            blocks = div_blocks(10, "= ")
        case 2:
            blocks = div_blocks(5, "- ")
        case 3:
            blocks = div_blocks(3, "*")
        case _:
            blocks = div_blocks(10, "= ")
    blocks = blocks.strip()
    if not message:
        return blocks
    return f"{blocks} {message.strip()} {blocks}"





def format_section(title: str, data: dict) -> str:
    blocks = div_blocks(3, "*")
    title_line = f"{blocks} {title} {blocks}"
    if not data:
        return title_line + "\n(empty)"

    # stringify keys/values; you can also prettify keys here if you want
    items = [(str(k), data[k]) for k in data.keys()]
    width = max(len(k) for k, _ in items) + 2

    lines = [title_line]
    for k, v in items:
        lines.append(f" {k:<{width}}: {v}")
    lines.append(f"{blocks} End of {title} {blocks}")
    return "\n".join(lines)
