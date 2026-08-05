import re
from parsers.frac_to_dec import fraction_to_decimal


# Every Ruffino drawer row has a rigid 6-number dimensional block:
#     qty   width(int frac)   depth(int)   height(int frac)
# Width and height always carry a fraction; depth is a whole number. That shape
# is distinctive enough to locate every row start even when the order PDF is
# copied as one unbroken line with no row delimiters (the reported bug).
#
# Column order matches the PDF dimension table: Qty, Width, Depth, Height.
ROW_SIGNATURE = re.compile(
    r"(\d+)\s+(\d+)\s+(\d+/\d+)\s+(\d+)\s+(\d+)\s+(\d+/\d+)"
)


def parse_ruffino_box(raw_text: str) -> tuple[str, str | None, str | None]:
    """
    Parse Ruffino drawer-box data.

    The order PDF's dimension table is usually pasted as ONE line with no row
    breaks, e.g.:

        2 26 3/16 21 9 1/4 2 (2)4 20 3/16 21 7 1/4 11 (2), 13 (2)1 ...

    Rows are recovered by anchoring on each row's fixed dimensional block
    (ROW_SIGNATURE). Everything between one block and the next is that row's
    Ref ID. Because `\\s+` also matches newlines, a multi-line paste parses
    through the exact same path.

    Where a row's ref ends in a bare cabinet number and the next row's qty is a
    bare number, the copy glues them together (".. 4 1/4 2" + "2 20 .." -> "22")
    and the greedy signature swallows both as the next qty. Drawer quantities
    are single-digit, so the trailing digit is the real qty and the leading
    digit(s) are the previous row's final cabinet number -- see redistribution
    below. (Validated by the invariant that a row's qty equals the sum of its
    ref counts, e.g. "11 (2), 13 (2)" -> 4.)

    Output format (Allmoxy field order):
        [quantity]\t[height]\t[width]\t[depth]\t[ref_id]
    """
    text = raw_text.strip()
    if not text:
        return "error", None, "No valid data found"

    matches = list(ROW_SIGNATURE.finditer(text))
    if not matches:
        return "error", None, "No valid data found"

    # --------------------------
    # Slice text into one row per signature; the gap after each block is its ref
    # --------------------------
    rows = []
    for idx, m in enumerate(matches):
        qty, w_int, w_frac, depth, h_int, h_frac = m.groups()
        ref_start = m.end()
        ref_end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        rows.append({
            "qty": qty,
            "width": f"{w_int} {w_frac}",
            "depth": depth,
            "height": f"{h_int} {h_frac}",
            "ref": text[ref_start:ref_end].strip(),
        })

    # --------------------------
    # Redistribute glued ref/qty digits (see docstring)
    # --------------------------
    for i in range(1, len(rows)):
        qty = rows[i]["qty"]
        if len(qty) > 1:
            glued, real_qty = qty[:-1], qty[-1]
            rows[i]["qty"] = real_qty
            prev_ref = rows[i - 1]["ref"]
            rows[i - 1]["ref"] = f"{prev_ref} {glued}".strip() if prev_ref else glued

    # --------------------------
    # Build output rows
    # --------------------------
    output_lines = []
    for line_num, row in enumerate(rows, start=1):
        if not row["ref"]:
            return "error", None, f"Row {line_num}: Missing reference ID"

        try:
            width_val = fraction_to_decimal(row["width"])
            depth_val = fraction_to_decimal(row["depth"])
            height_val = fraction_to_decimal(row["height"])
        except (ValueError, ZeroDivisionError):
            return "error", None, f"Row {line_num}: Invalid fraction format"

        # Order: Quantity, Height, Width, Depth, Ref ID
        output_lines.append(
            f"{row['qty']}\t{height_val}\t{width_val}\t{depth_val}\t{row['ref']}"
        )

    if not output_lines:
        return "error", None, "No valid data found"

    return "success", "\n".join(output_lines), None
