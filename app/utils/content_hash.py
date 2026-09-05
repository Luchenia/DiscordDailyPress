from hashlib import sha256


def calculate_source_content_hash(content: str) -> str:
    """Return a deterministic SHA-256 hex digest for exact source content."""
    return sha256(content.encode("utf-8")).hexdigest()
