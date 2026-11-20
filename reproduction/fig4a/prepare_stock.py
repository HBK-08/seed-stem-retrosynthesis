"""Build an exact disk-backed SMILES inventory from SimpRetro's emolecules.txt."""

import argparse
import hashlib
import sqlite3
import tempfile
from pathlib import Path


STOCK_SHA256 = "eb0ff886bcb5d2b71f935ed1658576deb7b2ead84adeffe912ed09f33efc4815"


def build(source, destination):
    if source.stat().st_size != 896953382:
        raise ValueError("Unexpected size for the published emolecules.txt")
    if destination.exists():
        raise FileExistsError(destination)
    digest = hashlib.sha256()
    lines = 0
    with tempfile.TemporaryDirectory(dir=destination.parent) as tmp:
        staging = Path(tmp) / "stock.sqlite"
        db = sqlite3.connect(staging)
        try:
            db.execute("PRAGMA journal_mode=OFF")
            db.execute("PRAGMA synchronous=OFF")
            db.execute("PRAGMA cache_size=-262144")
            db.execute("CREATE TABLE stock (smiles TEXT PRIMARY KEY) WITHOUT ROWID")
            with source.open("rb") as stream:
                while chunk := stream.readlines(4 * 1024**2):
                    digest.update(b"".join(chunk))
                    db.executemany("INSERT OR IGNORE INTO stock VALUES (?)",
                                   ((row.decode("ascii").strip(),) for row in chunk))
                    lines += len(chunk)
            if digest.hexdigest() != STOCK_SHA256:
                raise ValueError("Inventory SHA-256 differs from the archived author download.")
            unique, = db.execute("SELECT count(*) FROM stock").fetchone()
            db.execute("CREATE TABLE source (sha256 TEXT, lines INTEGER, unique_smiles INTEGER)")
            db.execute("INSERT INTO source VALUES (?,?,?)", (digest.hexdigest(), lines, unique))
            db.commit()
            print("SHA-256, input lines, unique strings:", digest.hexdigest(), lines, unique)
        finally:
            db.close()
        staging.rename(destination)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    build(args.source, args.destination)
