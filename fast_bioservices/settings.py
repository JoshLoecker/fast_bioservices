from pathlib import Path

import appdirs

# Cache settings
cache_dir: Path = Path(appdirs.user_cache_dir("fast_bioservices"))
cache_name: Path = Path(
    appdirs.user_cache_dir("fast_bioservices"), "fast_bioservices_cache"
)

# Log settings
log_filepath: Path = Path(cache_dir, "fast_bioservices.log")

if not log_filepath.exists():
    log_filepath.parent.mkdir(parents=True, exist_ok=True)
    log_filepath.touch(exist_ok=True)
