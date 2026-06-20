#!/usr/bin/env python3
"""
OutcarParser — comprehensive OUTCAR parsing for all physical quantities.
Extracts: energy, forces, stress, band gap, Fermi level, etc.
"""

import re
import numpy as np


class OutcarParser:
    """Parse VASP OUTCAR files and extract key results."""

    def __init__(self, outcar_path):
        self.path = outcar_path
        self._content = None
        self._lines = None

    @property
    def content(self):
        if self._content is None:
            with open(self.path, 'r', errors='ignore') as f:
                self._content = f.read()
        return self._content

    @property
    def lines(self):
        if self._lines is None:
            self._lines = self.content.split('\n')
        return self._lines

    # ---- Energy ----

    def get_total_energy(self):
        """Extract final free energy TOTEN (eV)."""
        pattern = r"free\s+energy\s+TOTEN\s*=\s*([\d\.\-E\+\s]+)"
        matches = re.findall(pattern, self.content)
        if matches:
            return float(matches[-1].strip().split()[0])
        return None

    def get_energy_without_entropy(self):
        """Extract energy(sigma->0) (eV)."""
        pattern = r"energy\s+without\s+entropy\s*=\s*([\d\.\-\+E]+)"
        matches = re.findall(pattern, self.content)
        if matches:
            return float(matches[-1].strip())
        return None

    def get_energy_zero(self):
        """Extract energy at T=0, aka E0 (eV)."""
        pattern = r"energy\(sigma->0\)\s*=\s*([\d\.\-\+E]+)"
        matches = re.findall(pattern, self.content)
        if matches:
            return float(matches[-1].strip())
        return None

    def get_fermi_level(self):
        """Extract Fermi level E-fermi (eV)."""
        pattern = r"E-fermi\s*:\s*([\d\.\-]+)"
        matches = re.findall(pattern, self.content)
        if matches:
            return float(matches[-1])
        return None

    # ---- Ionic convergence ----

    def has_converged(self):
        """Check if ionic relaxation reached required accuracy."""
        return "reached required accuracy" in self.content

    def get_n_ionic_steps(self):
        """Count number of ionic steps completed."""
        return len(re.findall(r"free\s+energy\s+TOTEN", self.content))

    def get_final_forces(self):
        """Extract forces on atoms at the final step (eV/A)."""
        # Find the last TOTAL-FORCE block
        blocks = self.content.split("TOTAL-FORCE")
        if len(blocks) < 2:
            return None
        last_block = blocks[-1]
        lines = last_block.strip().split('\n')
        forces = []
        in_forces = False
        for line in lines:
            if "----" in line:
                if in_forces:
                    break
                in_forces = True
                continue
            if in_forces and line.strip():
                parts = line.strip().split()
                if len(parts) >= 6:
                    try:
                        forces.append([float(x) for x in parts[3:6]])
                    except ValueError:
                        break
        return np.array(forces) if forces else None

    def get_max_force(self):
        """Get maximum force component at final step (eV/A)."""
        forces = self.get_final_forces()
        if forces is not None and len(forces) > 0:
            return float(np.max(np.abs(forces)))
        return None

    # ---- Stress ----

    def get_stress(self):
        """Extract final stress tensor (kB)."""
        blocks = self.content.split("FORCE on cell")
        if len(blocks) < 2:
            # Try alternative: "in kB"
            pattern = r"in kB[\s\S]{0,500}?Total\s+([\d\.\-\s]+)"
            match = re.search(pattern, self.content)
            if match:
                vals = match.group(1).strip().split()
                return np.array([float(v) for v in vals])
            return None

        last_block = blocks[-1]
        # Find stress in kB section
        pattern = r"Total\s+([\-\d\.\s]+)"
        match = re.search(pattern, last_block)
        if match:
            vals = match.group(1).strip().split()
            return np.array([float(v) for v in vals])
        return None

    # ---- Band structure ----

    def get_band_gap(self):
        """
        Extract band gap from OUTCAR header line.
        VASP prints: ' band gap  X.XXXX  eV' near material start.
        Returns (vbm, cbm, gap, is_direct).
        """
        lines = self.lines
        # VASP band gap near start of OUTCAR (spin-degenerate case)
        for line in lines[:100]:
            if "gap" in line.lower() and "eV" in line:
                # e.g. "band gap     0.0000  eV"
                pass

        # Look for the detailed band gap section
        in_band_section = False
        vbm_energy = None
        cbm_energy = None
        vbm_kpt = None
        cbm_kpt = None

        for i, line in enumerate(lines):
            if "band No." in line and "band energies" in line:
                in_band_section = True
                continue
            if "Fermi energy" in line and in_band_section:
                # We've reached the end of the band listing
                # Extract VBM/CBM from context
                break

        # Simpler approach: grep for the band-gap line near end
        for line in reversed(lines):
            if "band gap" in line.lower():
                try:
                    parts = line.strip().split()
                    gap = float(parts[-2])
                    return gap
                except (ValueError, IndexError):
                    pass

        return None

    def get_vbm_cbm(self):
        """
        Extract VBM and CBM energies from OUTCAR.
        Looks for the highest occupied and lowest unoccupied band energies
        at gamma or any k-point.
        """
        vbm = None
        cbm = None
        efermi = self.get_fermi_level()

        # Parse band energies at each k-point
        # Format: k-point  X : Y Y Y  weight = Z
        #   band No.  band energies     occupation
        #   1        -10.0000      1.00000
        band_data = []
        current_kpt = None
        current_bands = []

        for line in self.lines:
            if "k-point" in line and "weight" in line:
                if current_bands:
                    band_data.append((current_kpt, current_bands))
                current_bands = []
                continue
            if current_bands is not None:
                parts = line.strip().split()
                if len(parts) >= 3 and parts[0].isdigit():
                    band_idx = int(parts[0])
                    energy = float(parts[1])
                    occ = float(parts[2])
                    current_bands.append((band_idx, energy, occ))
                elif ("band" in line.lower() and "No." in line):
                    continue  # skip header
                elif "spin" in line.lower():
                    continue  # spin component header
                elif line.strip() == "":
                    continue
                else:
                    # End of band listing
                    if current_bands:
                        band_data.append((current_kpt, current_bands))
                    current_bands = None

        if not band_data:
            return None, None

        # Find highest occupied and lowest unoccupied across all k-points
        all_energies = []
        for kpt, bands in band_data:
            for idx, energy, occ in bands:
                all_energies.append((energy, occ))

        occupied = [(e, o) for e, o in all_energies if o > 0.5]
        unoccupied = [(e, o) for e, o in all_energies if o < 0.5]

        if occupied:
            vbm = max(occupied, key=lambda x: x[0])[0]
        if unoccupied:
            cbm = min(unoccupied, key=lambda x: x[0])[0]

        return vbm, cbm

    def get_kpoints_info(self):
        """Extract number of k-points and irreducible k-points."""
        pattern = r"Found\s+(\d+)\s+irreducible\s+k-points"
        match = re.search(pattern, self.content)
        n_irr = int(match.group(1)) if match else None

        pattern2 = r"generate\s+(\d+)\s+k-points"
        match2 = re.search(pattern2, self.content)
        n_total = int(match2.group(1)) if match2 else None

        return n_total, n_irr

    # ---- SCF convergence ----

    def get_scf_history(self, last_n_steps=None):
        """
        Get total energy and dE at each electronic step for the last
        ionic step.
        Returns list of (scf_step, energy, dE) tuples.
        """
        # Find the last ionic step's SCF section
        blocks = self.content.split("FREE ENERGIE OF THE ION-ELECTRON")
        if len(blocks) < 2:
            return []

        # The LAST iteration
        last = blocks[-1]
        history = []
        for line in last.split('\n'):
            if "DAV:" in line or "RMM:" in line:
                parts = line.strip().split()
                if len(parts) >= 5:
                    try:
                        step = int(parts[1])
                        energy = float(parts[2])
                        dE = float(parts[3])
                        history.append((step, energy, dE))
                    except (ValueError, IndexError):
                        pass
        return history

    def get_ionic_convergence_history(self):
        """
        Get energy and max force at each ionic step.
        Returns list of (step, energy, max_force) tuples.
        """
        history = []

        # Split by ionic step markers
        energy_pattern = r"free\s+energy\s+TOTEN\s*=\s*([\d\.\-\+E\s]+)"
        energies = [float(m.strip().split()[0])
                    for m in re.findall(energy_pattern, self.content)]

        # Get max forces from TOTAL-FORCE sections
        force_blocks = self.content.split("TOTAL-FORCE")[1:]
        max_forces = []
        for block in force_blocks:
            lines = block.strip().split('\n')
            force_vals = []
            for line in lines[2:]:  # skip header
                parts = line.strip().split()
                if len(parts) >= 6:
                    try:
                        fx, fy, fz = float(parts[3]), float(
                            parts[4]), float(parts[5])
                        force_vals.append(
                            np.sqrt(fx**2 + fy**2 + fz**2))
                    except ValueError:
                        break
            if force_vals:
                max_forces.append(max(force_vals))

        for i in range(min(len(energies), len(max_forces))):
            history.append((i + 1, energies[i], max_forces[i]))

        return history

    # ---- Volume / cell ----

    def get_cell_volume(self):
        """Extract final cell volume (A^3)."""
        pattern = r"volume of cell\s*:\s*([\d\.]+)"
        matches = re.findall(pattern, self.content)
        if matches:
            return float(matches[-1])
        return None

    def get_lattice_vectors(self):
        """Extract final lattice vectors (A)."""
        # Find "direct lattice vectors" section
        pattern = (
            r"direct lattice vectors[\s\S]{0,200}?"
            r"([\d\.\-\s]+)\n\s*([\d\.\-\s]+)\n\s*([\d\.\-\s]+)"
        )
        match = re.search(pattern, self.content)
        if match:
            a1 = np.array([float(x) for x in match.group(1).split()])
            a2 = np.array([float(x) for x in match.group(2).split()])
            a3 = np.array([float(x) for x in match.group(3).split()])
            return a1, a2, a3
        return None

    # ---- Performance info ----

    def get_elapsed_time(self):
        """Extract total elapsed time (seconds)."""
        pattern = r"Total CPU time used \(sec\):\s*([\d\.]+)"
        match = re.search(pattern, self.content)
        if match:
            return float(match.group(1))
        return None

    def get_ncores(self):
        """Extract number of cores used."""
        pattern = r"running on\s+(\d+)\s+total cores"
        match = re.search(pattern, self.content)
        if match:
            return int(match.group(1))
        return None

    # ---- Bader ----

    def get_bader_charges(self, acf_path=None):
        """
        Parse Bader ACF.dat file for atomic charges.
        If acf_path is not given, assumes ACF.dat is in the same directory.
        """
        import os
        if acf_path is None:
            acf_path = os.path.join(os.path.dirname(self.path), "ACF.dat")
        if not os.path.exists(acf_path):
            return None

        charges = []
        with open(acf_path, 'r') as f:
            lines = f.readlines()
        # Skip header lines
        in_data = False
        for line in lines:
            if "----" in line:
                in_data = True
                continue
            if in_data and line.strip():
                parts = line.strip().split()
                if len(parts) >= 5:
                    try:
                        atom_idx = int(parts[0])
                        x, y, z = float(parts[1]), float(
                            parts[2]), float(parts[3])
                        charge = float(parts[4])
                        charges.append({
                            "atom": atom_idx,
                            "x": x, "y": y, "z": z,
                            "charge": charge,
                        })
                    except (ValueError, IndexError):
                        break
        return charges

    # ---- Summary ----

    def summary(self):
        """Return a dict with all extractable results."""
        return {
            "total_energy_eV": self.get_total_energy(),
            "energy_without_entropy_eV": self.get_energy_without_entropy(),
            "fermi_level_eV": self.get_fermi_level(),
            "converged": self.has_converged(),
            "n_ionic_steps": self.get_n_ionic_steps(),
            "max_force_eV_A": self.get_max_force(),
            "cell_volume_A3": self.get_cell_volume(),
            "band_gap_eV": self.get_band_gap(),
            "cpu_time_sec": self.get_elapsed_time(),
        }
