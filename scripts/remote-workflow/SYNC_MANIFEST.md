# Remote Workflow Sync Manifest

- Synced at: 2026-06-18 21:20:00 +08:00
- Remote host: lilin
- Remote root: `/home/lilin/calculation/1_dft/02_workflow`
- Local root: `C:\Users\11658\.codex\skills\vasp-2d-monolayer\scripts\remote-workflow`
- Uploaded archive: `/home/lilin/vasp2d_remote_workflow_20260618_163042.tgz`
- Remote staging dir: `/home/lilin/.tmp/vasp2d_sync_20260618_163042`
- Remote backup dir: `/home/lilin/calculation/1_dft/02_workflow_backup_code_20260618_163042`
- Included: `workflow.py`, `config/`, `modules/`, `templates/`, `submit/`, `collect/`, `tests/`
- Excluded: `projects/`, `__pycache__/`, `*.pyc`, calculation outputs
- Core file count: 35

## Local Changes Pending Remote Sync

As of 2026-06-19, the local mirror has additional effective-mass and
mobility workflow changes that have **not** been synced to `lilin`:

- `workflow.py`: use `11_effective_mass` as the effective-mass directory; depend on both `02_scf` and `03_pbeband`
- `modules/base.py`: add the `11_effective_mass` manager job, runtime local-kline generation, EIGENVAL parsing, curvature fitting, and quality checks
- `workflow.py`: recognize `12_mobility/results/mobility_summary.yaml` as the mobility manager completion interface
- `modules/base.py`: add the `12_mobility` deformation-potential manager, strain relax/SCF/edge subruns, LOCPOT vacuum alignment, `C2D`/`E1` fitting, and mobility summaries
- `config/precision_standard.yaml`: enable production 2D EM defaults
- `config/precision_standard.yaml`: enable production 2D mobility defaults
- `config/precision_quick.yaml`: add debug EM and mobility defaults while keeping quick EM/mobility disabled
- `templates/incar/incar_em.j2`: add `ISYM=0` and `LORBIT=11`

The remote SHA256 section below still records the last synced server state.

## Remote Verification

```text
cd /home/lilin/calculation/1_dft/02_workflow
python3 -m py_compile workflow.py modules/base.py submit/slurm.py  # PASS
python3 -m unittest discover -s tests                            # PASS, 20 tests
python3 workflow.py --help                                       # PASS
python3 workflow.py new --help                                   # PASS, shows --material-type
```

## Remote SHA256

```text
0c9204fb7eaf190015684eae470b0e807a23b7de6c3b93bc80e542717bbad53d  collect/__init__.py
8be27f47a2a0299dd81c00c165d41b2f5dbd0eece897f4970bd988f00224dc89  collect/outcar_parser.py
c5c13a79f4ac625c17608faed87b317f9c69080e5b3c9324ac11306ade837d7d  config/elements.yaml
345340f80cfa849344acd8effacc443c904736bbbde7309535729574feb86e55  config/precision_quick.yaml
11d30a597799b9ab354e32d566413b32b007279bfc93ddf18c805e5758f19fa8  config/precision_standard.yaml
db612e7da999d6240fa950466a24f36640e1c51c7d7d46eeba3aef40b7dc337d  config/settings.yaml
c1c444340fdcf2dd7a3f76943b18883a7c2218e2f53bc9904ea704615141459a  modules/adsorption.py
1c3e9e8b384c60c40113d2a91bbd75a2b34fea86821538a0bf76c0b24b8f8cd7  modules/base.py
18b5f4522dc5988328ce58b6fcbafe39c23a77cb8290efe68d93191db8977d66  modules/__init__.py
311a44eeef436c0e7393658497bd22fd5f4ce5a61ca8c7d3f53f56221c23b6fe  submit/__init__.py
4f9ba81d97216d470ea2defd9b80008a8c2cc2b61c6c342cadad45741205afbb  submit/slurm.py
b4d34d1726474d07bc504f2851a9aaac77675436f538576a31aeac9940da25aa  templates/incar/incar_aimd.j2
beb1e00cb11280a4d7db277dcd4adf094e3307c1a4dc0ad44c6b40f485b386d5  templates/incar/incar_bader.j2
c70a5c653b3b37ac51bf82255c05595b00ebf9c211ce72aeafb661cfc541feef  templates/incar/incar_band.j2
044f36668ec03f30662310e30dccd5fb1d99e82c83605d30593a883dfc0be956  templates/incar/incar_ccd.j2
4b8ded0d0d76fca97cfd2ce0b119654ce1e6d279d67617d19ea23c5fdda5bd33  templates/incar/incar_dos.j2
c2029b5576e6981d6e5c062889d75636538494eda6167c01fead89487f1be965  templates/incar/incar_em.j2
133a35aea8085991bc5bafb140e3f41769a121bc319927b70317fc8e7a297342  templates/incar/incar_hse_band.j2
2dcbd8f43e4d1bb51c642a9400644af4ce3b7baa05a1d88d907ba26b67fd5327  templates/incar/incar_hse.j2
3042b92ed5a31ee25c3a728ecfe858067f80bc772c4f6313140d7e5869dbb246  templates/incar/incar_hse_scf.j2
4b7106c0e49f2e273b76fae4d302842beb5bbaca797744726a1f9a569f7e17e2  templates/incar/incar_optical_hse.j2
f489bcb5615191ec312f25ed030f0678b2781b131512d80ab4ab8af2bb14ae50  templates/incar/incar_optical.j2
6992e822cd0f8e6ea56716aaf8bba9ea2eab30fcde22d2fe27a274704d068aca  templates/incar/incar_opt.j2
a216181b47d06db167744c69a676c66dfe10d49fd6119ff445fb6d856a9bf118  templates/incar/incar_phonopy.j2
b2d6e9e1fe9c504b7d3c49299707f417948d79a053e0d420ca181df849abd811  templates/incar/incar_phonopy_fd.j2
b07a9e4c4aaa25810ac8272d20c1c406360d7e63032c53cf03fc668d607f5ef9  templates/incar/incar_potential.j2
0e66e6b697f89ce779ffb254f6c2c817495202a5a2bb29332039a61e26a62128  templates/incar/incar_scf.j2
df8feff5062e8b28de120cac521e99274048efd5360829020e4f7e59df024c04  templates/incar/incar_soc.j2
f15957527e39deccf93e194fa4d982da341a378207fd2a5bcc5444d2535de566  templates/incar/incar_vacuum.j2
48a2f2ecb51d0fa300e637ed5a71159d935d7f477fafa6b7d145a79f5e0945fc  templates/kpoints.j2
497ad6c995666ad5ac159bd6e5c9cc79099a021c6c2cba431776715a88524d6c  templates/optcell.j2
4a0c7d3f9967f45edca1e5d4288fad7c60807d6aa23c8278f7545afb00ccc34e  templates/sub.j2
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  tests/__init__.py
70beacdae6dc147d7242e25b7d8d4e3753034e149fe403500a9a833573433d1e  tests/test_parameter_merge.py
3d3731cb97021b450d797e1bbd0c010d5ba16942e9705908af667de524f74f35  workflow.py
```

## Local SHA256

```text
0c9204fb7eaf190015684eae470b0e807a23b7de6c3b93bc80e542717bbad53d  collect/__init__.py
8be27f47a2a0299dd81c00c165d41b2f5dbd0eece897f4970bd988f00224dc89  collect/outcar_parser.py
c5c13a79f4ac625c17608faed87b317f9c69080e5b3c9324ac11306ade837d7d  config/elements.yaml
e3d6e2be8cd1d30e6b68e44f43387e3d3c37a600b8d5e1537fef5cf5b579c821  config/precision_quick.yaml
c1a7937121926f828205ae65932a7cdccde44a64c4072b8c45951a30fc441e31  config/precision_standard.yaml
db612e7da999d6240fa950466a24f36640e1c51c7d7d46eeba3aef40b7dc337d  config/settings.yaml
18b5f4522dc5988328ce58b6fcbafe39c23a77cb8290efe68d93191db8977d66  modules/__init__.py
c1c444340fdcf2dd7a3f76943b18883a7c2218e2f53bc9904ea704615141459a  modules/adsorption.py
ce28f707199198408db563886c3f39fc001e2387d34fe8f99dcc08bb3ad14a29  modules/base.py
311a44eeef436c0e7393658497bd22fd5f4ce5a61ca8c7d3f53f56221c23b6fe  submit/__init__.py
4f9ba81d97216d470ea2defd9b80008a8c2cc2b61c6c342cadad45741205afbb  submit/slurm.py
b4d34d1726474d07bc504f2851a9aaac77675436f538576a31aeac9940da25aa  templates/incar/incar_aimd.j2
beb1e00cb11280a4d7db277dcd4adf094e3307c1a4dc0ad44c6b40f485b386d5  templates/incar/incar_bader.j2
c70a5c653b3b37ac51bf82255c05595b00ebf9c211ce72aeafb661cfc541feef  templates/incar/incar_band.j2
044f36668ec03f30662310e30dccd5fb1d99e82c83605d30593a883dfc0be956  templates/incar/incar_ccd.j2
4b8ded0d0d76fca97cfd2ce0b119654ce1e6d279d67617d19ea23c5fdda5bd33  templates/incar/incar_dos.j2
d8fcf198b4fed35ff505002d6af5cfcbab55c6851e916b67def22679e126b9c4  templates/incar/incar_em.j2
2dcbd8f43e4d1bb51c642a9400644af4ce3b7baa05a1d88d907ba26b67fd5327  templates/incar/incar_hse.j2
133a35aea8085991bc5bafb140e3f41769a121bc319927b70317fc8e7a297342  templates/incar/incar_hse_band.j2
3042b92ed5a31ee25c3a728ecfe858067f80bc772c4f6313140d7e5869dbb246  templates/incar/incar_hse_scf.j2
6992e822cd0f8e6ea56716aaf8bba9ea2eab30fcde22d2fe27a274704d068aca  templates/incar/incar_opt.j2
f489bcb5615191ec312f25ed030f0678b2781b131512d80ab4ab8af2bb14ae50  templates/incar/incar_optical.j2
4b7106c0e49f2e273b76fae4d302842beb5bbaca797744726a1f9a569f7e17e2  templates/incar/incar_optical_hse.j2
a216181b47d06db167744c69a676c66dfe10d49fd6119ff445fb6d856a9bf118  templates/incar/incar_phonopy.j2
b2d6e9e1fe9c504b7d3c49299707f417948d79a053e0d420ca181df849abd811  templates/incar/incar_phonopy_fd.j2
b07a9e4c4aaa25810ac8272d20c1c406360d7e63032c53cf03fc668d607f5ef9  templates/incar/incar_potential.j2
0e66e6b697f89ce779ffb254f6c2c817495202a5a2bb29332039a61e26a62128  templates/incar/incar_scf.j2
df8feff5062e8b28de120cac521e99274048efd5360829020e4f7e59df024c04  templates/incar/incar_soc.j2
f15957527e39deccf93e194fa4d982da341a378207fd2a5bcc5444d2535de566  templates/incar/incar_vacuum.j2
48a2f2ecb51d0fa300e637ed5a71159d935d7f477fafa6b7d145a79f5e0945fc  templates/kpoints.j2
497ad6c995666ad5ac159bd6e5c9cc79099a021c6c2cba431776715a88524d6c  templates/optcell.j2
4a0c7d3f9967f45edca1e5d4288fad7c60807d6aa23c8278f7545afb00ccc34e  templates/sub.j2
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  tests/__init__.py
70beacdae6dc147d7242e25b7d8d4e3753034e149fe403500a9a833573433d1e  tests/test_parameter_merge.py
0d24835988e03e012d4ad83e51de8fdf230b64fa0144697d493305adc6c1e006  workflow.py
```
