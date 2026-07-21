import re
from parsers.frac_to_dec import fraction_to_decimal


# ---------------------------------------------------------------------------
# P Cabinetry (Cabinet Vision "Door List") parser.
#
# This source is unusual: when a dimension table is copied off the PDF, the
# ENTIRE table lands on a single line with all door entries run together and
# no separator between them. Headers ("Qty Width x Height Type Cabinet (Qty)"),
# section labels ("DF large (Stain Buyout)"), and page/print junk are mixed in.
#
# A single door entry looks like:
#     [qty] [width] x [height] [type] [cabinet][ (qty)]
# e.g. "4 13 3/8 x 11 11/16 DF 10 (4)" or "1 24 1/4 x 6 1/2 FF 10"
#
# The hard part: an entry with quantity 1 has NO trailing "(qty)" echo, so its
# cabinet number glues directly onto the NEXT entry's quantity with no space
# (e.g. "...FF 201 14 13/16 x..." is really cabinet 20 + next qty 1 + width 14).
#
# We sidestep the ambiguous leading quantity entirely by anchoring on the "x"
# separator + door type, and we recover each entry's quantity from a reliable
# invariant instead of the glued digit:
#     * quantity == the trailing "(n)" echo  (single cabinet, qty > 1), OR
#     * quantity == number of comma-separated cabinets ("15, 19" -> 2), OR
#     * quantity == 1
# A glued next-quantity is then stripped off the cabinet field.
# ---------------------------------------------------------------------------

# Matches one door entry's reliable core, starting at the WIDTH (the leading
# quantity is intentionally NOT captured -- see notes above).
ENTRY_PATTERN = re.compile(
    r"(?P<width>\d+(?:\s+\d+/\d+)?)"          # width: whole + optional fraction
    r"\s+[xX]\s+"                              # 'x' separator
    r"(?P<height>\d+(?:\s+\d+/\d+)?)"          # height: whole + optional fraction
    r"\s+(?P<type>[A-Za-z]+)"                  # door type (DF, FF, S, P, BE, TE, WE...)
    r"\s+(?P<cab>\d+(?:\s*,\s*\d+)*)"          # cabinet number(s); may include glued next qty
    r"(?:\s*\((?P<paren>\d+)\))?"              # optional "(qty)" echo
)


def _entry_qty(match) -> int:
    """
    Recover an entry's quantity WITHOUT relying on the glued leading digit.

    A glued next-quantity only adds digits to the last cabinet number, never a
    new comma, so the comma count is unaffected by the gluing.
    """
    if match.group("paren"):
        return int(match.group("paren"))
    return match.group("cab").count(",") + 1


def _strip_glued_qty(cab_raw: str, next_qty: int) -> str:
    """
    Remove the next entry's glued-on quantity from the end of the cabinet field.

    e.g. ("201", 1) -> "20"   ("15, 192", 2) -> "15, 19"   ("381", 1) -> "38"
    """
    qn = str(next_qty)
    parts = [p.strip() for p in cab_raw.split(",")]
    last = parts[-1]
    if last.endswith(qn) and len(last) > len(qn):
        parts[-1] = last[: -len(qn)]
    return ", ".join(parts)


def parse_p_cabinetry(raw_text: str) -> tuple[str, str | None, str | None]:
    """
    Parse P Cabinetry (Cabinet Vision Door List) input.

    Output format (per row):
        [quantity]\t[width]\t[height]\t[cabinet]
    """
    # Everything copies onto one line, but be tolerant of multi-line pastes:
    # join into a single string so entries that wrap are still found.
    text = " ".join(raw_text.splitlines())

    matches = list(ENTRY_PATTERN.finditer(text))
    if not matches:
        return "error", None, "No valid door entries found. Check the pasted data."

    # Pre-compute each entry's quantity (needed to un-glue neighbouring cabinets).
    quantities = [_entry_qty(m) for m in matches]

    output_lines = []
    for idx, match in enumerate(matches):
        cab_raw = match.group("cab")

        # If this entry has no "(qty)" echo, the NEXT entry's quantity is glued
        # to the end of this cabinet field (detected by an empty gap before the
        # next entry). Strip it back off.
        if idx < len(matches) - 1:
            gap = text[match.end():matches[idx + 1].start()]
            if gap.strip() == "":
                cab_raw = _strip_glued_qty(cab_raw, quantities[idx + 1])

        ref_id = ", ".join(p.strip() for p in cab_raw.split(","))

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
