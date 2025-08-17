import os
import time
import threading
import rarfile
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from typing import List
from watchdog.events import FileSystemEventHandler
from concurrent.futures import ThreadPoolExecutor, as_completed
from radarr_extractor.config import (
    RADARR_API_KEY,
    RADARR_URL,
    EXTRACTED_DIR,
    DOWNLOAD_DIR,
    EXTRACT_MODE,
    RADARR_NOTIFY,
    EXTRACT_ONLY_MEDIA,
    MAX_CONCURRENT_EXTRACTS,
    STABILITY_WINDOW_SEC,
    STABILITY_POLLS,
    MAX_WAIT_PER_ARCHIVE_SEC,
    logger,
)
from radarr_extractor.tracker import record_extracted_file, is_file_extracted

def is_temp_directory(path: str) -> bool:
    """Check if the path is within a temp directory using component-aware check."""
    try:
        parts = os.path.normpath(path).split(os.sep)
        return any(p.lower() in {"tmp", "temp"} for p in parts)
    except Exception:
        return False

def is_compressed_file(filename: str) -> bool:
    """Check if file is a compressed archive."""
    compressed_extensions = ['.rar', '.zip', '.7z', '.tar.gz', '.tar.bz2', '.tar', '.tgz', '.tbz2']
    return any(filename.lower().endswith(ext) for ext in compressed_extensions)

def _is_safe_path(base_dir: str, target_path: str) -> bool:
    base = os.path.realpath(base_dir)
    target = os.path.realpath(target_path)
    return os.path.commonpath([base, target]) == base


def _safe_extract_zip(zip_path: str, dest_dir: str) -> None:
    import zipfile
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for info in zf.infolist():
            name = info.filename
            if name.endswith('/'):
                out_path = os.path.join(dest_dir, name)
                if not _is_safe_path(dest_dir, out_path):
                    raise Exception(f"Unsafe zip member path: {name}")
                os.makedirs(out_path, exist_ok=True)
                continue
            out_path = os.path.join(dest_dir, name)
            if not _is_safe_path(dest_dir, out_path):
                raise Exception(f"Unsafe zip member path: {name}")
            if not _should_extract_member(name):
                continue
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with zf.open(info, 'r') as src, open(out_path, 'wb') as dst:
                # Stream in chunks to reduce memory spikes
                while True:
                    chunk = src.read(1024 * 1024)
                    if not chunk:
                        break
                    dst.write(chunk)


def _safe_extract_tar(tar_path: str, dest_dir: str, mode: str) -> None:
    import tarfile
    with tarfile.open(tar_path, mode) as tf:
        members = []
        for m in tf.getmembers():
            if m.islnk() or m.issym():
                raise Exception(f"Unsafe tar member (link): {m.name}")
            out_path = os.path.join(dest_dir, m.name)
            if not _is_safe_path(dest_dir, out_path):
                raise Exception(f"Unsafe tar member path: {m.name}")
            if _should_extract_member(m.name) or m.isdir():
                members.append(m)
        tf.extractall(dest_dir, members=members)


def _safe_extract_rar(rar_path: str, dest_dir: str) -> None:
    with rarfile.RarFile(rar_path) as rf:
        for info in rf.infolist():
            name = info.filename
            out_path = os.path.join(dest_dir, name)
            if not _is_safe_path(dest_dir, out_path):
                raise Exception(f"Unsafe rar member path: {name}")
            if _should_extract_member(name):
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                rf.extract(info, path=dest_dir)


def _safe_extract_7z(seven_path: str, dest_dir: str) -> None:
    try:
        import py7zr
    except ImportError:
        raise Exception("py7zr library required for 7z extraction")
    with py7zr.SevenZipFile(seven_path, mode='r') as z:
        names: List[str] = [n for n in z.getnames() if _should_extract_member(n)]
        for name in names:
            out_path = os.path.join(dest_dir, name)
            if not _is_safe_path(dest_dir, out_path):
                raise Exception(f"Unsafe 7z member path: {name}")
        try:
            z.extractall(path=dest_dir, targets=names)
        except TypeError:
            z.extractall(path=dest_dir)



_MEDIA_EXTS = {'.mkv', '.mp4', '.avi', '.mov', '.mpg', '.mpeg', '.m4v', '.ts', '.srt', '.sub', '.idx', '.ass', '.sup'}
_JUNK_EXTS = {'.nfo', '.jpg', '.jpeg', '.png', '.url', '.sfv', '.txt'}


def _should_extract_member(name: str) -> bool:
    base = os.path.basename(name).lower()
    if base.startswith('sample'):
        return False
    _, ext = os.path.splitext(base)
    if ext in _JUNK_EXTS:
        return False
    if EXTRACT_ONLY_MEDIA:
        return ext in _MEDIA_EXTS
    return True


def _compute_extract_dir(archive_path: str) -> str:
    if EXTRACT_MODE == 'extracted_dir':
        try:
            root = os.path.realpath(DOWNLOAD_DIR)
            parent = os.path.realpath(os.path.dirname(archive_path))
            if os.path.commonpath([root, parent]) == root:
                rel = os.path.relpath(parent, root)
                dest = os.path.join(EXTRACTED_DIR, rel)
            else:
                dest = EXTRACTED_DIR
        except Exception:
            dest = EXTRACTED_DIR
        os.makedirs(dest, exist_ok=True)
        return dest
    return os.path.dirname(archive_path)


def extract_archive(archive_path: str) -> str:
    """Extract archive using safe extraction routines."""
    logger.info(f"Starting archive extraction for: {archive_path}")
    extract_dir = _compute_extract_dir(archive_path)
    logger.info(f"Extracting to: {extract_dir}")
    try:
        archive_lower = archive_path.lower()
        if archive_lower.endswith('.rar'):
            logger.info("Detected RAR archive")
            _safe_extract_rar(archive_path, extract_dir)
        elif archive_lower.endswith('.zip'):
            logger.info("Detected ZIP archive")
            _safe_extract_zip(archive_path, extract_dir)
        elif archive_lower.endswith('.7z'):
            logger.info("Detected 7Z archive")
            _safe_extract_7z(archive_path, extract_dir)
        elif archive_lower.endswith(('.tar.gz', '.tgz')):
            logger.info("Detected TAR.GZ archive")
            _safe_extract_tar(archive_path, extract_dir, 'r:gz')
        elif archive_lower.endswith(('.tar.bz2', '.tbz2')):
            logger.info("Detected TAR.BZ2 archive")
            _safe_extract_tar(archive_path, extract_dir, 'r:bz2')
        elif archive_lower.endswith('.tar'):
            logger.info("Detected TAR archive")
            _safe_extract_tar(archive_path, extract_dir, 'r')
        else:
            logger.warning(f"Unsupported archive format: {archive_path}")
            raise Exception(f"Unsupported archive format: {archive_path}")
        logger.info(f"Extraction completed successfully to: {extract_dir}")
        return extract_dir
    except Exception as e:
        logger.error(f"Extraction failed: {str(e)}")
        raise

def notify_radarr(extracted_path: str) -> None:
    """Notify Radarr about the new extracted files with retries and toggle."""
    if not RADARR_NOTIFY:
        logger.info("RADARR_NOTIFY disabled; skipping Radarr notification")
        return
    if not RADARR_URL or not RADARR_API_KEY:
        logger.warning("RADARR_URL or RADARR_API_KEY not set; skipping Radarr notification")
        return
    headers = {
        'X-Api-Key': RADARR_API_KEY,
        'Content-Type': 'application/json'
    }
    endpoint = f"{RADARR_URL}/api/v3/command"
    payload = {"name": "RescanMovie", "path": extracted_path}
    last_err = None
    for attempt in range(3):
        try:
            resp = requests.post(endpoint, json=payload, headers=headers, timeout=10)
            resp.raise_for_status()
            logger.info(f"Notified Radarr to rescan: {extracted_path}")
            return
        except Exception as e:
            last_err = e
            wait = 2 ** attempt
            logger.warning(f"Radarr notify failed (attempt {attempt+1}/3): {e}; retrying in {wait}s")
            time.sleep(wait)
    logger.error(f"Failed to notify Radarr after retries: {last_err}")

_PROCESS_LOCKS = {}

# Global executor for concurrency (optional)
_EXECUTOR = None
try:
    if MAX_CONCURRENT_EXTRACTS and MAX_CONCURRENT_EXTRACTS > 1:
        _EXECUTOR = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_EXTRACTS, thread_name_prefix="extractor")
except Exception:
    _EXECUTOR = None


def _submit_process(path: str):
    if _EXECUTOR is None:
        process_file(path)
    else:
        _EXECUTOR.submit(process_file, path)


def _get_lock(path: str) -> threading.Lock:
    key = os.path.realpath(path)
    lock = _PROCESS_LOCKS.get(key)
    if lock is None:
        lock = threading.Lock()
        _PROCESS_LOCKS[key] = lock
    return lock


def _wait_for_file_stable(path: str, interval: float = 2.0, timeout: float = 60.0) -> bool:
    """Wait until file size is unchanged for configured stability window or timeout."""
    deadline = time.time() + max(5, MAX_WAIT_PER_ARCHIVE_SEC)
    last = None
    stable_count = 0
    while time.time() < deadline:
        try:
            size = os.path.getsize(path)
        except Exception:
            return False
        if last is not None and size == last:
            stable_count += 1
            if stable_count >= max(1, STABILITY_POLLS):
                return True
        else:
            stable_count = 0
        last = size
        time.sleep(max(1, STABILITY_WINDOW_SEC))
    return False


def process_file(file_path: str) -> None:
    """Process a downloaded file if it's compressed with locking and stability check."""
    if is_file_extracted(file_path):
        logger.info(f"File already processed, skipping: {file_path}")
        return

    if is_temp_directory(file_path):
        logger.debug(f"Skipping file in temp directory: {file_path}")
        return

    if not is_compressed_file(file_path):
        logger.info(f"File is not compressed, skipping: {file_path}")
        return

    lock = _get_lock(file_path)
    if not lock.acquire(blocking=False):
        logger.info(f"Extraction already in progress for: {file_path}")
        return
    try:
        logger.info(f"Checking file for extraction: {file_path}")
        if not _wait_for_file_stable(file_path):
            logger.warning(f"File did not become stable in time: {file_path}")
        logger.info(f"Starting extraction: {file_path}")
        extracted_path = extract_archive(file_path)
        logger.info(f"Successfully extracted to: {extracted_path}")
        record_extracted_file(file_path)
        notify_radarr(extracted_path)
    except Exception as e:
        logger.error(f"Failed to process file {file_path}: {str(e)}")
    finally:
        try:
            lock.release()
        except Exception:
            pass

def scan_directory(directory):
    """Recursively scan directory for compressed files with optional concurrency."""
    logger.info(f"Scanning directory: {directory}")
    tasks = []
    try:
        for root, dirs, files in os.walk(directory):
            if is_temp_directory(root):
                logger.debug(f"Skipping temp directory: {root}")
                dirs[:] = []  # Clear the dirs list to prevent recursion
                continue
                
            logger.info(f"Checking subfolder: {root}")
            for file in files:
                full_path = os.path.join(root, file)
                if is_compressed_file(full_path):
                    logger.info(f"Found compressed file: {full_path}")
                    if _EXECUTOR is None:
                        process_file(full_path)
                    else:
                        tasks.append(_EXECUTOR.submit(process_file, full_path))
        if tasks:
            for _ in as_completed(tasks):
                pass
    except Exception as e:
        logger.error(f"Error scanning directory {directory}: {e}")

class DownloadHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and not is_temp_directory(event.src_path) and not event.src_path.endswith('.DS_Store'):
            logger.info(f"File system event - New file detected: {event.src_path}")
            _submit_process(event.src_path)

    def on_modified(self, event):
        if not event.is_directory and not is_temp_directory(event.src_path) and not event.src_path.endswith('.DS_Store'):
            logger.info(f"File system event - File modified: {event.src_path}")
            _submit_process(event.src_path)
