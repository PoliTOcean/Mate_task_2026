import os
import sys

import cv2
import numpy as np

# Permette di importare i moduli fratelli (model_3d, frame) anche quando final.py
# viene caricato da un'altra CWD (es. da NEXUS via importlib), non solo da CLI.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def aggiorna_equazioni_cad(lunghezza_cm, altezza_cm, file_txt_path="equations.txt"):
    try:
        # !!!!!!!!!!!!!!
        # NEL TESTO DI EQUATIONS.TXT C'è lunghezza_1, lunghezza_2, lunghezza_3 (per il cad)
        # adesso sto passando lunghezza e altezza
        testo_equazioni = (
            f'"lunghezza" = {lunghezza_cm:.1f}\n'
            f'"altezza" = {altezza_cm:.1f}\n'
        )

        with open(file_txt_path, "w", encoding="utf-8") as file:
            file.write(testo_equazioni)

        print(f"--- FASE 4: ESPORTAZIONE CAD ---")
        print(f"File '{file_txt_path}' aggiornato con successo!")
        print(f"Nuovi dati inviati al CAD -> Lunghezza: {lunghezza_cm:.1f}, Altezza: {altezza_cm:.1f}\n")

    except Exception as e:
        print(f"Errore durante la scrittura del file delle equazioni: {e}")


def analyze(image_path, output_dir=".", equations_path=None,
            pixels_per_cm=None, write_equations=True):
    """Analizza una singola immagine del coral garden e ritorna le misure.

    Pipeline:
      Fase 1 - righello arancione -> scala pixel/cm
      Fase 2 - target colorati (non-blu, 4-6 lati) -> conteggio + POSIZIONE + colore
      Fase 3 - tubi PVC bianchi -> bounding box -> lunghezza/altezza in cm

    A differenza della vecchia versione GUI, questa funzione NON apre finestre
    (niente cv2.imshow/waitKey): scrive l'immagine annotata su disco e ritorna
    un dict strutturato, così è richiamabile da un server.

    Args:
        image_path: percorso dell'immagine da analizzare.
        output_dir: cartella dove scrivere l'immagine annotata.
        equations_path: percorso del file equations.txt (default: <output_dir>/equations.txt).
        pixels_per_cm: scala nota da usare quando il righello arancione non e'
            presente nell'immagine (es. la foto del RETRO ha un righello
            trasparente). Se fornita, la Fase 1 viene saltata. In tal caso la
            scala viene riutilizzata dal lato che il righello ce l'ha (il fronte).
        write_equations: se True scrive equations.txt (fallback SolidWorks).
            L'orchestratore lo scrive una volta sola, quindi puo' disattivarlo.

    Returns:
        dict con chiavi:
          ok (bool), length_cm (float|None), height_cm (float|None),
          targets_count (int), annotated_path (str|None), error (str|None),
          pixels_per_cm (float|None),
          targets (list di dict: x_cm, y_cm, w_cm, h_cm, color_bgr)
            posizione del centro del target rispetto allo spigolo
            in-basso-a-sinistra del bounding box PVC del lato (Y verso l'alto).
    """
    os.makedirs(output_dir, exist_ok=True)
    if equations_path is None:
        equations_path = os.path.join(output_dir, "equations.txt")

    base_name = os.path.splitext(os.path.basename(image_path))[0]
    annotated_path = os.path.join(output_dir, f"{base_name}_annotated.jpg")

    result = {
        "ok": False,
        "length_cm": None,
        "height_cm": None,
        "targets_count": 0,
        "annotated_path": None,
        "error": None,
        "pixels_per_cm": None,
        "targets": [],
    }

    img = cv2.imread(image_path)
    if img is None:
        print(f"Errore: Impossibile caricare {image_path}")
        result["error"] = "image_unreadable"
        return result

    output_img = img.copy()

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    kernel = np.ones((5, 5), np.uint8)

    # =========================================================================
    # FASE 1: RILEVAMENTO RIGHELLO ARANCIONE (Calcolo Scala)
    # =========================================================================
    # Il bounding box del righello serve anche per escluderlo dalle fasi 2/3.
    # Quando la scala e' passata dall'esterno (foto del RETRO con righello
    # trasparente) saltiamo la detection: nessuna area da escludere.
    LUNGHEZZA_RIGHELLO_CM = 50.0
    x_r = y_r = w_r = h_r = 0

    if pixels_per_cm is None:
        lower_orange = np.array([5, 150, 150])
        upper_orange = np.array([25, 255, 255])

        ruler_mask = cv2.inRange(hsv, lower_orange, upper_orange)
        ruler_contours, _ = cv2.findContours(ruler_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if len(ruler_contours) == 0:
            print("Errore: Righello arancione non trovato. Impossibile calcolare i cm reali.")
            print("        (Per il lato col righello trasparente, passare pixels_per_cm.)")
            result["error"] = "ruler_not_found"
            return result

        best_ruler = max(ruler_contours, key=cv2.contourArea)
        x_r, y_r, w_r, h_r = cv2.boundingRect(best_ruler)

        ruler_length_pixels = w_r if w_r > h_r else h_r
        pixels_per_cm = ruler_length_pixels / LUNGHEZZA_RIGHELLO_CM

        print(f"--- FASE 1: CALCOLO SCALA ---")
        print(f"Righello Arancione: {ruler_length_pixels} pixel = 50 cm")
        print(f"1 cm = {pixels_per_cm:.2f} pixel\n")

        cv2.rectangle(output_img, (x_r, y_r), (x_r + w_r, y_r + h_r), (0, 255, 255), 2)
        cv2.putText(output_img, "RIGHELLO 50cm", (x_r, y_r - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
    else:
        print(f"--- FASE 1: SCALA FORNITA DALL'ESTERNO ---")
        print(f"1 cm = {pixels_per_cm:.2f} pixel (righello non rilevato in questa foto)\n")

    result["pixels_per_cm"] = pixels_per_cm
    has_ruler = (w_r > 0 and h_r > 0)

    # =========================================================================
    # FASE 2: RILEVAMENTO TARGET UNIVERSALE (Qualsiasi Colore, NO BLU)
    # =========================================================================
    lower_vibrant = np.array([0, 60, 50])
    upper_vibrant = np.array([180, 255, 255])
    vibrant_mask = cv2.inRange(hsv, lower_vibrant, upper_vibrant)

    lower_blue = np.array([85, 40, 40])
    upper_blue = np.array([135, 255, 255])
    blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)

    # colori accesi - acqua
    target_mask = cv2.bitwise_and(vibrant_mask, cv2.bitwise_not(blue_mask))

    # Escludiamo il righello dall'analisi dei target
    target_mask[y_r:y_r + h_r, x_r:x_r + w_r] = 0

    target_mask = cv2.morphologyEx(target_mask, cv2.MORPH_CLOSE, kernel)
    target_mask = cv2.morphologyEx(target_mask, cv2.MORPH_OPEN, kernel)

    target_contours, _ = cv2.findContours(target_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    print(f"--- FASE 2: DETECT TARGET UNIVERSALI ---")
    target_count = 0
    # Dati grezzi in pixel; convertiti in cm dopo la Fase 3 (serve il box PVC).
    raw_targets = []  # (cX, cY, w_px, h_px, color_bgr)

    for cnt in target_contours:
        if cv2.contourArea(cnt) < 100:
            continue

        epsilon = 0.04 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)

        if 4 <= len(approx) <= 6:
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
            else:
                continue

            x_b, y_b, w_b, h_b = cv2.boundingRect(cnt)

            # Colore medio reale del target (dentro la sua bounding box, solo i
            # pixel del target) -> servira' a colorare il quadrato nel 3D.
            cell_mask = np.zeros(target_mask.shape, np.uint8)
            cv2.drawContours(cell_mask, [cnt], -1, 255, -1)
            mean_bgr = cv2.mean(img, mask=cell_mask)[:3]
            color_bgr = tuple(int(c) for c in mean_bgr)

            target_count += 1
            raw_targets.append((cX, cY, w_b, h_b, color_bgr))
            print(f"Target #{target_count} Rilevato -> Centro: X={cX}, Y={cY}, "
                  f"colore BGR={color_bgr}")

            # Disegna i contorni dei target trovati
            cv2.drawContours(output_img, [approx], -1, (0, 255, 0), 2)
            cv2.circle(output_img, (cX, cY), 5, (0, 0, 255), -1)
            cv2.putText(output_img, f"T:{target_count}", (cX - 15, cY - 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    print(f"Totale target identificati sul campo: {target_count}\n")
    result["targets_count"] = target_count

    # =========================================================================
    # FASE 3: MISURAZIONE INGOMBRO MASSIMO STRUTTURA (Tubi Bianchi)
    # =========================================================================
    lower_white = np.array([0, 0, 180])
    upper_white = np.array([180, 50, 255])
    pvc_mask = cv2.inRange(hsv, lower_white, upper_white)

    # Escludiamo il righello anche dai tubi
    pvc_mask[y_r:y_r + h_r, x_r:x_r + w_r] = 0

    pvc_mask = cv2.morphologyEx(pvc_mask, cv2.MORPH_CLOSE, kernel)
    pvc_mask = cv2.morphologyEx(pvc_mask, cv2.MORPH_OPEN, kernel)

    # Pulizia: tieni solo i componenti "da tubo", scartando il rumore bianco del
    # fondo (telo/riflessi: blob piccoli) e le etichette/cartellini (blob quadrati
    # molto pieni). Cosi' il bounding box non viene gonfiato da bianchi spuri.
    n_lab, labels, stats, _ = cv2.connectedComponentsWithStats(pvc_mask)
    if n_lab > 1:
        areas = stats[1:, cv2.CC_STAT_AREA]
        min_area = max(60, int(0.0004 * pvc_mask.shape[0] * pvc_mask.shape[1]))
        clean = np.zeros_like(pvc_mask)
        for i in range(1, n_lab):
            x, y, w_c, h_c, area = stats[i]
            if area < min_area:
                continue  # rumore del fondo
            fill = area / float(w_c * h_c + 1e-9)
            aspect = max(w_c, h_c) / float(min(w_c, h_c) + 1e-9)
            # etichetta = rettangolo piccolo, quasi pieno e poco allungato
            is_label = fill > 0.80 and aspect < 2.2 and max(w_c, h_c) < 0.18 * max(pvc_mask.shape)
            if is_label:
                continue
            clean[labels == i] = 255
        if cv2.countNonZero(clean) > 0:
            pvc_mask = clean

    punti_pvc = cv2.findNonZero(pvc_mask)

    print(f"--- FASE 3: MISURE STRUTTURA PVC ---")
    if punti_pvc is None:
        print("Errore: Impossibile isolare la struttura in PVC dei tubi.")
        result["error"] = "pvc_not_found"
        # Salviamo comunque l'immagine annotata (righello + target) per debug.
        cv2.imwrite(annotated_path, output_img)
        result["annotated_path"] = annotated_path
        return result

    x_t, y_t, w_t, h_t = cv2.boundingRect(punti_pvc)

    lunghezza_tubi_cm = w_t / pixels_per_cm
    altezza_tubi_cm = h_t / pixels_per_cm

    print(f"LUNGHEZZA TOTALE STRUTTURA: {lunghezza_tubi_cm:.1f} cm")
    print(f"ALTEZZA TOTALE STRUTTURA: {altezza_tubi_cm:.1f} cm")

    # Esporta la maschera PVC e il suo bounding box: servono a VALIDARE i tubi
    # del telaio predefinito contro i pixel bianchi reali (vedi frame.validate_
    # frame), cosi' teniamo solo i tubi che esistono davvero in questa foto.
    result["pvc_mask"] = pvc_mask
    result["pvc_bbox"] = (x_t, y_t, w_t, h_t)

    # Converte le posizioni dei target in cm reali, rispetto allo spigolo
    # in-basso-a-sinistra del box PVC. Y e' rivolta verso l'alto (origine in
    # basso) cosi' l'alto della struttura nella foto e' l'alto nel modello 3D.
    targets_cm = []
    for cX, cY, w_px, h_px, color_bgr in raw_targets:
        targets_cm.append({
            "x_cm": (cX - x_t) / pixels_per_cm,
            "y_cm": (y_t + h_t - cY) / pixels_per_cm,
            "w_cm": w_px / pixels_per_cm,
            "h_cm": h_px / pixels_per_cm,
            "color_bgr": color_bgr,
        })
    result["targets"] = targets_cm

    if write_equations:
        aggiorna_equazioni_cad(lunghezza_tubi_cm, altezza_tubi_cm, equations_path)

    # Disegna il Box Verde dell'ingombro reale richiesto dal regolamento
    cv2.rectangle(output_img, (x_t, y_t), (x_t + w_t, y_t + h_t), (0, 255, 0), 3)

    # Scrive i dati finali per i giudici sulla Ground Station
    cv2.putText(output_img, f"LUNGHEZZA REALE: {lunghezza_tubi_cm:.1f} cm", (40, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(output_img, f"ALTEZZA REALE: {altezza_tubi_cm:.1f} cm", (40, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)

    cv2.imwrite(annotated_path, output_img)

    result["ok"] = True
    result["length_cm"] = round(lunghezza_tubi_cm, 1)
    result["height_cm"] = round(altezza_tubi_cm, 1)
    result["annotated_path"] = annotated_path
    return result


def analizza_coral_garden_universale(image_path):
    """Versione GUI legacy: analizza e mostra il risultato in una finestra.

    Mantenuta per l'uso interattivo da CLI. Delega tutta la logica ad analyze();
    l'unica differenza è la visualizzazione con cv2.imshow.
    """
    result = analyze(image_path, output_dir=".", equations_path="equations.txt")

    annotated_path = result.get("annotated_path")
    if annotated_path is None:
        # analyze() ha fallito ancora prima di produrre un'immagine (es. file illeggibile)
        return result

    output_img = cv2.imread(annotated_path)
    cv2.imshow("Monitor Ground Station", output_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    return result


def ricostruisci_3d(front_path, back_path=None, depth_cm=36.0,
                    output_dir=".", equations_path="equations.txt",
                    obj_path="coral_garden.obj", show=True):
    """Pipeline completa fronte+retro -> modello 3D + equations.txt + .obj.

    1. analizza il fronte (righello arancione -> scala);
    2. analizza il retro riusando la scala del fronte (il retro ha il righello
       trasparente, non rilevabile col filtro arancione);
    3. costruisce il modello 3D con tutti i target su entrambi i lati;
    4. scrive equations.txt (fallback SolidWorks) ed esporta il .obj;
    5. apre il viewer 3D ruotabile per la demo (se show=True).

    Args:
        front_path: foto del fronte (con righello arancione 50 cm).
        back_path: foto del retro (righello trasparente); None se vista singola.
        depth_cm: profondita' della struttura (larghezza nota da regolamento).

    Returns:
        il dict del modello 3D (vedi model_3d.build_model).
    """
    import model_3d

    print("==================== LATO FRONTE ====================")
    front = analyze(front_path, output_dir=output_dir,
                    equations_path=equations_path, write_equations=True)
    if not front.get("ok"):
        print(f"\nAnalisi del fronte fallita: {front.get('error')}")
        return None

    back = None
    if back_path:
        print("\n==================== LATO RETRO ====================")
        # Riusa la scala del fronte: il righello del retro e' trasparente.
        back = analyze(back_path, output_dir=output_dir,
                       pixels_per_cm=front["pixels_per_cm"],
                       write_equations=False)
        if not back.get("ok"):
            print(f"\nAnalisi del retro fallita ({back.get('error')}): "
                  f"procedo con la sola vista frontale.")
            back = None

    print("\n==================== MODELLO 3D ====================")
    model = model_3d.build_model(front, back, depth_cm=depth_cm)
    n_front = sum(1 for t in model["targets"] if t["side"] == "front")
    n_back = sum(1 for t in model["targets"] if t["side"] == "back")
    print(f"Target ricostruiti: {len(model['targets'])} "
          f"({n_front} fronte + {n_back} retro)")
    print(f"Box: L={model['length_cm']:.1f}  H={model['height_cm']:.1f}  "
          f"P={model['depth_cm']:.1f} cm")

    model_3d.export_mesh(model, os.path.join(output_dir, obj_path))

    if show:
        model_3d.show_interactive(model)

    return model


def reconstruct(front_path, back_path=None, output_dir=".",
                equations_path=None, depth_cm=36.0, obj_name="coral_garden.obj"):
    """API headless per NEXUS: ricostruisce il coral garden ed esporta il .obj.

    A differenza di `ricostruisci_3d`, NON apre nessuna finestra (niente viewer):
    genera solo il file .obj da aprire in un tool CAD, scrive equations.txt e
    ritorna un dict con la stessa forma di `analyze` (cosi' la route Flask non
    cambia contratto) piu' `obj_path`.

    Args:
        front_path: foto del fronte (righello arancione 50 cm).
        back_path: foto del retro (righello trasparente); None/"" = vista singola.
        output_dir: cartella dove scrivere .obj, equations.txt e annotate.
        equations_path: path di equations.txt (default <output_dir>/equations.txt).
        depth_cm: profondita'/larghezza struttura.
        obj_name: nome del file .obj generato dentro output_dir.

    Returns:
        dict: {ok, length_cm, height_cm, targets_count, annotated_path,
               obj_path, error}
    """
    import model_3d

    os.makedirs(output_dir, exist_ok=True)
    if equations_path is None:
        equations_path = os.path.join(output_dir, "equations.txt")

    result = {
        "ok": False, "length_cm": None, "height_cm": None,
        "targets_count": 0, "annotated_path": None, "obj_path": None,
        "error": None,
    }

    front = analyze(front_path, output_dir=output_dir,
                    equations_path=equations_path, write_equations=True)
    if not front.get("ok"):
        result["error"] = front.get("error") or "front_failed"
        result["annotated_path"] = front.get("annotated_path")
        return result

    back = None
    if back_path:
        back = analyze(back_path, output_dir=output_dir,
                       pixels_per_cm=front["pixels_per_cm"],
                       write_equations=False)
        if not back.get("ok"):
            back = None  # ripiega sulla sola vista frontale

    model = model_3d.build_model(front, back, depth_cm=depth_cm)
    obj_path = os.path.join(output_dir, obj_name)
    model_3d.export_mesh(model, obj_path)

    result.update({
        "ok": True,
        "length_cm": model["length_cm"],
        "height_cm": model["height_cm"],
        "targets_count": len(model["targets"]),
        "annotated_path": front.get("annotated_path"),
        "obj_path": obj_path,
    })
    return result


# Esegui la pipeline completa (solo da CLI, NON all'import)
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Ricostruzione 3D del Coral Garden da fronte + retro.")
    parser.add_argument("--front", default="righello.jpg",
                        help="foto del fronte (righello arancione 50 cm)")
    parser.add_argument("--back", default="nuova.jpg",
                        help="foto del retro (righello trasparente); "
                             "stringa vuota per usare solo il fronte")
    parser.add_argument("--depth", type=float, default=36.0,
                        help="profondita'/larghezza struttura in cm")
    parser.add_argument("--no-show", action="store_true",
                        help="non aprire il viewer 3D (utile per i test)")
    args = parser.parse_args()

    ricostruisci_3d(args.front, args.back or None,
                    depth_cm=args.depth, show=not args.no_show)
