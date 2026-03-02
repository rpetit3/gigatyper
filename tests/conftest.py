"""Load bin/gigatyper (no .py extension) as an importable module."""
import importlib.machinery
import importlib.util
from pathlib import Path

# Load the script as a module so tests can import its functions
_script = Path(__file__).resolve().parent.parent / "bin" / "gigatyper"
_loader = importlib.machinery.SourceFileLoader("gigatyper_mod", str(_script))
_spec = importlib.util.spec_from_file_location("gigatyper_mod", _script, loader=_loader)
gigatyper_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gigatyper_mod)
