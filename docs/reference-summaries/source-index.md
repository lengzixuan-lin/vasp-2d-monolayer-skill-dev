# Source Index

This index records the local sources reviewed for task_003 and why raw source materials remain excluded from Git.

| Source path | Category | File type | Summarized | Git status / exclusion reason |
|---|---|---:|---|---|
| `vasp_references资料/vaspkit/vaspkit_readme.md` | VASPKIT tutorial/manual | Markdown | yes | Summary only committed; source remains local. |
| `vasp_references资料/vaspkit/0b8519a4-d1a1-42ff-be37-5fad1ff8927a_origin.pdf` | VASPKIT original PDF | PDF | indirectly via Markdown | Excluded: raw PDF and large third-party material. |
| `vasp_references资料/vaspkit/images/` | VASPKIT extracted figures | image folder | no | Excluded: extracted images are large and not needed for text review. |
| `vasp_references资料/vaspkit/*content_list*.json`, `*_model.json`, `block_list.json`, `layout.json` | VASPKIT parser/cache output | JSON | no | Excluded: generated extraction/cache files. |
| `vasp_references资料/JAMIP/JAMIP-V1.0.1.Manual-Chs.pdf-b1938462-d000-4f32-804a-ffd5d1b44a05/JAMIP.md` | JAMIP manual | Markdown | yes | Summary only committed; source remains local. |
| `vasp_references资料/JAMIP/JAMIP-V1.0.1.Manual-Chs.pdf-b1938462-d000-4f32-804a-ffd5d1b44a05/e20b3115-f4f6-4abf-bf42-d613d06b30a3_origin.pdf` | JAMIP original PDF | PDF | indirectly via Markdown | Excluded: raw PDF and large third-party material. |
| `vasp_references资料/JAMIP/JAMIP-V1.0.1.Manual-Chs.pdf-b1938462-d000-4f32-804a-ffd5d1b44a05/images/` | JAMIP extracted figures | image folder | no | Excluded: extracted images are large and not needed for text review. |
| `vasp_references资料/JAMIP/JAMIP-V1.0.1.Manual-Chs.pdf-b1938462-d000-4f32-804a-ffd5d1b44a05/*content_list*.json`, `*_model.json`, `block_list.json`, `layout.json`, `origin_file.html` | JAMIP parser/cache output | JSON/HTML | no | Excluded: generated extraction/cache artifacts. |
| `vasp_references资料/JAMIP/jamip-1.0.2/README` | JAMIP package overview | text | yes | Summary only committed; source tree remains local. |
| `vasp_references资料/JAMIP/jamip-1.0.2/jamip/abtools/vasp/tasks.py` | JAMIP VASP task model | Python source | yes | Source tree excluded; design patterns summarized. |
| `vasp_references资料/JAMIP/jamip-1.0.2/jamip/abtools/vasp/setvasp.py` | JAMIP VASP input generation | Python source | yes | Source tree excluded; design patterns summarized. |
| `vasp_references资料/JAMIP/jamip-1.0.2/jamip/abtools/vasp/vaspflow.py` | JAMIP VASP workflow orchestration | Python source | yes | Source tree excluded; design patterns summarized. |
| `vasp_references资料/JAMIP/jamip-1.0.2/jamip/abtools/vasp/check.py` | JAMIP VASP status checking | Python source | yes | Source tree excluded; design patterns summarized. |
| `vasp_references资料/JAMIP/jamip-1.0.2/jamip/abtools/vasp/errorkey.py` | JAMIP VASP error-key map | Python source | yes | Source tree excluded; design patterns summarized. |
| `vasp_references资料/JAMIP/jamip-1.0.2/jamip/abtools/vasp/vaspio.py` | JAMIP VASP input/output writing | Python source | yes | Source tree excluded; design patterns summarized. |
| `vasp_references资料/JAMIP/jamip-1.0.2/jamip/compute/cluster.py` | JAMIP scheduler script generation | Python source | yes | Source tree excluded; design patterns summarized. |
| `vasp_references资料/JAMIP/jamip-1.0.2/jamip/compute/launch.py` | JAMIP task submission loop | Python source | yes | Source tree excluded; design patterns summarized. |
| `vasp_references资料/JAMIP/jamip-1.0.2/jamip/compute/manager.py` | JAMIP queue manager and continuation | Python source | yes | Source tree excluded; design patterns summarized. |
| `vasp_references资料/JAMIP/jamip-1.0.2/jamip/compute/pool.py` | JAMIP task pool state | Python source | yes | Source tree excluded; design patterns summarized. |
| `vasp_references资料/JAMIP/jamip-1.0.2/jamip/compute/queues.py` | JAMIP priority subtask queue | Python source | yes | Source tree excluded; design patterns summarized. |
| `vasp_references资料/JAMIP/jamip-1.0.2/jamip/analysis/vasp/band.py` | VASP band/effective-mass parsing | Python source | yes | Source tree excluded; design patterns summarized. |
| `vasp_references资料/JAMIP/jamip-1.0.2/jamip/analysis/vasp/dos.py` | VASP DOS parsing | Python source | yes | Source tree excluded; design patterns summarized. |
| `vasp_references资料/JAMIP/jamip-1.0.2/jamip/analysis/vasp/optics.py` | VASP optical parsing | Python source | partially | Source tree excluded; design patterns summarized at a high level. |
| `vasp_references资料/JAMIP/jamip-1.0.2/jamip/analysis/vasp/outcar.py` | OUTCAR parameter parsing | Python source | yes | Source tree excluded; design patterns summarized. |

## Exclusion Rule

Only these curated Markdown summaries are intended for Git. If future work needs raw files, use a separate user-approved upload/storage method rather than adding them to this repository.
