from pathlib import Path

import appdirs

# Cache settings
_root_cache_dir: Path = Path(appdirs.user_cache_dir("fast_bioservices"))
cache_dir: Path = Path(_root_cache_dir, "fast_bioservices_cache")
log_filepath: Path = Path(_root_cache_dir, "fast_bioservices.log")

_root_cache_dir.mkdir(parents=True, exist_ok=True)
cache_dir.mkdir(parents=True, exist_ok=True)
log_filepath.touch(exist_ok=True)