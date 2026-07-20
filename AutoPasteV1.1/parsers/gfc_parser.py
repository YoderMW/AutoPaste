from parsers.frac_to_dec import fraction_to_decimal


def parse_gfc(raw_text: str) -> tuple[str, str | None, str | None]:
    output_lines = []

    for line_number, line in enumerate(raw_text.splitlines(), start=1):
        parts = line.strip().split()

        if not parts:
            continue

        # ERROR CHECK #1: first two values must be digits
        if len(parts) < 2 or not parts[0].isdigit() or not parts[1].isdigit():
            return (
                "error",
                None,
                f"Line {line_number}: First two values must be numeric (ref_id and quantity)"
            )

        ref_id = parts[0]
        qty = parts[1]




        # --------------------------
        # Extract HEIGHT
        # --------------------------
        height_tokens = []
        i = 2
        while i < len(parts) and parts[i].upper() != "X":
            height_tokens.append(parts[i])
            i += 1

        if not height_tokens:
            return (
                "error",
                None,
                f"Line {line_number}: Missing height value"
            )

        height_str = " ".join(height_tokens)

        # Find "X"
        if i >= len(parts) or parts[i].upper() != "X":
            return (
                "error",
                None,
                f"Line {line_number}: Missing 'X' separator"
            )

        i += 1  # Skip "X"

        # --------------------------
        # Extract WIDTH
        # --------------------------
        if i >= len(parts):
            return (
                "error",
                None,
                f"Line {line_number}: Missing width value"
            )

        width_tokens = []
        width_tokens.append(parts[i])
        i += 1

        # Optional fractional part
        if i < len(parts) and "/" in parts[i]:
            width_tokens.append(parts[i])
            i += 1

        width_str = " ".join(width_tokens)

        # --------------------------
        # Convert height and width
        # --------------------------
        try:
            height_out = fraction_to_decimal(height_str)
            width_out = fraction_to_decimal(width_str)
        except ValueError:
            return (
                "error",
                None,
                f"Line {line_number}: Invalid fraction format"
            )

        # Build output line
        output_lines.append(
            f"{qty}\t{height_out}\t{width_out}\t{ref_id}"
        )

    # No errors → success
    return "success", "\n".join(output_lines), None
