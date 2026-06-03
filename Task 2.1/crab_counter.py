import os
from ultralytics import YOLO

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Colori ANSI ---
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

model = YOLO(os.path.join(BASE_DIR, "best.pt"))

# Testa su tutte le immagini nella cartella practice/
practice_dir = os.path.join(BASE_DIR, "practice")
images = sorted(f for f in os.listdir(practice_dir)
                if f.lower().endswith((".jpg", ".jpeg", ".png"))
                and not f.startswith("out_"))

print(f"\n{BOLD}{CYAN}{'═' * 52}{RESET}")
print(f"{BOLD}{CYAN}   🦀  Crab Detector — {len(images)} immagini{RESET}")
print(f"{BOLD}{CYAN}{'═' * 52}{RESET}\n")

for i, fname in enumerate(images, 1):
    img_path = os.path.join(practice_dir, fname)
    results = model(img_path, conf=0.5, verbose=False)

    # Conta per classe
    boxes = results[0].boxes
    names = results[0].names
    counts = {}
    for box in boxes:
        label = names[int(box.cls)]
        counts[label] = counts.get(label, 0) + 1

    # Salva immagine annotata
    out_path = os.path.join(practice_dir, f"out_{fname}")
    results[0].save(out_path)

    # Riga principale (il modello rileva solo green crab)
    invasive_count = counts.get("green", 0)
    print(f"  {BOLD}{WHITE}[{i}/{len(images)}] {fname}{RESET}")

    if invasive_count > 0:
        invasive_str = f"{CLASS_COLORS['green']}{invasive_count} green crab (invasive){RESET}"
    else:
        invasive_str = f"{DIM}nessun granchio invasivo{RESET}"
    print(f"        {invasive_str}")
    print(f"        {BOLD}{YELLOW}Invasivi: {invasive_count}{RESET}")
    print(f"        {DIM}→ {out_path}{RESET}")
    print()

print(f"{BOLD}{CYAN}{'═' * 52}{RESET}\n")
