from ultralytics import YOLO
import os

class YOLOModel:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            # Загружаем модель один раз
            cls._instance = YOLO('yolov8n.pt')
        return cls._instance

# Загружаем модель заранее
model = YOLOModel.get_instance()
