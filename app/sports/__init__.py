"""
Sports module - Auto-discovers and registers all available sports.
"""
import importlib
import pkgutil
from pathlib import Path


def discover_sports():
    """
    Automatically discover and import all sport modules.
    Each sport's __init__.py should call register_sport() when imported.
    """
    sports_dir = Path(__file__).parent
    
    for module_info in pkgutil.iter_modules([str(sports_dir)]):
        if module_info.ispkg:  # Only import packages (folders with __init__.py)
            try:
                importlib.import_module(f"app.sports.{module_info.name}")
            except ImportError as e:
                print(f"⚠ Could not load sport module '{module_info.name}': {e}")
