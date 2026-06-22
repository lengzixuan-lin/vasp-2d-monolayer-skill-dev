#!/usr/bin/env python3
"""Small local helpers for provenance and result-label file records."""

import hashlib
import os


def file_sha256(path, block_size=1024 * 1024):
    """Return a local SHA256 digest for an existing file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            h.update(block)
    return h.hexdigest()


def path_record(path, base_dir=None, role=None, required=False):
    """Build a reviewable local file record without assuming it exists."""
    exists = os.path.exists(path)
    record = {
        "path": os.path.relpath(path, base_dir) if base_dir else path,
        "exists": exists,
        "required": required,
    }
    if role:
        record["role"] = role
    if exists and os.path.isfile(path):
        record["size_bytes"] = os.path.getsize(path)
        record["sha256"] = file_sha256(path)
    return record
