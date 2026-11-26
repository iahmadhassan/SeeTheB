# N27 template and coordinates

- `Coord_x`, `Coord_y`, and `Coord_z` are FreeSurfer `tkRAS` coordinates in
  millimetres, per the threeBrain electrode documentation.
- The five test coordinates and labels are the first five contacts in the
  official threeBrain sample electrode table. All five loaded and appeared at
  plausible posterior-lateral cortical locations on the N27 pial surface in
  the viewer; this is a demo check, not clinical localization.
- Sources:
  - [threeBrain electrode documentation](https://dipterix.org/threeBrain/)
  - [threeBrain sample electrode table](https://raw.githubusercontent.com/dipterix/threeBrain-sample/master/vignettes/electrodes.csv)
- The package's default template directory is returned by
  `threeBrain::default_template_directory()`; the expected subject folder is
  `N27`.
