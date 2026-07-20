def parse_schwartz(raw_text: str) -> tuple[str, str | None, str | None]:
    """
    Parse Schwartz Woodworking LLC input data.

    Expected format (per line):
    4 poplar x x DUSYNS3
    2 BSM x x DUNONS3

    Lines with dimensions (e.g., "4 BSM 6 7/8 x 30 x 16 *CDC4 no prep") are skipped.
    Only lines with "x x" immediately after species are processed.

    Output format:
        [part_number]\t[quantity]
    """
    output_lines = []

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    for line_num, line in enumerate(lines, start=1):
        parts = line.split()

        # Need at least 4 parts: quantity, species, x, x, part_number
        if len(parts) < 5:
            continue

        try:
            # First part is quantity
            qty_str = parts[0]

            # Validate quantity is a whole number
            if qty_str.isdigit():
                qty = qty_str
            elif qty_str.replace(".", "").isdigit():
                whole, dot, decimal = qty_str.partition(".")
                if decimal and all(c == "0" for c in decimal):
                    qty = whole  # convert 4.00 → 4
                else:
                    return "error", None, f"Error: Line {line_num} quantity must be a whole number"
            else:
                return "error", None, f"Error: Line {line_num} quantity must be a whole number"

            # Second part is species (ignored)
            # species = parts[1]

            # Third and fourth parts determine if we process this line
            # Only process if they are both "x"
            if parts[2].lower() == "x" and parts[3].lower() == "x":
                # Fifth part is the part number
                part_number = parts[4]

                # Build output line: part_number, quantity
                output_lines.append(f"{part_number}\t{qty}")
            else:
                # Skip lines with dimensions (not "x x")
                continue

        except (IndexError, ValueError) as e:
            return "error", None, f"Error: Line {line_num} invalid format"

    if not output_lines:
        return "error", None, "Error: No valid data found"

    return "success", "\n".join(output_lines), None