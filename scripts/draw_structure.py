"""Render a SMILES for comparison with the original problem image."""

import argparse
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import Draw, rdMolDescriptors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("smiles")
    parser.add_argument("output", type=Path, help="destination PNG file")
    args = parser.parse_args()
    molecule = Chem.MolFromSmiles(args.smiles)
    if molecule is None or molecule.GetNumAtoms() == 0:
        parser.error("Provide a valid, nonempty SMILES.")
    if args.output.suffix.lower() != ".png":
        parser.error("Use a .png output filename.")

    Draw.MolToFile(molecule, str(args.output), size=(720, 400), imageType="png")
    print("SMILES:", Chem.MolToSmiles(molecule))
    print("Formula:", rdMolDescriptors.CalcMolFormula(molecule))
    print("Chiral centers:", Chem.FindMolChiralCenters(molecule, includeUnassigned=True))


if __name__ == "__main__":
    main()
