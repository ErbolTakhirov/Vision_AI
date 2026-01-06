import cv2
import logging
from ultralytics import YOLO

logger = logging.getLogger(__name__)

class VisionSystem:
    def __init__(self, model_path="../yolov8n.pt"):
        self.model = None
        try:
            logger.info(f"👁️ Загрузка YOLO из {model_path}...")
            self.model = YOLO(model_path)
            logger.info("✅ Vision System готова")
        except Exception as e:
            logger.error(f"❌ Ошибка YOLO: {e}")
            # Try loading generic if local fails
            try:
                self.model = YOLO("yolov8n.pt")
            except:
                pass

    def detect(self, frame):
        """
        Возвращает список обнаруженных классов.
        """
        if not self.model:
            return []
            
        # Run inference
        results = self.model(frame, verbose=False, conf=0.5)
        
        detected_objects = []
        for r in results:
            for c in r.boxes.cls:
                name = self.model.names[int(c)]
                detected_objects.append(name)
        
        # Возвращаем уникальные объекты
        return list(set(detected_objects))
