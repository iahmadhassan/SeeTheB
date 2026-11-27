args <- commandArgs(trailingOnly = FALSE)
script_arg <- sub("^--file=", "", args[grepl("^--file=", args)][1])
project_dir <- normalizePath(file.path(dirname(script_arg), ".."))

library(freesurferformats)
library(threeBrain)

volume_path <- file.path(default_template_directory(), "N27", "mri", "brain.finalsurfs.mgz")
output_dir <- file.path(project_dir, "web", "assets", "mri")
volume_file <- file.path(output_dir, "N27-anatomy.raw")
metadata_file <- file.path(project_dir, "data", "mri-volume.json")

if (!file.exists(volume_path)) {
  stop("N27 anatomical MRI volume is missing: ", volume_path)
}

volume <- read.fs.mgh(volume_path, with_header = TRUE)
anatomy <- volume$data[, , , 1]
dimensions <- dim(anatomy)
vox2tkr <- mghheader.vox2ras.tkreg(volume$header)
positive_intensities <- anatomy[anatomy > 0]
upper_intensity <- unname(stats::quantile(positive_intensities, 0.99, na.rm = TRUE))
if (!is.finite(upper_intensity) || upper_intensity <= 2) {
  stop("N27 anatomical MRI volume has no usable positive intensities.")
}

normalized <- as.raw(round(255 * pmax(0, pmin(1, (as.vector(anatomy) - 2) / (upper_intensity - 2)))))
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
connection <- file(volume_file, open = "wb")
writeBin(normalized, connection)
close(connection)

metadata <- list(
  src = "assets/mri/N27-anatomy.raw",
  dimensions = as.list(dimensions),
  tkras_to_voxel = lapply(seq_len(4), function(row) as.list(solve(vox2tkr)[row, ])),
  display_bounds = list(horizontal = c(32, 224), vertical = c(32, 224)),
  sweep_ranges_tkras_mm = list(
    axial = c(-70, 70),
    coronal = c(-65, 65),
    sagittal = c(-60, 60)
  ),
  source = "N27/mri/brain.finalsurfs.mgz",
  space = "FreeSurfer tkRAS, millimetres"
)
jsonlite::write_json(metadata, metadata_file, auto_unbox = TRUE, pretty = TRUE)
message("Saved the N27 anatomical MRI volume and scan metadata: ", metadata_file)
