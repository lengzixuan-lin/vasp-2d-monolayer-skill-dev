# Task 006 Verification Summary

## Goal

Resolve the VASPKIT optical task-number ambiguity for the actual `lilin` environment before future optical workflow implementation review.

## Result

The installed server version is:

- `/home/lilin/software/vaspkit.1.3.1/bin/vaspkit`
- `VASPKIT Standard Edition 1.3.1 (03 Dec. 2021)`

Verified task mapping:

- `710`: 2D optical spectra for low-dimensional/monolayer semiconductor workflows.
- `711`: bulk semiconductor optical spectra.

For monolayer optical post-processing, future docs and code should use `vaspkit -task 710`, not `711`.

## Inputs and Outputs

Task `710` requires at least `POSCAR`; the bundled `optical_2D` example also documents optional extraction of `REAL.in` and `IMAG.in` from `vasprun.xml`.

Expected 2D output files include:

- `ABSORPTION_2D.dat`
- `REFLECTION_2D.dat`
- `TRANSMISSION_2D.dat`
- `REAL_OPTICAL_CONDUCTIVITY_2D.dat`
- `IMAG_OPTICAL_CONDUCTIVITY_2D.dat`

## Safety Boundary

- Server inspection performed: yes, after explicit user authorization in the current conversation.
- Server commands were inspection-only.
- No `sbatch`.
- No VASP run.
- No server dry-run.
- No remote writes, deletes, overwrites, moves, or sync.
- No real calculation task edits.
- No `scripts/remote-workflow/**` implementation edits.

## Recommendation

Future optical workflow review should:

- keep VASP `LOPTICS` as the raw response step;
- use `vaspkit -task 710` as the verified VASPKIT conversion step for 2D optical spectra;
- label `711` as a bulk-only path and reject it for monolayer optical absorption summaries;
- record `POSCAR`, `vasprun.xml` or `REAL.in`/`IMAG.in`, `LOPTICS`, `NBANDS`, and generated `*_2D.dat` files in result provenance.
