#!/usr/bin/env python3
"""Generate repeatable illustrative EEG samples and threeBrain value tables."""

import csv
import json
import math
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ELECTRODES_FILE = DATA / "electrodes.csv"
SIGNALS_FILE = DATA / "signals.json"
EVENTS_FILE = DATA / "events.json"
VALUES_FILE = DATA / "values.csv"

SEED = 20261127
SAMPLE_RATE = 250
DURATION = 20
SAMPLE_COUNT = SAMPLE_RATE * DURATION
CHANNELS = [
    "Fp1", "Fp2", "F3", "Fz", "F4", "FC3", "FC4", "C3",
    "Cz", "C4", "CP3", "CP4", "P3", "Pz", "P4",
]

EVENTS = [
    {
        "start": 0.0,
        "end": 4.0,
        "label": "Rest",
        "caption": "Rest: posterior alpha and sensorimotor mu rhythms are at baseline.",
    },
    {
        "start": 4.0,
        "end": 8.0,
        "label": "Left-hand imagery",
        "caption": "Left-hand imagery: mu rhythm weakens over the right motor cortex (C4).",
    },
    {
        "start": 8.0,
        "end": 10.0,
        "label": "Rest",
        "caption": "Rest: sensorimotor rhythms return toward their baseline level.",
    },
    {
        "start": 10.0,
        "end": 14.0,
        "label": "Right-hand imagery",
        "caption": "Right-hand imagery: mu rhythm weakens over the left motor cortex (C3).",
    },
    {
        "start": 14.0,
        "end": 15.0,
        "label": "Eye blink",
        "caption": "Eye blink: a large slow frontal deflection appears at Fp1 and Fp2.",
    },
    {
        "start": 15.0,
        "end": 16.0,
        "label": "Recovery",
        "caption": "Recovery: the blink deflection subsides and the background continues.",
    },
    {
        "start": 16.0,
        "end": 17.0,
        "label": "Muscle artifact",
        "caption": "Muscle artifact: a brief high-frequency burst appears on frontal channels.",
    },
    {
        "start": 17.0,
        "end": 20.0,
        "label": "Rest",
        "caption": "Rest: the illustrative EEG returns to its resting rhythm before looping.",
    },
]


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def standard_deviation(values: list[float]) -> float:
    average = mean(values)
    return math.sqrt(sum((value - average) ** 2 for value in values) / len(values))


def pink_noise(rng: random.Random, count: int, rows: int = 16) -> list[float]:
    """Voss-McCartney pink noise, normalized to unit standard deviation."""
    state = [rng.uniform(-1.0, 1.0) for _ in range(rows)]
    values = []
    for index in range(count):
        row = 0
        bit = index
        while bit & 1 == 0 and row < rows - 1:
            row += 1
            bit >>= 1
        state[row] = rng.uniform(-1.0, 1.0)
        values.append(sum(state))
    average = mean(values)
    scale = standard_deviation(values)
    return [(value - average) / scale for value in values]


def event_at(time_s: float) -> str:
    for event in EVENTS:
        if event["start"] <= time_s < event["end"]:
            return event["label"]
    raise ValueError(f"No event covers time {time_s}")


def band_power(
    samples: list[float],
    center: int,
    sample_rate: int,
    window_size: int = SAMPLE_RATE,
) -> float:
    """Estimate 8–12 Hz power using Hann-windowed sinusoidal projections."""
    half = window_size // 2
    window = [0.5 - 0.5 * math.cos(2.0 * math.pi * i / (window_size - 1))
              for i in range(window_size)]
    weighted = [
        samples[(center - half + i) % len(samples)] * window[i]
        for i in range(window_size)
    ]
    window_sum = sum(window)
    amplitudes = []
    for frequency in range(8, 13):
        real = 0.0
        imaginary = 0.0
        for i, value in enumerate(weighted):
            phase = 2.0 * math.pi * frequency * i / sample_rate
            real += value * math.cos(phase)
            imaginary -= value * math.sin(phase)
        amplitudes.append(2.0 * math.hypot(real, imaginary) / window_sum)
    return sum(amplitude * amplitude for amplitude in amplitudes) / len(amplitudes)


def window_rms(samples: list[float], center: int, size: int = SAMPLE_RATE // 2) -> float:
    half = size // 2
    window = [samples[(center - half + i) % len(samples)] for i in range(size)]
    return math.sqrt(sum(value * value for value in window) / size)


def generate_signals(rng: random.Random) -> dict[str, list[float]]:
    signals = {}
    frontal = {"Fp1", "Fp2", "F3", "F4"}
    motor = {"C3", "C4"}
    posterior = {"P3", "Pz", "P4"}
    frontal_muscle = {"Fp1", "Fp2", "F3", "F4", "FC3", "FC4"}

    for channel_index, channel in enumerate(CHANNELS):
        noise = pink_noise(rng, SAMPLE_COUNT)
        alpha_amplitude = 20.0 if channel in posterior else 2.0
        mu_amplitude = 17.0 if channel in motor else (5.0 if channel in {"FC3", "FC4", "CP3", "CP4"} else 1.5)
        alpha_phase = rng.uniform(0.0, 2.0 * math.pi)
        mu_phase = rng.uniform(0.0, 2.0 * math.pi)
        mu_frequency = 10.0 + (channel_index % 3)
        muscle_frequency = rng.uniform(36.0, 76.0)
        samples = []

        for index in range(SAMPLE_COUNT):
            time_s = index / SAMPLE_RATE
            event = event_at(time_s)
            mu_scale = 1.0
            if channel == "C4" and event == "Left-hand imagery":
                mu_scale = 0.30
            elif channel == "C3" and event == "Right-hand imagery":
                mu_scale = 0.30

            value = (
                alpha_amplitude * math.sin(2.0 * math.pi * 10.0 * time_s + alpha_phase)
                + mu_amplitude * mu_scale
                * math.sin(2.0 * math.pi * mu_frequency * time_s + mu_phase)
                + 3.0 * noise[index]
            )

            if event == "Eye blink":
                blink = math.exp(-0.5 * ((time_s - 14.5) / 0.115) ** 2)
                if channel in {"Fp1", "Fp2"}:
                    value += 125.0 * blink
                elif channel in frontal:
                    value += 42.0 * blink
                else:
                    value += 1.0 * blink

            if event == "Muscle artifact" and channel in frontal_muscle:
                envelope = math.sin(math.pi * (time_s - 16.0))
                value += envelope * (
                    24.0 * math.sin(2.0 * math.pi * muscle_frequency * time_s)
                    + 12.0 * rng.uniform(-1.0, 1.0)
                )

            samples.append(value)
        signals[channel] = samples

    return signals


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    with ELECTRODES_FILE.open(newline="", encoding="utf-8") as source:
        electrode_rows = list(csv.DictReader(source))
    if [row["Label"] for row in electrode_rows] != CHANNELS:
        raise ValueError("electrodes.csv must contain the 15 expected channels in order")

    rng = random.Random(SEED)
    signals = generate_signals(rng)
    signal_payload = {
        "channels": CHANNELS,
        "sampling_rate_hz": SAMPLE_RATE,
        "duration_s": DURATION,
        "units": "microvolts",
        "seed": SEED,
        "samples": {
            channel: [round(value, 4) for value in values]
            for channel, values in signals.items()
        },
    }
    SIGNALS_FILE.write_text(
        json.dumps(signal_payload, separators=(",", ":"), ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    EVENTS_FILE.write_text(
        json.dumps(EVENTS, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    time_points = [step / 10.0 for step in range(DURATION * 10)]
    baseline_centers = [
        round(time_s * SAMPLE_RATE)
        for time_s in time_points
        if 0.5 <= time_s <= 3.5
    ]
    baseline_power = {
        channel: mean([
            band_power(signals[channel], center, SAMPLE_RATE)
            for center in baseline_centers
        ])
        for channel in CHANNELS
    }

    with VALUES_FILE.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.writer(destination, lineterminator="\n")
        writer.writerow(["Electrode", "Subject", "Project", "Time", "ERD_percent", "RMS_uV"])
        for step, time_s in enumerate(time_points):
            center = round(time_s * SAMPLE_RATE)
            for row, channel in zip(electrode_rows, CHANNELS):
                power = band_power(signals[channel], center, SAMPLE_RATE)
                baseline = baseline_power[channel]
                erd_percent = 100.0 * (power - baseline) / baseline
                rms = window_rms(signals[channel], center)
                writer.writerow([
                    int(row["Electrode"]),
                    row["Subject"],
                    "Illustrative",
                    f"{time_s:.1f}",
                    f"{erd_percent:.4f}",
                    f"{rms:.4f}",
                ])

    print(f"Wrote {SAMPLE_COUNT} samples/channel at {SAMPLE_RATE} Hz for {len(CHANNELS)} channels.")
    print(f"Wrote {len(EVENTS)} event intervals and {len(time_points) * len(CHANNELS)} viewer-value rows.")
    for time_s in (2.0, 6.0, 12.0, 14.5):
        event = event_at(time_s)
        active = {
            channel: next(
                row for row in csv.DictReader(VALUES_FILE.open(newline="", encoding="utf-8"))
                if row["Electrode"] == str(CHANNELS.index(channel) + 1)
                and float(row["Time"]) == time_s
            )
            for channel in ("C3", "C4", "Fp1", "Fp2")
        }
        print(
            f"{time_s:>4.1f}s {event}: "
            + ", ".join(
                f"{channel} ERD={row['ERD_percent']}% RMS={row['RMS_uV']}uV"
                for channel, row in active.items()
            )
        )


if __name__ == "__main__":
    main()
