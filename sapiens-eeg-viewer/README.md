# Sapiens EEG viewer — threeBrain setup

Setup/demo only; the final application page has not been built. The project is
under `sapiens-eeg-viewer/`; `web/` is reserved and empty.

## Environment and commands

Fedora Linux 44, R 4.4.3, threeBrain 1.2.0. System `R` was initially missing and
system installation required a sudo password, so a user-local micromamba
environment was used. Run these from the repository root, in order:

```sh
MAMBA_ROOT_PREFIX=/tmp/micromamba-root ~/.local/bin/micromamba create -y \
  -p "$HOME/.local/share/sapiens-eeg-viewer/r-env" \
  -c conda-forge r-base=4.4 r-threebrain

~/.local/bin/micromamba run -p "$HOME/.local/share/sapiens-eeg-viewer/r-env" R --version
~/.local/bin/micromamba run -p "$HOME/.local/share/sapiens-eeg-viewer/r-env" \
  Rscript sapiens-eeg-viewer/scripts/setup.R

python3 sapiens-eeg-viewer/scripts/generate_values.py
~/.local/bin/micromamba run -p "$HOME/.local/share/sapiens-eeg-viewer/r-env" \
  Rscript sapiens-eeg-viewer/scripts/demo.R
```

`scripts/setup.R` uses `brain_setup(show_example = FALSE)` so the noninteractive
script exits after setup. The requested default `brain_setup()` call was also
run; it opened the browser viewer and kept its local server alive until stopped.
N27 was downloaded to
`/home/ahmadhassan/.local/share/R/threeBrain/templates/N27`, and the package
reported that the subject passed its check. The initial CRAN source install
attempt and its errors are retained in `data/r-install.log`.

The demo data contains five N27 contacts and 100 time points per contact
(500 value rows), with deterministic sine-plus-noise `Signal` values.
Coordinates are FreeSurfer `tkRAS`, in millimetres. See
[`data/N27-notes.md`](data/N27-notes.md) for provenance. In the installed API,
`set_electrode_values()` takes `table_or_path` (not `electrodes`); the script
uses the installed method's formal argument.

## Verification

| Step | Result | Evidence |
|---|---|---|
| 4. Open N27 brain | PASS | N27 setup viewer rendered the brain and MRI in the browser. |
| 5. Test electrodes | PASS | Five documented sample contacts loaded and appeared on the pial surface. |
| 6. Time-varying values | PASS | `Signal` loaded; Play/Pause advanced Time from 0.000 to 0.805 in about 1.8 seconds. |
| 7. Surface colouring | PASS | With the pointer over the brain, `k` cycles Surface Color to `sync from electrodes`; mapped values were displayed. |
| 8. Standalone/offline | PASS | [`public/viewer.html`](public/viewer.html) opened from disk with HTTP(S) requests blocked; no external requests were made. |

The standalone is one approximately 24 MB HTML file. It opens with `Signal`
selected and Surface Color set to `sync from electrodes`. The Data
Visualization panel also exposes the Time field and Play/Pause checkbox.

## External JavaScript control research

The package documents a local WebSocket hub in
[viewer_hub](https://dipterix.org/threeBrain/reference/viewer_hub.html) and
[its protocol/examples](https://github.com/dipterix/threeBrain/blob/master/examples/WebSocket/README.md).
The page must connect to the hub from its control panel. The documented
commands include `focused_electrode` (select a subject/electrode),
`display_data` (select a variable), and `set_electrode_data` (supply values).
The generic `controllers` command sets panel settings, but the documentation
does not give a specific external payload for setting Time or Play/Pause; those
external operations are therefore unconfirmed. In-page Time and Play/Pause
were verified.

Cite: Wang Z, Magnotti JF, Zhang X, Beauchamp MS. YAEL: your advanced electrode localizer. eNeuro 2023.
