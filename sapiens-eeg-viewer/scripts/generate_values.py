#!/usr/bin/env python3
"""Generate deterministic, time-varying test values for the N27 contacts."""

import csv
import math
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "values.csv"
ELECTRODES = ROOT / "data" / "electrodes.csv"


def main() -> None:
    rng = random.Random(27)
    with ELECTRODES.open(newline="", encoding="utf-8") as source:
        electrodes = list(csv.DictReader(source))

    with OUTPUT.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.writer(destination)
        writer.writerow(["Electrode", "Subject", "Project", "Time", "Signal"])
        for electrode in electrodes:
            number = int(electrode["Electrode"])
            phase = (number - 1) * math.pi / 5
            for step in range(100):
                time = step / 99
                signal = math.sin(2 * math.pi * time + phase) + rng.uniform(-0.1, 0.1)
                writer.writerow(
                    [number, electrode["Subject"], "Demo", f"{time:.6f}", f"{signal:.8f}"]
                )


if __name__ == "__main__":
    main()
