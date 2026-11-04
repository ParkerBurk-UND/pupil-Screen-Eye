"""Minimal one-camera pupil tracker.

This intentionally bypasses the full Pupil Capture application. It reads one
webcam or video source, runs the existing 2D pupil detector, and displays the
detected pupil position.
"""

import argparse
import json
import sys
from pathlib import Path

import cv2
from pupil_detectors import Detector2D, Roi


def parse_source(value: str):
    """Use a numeric camera index or a path to a video file."""
    try:
        return int(value)
    except ValueError:
        return value


def draw_detection(frame, result, confidence_threshold: float):
    """Draw the detector result and return its pixel/normalized coordinates."""
    confidence = float(result["confidence"])
    if confidence < confidence_threshold:
        cv2.putText(
            frame,
            f"No reliable pupil (confidence={confidence:.2f})",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2,
        )
        return None

    height, width = frame.shape[:2]
    center_x, center_y = result["ellipse"]["center"]
    axes_x, axes_y = result["ellipse"]["axes"]
    center = (round(center_x), round(center_y))
    axes = (max(1, round(axes_x / 2)), max(1, round(axes_y / 2)))

    cv2.ellipse(
        frame,
        center,
        axes,
        float(result["ellipse"]["angle"]),
        0,
        360,
        (0, 255, 0),
        2,
    )
    cv2.drawMarker(
        frame,
        center,
        (0, 0, 255),
        cv2.MARKER_CROSS,
        12,
        2,
    )

    # Match Pupil's normalized coordinate convention: x is left-to-right and
    # y is bottom-to-top.
    normalized_x = center_x / width
    normalized_y = 1.0 - center_y / height
    label = (
        f"pixel=({center_x:.1f}, {center_y:.1f})  "
        f"norm=({normalized_x:.3f}, {normalized_y:.3f})  "
        f"confidence={confidence:.2f}"
    )
    cv2.putText(
        frame,
        label,
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 255, 0),
        2,
    )
    return {
        "pixel_x": center_x,
        "pixel_y": center_y,
        "normalized_x": normalized_x,
        "normalized_y": normalized_y,
        "confidence": confidence,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        default="0",
        help="Camera index or video path (default: 0).",
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.6,
        help="Minimum confidence for drawing a pupil (default: 0.6).",
    )
    parser.add_argument(
        "--print-results",
        action="store_true",
        help="Print each reliable detection as one JSON object per line.",
    )
    parser.add_argument(
        "--no-display",
        action="store_true",
        help="Process frames without opening an OpenCV window.",
    )
    parser.add_argument(
        "--no-loop",
        action="store_true",
        help="Stop when a video file reaches its final frame.",
    )
    args = parser.parse_args()

    source = parse_source(args.source)
    if isinstance(source, str) and not Path(source).exists():
        print(f"Video file not found: {source}", file=sys.stderr)
        return 2

    capture = cv2.VideoCapture(source)
    if not capture.isOpened():
        print(f"Could not open camera/video source: {args.source}", file=sys.stderr)
        return 1

    detector = Detector2D()
    print("Press q or Escape to stop.")

    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                if isinstance(source, str) and not args.no_loop:
                    # Restart file sources so an uploaded/test video behaves
                    # like a looping GIF. Camera sources are never rewound.
                    capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            height, width = gray.shape[:2]
            result = detector.detect(
                gray_img=gray,
                roi=Roi(0, 0, width, height),
            )
            detection = draw_detection(frame, result, args.min_confidence)

            if args.print_results and detection is not None:
                print(json.dumps(detection), flush=True)

            if not args.no_display:
                cv2.imshow("Single-eye pupil tracker", frame)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), 27):
                    break
    finally:
        capture.release()
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
