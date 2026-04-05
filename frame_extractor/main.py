import argparse
from utils import setup_logger
from extractor import VideoExtractor

def parse_args():
    parser = argparse.ArgumentParser(
        description="Extrator Inteligente de Frames (Motor Clínico de Aquisição de Dados)",
        epilog="Exemplo: python main.py --input videos_originais --output frames --interval 0.5 --sharpness-threshold 80 --csv"
    )
    parser.add_argument("--input", required=True, help="Caminho da pasta contendo os vídeos originais (.mp4, .avi, etc)")
    parser.add_argument("--output", required=True, help="Caminho da pasta destino para armazenar as sub-pastas com fotos")
    parser.add_argument("--interval", type=float, default=0.5, help="Intervalo (em segundos) da captura dos frames (Padrão: 0.5s)")
    parser.add_argument("--sharpness-threshold", type=float, default=60.0, help="Nitidez mínima (Foco) da Membrana. Valores entre 30 e 100.")
    parser.add_argument("--min-brightness", type=float, default=25.0, help="Luminosidade mínima. Rejeita o frame se for menor que isso (tela preta do otoscópio). Padrão: 25.0")
    parser.add_argument("--csv", action="store_true", help="Aciona a criação automática de um arquivo .csv")
    
    return parser.parse_args()

if __name__ == "__main__":
    logger = setup_logger()
    args = parse_args()
    
    logger.info("============== OTTO MLOps: FRAME EXTRACTOR ==============")
    logger.info(f"Input : {args.input}")
    logger.info(f"Output: {args.output}")
    logger.info(f"Taxa  : 1 foto a cada {args.interval} segundos")
    logger.info(f"Filtro Nitidez: >= {args.sharpness_threshold} (Aplicado no Centro do Quadro)")
    logger.info(f"Filtro Brilho : >= {args.min_brightness}")
    logger.info("=========================================================")
    
    extractor = VideoExtractor(
        input_dir=args.input,
        output_dir=args.output,
        interval=args.interval,
        sharpness_threshold=args.sharpness_threshold,
        min_brightness=args.min_brightness,
        generate_csv=args.csv,
        logger=logger
    )
    
    extractor.process_all()
    logger.info("Iniciativa de Captação Finalizada!")
