"""
__init__.py
Loader that reads registry.json, loads vocabulary and mappings for each 
registered tag type, and returns a sorted list of Tagtype instances.
"""

import importlib
import json
from pathlib import Path
from typing import Optional
from tags.tag_type import TagType

REPO_ROOT = Path(__file__).parent.parent

#----------------------------------------------------------------------------
# Load all registered tag types
#----------------------------------------------------------------------------

def load_all(root: Optional[Path] = None) -> list[TagType]:
    """
    Read tag_types/registry.json and build TagType instances for 
    every registered type.
    Currently reads from pre-migration paths:
        - vocabulary: <type>/vocabulary.json (e.g. genres/vocabulary.json)
        - mappings: <type>.json (e.g. mappings/genres.json)
    After PR #2 migration, these will read from tag_types/<type>/.
    """
    if root is None:
        root = REPO_ROOT / "tag_types"

    registry = json.loads((root / "registry.json").read_text())
    out: list[TagType] = []

    for name, cfg in registry.items():
        d = root / name

        # Vocabulary: <type>/vocabulary.json
        vocab_path = REPO_ROOT / name / "vocabulary.json"
        if vocab_path.exists():
            vocab = json.loads(vocab_path.read_text())
        else:
            vocab = {}

        # Mappings: mappings/<type>.json
        maps_path = REPO_ROOT / "mappings" / f"{name}.json"
        if maps_path.exists():
            maps = json.loads(maps_path.read_text())
        else:
            maps = {}

        # Optional custom classify function
        fn = None
        if (d / "classify.py").exists():
            mod = importlib.import_module(f"tag_types.{name}.classify")
            fn = getattr(mod, "classify", None)

        out.append(TagType(
            name=name,
            directory=d,
            priority=cfg.get("priority", 100),
            vocabulary=vocab,
            mappings=maps,
            classify_fn=fn,
        ))

    return sorted(out, key=lambda t: t.priority)
