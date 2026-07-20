import re
from parsers.frac_to_dec import fraction_to_decimal


def parse_legacy(raw_text: str) -> tuple[str, str | None, str | None]:
    """
    Parse Legacy Crafted Cabinets input data format.

    Expected format: 5 lines per record
    - Line 1: [ref_id] [quantity]
    - Lines 2-4: Additional data (ignored)
    - Line 5: [data] [width] x [height]

    Output format:
        [quantity]\t[width]\t[height]\t[ref_id]
    """
    output_lines = []

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    # Process every 5 lines as one record
    for i in range(0, len(lines), 5):
        # Ensure we have 5 lines to work with
        if i + 4 >= len(lines):
            break

        try:
            line1 = lines[i]
            line5 = lines[i + 4]

            line5 = re.sub(r'(\d+)\s+(\d+/\d+)', r'\1-\2', line5)

            # Parse line 1 for reference ID and quantity
            parts1 = line1.split()
            if len(parts1) < 2:
                return "error", "", f"Error: Line {i + 1} missing reference ID or quantity"

            reference_id = parts1[0]

            # Convert quantity to whole number (remove .0 or .00)
            try:
                quantity_float = float(parts1[1])
                quantity = str(int(quantity_float))
            except ValueError:
                return "error", "", f"Error: Line {i + 1} invalid quantity"

            # Parse line 5 for dimensions
            parts5 = line5.split()

            # Find 'x' separator
            if 'x' not in parts5:
                return "error", "", f"Error: Line {i + 5} missing 'x' separator"

            x_index = parts5.index('x')

            # Extract width and height around 'x' separator
            if x_index == 0 or x_index >= len(parts5) - 1:
                return "error", "", f"Error: Line {i + 5} missing width or height"

            width_raw = parts5[x_index - 1]
            height_raw = parts5[x_index + 1]

            # Replace hyphens with spaces for fraction parsing
            width_raw = width_raw.replace("-", " ")
            height_raw = height_raw.replace("-", " ")

            # Convert to decimal inches
            decimal_width = fraction_to_decimal(width_raw)
            decimal_height = fraction_to_decimal(height_raw)

            # Build output line: quantity, width, height, ref_id
            output_lines.append(f"{quantity}\t{decimal_width}\t{decimal_height}\t{reference_id}")

        except Exception as e:
            return "error", "", f"Error processing record starting at line {i + 1}: {str(e)}"

    # Check if parsing produced any valid data
    if not output_lines:
        return "error", "", "Error: No valid data found"

    return "success", "\n".join(output_lines), "\n".join(output_lines)