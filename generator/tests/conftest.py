import sys
from pathlib import Path

#makes generator/scripts importable in tests
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
