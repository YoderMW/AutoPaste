import re

from parsers.frac_to_dec import fraction_to_decimal


# ---------------------------------------------------------------------------
# Dean S4S parser -- supports TWO input formats.
#
# ORIGINAL FORMAT (no description, no ref ID):
#     [qty] [width] x [height]
#     "1 4 1/2 x 90"          ->  1 | 4.5 | 90
#   Output: qty, width, height  (3 columns)
#
# NEW FORMAT (off a PDF; description + ref ID list):
#     [qty] [description] [width] x [length] [ref ID list]
#     "2 Mid Stile 3 1/8 x 18 1/16 153 (2)"       ->  2 | 3.125 | 18.0625 | 153 (2)
#     "4 Filler Front 1 1/2 x 95 113, 178, 182"   ->  4 | 1.5 | 95 | 113, 178, 182
#   Output: qty, width, length, ref ID  (4 columns)
#
# The description ("Mid Stile", "Filler Front", "Top Rail", "Baseboard"...) is
# discarded. The ref ID list is passed through verbatim apart from whitespace
# normalisation, including the "(n)" echo that repeats the quantity.
#
# Quantity always comes from the leading number in both formats.
#
# The two formats are told apart by the description: only the new one carries
# letters (beyond the "x" separator). The whole paste is treated as one format
# or the other so the output never mixes 3- and 4-column rows -- gui.py sizes
# the F4 auto-entry cycle from the first row's column count.
# ---------------------------------------------------------------------------

# A dimension: whole, whole + fraction, or bare fraction. The whole+fraction
# alternative comes first so "3 1/8" is never truncated to just "3".
_DIM = r"\d+\s+\d+/\d+|\d+/\d+|\d+"

# One ref ID plus its optional "(n)" quantity echo.
_REF_ITEM = r"\d+(?:\s*\(\d+\))?"

NEW_ENTRY_PATTERN = re.compile(
    r"^(?P<qty>\d+)"                                       # leading quantity
    r"\s+(?P<desc>[A-Za-z][A-Za-z.\-\s]*?)"                # description (letters only)
    rf"\s+(?P<width>{_DIM})"                               # width
    r"\s+[xX]\s+"                                          # 'x' separator
    rf"(?P<length>{_DIM})"                                 # length / height
    rf"\s+(?P<ref>{_REF_ITEM}(?:\s*,\s*{_REF_ITEM})*)"     # ref ID list
    r"\s*$"
)


def _has_description(line: str) -> bool:
    """
    True if the line carries letters somewhere other than the "x" separator,
    i.e. it is the new format. "1 4 1/2 x 90" -> False,
    "1 Top Rail 1 1/2 x 36 7/8 153" -> True.
    """
    return any(
        token.lower() != "x" and any(char.isalpha() for char in token)
        for token in line.split()
    )


def _clean_ref(ref_raw: str) -> str:
    """Normalise whitespace in a ref list: "113,178  (2)" -> "113, 178 (2)"."""
    return ", ".join(
        re.sub(r"\s+", " ", part.strip())
        for part in ref_raw.split(",")
    )


def _parse_new_format(lines: list[tuple[int, str]]) -> tuple[str, str | None, str | None]:
    """Parse the description + ref ID format. Any unparseable line fails the paste."""
    output_lines = []

    for line_number, line in lines:
        match = NEW_ENTRY_PATTERN.match(line)

        if not match:
            return (
                "error",
                None,
                f"Line {line_number}: Expected "
                f"'[qty] [description] [width] x [length] [ref ID]'"
            )

        try:
            width_out = fraction_to_decimal(match.group("width").strip())
            length_out = fraction_to_decimal(match.group("length").strip())
        except (ValueError, ZeroDivisionError):
            return "error", None, f"Line {line_number}: Invalid fraction format"

        output_lines.append(
            f"{match.group('qty')}\t{width_out}\t{length_out}"
            f"\t{_clean_ref(match.group('ref'))}"
        )

    return "success", "\n".join(output_lines), None


def _parse_original_format(lines: list[tuple[int, str]]) -> tuple[str, str | None, str | None]:
    """Parse the original "[qty] [width] x [height]" format."""
    output_lines = []

    for line_number, line in lines:
        parts = line.split()

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

    return "success", "\n".join(output_lines), None


def parse_dean_s4s(raw_text: str) -> tuple[str, str | None, str | None]:
    """
    Parse Dean S4S input data, in either supported format.

    Original format (per line):
        [qty] [width] x [height]
            1 4 1/2 x 90
            2 2 x 39
        Output: [qty]\t[width]\t[height]

    New format (per line):
        [qty] [description] [width] x [length] [ref ID list]
            2 Mid Stile 3 1/8 x 18 1/16 153 (2)
            4 Filler Front 1 1/2 x 95 113, 178, 182, 184
        Output: [qty]\t[width]\t[length]\t[ref ID list]

    Widths and lengths can each be a whole number ("90"), a whole number plus a
    fraction ("4 1/2"), or a bare fraction ("3/8").
    """
    lines = [
        (line_number, line.strip())
        for line_number, line in enumerate(raw_text.splitlines(), start=1)
        if line.strip()
    ]

    if not lines:
        return "error", None, "No valid data found"

    # One description anywhere in the paste means the whole paste is the new
    # format; a malformed row then reports as a new-format error instead of
    # being silently retried as the original format.
    if any(_has_description(line) for _, line in lines):
        return _parse_new_format(lines)

    return _parse_original_format(lines)
