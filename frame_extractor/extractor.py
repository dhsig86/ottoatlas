import cv2
import os
import csv
from utils import calculate_sharpness, is_bright_enough

class VideoExtractor:
    def __init__(self, input_dir, output_dir, interval, sharpness_threshold, min_brightness, generate_csv, logger):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.interval = interval
        self.sharpness_threshold = sharpness_threshold
        self.min_brightness = min_brightness
        self.generate_csv = generate_csv
        self.logger = logger
        
    def process_all(self):
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        csv_data = []
        if self.generate_csv:
            csv_data.append(["video_nome", "frame_arquivo", "timestamp_seg", "score_brilho", "score_nitidez_central"])
            
        valid_extensions = ('.mp4', '.avi', '.mov', '.mkv')
        
        if not os.path.exists(self.input_dir):
            self.logger.error(f"A pasta de entrada '{self.input_dir}' não foi encontrada.")
            return

        videos = [f for f in os.listdir(self.input_dir) if f.lower().endswith(valid_extensions)]
        if not videos:
            self.logger.warning(f"Nenhum vídeo encontrado na pasta '{self.input_dir}'.")
            return

        for file in videos:
            self.logger.info(f"Processando vídeo: {file}...")
            try:
                video_csv = self._process_video(file)
                if self.generate_csv:
                    csv_data.extend(video_csv)
            except Exception as e:
                self.logger.error(f"Erro Crítico ao processar '{file}': {e}. Pulando para o próximo.")
                
        if self.generate_csv and len(csv_data) > 1:
            csv_path = os.path.join(self.output_dir, "metadados_extracao.csv")
            with open(csv_path, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(csv_data)
            self.logger.info(f"Relatório de Metadados salvo com sucesso em: {csv_path}")

    def _process_video(self, filename):
        video_path = os.path.join(self.input_dir, filename)
        video_name = os.path.splitext(filename)[0]
        video_out_dir = os.path.join(self.output_dir, video_name)
        
        if not os.path.exists(video_out_dir):
            os.makedirs(video_out_dir)
            
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        # Proteção contra falhas de metadados do vídeo
        if fps <= 0 or fps != fps:
            fps = 30.0
            
        frame_interval = int(fps * self.interval)
        if frame_interval < 1: 
            frame_interval = 1
        
        csv_rows = []
        frame_idx = 0
        saved_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_idx % frame_interval == 0:
                timestamp = frame_idx / fps
                
                # 1. Filtro de Telas Escuras (Gaveta / Entrada)
                brightness_val, is_bright = is_bright_enough(frame, self.min_brightness)
                if not is_bright:
                    frame_idx += 1
                    continue
                    
                # 2. Filtro de Foco no Centro da Membrana Tympânica
                sharpness = calculate_sharpness(frame)
                
                if sharpness >= self.sharpness_threshold:
                    out_filename = f"frame_{saved_count:04d}_{timestamp:.2f}s.jpg"
                    out_path = os.path.join(video_out_dir, out_filename)
                    cv2.imwrite(out_path, frame)
                    
                    csv_rows.append([filename, out_filename, f"{timestamp:.2f}", f"{brightness_val:.2f}", f"{sharpness:.2f}"])
                    saved_count += 1
                else:
                    pass
                    
            frame_idx += 1
            
        cap.release()
        self.logger.info(f"Finalizado '{filename}': {saved_count} frames nítidos extraídos.")
        return csv_rows
