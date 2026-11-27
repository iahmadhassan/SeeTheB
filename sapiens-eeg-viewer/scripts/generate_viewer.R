args <- commandArgs(trailingOnly = FALSE)
script_arg <- sub("^--file=", "", args[grepl("^--file=", args)][1])
project_dir <- normalizePath(file.path(dirname(script_arg), ".."))

library(threeBrain)

n27_path <- file.path(default_template_directory(), "N27")
electrode_file <- file.path(project_dir, "data", "electrodes.csv")
values_file <- file.path(project_dir, "data", "values.csv")
if (!dir.exists(n27_path)) {
  stop("N27 template directory is missing: ", n27_path)
}
if (!file.exists(electrode_file) || !file.exists(values_file)) {
  stop("Generate data/electrodes.csv and data/values.csv before building the viewer.")
}

x <- threeBrain(path = n27_path, subject_code = "N27", surface_types = "pial")
x$set_electrodes(electrodes = electrode_file, priority = "sphere")
x$set_electrode_values(table_or_path = values_file)

widget <- plot(
  x,
  side_canvas = FALSE,
  control_display = FALSE,
  controllers = list(
    "Display Data" = "ERD_percent",
    "Surface Color" = "sync from electrodes",
    "Map Electrodes" = FALSE,
    "Surface Mapping" = "no mapping",
    "Volume Mapping" = "no mapping",
    "Visibility" = "all visible",
    "Text Visibility" = TRUE,
    "Text Scale" = 2,
    "Show Legend" = FALSE,
    "Show Time" = FALSE
  )
)
viewer_path <- file.path(project_dir, "public", "viewer.html")
save_brain(widget = widget, path = viewer_path, title = "Illustrative N27 EEG viewer")
message("Saved standalone viewer: ", viewer_path)
