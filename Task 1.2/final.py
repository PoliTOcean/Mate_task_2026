import os

import cv2
import numpy as np


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


def analyze(image_path, output_dir=".", equations_path=None):
    """Analizza una singola immagine del coral garden e ritorna le misure.

    Pipeline (invariata):
      Fase 1 - righello arancione -> scala pixel/cm
      Fase 2 - target colorati (non-blu, 4-6 lati) -> conteggio
      Fase 3 - tubi PVC bianchi -> bounding box -> lunghezza/altezza in cm

    A differenza della vecchia versione GUI, questa funzione NON apre finestre
    (niente cv2.imshow/waitKey): scrive l'immagine annotata su disco e ritorna
    un dict strutturato, così è richiamabile da un server.

    Args:
        image_path: percorso dell'immagine da analizzare.
        output_dir: cartella dove scrivere l'immagine annotata.
        equations_path: percorso del file equations.txt (default: <output_dir>/equations.txt).

    Returns:
        dict con chiavi:
          ok (bool), length_cm (float|None), height_cm (float|None),
          targets_count (int), annotated_path (str|None), error (str|None)
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
    LUNGHEZZA_RIGHELLO_CM = 50.0
    lower_orange = np.array([5, 150, 150])
    upper_orange = np.array([25, 255, 255])

    ruler_mask = cv2.inRange(hsv, lower_orange, upper_orange)
    ruler_contours, _ = cv2.findContours(ruler_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if len(ruler_contours) == 0:
        print("Errore: Righello arancione non trovato. Impossibile calcolare i cm reali.")
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
    target_centers = []

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

            target_count += 1
            target_centers.append((cX, cY))
            print(f"Target #{target_count} Rilevato (Qualsiasi Colore) -> Centro: X={cX}, Y={cY}")

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


# Esegui il test definitivo (solo da CLI, NON all'import)
if __name__ == "__main__":
    analizza_coral_garden_universale('righello.jpg')
