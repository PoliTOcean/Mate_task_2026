import cv2
import numpy as np

def misura_ingombro_tubi_pvc(image_path):
    # 1. Carica l'immagine
    img = cv2.imread(image_path)
    if img is None:
        print(f"Errore: Impossibile caricare {image_path}")
        return

    output_img = img.copy()
    
    # 2. Convertiamo in HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # =========================================================================
    # DETECT RIGHELLO VERDE (Calcolo Scala)
    # =========================================================================
    LUNGHEZZA_RIGHELLO_CM = 50.0
    lower_green = np.array([35, 70, 50])
    upper_green = np.array([85, 255, 255])

    ruler_mask = cv2.inRange(hsv, lower_green, upper_green)
    ruler_contours, _ = cv2.findContours(ruler_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if len(ruler_contours) == 0:
        print("Errore: Righello verde non trovato.")
        return

    best_ruler = max(ruler_contours, key=cv2.contourArea)
    x_r, y_r, w_r, h_r = cv2.boundingRect(best_ruler)
    pixels_per_cm = w_r / LUNGHEZZA_RIGHELLO_CM

    print(f"--- FASE 1: SCALA PIXEL ---")
    print(f"Righello Verde: {w_r} pixel = 50 cm")
    print(f"1 cm equivale a: {pixels_per_cm:.2f} pixel\n")
    
    # Evidenzia il righello in giallo
    cv2.rectangle(output_img, (x_r, y_r), (x_r + w_r, y_r + h_r), (0, 255, 255), 2)

    # =========================================================================
    # DETECT TUBI BIANCHI (Isoliamo il PVC dallo sfondo blu)
    # =========================================================================
    # Il bianco in HSV ha una saturazione bassa (S) e un valore alto (V)
    lower_white = np.array([0, 0, 180])   
    upper_white = np.array([180, 50, 255])  
    
    pvc_mask = cv2.inRange(hsv, lower_white, upper_white)
    
    # Escludiamo l'area del righello dalla maschera del bianco per evitare errori
    pvc_mask[y_r:y_r+h_r, x_r:x_r+w_r] = 0
    
    # Pulizia della maschera per unire i tubi ed eliminare scritte o riflessi
    kernel = np.ones((5,5), np.uint8)
    pvc_mask = cv2.morphologyEx(pvc_mask, cv2.MORPH_CLOSE, kernel)
    pvc_mask = cv2.morphologyEx(pvc_mask, cv2.MORPH_OPEN, kernel)
    
    # Trova tutti i punti bianchi (i pixel dei tubi)
    punti_pvc = cv2.findNonZero(pvc_mask)

    # =========================================================================
    # FASE 3: CALCOLO DEL VERO INGOMBRO DEI TUBI
    # =========================================================================
    print(f"--- FASE 2: MISURE DEI TUBI ---")
    if punti_pvc is not None:
        # BoundingRect trova il rettangolo perfetto che racchiude TUTTI i punti bianchi
        x_t, y_t, w_t, h_t = cv2.boundingRect(punti_pvc)
        
        # Convertiamo larghezza e altezza in centimetri reali
        lunghezza_tubi_cm = w_t / pixels_per_cm
        altezza_tubi_cm = h_t / pixels_per_cm
        
        print(f"LUNGHEZZA REALE TUBI: {lunghezza_tubi_cm:.1f} cm")
        print(f"ALTEZZA REALE TUBI: {altezza_tubi_cm:.1f} cm")
        
        # Disegna il box di ingombro REALE dei tubi (Verde brillante)
        cv2.rectangle(output_img, (x_t, y_t), (x_t + w_t, y_t + h_t), (0, 255, 0), 3)
        
        # Scrittura dati sulla foto
        cv2.putText(output_img, f"LUNGHEZZA TUBI PVC: {lunghezza_tubi_cm:.1f} cm", (40, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(output_img, f"ALTEZZA TUBI PVC: {altezza_tubi_cm:.1f} cm", (40, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
    else:
        print("Errore: Non sono riuscito a isolare i tubi in PVC bianchi.")

    # Mostra i risultati
    cv2.imshow("Cosa vede il robot (Solo Tubi Bianchi)", pvc_mask)
    cv2.imshow("Misurazione Reale Struttura PVC", output_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# Esegui il test
misura_ingombro_tubi_pvc('righello.jpg')