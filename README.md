# Single-eye pupil tracker

This repository contains a minimal one-camera pupil tracker for the Screen Eye
project. It reads a webcam or eye video, detects the pupil with the Pupil Labs
2D detector, draws the detected ellipse, and reports the pupil position.

## Setup

Use Python 3.11, then create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run with a camera

```powershell
python single_eye_tracker.py
```

Press `q` or `Escape` to stop.

## Run with a video

Video files loop automatically:

```powershell
python single_eye_tracker.py --source "path\to\eye_video.mp4"
```

Use `--no-loop` to stop at the end of the video. Use `--print-results` to
print one JSON object for each reliable detection.

The detector reports pixel coordinates, normalized coordinates, and a
confidence score. The current default confidence threshold is `0.60`.

This is the pupil-localization stage only. Patient-specific calibration,
display mapping, smoothing, and prosthetic-eye rendering are separate stages.
