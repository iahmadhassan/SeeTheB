# Sapiens EEG demo

Illustrative N27 / threeBrain demonstration. These are simulated signals, not
human recordings or clinical data. Contacts are placed at the cortex for
clarity; real EEG electrodes sit on the scalp.

## Rebuild and run

Run from the repository root, in this order:

```sh
~/.local/bin/micromamba run -p "$HOME/.local/share/sapiens-eeg-viewer/r-env" \
  Rscript sapiens-eeg-viewer/scripts/make_electrodes.R
python3 sapiens-eeg-viewer/scripts/make_data.py
~/.local/bin/micromamba run -p "$HOME/.local/share/sapiens-eeg-viewer/r-env" \
  Rscript sapiens-eeg-viewer/scripts/generate_viewer.R
sapiens-eeg-viewer/scripts/serve.sh
```

Open <http://127.0.0.1:8000/web/>. The server serves `web/`, `public/`, and
`data/` from one origin, allowing the page to read the viewer's Time field.
`PORT` can override the default server port.

Environment used: Fedora Linux 44, R 4.4.3, threeBrain 1.2.0. The R environment
and N27 template were installed previously; the template is located at
`~/.local/share/R/threeBrain/templates/N27`.

## Electrode placement and coordinate provenance

The requested direct transformation of MNE's standard montage to N27 was not
used: a documented MNE-head-to-N27 transform could not be verified. The
permitted anatomical fallback in [`scripts/make_electrodes.R`](scripts/make_electrodes.R)
uses the N27 template's `mri/aparc+aseg.mgz` labels and `surf/lh.pial` /
`surf/rh.pial` meshes. It chooses the pial vertex nearest the centroid of the
named FreeSurfer aparc region for each electrode's hemisphere; midline sites
target x=0. The region assignments are frontalpole, rostralmiddlefrontal,
superiorfrontal, caudalmiddlefrontal, precentral, paracentral, postcentral,
superiorparietal, and precuneus. These are illustrative anatomical locations,
not standard 10-20 cortical projections or clinical localization.

`Coord_x`, `Coord_y`, and `Coord_z` are FreeSurfer tkRAS coordinates in
millimetres, matching the package sample table's coordinate convention.
Additional MNI305 columns are transformed from those tkRAS positions with
threeBrain's `apply_transform_points(from = "tkrRAS", to = "MNI305")`.

The N27 template supplies full-resolution FreeSurfer pial meshes, but not the
`Standard 141` vertex data that threeBrain's surface-electrode mapping expects.
Calling `calculate_template_coordinates()` for surface electrodes failed with
the exact error `argument is not a matrix`. The demo therefore keeps contact
geometry at the selected pial coordinates rather than claiming that a
standard-141 surface projection succeeded. Although the standalone viewer is
configured for `Surface Color = sync from electrodes` and `Map Electrodes`,
the N27 surface did not visibly change color with the generated values; this
is a known blocker (see the test results).

## Generated data and synchronization

[`scripts/make_data.py`](scripts/make_data.py) uses seed `20261127` to write
15 channels at 250 Hz for 20 seconds (5000 samples per channel), plus event
captions and 10-Hz viewer values. `ERD_percent` is the change in 8–12 Hz power
relative to the rest baseline; `RMS_uV` is the 0.5-second-window RMS. The
illustrative left-hand imagery reduces C4 mu power; right-hand imagery reduces
C3 mu power; the blink peaks at Fp1/Fp2.

[`scripts/generate_viewer.R`](scripts/generate_viewer.R) loads the electrode
table and calls `set_electrode_values(table_or_path = ...)`, selects
`ERD_percent`, enables electrode mapping, and saves the standalone
[`public/viewer.html`](public/viewer.html). The page's tested sync mode is
same-origin control: it reads and writes the viewer's Time field and toggles
its Play/Pause checkbox through the iframe DOM.

Play was measured over two complete loops: the first wrap occurred at 20.54 s
wall time and the second at 40.60 s. This is approximately 1.00 viewer-second
per wall-clock second at the default speed.

## Test results

| Test | Result | Evidence |
|---|---|---|
| E1. HTTP(S) blocked except localhost; page, iframe, and traces render offline | PASS | No external requests and no browser console errors. [`web/screenshots/offline-render.png`](web/screenshots/offline-render.png) |
| E2. Four requested timepoints, captions, and expected value behavior | FAIL | Captions and traces match at t=2, 6, 12, and 14.5 s; C4 ERD is -97.0208% at t=6, C3 ERD is -84.3473% at t=12, and Fp1 is 126.3 µV at t=14.5. The viewer's cortical surface/electrode colors did not visibly update, so this test is not a pass. Screenshots: [`t-02-rest.png`](web/screenshots/t-02-rest.png), [`t-06-left-imagery.png`](web/screenshots/t-06-left-imagery.png), [`t-12-right-imagery.png`](web/screenshots/t-12-right-imagery.png), [`t-145-eye-blink.png`](web/screenshots/t-145-eye-blink.png). |
| E3. Two complete playback loops | PASS | Play wrapped at 20.54 s and 40.60 s wall time. [`web/screenshots/two-cycle-loop.png`](web/screenshots/two-cycle-loop.png) |

The remaining blocker for E2 is a supported N27 surface-mapping path that
produces visible value-colored contacts or surface vertices. The data values,
captions, waveforms, same-origin time control, offline rendering, and looping
were verified independently.

Cite: Wang Z, Magnotti JF, Zhang X, Beauchamp MS. YAEL: your advanced electrode localizer. eNeuro 2023.
