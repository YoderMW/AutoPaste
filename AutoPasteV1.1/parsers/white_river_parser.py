def parse_white_river(raw_text: str) -> tuple[str, str, str | None]:
    output_lines = []
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    for line_num, line in enumerate(lines, start=1):
        parts = line.split()

        if "QTY" in parts or "STYLE" in parts:
            continue

        # Count numerical vs non-numerical parts
        numerical_values = []
        has_text = False

        for part in parts:
            try:
                numerical_values.append(float(part))
            except ValueError:
                # Found non-numerical text (should be style like "Drawer" or "Box")
                has_text = True
                continue

        # White River data should have text (style) and exactly 4 numbers
        if not has_text:
            return "error", "", "Wrong data format - expected style text (e.g., 'Drawer Box')"

        if len(numerical_values) != 4:
            return "error", "", f"Line {line_num}: expected 4 numeric values"

        qty_f, width, height, depth = numerical_values

        if not qty_f.is_integer():
            return "error", "", f"Line {line_num}: quantity must be whole"

        quantity = str(int(qty_f))

        def clean(n):
            return str(int(n)) if n.is_integer() else str(n)

        output_lines.append(
            f"{quantity}\t{clean(height)}\t{clean(width)}\t{clean(depth)}"
        )

    if not output_lines:
        return "error", "", "No valid data found"

    return "success", "\n".join(output_lines), None