import re
from parsers.frac_to_dec import fraction_to_decimal


# Matches the Ref ID at the END of the line.
# Ref ID = one or more "number (optional (count))" groups, separated by commas.
# Examples matched: "127", "116, 117, 132, 133", "132 (2), 133 (2)"
#
# Because each group must be comma-joined, this never swallows the
# space-separated Depth value that precedes the ref -- even on lines that
# omit the "logo" word (e.g. "4 19 1/8 5 18 132 (2), 133 (2)").
REF_ID_PATTERN = re.compile(
    r"(\d+(?:\s*\(\d+\))?(?:\s*,\s*\d+(?:\s*\(\d+\))?)*)\s*$"
)


def _take_dimension(parts: list[str], i: int) -> tuple[str, int]:
    """
    Read one dimension starting at index `i`: a whole number followed by an
    optional fraction token (e.g. "16" "1/8" -> "16 1/8"). Returns the joined
    dimension string and the next unread index.
    """
    tokens = [parts[i]]
    i += 1
    if i < len(parts) and "/" in parts[i]:
        tokens.append(parts[i])
        i += 1
    return " ".join(tokens), i


def parse_dean_boxes(raw_text: str) -> tuple[str, str | None, str | None]:
    """
    Parse Dean Boxes (drawer box) input data format.

    Each record is one line, copied off the order PDF's dimension table:
        [qty] [width] [height] [depth] [logo?] [ref_id]

    The "logo" word and the (usually empty) Front Holes column are optional, so
    the token count per line varies. To stay robust the Ref ID is pulled off
    the END of the line first; the remaining tokens are then read positionally
    (qty, width, height, depth) and anything left over ("logo", front holes) is
    ignored.

    Examples:
        1 16 1/8 4 1/2 21 logo 127
        4 19 1/8 4 1/2 18 logo 116, 117, 132, 133
        4 19 1/8 5 18 132 (2), 133 (2)

    Output format (Allmoxy field order -- Height and Width are swapped relative
    to the raw table):
        [quantity]\t[height]\t[width]\t[depth]\t[ref_id]
    """
    output_lines = []

    for line_number, raw_line in enumerate(raw_text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue

        # --------------------------
        # REF ID (from end of line)
        # --------------------------
        ref_match = REF_ID_PATTERN.search(line)
        if not ref_match:
            return (
                "error",
                None,
                f"Line {line_number}: Missing or invalid reference ID"
            )

        ref_id = ref_match.group(1).strip()
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
        # WIDTH, HEIGHT, DEPTH (each: whole + optional fraction)
        # --------------------------
        if i >= len(parts):
            return "error", None, f"Line {line_number}: Missing width value"
        width_str, i = _take_dimension(parts, i)

        if i >= len(parts):
            return "error", None, f"Line {line_number}: Missing height value"
        height_str, i = _take_dimension(parts, i)

        if i >= len(parts):
            return "error", None, f"Line {line_number}: Missing depth value"
        depth_str, i = _take_dimension(parts, i)

        # Any leftover tokens ("logo", front holes) are ignored.

        # --------------------------
        # Convert fractions to decimals
        # --------------------------
        try:
            width_out = fraction_to_decimal(width_str)
            height_out = fraction_to_decimal(height_str)
            depth_out = fraction_to_decimal(depth_str)
        except (ValueError, ZeroDivisionError):
            return (
                "error",
                None,
                f"Line {line_number}: Invalid fraction format"
            )

        # --------------------------
        # Build output line (Height, Width, Depth order for Allmoxy)
        # --------------------------
        output_lines.append(
            f"{qty}\t{height_out}\t{width_out}\t{depth_out}\t{ref_id}"
        )

    if not output_lines:
        return "error", None, "No valid data found"

    return "success", "\n".join(output_lines), None
