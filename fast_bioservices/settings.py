from pathlib import Path

import appdirs

# Cache settings
_cache_dir: Path = Path(appdirs.user_cache_dir("fast_bioservices"))
cache_dir: Path = Path(_cache_dir, "fast_bioservices_cache")
log_filepath: Path = Path(_cache_dir, "fast_bioservices.log")

if not log_filepath.exists():
    log_filepath.parent.mkdir(parents=True, exist_ok=True)
    log_filepath.touch(exist_ok=True)

if not cache_dir.exists():
    cache_dir.parent.mkdir(parents=True, exist_ok=True)
    cache_dir.touch(exist_ok=True)