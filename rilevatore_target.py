import cv2
import numpy as np

def detect_pink_targets_real(image_path):
    # 1. Carica l'immagine
    img = cv2.imread(image_path)
    if img is None:
        print(f"Errore: Impossibile caricare {image_path}")
        return

    output_img = img.copy()

    # 2. Convertiamo in HSV (ideale per isolare i colori specifici)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # 3. RANGE DEL COLORE ROSA/MAGENTA (Tarato sui target della foto)
    # Sotto l'acqua o con luci diverse potresti dover regolare leggermente questi valori
    lower_pink = np.array([140, 70, 70])   
    upper_pink = np.array([175, 255, 255])  

    # Crea la maschera: tiene solo il rosa, il resto diventa nero
    mask = cv2.inRange(hsv, lower_pink, upper_pink)
    
    # Pulizia dei piccoli pixel di rumore isolati sullo sfondo
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # 4. Trova i contorni delle sole zone rimaste rosa
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    print(f"--- Quadrati Target Rosa Rilevati ---")
    target_count = 0

    for cnt in contours:
        # Filtro dimensione: scarta riflessi microscopici
        if cv2.contourArea(cnt) < 100:
            continue
            
        # Approssimiamo la forma geometrica
        epsilon = 0.04 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        
        # Accettiamo forme da 4 a 6 lati (in prospettiva i quadrati possono distorcersi)
        if 4 <= len(approx) <= 6:
            target_count += 1
            
            # Calcolo del centro esatto (Centroide)
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
            else:
                cX, cY = 0, 0

            print(f"Target #{target_count} -> Centro Pixel: X={cX}, Y={cY}")

            # Disegniamo i risultati sull'immagine originale
            cv2.drawContours(output_img, [approx], -1, (0, 255, 0), 3) # Contorno Verde
            cv2.circle(output_img, (cX, cY), 6, (0, 0, 255), -1)       # Pallino Rosso
            cv2.putText(output_img, f"ID:{target_count} ({cX},{cY})", (cX - 30, cY - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    print(f"Totale target trovati con filtro colore: {target_count}")

    # Mostra i risultati visivi
    cv2.imshow("Cosa vede il filtro (Maschera Rosa)", mask)
    cv2.imshow("Risultato Rilevamento", output_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# Avvia il test usando il nome esatto della tua immagine della struttura
find_target_squares_robust = detect_pink_targets_real('nuova.jpg')