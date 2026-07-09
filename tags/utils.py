"""
utils.py
Shared helpers for the tags project.
"""

import json
from pathlib import Path 

REPO_ROOT = Path(__file__).parent.parent

def get_ol_session():
    """Return an authenticated OpenLibrary client using S3 keys from ~/.config/ol.ini."""
    from olclient.openlibrary import OpenLibrary
    from olclient.config import Config, Credentials
    cfg = Config().get_config()
    s3 = cfg["s3"]
    return OpenLibrary(credentials=Credentials(access=s3[0], secret=s3[1]))

def slug_to_tag_key(type_name: str, slug: str) -> str | None:
    """
    Given a tag type name (e.g. "genres") and a slug (e.g "sci-fi"),
    return the corresponding OL tag key (e.g "/tags/OL179T") by 
    looking it up in the type's vocabulary.json

    Return None if not found.
    """

    vocab_path = REPO_ROOT / "tag_types" / type_name / "vocabulary.json"
    if not vocab_path.exists():
        return None
    
    vocab = json.loads(vocab_path.read_text())
    for entry in vocab.get("tags", []):
        if entry.get("slug") == slug:
            return entry.get("key")
        
    return None
