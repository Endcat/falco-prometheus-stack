import re

# Regex patterns for attribute tokenization/generalization

# 1. UUID Pattern: e.g. 123e4567-e89b-12d3-a456-426614174000
_UUID_PATTERN = re.compile(
    r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
)

# 2. IPv4 Pattern: Matches valid IP addresses
_IP_PATTERN = re.compile(
    r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
    r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
)

# 3. Hex Pattern: Matches hex strings 6 chars or longer (e.g. hashes, memory addresses)
_HEX_PATTERN = re.compile(r'\b[0-9a-fA-F]{6,}\b')

# 4. Digit Pattern: Matches sequences of 5 or more digits (e.g. PIDs, ephemeral ports, timestamps)
_DIGIT_PATTERN = re.compile(r'\b\d{5,}\b')

# 5. Date Pattern: Matches YYYY-MM-DD, YYYYMMDD, etc. commonly found in filenames
_DATE_PATTERN = re.compile(r'\b20\d{2}[-_]?\d{2}[-_]?\d{2}\b')

def tokenize_attribute(attr: str) -> str:
    """
    Tokenize attribute string for generalization to reduce false positives.
    
    Applies the following transformations in order:
    1. UUID -> '<uuid>'
    2. IP addresses -> '<ip>'
    3. Dates (YYYY-MM-DD) -> '<date>'
    4. Hex strings (>=6 chars) -> 'x' * length
    5. Digit strings (>=5 chars) -> '0' * length
    
    Args:
        attr: Original attribute string
        
    Returns:
        Tokenized attribute string
    """
    if not attr:
        return attr

    # Handle numeric/non-string types gracefully
    if not isinstance(attr, str):
        attr = str(attr)

    # 1. Replace UUID with '<uuid>'
    result = _UUID_PATTERN.sub('<uuid>', attr)
    
    # 2. Replace IP addresses with '<ip>'
    result = _IP_PATTERN.sub('<ip>', result)
    
    # 3. Replace Date strings with '<date>'
    result = _DATE_PATTERN.sub('<date>', result)

    # 4. Replace hex strings (>=6 chars) with 'x' * length
    def hex_replacer(match: re.Match) -> str:
        return 'x' * len(match.group())
    result = _HEX_PATTERN.sub(hex_replacer, result)

    # 5. Replace digit strings (>=5 chars) with '0' * length
    def digit_replacer(match: re.Match) -> str:
        return '0' * len(match.group())
    result = _DIGIT_PATTERN.sub(digit_replacer, result)

    return result
