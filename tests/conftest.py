# Used to add src directory to python path before running tests
import sys
from pathlib import Path

src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, Path(src_dir).resolve().as_posix())
