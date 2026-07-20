# mavin_parser.py

species_map = {
    "M": "bsm",
    "C": "cherry",
    "H": "hickory",
    "F": "knotty oak",
    "O": "oak",
    "Q": "white oak",
    "R": "sap cherry",
    "W": "walnut",
    "E": "grey elm",
    "I": "hard maple",
    "D": "curly maple",
    "G": "wormy maple",
}


def parse_mavin(raw_text: str) -> tuple[str, str | None, str | None]:
    """
    Parses Mavin-style input data from entire PDF.

    Valid line types:
    1. Format 1: First part is digits only, second part is digits with exactly 1 period
       Example: 001 4.00 EA 03245DO1-R Door1 95.72 23.93
       Output: 03245DO1 sap cherry[TAB]4

    2. Format 2: First part is digits with exactly 1 period, second part contains a dash
       Example: 4.00 C14BDO1-M Total $ 59.69 238.76
       Output: C14BDO1 bsm[TAB]4

    When Format 1 items are repeated and followed by a Format 2 consolidation,
    only the consolidation is output (the repeated items are skipped).

    Skip lines containing:
    - "DF." anywhere in the line
    - "STOCK MOLDING" anywhere in the line
    """
    lines = raw_text.splitlines()
    output_lines = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Skip lines containing "DF." or "STOCK MOLDING"
        if "DF." in line or "STOCK MOLDING" in line:
            i += 1
            continue

        # Split line into parts
        parts = line.split()

        # Need at least 2 parts to check
        if len(parts) < 2:
            i += 1
            continue

        first_part = parts[0]
        second_part = parts[1]

        # Check for Format 1: first part is digits only, second part is digits with 1 period
        if first_part.isdigit() and second_part.count(".") == 1 and second_part.replace(".", "").isdigit():
            # Format 1: 001 4.00 EA 03245DO1-R Door1 95.72 23.93
            # Need at least 4 parts (id, qty, EA, part-species)
            if len(parts) < 4:
                return "error", "", f"Error on line {i + 1}: missing required fields"

            part_and_species = parts[3]

            # Validate part number has dash
            if "-" not in part_and_species:
                return "error", "", f"Error on line {i + 1}: missing dash in part number"

            # Look ahead to see if this is a repeated item
            is_repeated = False
            look_ahead = i + 1

            while look_ahead < len(lines):
                next_line = lines[look_ahead].strip()

                # Skip empty lines and lines to ignore
                if not next_line or "DF." in next_line or "STOCK MOLDING" in next_line:
                    look_ahead += 1
                    continue

                next_parts = next_line.split()
                if len(next_parts) < 2:
                    look_ahead += 1
                    continue

                next_first = next_parts[0]
                next_second = next_parts[1]

                # Check if next line is Format 1 (another item)
                if next_first.isdigit() and next_second.count(".") == 1 and next_second.replace(".", "").isdigit():
                    # It's another Format 1 item
                    if len(next_parts) >= 4 and "-" in next_parts[3]:
                        next_part_and_species = next_parts[3]
                        # If same part-species, it's repeated
                        if next_part_and_species == part_and_species:
                            is_repeated = True
                            break
                    # Different item, stop looking
                    break

                # Check if next line is Format 2 (consolidation)
                elif next_first.count(".") == 1 and next_first.replace(".", "").isdigit() and "-" in next_second:
                    # It's a Format 2 consolidation
                    if next_second == part_and_species:
                        is_repeated = True
                    break

                # Not a valid data line, keep looking
                look_ahead += 1

            # If this item is repeated, skip it and all repeats until we hit the consolidation
            if is_repeated:
                while i < len(lines):
                    curr_line = lines[i].strip()

                    if not curr_line or "DF." in curr_line or "STOCK MOLDING" in curr_line:
                        i += 1
                        continue

                    curr_parts = curr_line.split()
                    if len(curr_parts) >= 2:
                        curr_first = curr_parts[0]
                        curr_second = curr_parts[1]

                        # Check if we've reached the Format 2 consolidation
                        if curr_first.count(".") == 1 and curr_first.replace(".", "").isdigit() and "-" in curr_second:
                            # Found the consolidation, stop skipping
                            break

                    i += 1
                continue

            # Not repeated - parse normally
            qty_str = parts[1]

            # Validate and clean quantity
            if qty_str.isdigit():
                qty = qty_str
            elif qty_str.replace(".", "").isdigit():
                whole, dot, decimal = qty_str.partition(".")
                if decimal and all(c == "0" for c in decimal):
                    qty = whole  # convert 4.00 → 4
                else:
                    return "error", "", f"Error on line {i + 1}: invalid quantity"
            else:
                return "error", "", f"Error on line {i + 1}: invalid quantity"

            # Split part number and species
            part_number, species_code = part_and_species.split("-", 1)

            # Validate species code
            if len(species_code) != 1 or species_code.upper() not in species_map:
                return "error", "", f"Error on line {i + 1}: invalid species code '{species_code}'"

            species_name = species_map[species_code.upper()]

            # Build output line
            output_lines.append(f"{part_number} {species_name}\t{qty}")
            i += 1
            continue

        # Check for Format 2: first part is digits with 1 period, second part contains dash
        if first_part.count(".") == 1 and first_part.replace(".", "").isdigit() and "-" in second_part:
            # Format 2: 4.00 C14BDO1-M Total $ 59.69 238.76
            qty_str = parts[0]
            part_and_species = parts[1]

            # Validate and clean quantity
            if qty_str.isdigit():
                qty = qty_str
            elif qty_str.replace(".", "").isdigit():
                whole, dot, decimal = qty_str.partition(".")
                if decimal and all(c == "0" for c in decimal):
                    qty = whole  # convert 4.00 → 4
                else:
                    return "error", "", f"Error on line {i + 1}: invalid quantity"
            else:
                return "error", "", f"Error on line {i + 1}: invalid quantity"

            # Validate part number has dash
            if "-" not in part_and_species:
                return "error", "", f"Error on line {i + 1}: missing dash in part number"

            # Split part number and species
            part_number, species_code = part_and_species.split("-", 1)

            # Validate species code
            if len(species_code) != 1 or species_code.upper() not in species_map:
                return "error", "", f"Error on line {i + 1}: invalid species code '{species_code}'"

            species_name = species_map[species_code.upper()]

            # Build output line
            output_lines.append(f"{part_number} {species_name}\t{qty}")
            i += 1
            continue

        # Line doesn't match either format, skip it
        i += 1

    if not output_lines:
        return "error", "", "Error - No valid data found in input"

    return "success", "\n".join(output_lines), None