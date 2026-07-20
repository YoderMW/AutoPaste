def parse_mw_resi(raw_text: str) -> tuple[str, str | None, str | None]:
    """
    Parse Mullwoods Residential input data from Chrome or Adobe Acrobat formats.

    Handles two formats:
    - Chrome: AA 2) 20.5 x 11.75 #1.17(1) #1.21(1)
    - Acrobat: AA \n 2) 20.5 x 11.75 #1.17(1) #1.21(1)

    Output format:
        [quantity]\t[width]\t[height]\t[ref_id]
    """
    output_lines = []

    # Remove empty lines and trim spaces
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    # Used when Acrobat splits reference ID to separate line
    pending_ref_id = None

    for line_num, line in enumerate(lines, start=1):
        parts = line.split()

        # Case 1: Acrobat format - reference ID alone (like 'A' or 'AA')
        if len(parts) == 1 and parts[0].isalpha() and 1 <= len(parts[0]) <= 2:
            pending_ref_id = parts[0]
            continue

        try:
            # Case 2: Chrome format (reference ID on same line)
            if parts[0].isalpha() and 1 <= len(parts[0]) <= 2:
                reference_id = parts[0]
                quantity = parts[1].rstrip(")")
                width = parts[2]
                height = parts[4]

            # Case 3: Acrobat continuation line (use pending reference ID)
            elif pending_ref_id:
                reference_id = pending_ref_id
                quantity = parts[0].rstrip(")")
                width = parts[1]
                height = parts[3]
                pending_ref_id = None

            else:
                # Skip lines that don't match expected patterns
                continue

            # Remove any 'x' or 'X' characters from dimensions
            width = width.replace("x", "").replace("X", "")
            height = height.replace("x", "").replace("X", "")

            # Build output line: quantity, width, height, ref_id
            output_lines.append(f"{quantity}\t{width}\t{height}\t{reference_id}")

        except (IndexError, ValueError) as e:
            return "error", None, f"Invalid data format on line {line_num}"

    if not output_lines:
        return "error", None, "No valid data found"

    return "success", "\n".join(output_lines), None