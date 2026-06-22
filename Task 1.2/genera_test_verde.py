"""Genera immagini di test SINTETICHE con righello verde.

Le foto originali del coral garden hanno il righello arancione (`righello.jpg`)
o trasparente (`nuova.jpg`), quindi dopo il passaggio del rilevatore al verde non
verrebbero piu' riconosciute. Questo script ricolora i pixel arancioni del righello
in verde (sposta solo la tonalita' H, mantenendo saturazione e luminosita') e produce:

  - fronte.jpg : righello.jpg con righello verde (vista frontale)
  - retro.jpg  : la stessa immagine specchiata orizzontalmente, a simulare la vista
                 posteriore con il righello in una posizione diversa ("spostato")

Servono SOLO per provare la pipeline end-to-end: in gara verranno sostituite dalle
foto reali del ROV. I target rosa/magenta (H~160-175) NON rientrano nel range
arancione e quindi non vengono toccati.
"""

import cv2
import numpy as np

# Range HSV dell'arancione del righello originale (stesso usato dalla vecchia Fase 1).
LOWER_ORANGE = np.array([5, 150, 150])
UPPER_ORANGE = np.array([25, 255, 255])
GREEN_HUE = 60  # tonalita' verde target (OpenCV H 0-180)


def ricolora_in_verde(img):
    """Ritorna una copia di img con i pixel arancioni del righello portati a verde."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, LOWER_ORANGE, UPPER_ORANGE)
    hsv[mask > 0, 0] = GREEN_HUE  # cambio solo la tonalita', S e V restano
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


def main():
    sorgente = "righello.jpg"
    img = cv2.imread(sorgente)
    if img is None:
        print(f"Errore: impossibile caricare {sorgente}")
        return

    fronte = ricolora_in_verde(img)
    cv2.imwrite("fronte.jpg", fronte)
    print("Creato fronte.jpg (righello verde, vista frontale)")

    # Vista 'retro' simulata: specchio orizzontale (righello in posizione diversa).
    retro = ricolora_in_verde(cv2.flip(img, 1))
    cv2.imwrite("retro.jpg", retro)
    print("Creato retro.jpg (righello verde, vista posteriore simulata)")


if __name__ == "__main__":
    main()
