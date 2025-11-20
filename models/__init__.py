"""
Models package - automatically exports all modules from this directory.
"""
import importlib
import pkgutil
from pathlib import Path

# Get the current package path
__all__ = []

# Automatically import all modules in this package
_package_dir = Path(__file__).parent

for _module_info in pkgutil.iter_modules([str(_package_dir)]):
    _module_name = _module_info.name

    # Skip __init__ and __pycache__
    if _module_name.startswith('_'):
        continue

    try:
        # Import the module
        _module = importlib.import_module(f".{_module_name}", package=__name__)

        # Add to __all__ for explicit exports
        __all__.append(_module_name)

        # Make the module available at package level
        globals()[_module_name] = _module
    except (ImportError, AttributeError, SyntaxError) as e:
        # Log but don't fail if a module can't be imported
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("Failed to import module %s: %s", _module_name, e)
