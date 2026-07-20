from parsers.frac_to_dec import fraction_to_decimal


def parse_ruffino_box(raw_text: str) -> tuple[str, str | None, str | None]:
    output_lines = []

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    for line_num, line in enumerate(lines, start=1):
        parts = line.split()

        if len(parts) < 5:
            return "error", None, f"Line {line_num}: Not enough values"

        # --------------------------
        # QUANTITY
        # --------------------------
        if not parts[0].isdigit():
            return "error", None, f"Line {line_num}: Quantity must be a whole number"

        qty = parts[0]

        i = 1

        # --------------------------
        # WIDTH (can be integer or fraction)
        # --------------------------
        width_tokens = [parts[i]]
        i += 1

        if i < len(parts) and "/" in parts[i]:
            width_tokens.append(parts[i])
            i += 1

        width_str = " ".join(width_tokens)

        # --------------------------
        # HEIGHT
        # --------------------------
        if i >= len(parts):
            return "error", None, f"Line {line_num}: Missing height"

        height_tokens = [parts[i]]
        i += 1

        if i < len(parts) and "/" in parts[i]:
            height_tokens.append(parts[i])
            i += 1

        height_str = " ".join(height_tokens)

        # --------------------------
        # DEPTH
        # --------------------------
        if i >= len(parts):
            return "error", None, f"Line {line_num}: Missing depth"

        depth_tokens = [parts[i]]
        i += 1

        if i < len(parts) and "/" in parts[i]:
            depth_tokens.append(parts[i])
            i += 1

        depth_str = " ".join(depth_tokens)

        # --------------------------
        # REF ID (everything else)
        # --------------------------
        if i >= len(parts):
            return "error", None, f"Line {line_num}: Missing reference ID"

        ref_id = " ".join(parts[i:])

        # --------------------------
        # CONVERT FRACTIONS
        # --------------------------
        try:
            width_val = fraction_to_decimal(width_str)
            height_val = fraction_to_decimal(height_str)
            depth_val = fraction_to_decimal(depth_str)
        except ValueError:
            return "error", None, f"Line {line_num}: Invalid fraction format"

        # Remove trailing .0 if whole number
        def clean(val):
            return str(int(val)) if float(val).is_integer() else str(val)

        # --------------------------
        # BUILD OUTPUT
        # Order: Quantity, Height, Width, Depth, Ref ID
        # --------------------------
        output_lines.append(
            f"{qty}\t{clean(height_val)}\t{clean(width_val)}\t{clean(depth_val)}\t{ref_id}"
        )

    if not output_lines:
        return "error", None, "No valid data found"

    return "success", "\n".join(output_lines), None