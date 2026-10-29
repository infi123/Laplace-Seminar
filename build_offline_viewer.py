"""Compatibility wrapper: run the safe, modern build instead of the outdated viewer."""
import subprocess,sys
from pathlib import Path
subprocess.run([sys.executable,str(Path(__file__).resolve().parent/'build_all.py'),*sys.argv[1:]],check=True)
