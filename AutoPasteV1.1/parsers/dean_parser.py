import re
from parsers.frac_to_dec import fraction_to_decimal


# Matches the Ref ID at the END of the line.
# Ref ID = one or more "number (optional (count))" groups, separated by commas.
# Examples matched: "122", "112 (3)", "117, 118", "159 (2), 160 (2)"
REF_ID_PATTERN = re.compile(
    r"(\d+(?:\s*\(\d+\))?(?:\s*,\s*\d+(?:\s*\(\d+\))?)*)\s*$"
)


def parse_dean(raw_text: str) -> tuple[str, str | None, str | None]:
    """
    Parse Dean input data format.

    Expected format (per line):
        [qty] [width] x [height] [junk...] [ref_id]

    Examples:
        1 21 5/16 x 19 7/16 P L 2.00 3 1/4 : 3 1/4 Blum 5mm 2 1/4 (All) 122
        2 24 5/16 x 19 5/16 S L 2.00 3 1/4 : 3 1/4 Blum 5mm 2 1/4 (All) 117, 118
        3 21 3/4 x 13 1/2 DF N 0.00 2 1/4 (All) 112 (3)

    Output format:
        [quantity]\t[width]\t[height]\t[ref_id]
    """
    output_lines = []

    for line_number, line in enumerate(raw_text.splitlines(), start=1):
        line = line.strip()

        if not line:
            continue

        # --------------------------
        # Extract REF ID from end of line
        # --------------------------
        ref_match = REF_ID_PATTERN.search(line)
        if not ref_match:
            return (
                "error",
                None,
                f"Line {line_number}: Missing or invalid reference ID"
            )

        ref_id = ref_match.group(1).strip()
        # Remove the ref ID from the end so it doesn't interfere with parsing
        remainder = line[:ref_match.start()].strip()

        parts = remainder.split()

        # --------------------------
        # QUANTITY
        # --------------------------
        if not parts or not parts[0].isdigit():
            return (
                "error",
                None,
                f"Line {line_number}: Quantity must be a whole number"
            )

        qty = parts[0]
        i = 1

        # --------------------------
        # WIDTH (whole number + optional fraction, up until "x")
        # --------------------------
        if i >= len(parts):
            return (
                "error",
                None,
                f"Line {line_number}: Missing width value"
            )

        width_tokens = [parts[i]]
        i += 1

        # Optional fractional part (e.g., "5/16")
        if i < len(parts) and "/" in parts[i]:
            width_tokens.append(parts[i])
            i += 1

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
        # HEIGHT (whole number + optional fraction)
        # --------------------------
        if i >= len(parts):
            return (
                "error",
                None,
                f"Line {line_number}: Missing height value"
            )

        height_tokens = [parts[i]]
        i += 1

        # Optional fractional part
        if i < len(parts) and "/" in parts[i]:
            height_tokens.append(parts[i])
            i += 1

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
        output_lines.append(
            f"{qty}\t{width_out}\t{height_out}\t{ref_id}"
        )

    if not output_lines:
        return "error", None, "No valid data found"

    return "success", "\n".join(output_lines), None