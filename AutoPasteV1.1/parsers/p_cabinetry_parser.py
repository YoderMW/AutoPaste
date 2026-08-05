import re
from parsers.frac_to_dec import fraction_to_decimal


# ---------------------------------------------------------------------------
# P Cabinetry (Cabinet Vision "Door List") parser.
#
# A single door entry looks like:
#     [qty] [width] x [height] [type] [cabinet list]
# e.g. "4 13 3/8 x 11 11/16 DF 10 (4)" or "1 24 1/4 x 6 1/2 FF 10"
#
# The cabinet list is one or more cabinet numbers, each with an optional "(n)"
# echo giving how many doors go to that cabinet:
#     "10"             -> cabinet 10, 1 door
#     "10 (4)"         -> cabinet 10, 4 doors
#     "15, 19"         -> cabinets 15 and 19, 1 door each
#     "2 (2), 3 (2)"   -> cabinets 2 and 3, 2 doors each
# The entry's leading quantity is always the SUM of those echoes, so we never
# need to read the leading digit -- which matters, see below.
#
# COPY FORMATS
# ------------
# How this table lands on the clipboard depends on the PDF viewer, because PDF
# has no concept of a line -- each viewer reconstructs them from glyph geometry:
#
#   Firefox (PDF.js) / Edge  -- one entry per line, as displayed.
#   Chrome (PDFium)          -- rows may be concatenated with NO separator at
#                               all, because at a row boundary the x-position
#                               jumps backwards (not a positive gap, so no
#                               space is inserted) and the vertical delta can
#                               fall under PDFium's new-line threshold.
#
# Chrome's run-together form glues the next entry's leading quantity onto the
# end of this entry's cabinet list:
#
#     "...S 10" + "4 8 13/16 x..."  ->  "...S 104 8 13/16 x..."
#                                              ^^^ cabinet 10, next qty 4
#
# We handle both: entries are found by anchoring on the "x" separator + door
# type (never the ambiguous leading quantity), and a glued digit is detected by
# an empty gap between consecutive matches, then stripped using the next
# entry's quantity recovered from its echo sum.
#
# Note a glue landing after a ")" (e.g. "...3 (2)2 16 3/8 x...") needs no
# repair -- it falls outside the cabinet list and is simply skipped.
# ---------------------------------------------------------------------------

# One cabinet number plus its optional "(n)" echo.
_CAB_ITEM = r"\d+(?:\s*\(\d+\))?"

# Matches one door entry, starting at the WIDTH (the leading quantity is
# intentionally NOT captured -- see notes above).
ENTRY_PATTERN = re.compile(
    r"(?P<width>\d+(?:\s+\d+/\d+)?)"                    # width: whole + optional fraction
    r"\s+[xX]\s+"                                        # 'x' separator
    r"(?P<height>\d+(?:\s+\d+/\d+)?)"                    # height: whole + optional fraction
    r"\s+(?P<type>[A-Za-z]+)"                            # door type (DF, FF, S, P, BE, TE, WE...)
    rf"\s+(?P<cab>{_CAB_ITEM}(?:\s*,\s*{_CAB_ITEM})*)"   # cabinet list; may include a glued next qty
)

CAB_ITEM_PATTERN = re.compile(r"(\d+)(?:\s*\((\d+)\))?")


def _entry_qty(cab_raw: str) -> int:
    """
    Recover an entry's quantity WITHOUT relying on the glued leading digit.

    Quantity is the sum of the per-cabinet "(n)" echoes, counting a cabinet
    with no echo as 1:
        "10" -> 1    "10 (4)" -> 4    "15, 19" -> 2    "2 (2), 3 (2)" -> 4

    A glued next-quantity only lengthens the last cabinet NUMBER; it never adds
    an item or an echo, so the sum is unaffected by the gluing.
    """
    return sum(
        int(echo) if echo else 1
        for _, echo in CAB_ITEM_PATTERN.findall(cab_raw)
    )


def _clean_cab(cab_raw: str) -> str:
    """Normalise whitespace in a cabinet list: "2  (2),3 (2)" -> "2 (2), 3 (2)"."""
    return ", ".join(
        re.sub(r"\s+", " ", part.strip())
        for part in cab_raw.split(",")
    )


def _strip_glued_qty(cab_raw: str, next_qty: int) -> str:
    """
    Remove the next entry's glued-on quantity from the end of the cabinet list.

    e.g. ("104", 4) -> "10"   ("15, 191", 1) -> "15, 19"   ("381", 1) -> "38"

    Only a list ending in a bare cabinet number can carry a glued digit; if the
    list ends with an echo the glue landed after the ")" and is not ours.
    """
    parts = [p.strip() for p in cab_raw.split(",")]
    last = parts[-1]
    if "(" in last:
        return cab_raw

    qn = str(next_qty)
    if last.endswith(qn) and len(last) > len(qn):
        parts[-1] = last[: -len(qn)]
    return ", ".join(parts)


def parse_p_cabinetry(raw_text: str) -> tuple[str, str | None, str | None]:
    """
    Parse P Cabinetry (Cabinet Vision Door List) input.

    Accepts either copy format (one entry per line, or the whole table run
    together on one line -- see notes above).

    Output format (per row):
        [quantity]\t[width]\t[height]\t[cabinet list]
    """
    # Join into a single string so entries that wrap are still found, and so
    # both copy formats go down the same path.
    text = " ".join(raw_text.splitlines())

    matches = list(ENTRY_PATTERN.finditer(text))
    if not matches:
        return "error", None, "No valid door entries found. Check the pasted data."

    # Pre-compute each entry's quantity (needed to un-glue neighbouring cabinets).
    quantities = [_entry_qty(m.group("cab")) for m in matches]

    output_lines = []
    for idx, match in enumerate(matches):
        cab_raw = match.group("cab")

        # No text at all between this entry and the next means the rows were
        # concatenated, so the next entry's quantity is glued to the end of
        # this cabinet list. Strip it back off.
        if idx < len(matches) - 1:
            gap = text[match.end():matches[idx + 1].start()]
            if gap.strip() == "":
                cab_raw = _strip_glued_qty(cab_raw, quantities[idx + 1])

        ref_id = _clean_cab(cab_raw)

        try:
            width_out = fraction_to_decimal(match.group("width").strip())
            height_out = fraction_to_decimal(match.group("height").strip())
        except (ValueError, ZeroDivisionError):
            return (
                "error",
                None,
                f"Entry {idx + 1} (cabinet {ref_id}): Invalid dimension format"
            )

        output_lines.append(
            f"{quantities[idx]}\t{width_out}\t{height_out}\t{ref_id}"
        )

    return "success", "\n".join(output_lines), None
