import cv2
import logging

def setup_logger():
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    return logging.getLogger("FrameExtractor")

def crop_center(frame, crop_factor=0.6):
    """
    Corta e isola apenas a porção central da imagem (uma 'janela' no meio do quadro).
    Otoscópios produzem imagens com um círculo iluminado no centro e bordas pitch-black.
    O contraste extremo das bordas pretas engana a Inteligência Artificial.
    """
    h, w = frame.shape[:2]
    ch, cw = int(h * crop_factor), int(w * crop_factor)
    y = (h - ch) // 2
    x = (w - cw) // 2
    return frame[y:y+ch, x:x+cw]

def calculate_sharpness(frame):
    """
    Calcula a nitidez da imagem usando a Variância do Laplaciano apenas no Miolo Central!
    """
    center_roi = crop_center(frame)
    gray = cv2.cvtColor(center_roi, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()

def is_bright_enough(frame, min_brightness=25.0):
    """
    Bloqueia fotos tiradas enquanto o otoscópio está na gaveta ou fora da orelha (telas pretas).
    A média dos pixels deve ser maior que 'min_brightness'.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mean_val = cv2.mean(gray)[0]
    return mean_val, mean_val >= min_brightness
