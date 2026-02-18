import os

def sample_file(filename: str) -> str:
    """
    Returns the absolute path to a sample file in the tests/sample_data directory.
    """
    path = os.path.join(os.path.dirname(__file__), filename)
    return f"file://{path}"
