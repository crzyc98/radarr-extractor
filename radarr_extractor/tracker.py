import os
from contextlib import contextmanager
from radarr_extractor.config import TRACKER_FILE, logger

try:
    import fcntl  # POSIX-only
except ImportError:  # pragma: no cover - non-POSIX fallback
    fcntl = None


@contextmanager
def _locked_file(path: str, mode: str, lock_type: int):
    f = open(path, mode)
    try:
        if fcntl is not None:
            try:
                fcntl.flock(f, lock_type)
            except Exception:
                pass
        yield f
    finally:
        try:
            if fcntl is not None:
                try:
                    fcntl.flock(f, fcntl.LOCK_UN)
                except Exception:
                    pass
        finally:
            f.close()

def load_extracted_files():
    """Load the list of extracted files from the tracker file."""
    extracted_files = set()
    if os.path.exists(TRACKER_FILE):
        lock = fcntl.LOCK_SH if fcntl is not None else 0
        with _locked_file(TRACKER_FILE, 'r', lock) as f:
            for line in f:
                extracted_files.add(line.strip())
    return extracted_files

def record_extracted_file(file_path):
    """Record a successfully extracted file."""
    logger.info(f"Recording extracted file: {file_path}")
    # Ensure tracker directory exists
    os.makedirs(os.path.dirname(TRACKER_FILE), exist_ok=True)
    lock = fcntl.LOCK_EX if fcntl is not None else 0
    with _locked_file(TRACKER_FILE, 'a', lock) as f:
        f.write(file_path + '\n')

def is_file_extracted(file_path):
    """Check if a file has already been extracted."""
    extracted_files = load_extracted_files()
    return file_path in extracted_files
