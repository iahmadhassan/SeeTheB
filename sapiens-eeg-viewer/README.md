# Sapiens EEG demo

Illustrative N27 brain and simulated EEG signals, not human recordings or
clinical data. Electrodes are placed at the cortex for clarity; real EEG
electrodes sit on the scalp.

## Rebuild and run

Run these commands from the repository root, in order:

```sh
~/.local/bin/micromamba run -p "$HOME/.local/share/sapiens-eeg-viewer/r-env" \
  Rscript sapiens-eeg-viewer/scripts/make_electrodes.R
python3 sapiens-eeg-viewer/scripts/make_data.py
python3 -m pip install --target /tmp/seetheb-fast fast-simplification==0.2.0
PYTHONPATH=/tmp/seetheb-fast python3 sapiens-eeg-viewer/scripts/export_meshes.py
~/.local/bin/micromamba run -p "$HOME/.local/share/sapiens-eeg-viewer/r-env" \
  Rscript sapiens-eeg-viewer/scripts/generate_viewer.R
sapiens-eeg-viewer/scripts/serve.sh
```

Open <http://127.0.0.1:8000/web/>. The server hosts `web/`, `public/`, and
`data/` on one origin. Set `PORT` to use another port.

Environment: Fedora Linux 44, R 4.4.3, threeBrain 1.2.0, three.js 0.180.0.
The R environment and N27 template were installed previously; N27 is at
`~/.local/share/R/threeBrain/templates/N27`.

## Electrode placement

No verified transform from MNE's standard montage into N27 was available, so
the electrodes use the anatomical-placement fallback in
[`scripts/make_electrodes.R`](scripts/make_electrodes.R). For each assigned
FreeSurfer aparc region in `mri/aparc+aseg.mgz`, it selects the pial vertex
nearest that region's centroid; midline targets use tkRAS x=0. This is
schematic anatomical placement, not a standard 10-20 cortical projection.

Coordinates are FreeSurfer tkRAS, in millimetres, matching the threeBrain
sample-table convention. Each contact is offset 5 mm along its local outward
pial normal and has a 3 mm sphere radius. The script retains the original
pial coordinates in `Pial_x/y/z` and derives MNI305 columns with threeBrain's
`apply_transform_points(from = "tkrRAS", to = "MNI305")`.

Placement checks: C3 tkRAS x=-37.17 mm and C4 x=+37.25 mm; Fp1/Fp2 are
anterior, P3/Pz/P4 posterior, and Cz near the top midline. See the labelled
[`top`](web/screenshots/placement-top.png),
[`left`](web/screenshots/placement-left.png), and
[`right`](web/screenshots/placement-right.png) views.

## Renderer and data

The threeBrain N27 volume-electrode attempt (5 mm outward offset,
`SurfaceElectrode = FALSE`, `VertexNumber = -1`) did not show markers. The
surface-mapping call failed with `argument is not a matrix`; the N27 template
does not contain the expected Standard 141 vertex mapping. The custom scene is
therefore the primary visualization, and the standalone threeBrain viewer is
retained as an alternate tab.

[`scripts/export_meshes.py`](scripts/export_meshes.py) exports the N27
`lh.pial` and `rh.pial` meshes as local OBJ assets and decimates each to about
55,000 faces using `fast-simplification` 0.2.0. The bundled three.js renderer
loads these local meshes, draws a translucent cortex and 15 labelled spheres,
and maps negative ERD to blue and positive ERD to red, with a glow for stronger
values. No CDN is used.

[`scripts/make_data.py`](scripts/make_data.py) uses seed `20261127` to create
15 channels at 250 Hz for 20 seconds (5000 samples per channel), event
captions, and 10-Hz viewer values. `ERD_percent` is 8–12 Hz power change from
the rest baseline; `RMS_uV` is the 0.5-second-window RMS. Left-hand imagery
reduces C4 mu power, right-hand imagery reduces C3, and the blink peaks at
Fp1/Fp2.

The main scene follows the page's local Play/Pause and slider clock; waveform
traces, event captions, electrode values, and colours use that same time.
Selecting the threeBrain tab uses the documented same-origin iframe controls
for its Time field and Play/Pause checkbox. Two full local-clock loops took
42.36 seconds in the headless test (about 0.94 viewer-seconds per wall-second
under that load).

## Verification

| Test | Result | Evidence |
|---|---|---|
| E1. Offline page, viewer, traces; external HTTP(S) blocked except localhost | PASS | No external requests, console errors, or failed responses. [`offline-render.png`](web/screenshots/offline-render.png) |
| E2. Colours, captions, traces at 2, 6, 12, and 14.5 s | PASS | Custom scene: C4 ERD=-97.0208% at 6 s, C3 ERD=-84.3473% at 12 s, Fp1=126.3 µV at 14.5 s; expected captions and colour changes observed. [`t-2-rest.png`](web/screenshots/t-2-rest.png), [`t-6-left-hand-imagery.png`](web/screenshots/t-6-left-hand-imagery.png), [`t-12-right-hand-imagery.png`](web/screenshots/t-12-right-hand-imagery.png), [`t-145-eye-blink.png`](web/screenshots/t-145-eye-blink.png). |
| E3. Two full 20-second playback cycles | PASS | Both wraps observed; approximately 0.94 viewer-seconds per wall-second in the headless run. [`two-cycle-loop.png`](web/screenshots/two-cycle-loop.png). |
| Backup one-loop video | PASS (sampled) | [`demo.webm`](web/backup/demo.webm) shows the captured timeline from 0.3 to 19.4 s, encoded as a 20-second, 16-frame sequence; it is not a continuous full-frame-rate recording. |
| Placement and required presentation details | PASS | Labelled views above; ILLUSTRATIVE badge, scalp disclaimer, and YAEL/N27/threeBrain About content are present. |

Cite: Wang Z, Magnotti JF, Zhang X, Beauchamp MS. YAEL: your advanced electrode localizer. eNeuro 2023.
