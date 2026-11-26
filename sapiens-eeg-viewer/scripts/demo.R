args <- commandArgs(trailingOnly = FALSE)
script_arg <- sub("^--file=", "", args[grepl("^--file=", args)][1])
project_dir <- normalizePath(file.path(dirname(script_arg), ".."))

library(threeBrain)

n27_path <- file.path(default_template_directory(), "N27")
if (!dir.exists(n27_path)) {
  stop("N27 template directory is missing: ", n27_path)
}

x <- threeBrain(path = n27_path, subject_code = "N27", surface_types = "pial")
x$set_electrodes(electrodes = file.path(project_dir, "data", "electrodes.csv"))
x$set_electrode_values(table_or_path = file.path(project_dir, "data", "values.csv"))

widget <- plot(
  x,
  controllers = list(
    "Display Data" = "Signal",
    "Surface Color" = "sync from electrodes"
  )
)
viewer_path <- file.path(project_dir, "public", "viewer.html")
save_brain(widget = widget, path = viewer_path, title = "N27 test viewer")
message("Saved standalone viewer: ", viewer_path)
