import os

import cv2
from ultralytics import YOLO

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Colori ANSI (solo per l'output CLI) ---
RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
WHITE  = "\033[97m"
DIM    = "\033[2m"

CLASS_COLORS = {
    "green": "\033[92m",   # verde brillante
}

# The trained model only needs to be loaded once. It is loaded lazily so that
# importing this module (e.g. from a server) is cheap and side-effect free.
_model = None


def get_model():
    global _model
    if _model is None:
        _model = YOLO(os.path.join(BASE_DIR, "best.pt"))
    return _model


def analyze(image_path, output_dir, conf=0.5, equations_path=None):
    """Detect and count invasive European Green crabs in a single image.

    Runs YOLOv8 inference, draws bounding boxes around green crabs and prints
    the total count onto the annotated image (the competition requires the
    count shown on screen). Native Rock/Jonah crabs are not boxed nor counted.

    Args:
        image_path: image to analyse.
        output_dir: folder where the annotated image is written.
        conf: minimum detection confidence (default 0.5).
        equations_path: unused; kept for a uniform analyze() signature across tasks.

    Returns:
        dict with keys:
          ok (bool), green_count (int), total_detections (int),
          annotated_path (str|None), error (str|None)
    """
    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(image_path))[0]
    annotated_path = os.path.join(output_dir, f"{base_name}_annotated.jpg")

    result = {
        "ok": False,
        "green_count": 0,
        "total_detections": 0,
        "annotated_path": None,
        "error": None,
    }

    image = cv2.imread(image_path)
    if image is None:
        result["error"] = "image_unreadable"
        return result

    model = get_model()
    results = model(image_path, conf=conf, verbose=False)

    boxes = results[0].boxes
    names = results[0].names

    counts = {}
    for box in boxes:
        label = names[int(box.cls)]
        counts[label] = counts.get(label, 0) + 1

    green_count = counts.get("green", 0)

    # YOLO draws the boxes/labels; we add a large green-crab counter on top so
    # the judge can read the number directly off the displayed image.
    annotated = results[0].plot()
    cv2.putText(
        annotated,
        f"Green crabs: {green_count}",
        (20, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.2,
        (0, 200, 0),
        3,
        cv2.LINE_AA,
    )
    cv2.imwrite(annotated_path, annotated)

    result["ok"] = True
    result["green_count"] = green_count
    result["total_detections"] = int(len(boxes))
    result["annotated_path"] = annotated_path
    return result


# Esecuzione CLI: elabora tutte le immagini in practice/ (solo da __main__)
def _run_cli():
    practice_dir = os.path.join(BASE_DIR, "practice")
    images = sorted(f for f in os.listdir(practice_dir)
                    if f.lower().endswith((".jpg", ".jpeg", ".png"))
                    and not f.startswith("out_"))

    print(f"\n{BOLD}{CYAN}{'═' * 52}{RESET}")
    print(f"{BOLD}{CYAN}   🦀  Crab Detector — {len(images)} immagini{RESET}")
    print(f"{BOLD}{CYAN}{'═' * 52}{RESET}\n")

    for i, fname in enumerate(images, 1):
        img_path = os.path.join(practice_dir, fname)
        res = analyze(img_path, practice_dir)
        invasive_count = res["green_count"]

        # Match the original out_<name> naming for the CLI workflow.
        os.replace(
            res["annotated_path"],
            os.path.join(practice_dir, f"out_{fname}"),
        )

        print(f"  {BOLD}{WHITE}[{i}/{len(images)}] {fname}{RESET}")
        if invasive_count > 0:
            invasive_str = f"{CLASS_COLORS['green']}{invasive_count} green crab (invasive){RESET}"
        else:
            invasive_str = f"{DIM}nessun granchio invasivo{RESET}"
        print(f"        {invasive_str}")
        print(f"        {BOLD}{YELLOW}Invasivi: {invasive_count}{RESET}")
        print()

    print(f"{BOLD}{CYAN}{'═' * 52}{RESET}\n")


if __name__ == "__main__":
    _run_cli()
