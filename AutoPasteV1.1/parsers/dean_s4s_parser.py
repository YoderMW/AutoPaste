from parsers.frac_to_dec import fraction_to_decimal


def parse_dean_s4s(raw_text: str) -> tuple[str, str | None, str | None]:
    """
    Parse Dean S4S input data format.

    Expected format (per line):
        [qty] [width] x [height]

    Width and height can each be:
        - a whole number (e.g., "90")
        - a whole number + fraction (e.g., "4 1/2")
        - a bare fraction (e.g., "3/8")

    Examples:
        1 4 1/2 x 90
        2 2 x 39
        1 1 1/2 x 66

    Output format:
        [quantity]\t[width]\t[height]
    """
    output_lines = []

    for line_number, line in enumerate(raw_text.splitlines(), start=1):
        parts = line.strip().split()

        if not parts:
            continue

        # --------------------------
        # QUANTITY
        # --------------------------
        if not parts[0].isdigit():
            return (
                "error",
                None,
                f"Line {line_number}: Quantity must be a whole number"
            )

        qty = parts[0]
        i = 1

        # --------------------------
        # WIDTH (up until "x")
        # --------------------------
        width_tokens = []
        while i < len(parts) and parts[i].lower() != "x":
            width_tokens.append(parts[i])
            i += 1

        if not width_tokens:
            return (
                "error",
                None,
                f"Line {line_number}: Missing width value"
            )

        width_str = " ".join(width_tokens)

        # --------------------------
        # Expect "x" separator
        # --------------------------
        if i >= len(parts) or parts[i].lower() != "x":
            return (
                "error",
                None,
                f"Line {line_number}: Missing 'x' separator"
            )

        i += 1  # skip "x"

        # --------------------------
        # HEIGHT (everything after "x")
        # --------------------------
        height_tokens = parts[i:]

        if not height_tokens:
            return (
                "error",
                None,
                f"Line {line_number}: Missing height value"
            )

        height_str = " ".join(height_tokens)

        # --------------------------
        # Convert fractions to decimals
        # --------------------------
        try:
            width_out = fraction_to_decimal(width_str)
            height_out = fraction_to_decimal(height_str)
        except (ValueError, ZeroDivisionError):
            return (
                "error",
                None,
                f"Line {line_number}: Invalid fraction format"
            )

        # --------------------------
        # Build output line
        # --------------------------
        output_lines.append(f"{qty}\t{width_out}\t{height_out}")

    if not output_lines:
        return "error", None, "No valid data found"

    return "success", "\n".join(output_lines), None