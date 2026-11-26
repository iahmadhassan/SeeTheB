args <- commandArgs(trailingOnly = FALSE)
script_arg <- sub("^--file=", "", args[grepl("^--file=", args)][1])
project_dir <- normalizePath(file.path(dirname(script_arg), ".."))

library(threeBrain)
library(freesurferformats)

n27_path <- file.path(default_template_directory(), "N27")
if (!dir.exists(n27_path)) {
  stop("N27 template directory is missing: ", n27_path)
}

brain <- threeBrain(n27_path, "N27", surface_types = "pial")
lut <- freesurfer_lut$get_map()$map

region_id <- function(label) {
  matches <- names(lut)[vapply(lut, function(item) identical(item$Label, label), logical(1))]
  if (length(matches) != 1L) {
    stop("Expected exactly one FreeSurfer LUT label for ", label, "; got ", length(matches))
  }
  as.integer(matches)
}

volume <- read.fs.mgh(file.path(n27_path, "mri", "aparc+aseg.mgz"))
vertex_labels <- function(mesh) {
  voxels <- t(solve(brain$Torig) %*% rbind(t(mesh$vertices), 1))
  voxels <- round(voxels[, 1:3, drop = FALSE])
  dims <- dim(volume)
  inside <- rowSums(voxels < 0 | sweep(voxels, 2, dims[1:3], ">=")) == 0
  result <- rep(NA_integer_, nrow(voxels))
  index <- cbind(voxels[inside, , drop = FALSE] + 1L, rep(1L, sum(inside)))
  result[inside] <- volume[index]
  result
}

meshes <- lapply(c("lh", "rh"), function(hemi) {
  mesh <- read.fs.surface(file.path(n27_path, "surf", paste0(hemi, ".pial")))
  list(
    vertices = mesh$vertices,
    labels = vertex_labels(mesh),
    hemisphere = if (hemi == "lh") "left" else "right"
  )
})

spec <- data.frame(
  Label = c("Fp1", "Fp2", "F3", "Fz", "F4", "FC3", "FC4",
            "C3", "Cz", "C4", "CP3", "CP4", "P3", "Pz", "P4"),
  region = c("frontalpole", "frontalpole", "rostralmiddlefrontal",
             "superiorfrontal", "rostralmiddlefrontal",
             "caudalmiddlefrontal", "caudalmiddlefrontal",
             "precentral", "paracentral", "precentral",
             "postcentral", "postcentral",
             "superiorparietal", "precuneus", "superiorparietal"),
  side = c("left", "right", "left", "midline", "right",
           "left", "right", "left", "midline", "right",
           "left", "right", "left", "midline", "right"),
  stringsAsFactors = FALSE
)

select_vertex <- function(region, side) {
  candidate_rows <- lapply(meshes, function(mesh) {
    id <- region_id(paste0("ctx-", if (mesh$hemisphere == "left") "lh" else "rh", "-", region))
    vertex_indices <- which(mesh$labels == id)
    vertices <- mesh$vertices[vertex_indices, , drop = FALSE]
    data.frame(
      x = vertices[, 1],
      y = vertices[, 2],
      z = vertices[, 3],
      hemisphere = mesh$hemisphere,
      vertex_index = vertex_indices
    )
  })
  candidates <- do.call(rbind, candidate_rows)
  if (!nrow(candidates)) {
    stop("No N27 pial vertices map to aparc+aseg region: ", region)
  }
  if (side == "left") {
    candidates <- candidates[candidates$hemisphere == "left", , drop = FALSE]
  } else if (side == "right") {
    candidates <- candidates[candidates$hemisphere == "right", , drop = FALSE]
  }
  if (!nrow(candidates)) {
    stop("No candidate vertices in requested hemisphere for ", region, " (", side, ")")
  }

  target <- c(mean(candidates$x), mean(candidates$y), mean(candidates$z))
  if (side == "midline") {
    target[1] <- 0
  }
  distance <- (candidates$x - target[1])^2 +
    (candidates$y - target[2])^2 +
    (candidates$z - target[3])^2
  candidates[which.min(distance), , drop = FALSE]
}

coordinates <- do.call(rbind, lapply(seq_len(nrow(spec)), function(i) {
  point <- select_vertex(spec$region[i], spec$side[i])
  data.frame(
    Electrode = as.integer(i),
    Subject = "N27",
    Coord_x = point$x,
    Coord_y = point$y,
    Coord_z = point$z,
    Label = spec$Label[i],
    LabelPrefix = spec$Label[i],
    SurfaceElectrode = FALSE,
    SurfaceType = "pial",
    Radius = 5,
    VertexNumber = -1L,
    DistanceShifted = 3,
    Hemisphere = point$hemisphere
  )
}))

mni305 <- brain$electrodes$apply_transform_points(
  as.matrix(coordinates[c("Coord_x", "Coord_y", "Coord_z")]),
  from = "tkrRAS",
  to = "MNI305"
)
coordinates$MNI305_x <- mni305[, 1]
coordinates$MNI305_y <- mni305[, 2]
coordinates$MNI305_z <- mni305[, 3]

output <- file.path(project_dir, "data", "electrodes.csv")
write.csv(coordinates, output, row.names = FALSE, quote = TRUE)
cat("Wrote", nrow(coordinates), "N27 aparc+aseg-derived cortical contacts to", output, "\n")
print(coordinates, row.names = FALSE)
