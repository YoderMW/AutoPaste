def fraction_to_decimal(value: str) -> str:
    """
    Converts strings like:
      "13", "13 3/8", "3/8"
    into decimal strings like:
      "13", "13.375", "0.375"

    Always returns a string with trailing .0 removed.
    """
    # Whole + fraction (e.g., "13 3/8")
    if " " in value:
        whole, frac = value.split()
        num, den = frac.split("/")
        result = float(whole) + (float(num) / float(den))
    # Fraction only (e.g., "3/8")
    elif "/" in value:
        num, den = value.split("/")
        result = float(num) / float(den)
    # Whole number only (e.g., "15")
    else:
        result = float(value)

    # Remove trailing .0 by formatting
    if result.is_integer():
        return str(int(result))

    return str(result)
