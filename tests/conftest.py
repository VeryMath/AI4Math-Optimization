import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = ROOT / "skills" / "optimization-modeling" / "scripts"
for path in [ROOT, SCRIPT_ROOT]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
