#!/usr/bin/env python3
"""
Adsorption module for HER/OER free energy calculations.

This is the ONLY module that requires user interaction:
1. Analyze material surface → identify active sites
2. Generate REQUIRED_CONFIGS.yaml listing needed adsorption geometries
3. Pause workflow, wait for user to provide POSCAR files
4. Resume: compute adsorption energies, ΔG_H*, OER free energy diagram
"""

import os
import yaml
import numpy as np
from pathlib import Path


class AdsorptionAnalyzer:
    """
    Analyze a 2D material surface and determine required adsorption
    configurations for HER/OER calculations.
    """

    # HER active site types to check
    HER_SITES = ["top", "bridge", "hollow"]

    # OER intermediates on active metal site
    OER_INTERMEDIATES = ["OH", "O", "OOH"]

    def __init__(self, poscar_path):
        self.poscar_path = poscar_path
        self.elements = None
        self.positions = None
        self.lattice = None
        self._parse_poscar()

    def _parse_poscar(self):
        """Parse POSCAR to get elements, positions, lattice."""
        with open(self.poscar_path, 'r') as f:
            lines = f.readlines()

        scale = float(lines[1].strip())
        self.lattice = np.array([
            [float(x) * scale for x in lines[2].split()],
            [float(x) * scale for x in lines[3].split()],
            [float(x) * scale for x in lines[4].split()],
        ])

        element_names = lines[5].strip().split()
        counts = [int(x) for x in lines[6].strip().split()]

        # Read atom positions
        coord_type = lines[7].strip().lower()
        natoms = sum(counts)
        self.positions = []
        self.elements_list = []
        for i in range(natoms):
            parts = lines[8 + i].strip().split()
            pos = np.array([float(x) for x in parts[:3]])
            if coord_type[0] == 'd':
                # Direct coordinates → convert to cartesian
                pos = pos @ self.lattice
            self.positions.append(pos)

        # Assign elements
        for el, count in zip(element_names, counts):
            for _ in range(count):
                self.elements_list.append(el)

        self.elements = element_names
        self.counts = counts
        self.natoms = natoms

    def get_surface_atoms(self, z_tolerance=1.0):
        """
        Identify surface atoms (top and bottom layers).
        For 2D materials, these are atoms at the highest/lowest z.
        """
        z_coords = [p[2] for p in self.positions]
        z_max = max(z_coords)
        z_min = min(z_coords)

        top_surface = []
        bottom_surface = []
        for i, (el, pos) in enumerate(
                zip(self.elements_list, self.positions)):
            if abs(pos[2] - z_max) < z_tolerance:
                top_surface.append({
                    "index": i, "element": el,
                    "position": pos.tolist(),
                    "side": "top",
                })
            elif abs(pos[2] - z_min) < z_tolerance:
                bottom_surface.append({
                    "index": i, "element": el,
                    "position": pos.tolist(),
                    "side": "bottom",
                })

        return top_surface, bottom_surface

    def identify_unique_surface_elements(self):
        """Identify unique elements on the surface."""
        top, bottom = self.get_surface_atoms()
        top_elements = set(a["element"] for a in top)
        bottom_elements = set(a["element"] for a in bottom)
        return top_elements, bottom_elements

    def generate_her_requirements(self):
        """
        Generate list of required HER adsorption configurations.

        For HER, we need one H adsorbed at each unique surface site type
        (top, bridge, hollow) for each surface element.

        Returns list of dicts with: site_type, element, description
        """
        top_el, bottom_el = self.identify_unique_surface_elements()
        all_elements = top_el | bottom_el

        requirements = []
        for el in sorted(all_elements):
            for site in self.HER_SITES:
                requirements.append({
                    "calculation": "HER",
                    "element": el,
                    "site_type": site,
                    "adsorbate": "H",
                    "poscar_name": f"POSCAR_HER_{el}_{site}",
                    "description": f"H adsorbed at {site} site on {el}",
                })

        return requirements

    def generate_oer_requirements(self, active_side="top"):
        """
        Generate OER intermediate requirements.
        OER typically happens on metal sites (Mo, W, Pt, etc.).
        We identify transition metal elements on the surface.

        For each metal site → 3 intermediates: *OH, *O, *OOH
        """
        top, _ = self.get_surface_atoms()
        # Identify transition metals on surface
        metals = {"Mo", "W", "Pt", "Pd", "Rh", "Ru", "Ir", "Fe", "Co",
                   "Ni", "Mn", "Cr", "V", "Ti", "Cu", "Ag", "Au", "Nb",
                   "Ta", "Zr", "Hf", "Re", "Os"}

        surface_metals = set()
        for atom in top if active_side == "top" else _:
            if atom["element"] in metals:
                surface_metals.add(atom["element"])

        # Also check bottom side
        _, bottom = self.get_surface_atoms()
        for atom in bottom:
            if atom["element"] in metals:
                surface_metals.add(atom["element"])

        if not surface_metals:
            surface_metals = {"Metal"}  # placeholder

        requirements = []
        for metal in sorted(surface_metals):
            for intermediate in self.OER_INTERMEDIATES:
                requirements.append({
                    "calculation": "OER",
                    "metal_site": metal,
                    "intermediate": intermediate,
                    "adsorbate": intermediate,
                    "poscar_name": f"POSCAR_OER_{metal}_{intermediate}",
                    "description": (
                        f"{intermediate} adsorbed on {metal} surface site"),
                })

        # Also need clean surface and isolated H2O/H2 reference
        requirements.append({
            "calculation": "OER_ref",
            "metal_site": "N/A",
            "intermediate": "clean",
            "adsorbate": "none",
            "poscar_name": "POSCAR_OER_clean",
            "description": "Clean surface (no adsorbate) — reference",
        })

        return requirements


def generate_requirements_yaml(poscar_path, output_path):
    """
    Main entry point: analyze POSCAR and write REQUIRED_CONFIGS.yaml.

    This is called when the adsorption module is activated.
    The user should then provide the requested POSCAR files.
    """
    analyzer = AdsorptionAnalyzer(poscar_path)

    her_reqs = analyzer.generate_her_requirements()
    oer_reqs = analyzer.generate_oer_requirements()

    top_el, bottom_el = analyzer.identify_unique_surface_elements()

    config = {
        "material_info": {
            "elements": analyzer.elements,
            "natoms": analyzer.natoms,
            "surface_elements_top": sorted(top_el),
            "surface_elements_bottom": sorted(bottom_el),
        },
        "her_requirements": her_reqs,
        "oer_requirements": oer_reqs,
        "instructions": (
            "Please create POSCAR files for each configuration above.\n"
            "Place them in: <project_dir>/19_adsorption/sites/\n"
            "Then run: python workflow.py resume <project_name>\n\n"
            "HER configuration: One H atom placed ~1.5-2.0 A above\n"
            "  the specified surface atom (top/bridge/hollow position).\n"
            "OER intermediates: *OH, *O, *OOH placed on the metal site.\n"
            "  Use standard DFT adsorption geometries as starting points.\n"
        ),
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True,
                  sort_keys=False)

    return config


def print_requirements_summary(config):
    """Print a human-readable summary of required configurations."""
    print("\n" + "=" * 60)
    print("  ADSORPTION CONFIGURATION REQUIREMENTS")
    print("=" * 60)

    info = config["material_info"]
    print(f"\n  Material: {'/'.join(info['elements'])}")
    print(f"  Atoms: {info['natoms']}")
    print(f"  Surface elements (top): {', '.join(info['surface_elements_top'])}")
    print(f"  Surface elements (bottom): {', '.join(info['surface_elements_bottom'])}")

    print(f"\n  --- HER Sites ({len(config['her_requirements'])}) ---")
    for req in config["her_requirements"]:
        print(f"    [ ] {req['description']}")
        print(f"        File: {req['poscar_name']}")

    print(f"\n  --- OER Intermediates ({len(config['oer_requirements'])}) ---")
    for req in config["oer_requirements"]:
        print(f"    [ ] {req['description']}")
        print(f"        File: {req['poscar_name']}")

    print(f"\n  Next steps:")
    print(f"    1. Create POSCAR files for each [ ] item above")
    print(f"    2. Place them in: projects/<name>/19_adsorption/sites/")
    print(f"    3. Run: python workflow.py resume <project_name>")
    print("=" * 60 + "\n")


# ============================================================
# Free energy calculations (run after user provides POSCARs)
# ============================================================

def compute_her_free_energy(energy_H_star, energy_clean, energy_H2_gas):
    """
    Compute HER free energy: ΔG_H* = E(H*) - E(clean) - E(H2)/2 + ΔZPE - TΔS

    Standard correction for H*: ΔZPE - TΔS ≈ +0.24 eV at 298K
    (Norskov et al., J. Electrochem. Soc. 2005)

    Args:
        energy_H_star: Total energy of surface with adsorbed H (eV)
        energy_clean: Total energy of clean surface (eV)
        energy_H2_gas: Total energy of gas-phase H2 molecule (eV)

    Returns:
        ΔG_H* in eV (ideal catalyst: ΔG_H* ≈ 0 eV)
    """
    delta_E = energy_H_star - energy_clean - energy_H2_gas / 2.0
    delta_G = delta_E + 0.24  # standard correction
    return delta_G


def compute_oer_free_energy_diagram(energies, u_vs_rhe=0.0, ph=0):
    """
    Compute OER free energy diagram (4-electron pathway).

    OER mechanism in acid:
      (1) H2O + * → *OH + H+ + e-     ΔG1
      (2) *OH → *O + H+ + e-          ΔG2
      (3) H2O + *O → *OOH + H+ + e-   ΔG3
      (4) *OOH → * + O2 + H+ + e-     ΔG4

    Args:
        energies: dict with keys: E_clean, E_OH, E_O, E_OOH,
                  E_H2O_gas, E_H2_gas
        u_vs_rhe: Applied potential vs RHE (default 0 = equilibrium)
        ph: pH value (0 for acidic OER)

    Returns:
        dict with ΔG1, ΔG2, ΔG3, ΔG4 and overpotential η_OER
    """
    # Reference energies
    # H2O → 1/2 O2 + H2:  ΔG = 4.92 eV (experimental at 298K)
    # We use the computational hydrogen electrode (CHE) approach
    # μ(H+ + e-) = 1/2 μ(H2) - eU at U=0 vs RHE

    G_H2O_gas = energies.get("E_H2O_gas", -14.22)  # default VASP value
    G_H2_gas = energies.get("E_H2_gas", -6.77)     # default VASP value

    # Free energy of (H+ + e-) pair at given potential and pH
    G_proton_electron = 0.5 * G_H2_gas - u_vs_rhe - 0.059 * ph

    # Step energies (with ZPE + TS corrections - approximate)
    # Standard corrections from literature:
    # ZPE(OH*) = 0.35 eV, ZPE(O*) = 0.05 eV, ZPE(OOH*) = 0.41 eV
    # -TS term at 298K: -TS(OH*) = 0, -TS(O*) = 0, -TS(OOH*) = 0
    # H2O(g) ZPE = 0.56 eV, TS = 0.67 eV → G_H2O = E_H2O + 0.56 - 0.67

    E_clean = energies.get("E_clean", 0)
    E_OH = energies.get("E_OH", 0)
    E_O = energies.get("E_O", 0)
    E_OOH = energies.get("E_OOH", 0)

    # Step 1: * + H2O → *OH + H+ + e-
    dG1 = (E_OH + 0.35) - (E_clean + G_H2O_gas + 0.56 - 0.67) + \
        G_proton_electron

    # Step 2: *OH → *O + H+ + e-
    dG2 = (E_O + 0.05) - (E_OH + 0.35) + G_proton_electron

    # Step 3: *O + H2O → *OOH + H+ + e-
    dG3 = (E_OOH + 0.41) - (E_O + 0.05) - \
        (G_H2O_gas + 0.56 - 0.67) + G_proton_electron

    # Step 4: *OOH → * + O2 + H+ + e-
    # ΔG_total = 4.92 eV for full OER
    dG4 = 4.92 - (dG1 + dG2 + dG3)

    # Overpotential
    max_dG = max(dG1, dG2, dG3, dG4)
    eta_OER = max_dG - 1.23  # theoretical minimum for each step is 1.23 eV

    return {
        "dG1_OER": dG1,
        "dG2_OER": dG2,
        "dG3_OER": dG3,
        "dG4_OER": dG4,
        "overpotential_V": eta_OER,
        "rate_determining_step": ["Step 1", "Step 2", "Step 3", "Step 4"][
            [dG1, dG2, dG3, dG4].index(max_dG)
        ],
        "u_vs_rhe": u_vs_rhe,
        "ph": ph,
    }
