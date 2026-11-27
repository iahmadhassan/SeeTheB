#!/usr/bin/env python3
"""Export decimated N27 pial meshes as local OBJ assets."""

import argparse
import struct
from pathlib import Path

import numpy as np

try:
    import fast_simplification
except ImportError as error:
    raise SystemExit(
        "Mesh export requires fast-simplification; install with "
        "`python3 -m pip install fast-simplification`."
    ) from error


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_N27 = Path.home() / ".local/share/R/threeBrain/templates/N27"
OUTPUT = ROOT / "web/assets/brains"
TARGET_FACES = 55_000


def read_surface(path: Path) -> tuple[np.ndarray, np.ndarray]:
    with path.open("rb") as source:
        if source.read(3) != b"\xff\xff\xfe":
            raise ValueError(f"{path} is not a FreeSurfer triangular surface")
        source.readline()
        source.readline()
        counts = source.read(8)
        if len(counts) != 8:
            raise ValueError(f"{path} has a truncated vertex/face count")
        vertex_count, face_count = struct.unpack(">ii", counts)
        vertices = np.fromfile(source, dtype=">f4", count=vertex_count * 3)
        faces = np.fromfile(source, dtype=">i4", count=face_count * 3)
    if vertices.size != vertex_count * 3 or faces.size != face_count * 3:
        raise ValueError(f"{path} has truncated mesh data")
    return (
        vertices.astype(np.float32).reshape((-1, 3)),
        faces.astype(np.int32).reshape((-1, 3)),
    )


def decimate(vertices: np.ndarray, faces: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    simplified_vertices, simplified_faces = fast_simplification.simplify(
        vertices,
        faces,
        target_count=TARGET_FACES,
    )
    best = (simplified_vertices.astype(np.float32), simplified_faces.astype(np.int32))
    count = len(best[1])
    if not 40_000 <= count <= 60_000:
        raise RuntimeError(
            f"Decimation produced {count:,} faces; expected 40,000–60,000"
        )
    return best


def write_obj(path: Path, vertices: np.ndarray, faces: np.ndarray) -> None:
    # Rotate tkRAS into a Y-up scene while preserving handedness.
    scene_vertices = vertices[:, [0, 2, 1]].copy()
    scene_vertices[:, 2] *= -1
    with path.open("w", encoding="ascii", newline="\n") as output:
        output.write("# N27 pial mesh; FreeSurfer tkRAS, transformed to Y-up\n")
        for x, y, z in scene_vertices:
            output.write(f"v {x:.4f} {y:.4f} {z:.4f}\n")
        for a, b, c in faces + 1:
            output.write(f"f {a} {b} {c}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n27", type=Path, default=DEFAULT_N27)
    args = parser.parse_args()
    if not args.n27.is_dir():
        raise FileNotFoundError(f"N27 template directory not found: {args.n27}")
    OUTPUT.mkdir(parents=True, exist_ok=True)

    for hemisphere in ("lh", "rh"):
        source = args.n27 / "surf" / f"{hemisphere}.pial"
        vertices, faces = read_surface(source)
        reduced_vertices, reduced_faces = decimate(vertices, faces)
        destination = OUTPUT / f"{hemisphere}-pial.obj"
        write_obj(destination, reduced_vertices, reduced_faces)
        print(
            f"{hemisphere}: {len(vertices):,} vertices / {len(faces):,} faces -> "
            f"{len(reduced_vertices):,} vertices / {len(reduced_faces):,} faces "
            f"({destination})"
        )


if __name__ == "__main__":
    main()
