#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String


def _add_workspace_venv_site_packages() -> None:
    current_file = Path(__file__).resolve()

    for parent in current_file.parents:
        venv_site_packages = parent / '.venv' / 'lib' / 'python3.12' / 'site-packages'
        if venv_site_packages.is_dir() and str(venv_site_packages) not in sys.path:
            sys.path.insert(0, str(venv_site_packages))
            return


_add_workspace_venv_site_packages()

from ultralytics import YOLO


class Yolov8PersonDetector(Node):
    def __init__(self) -> None:
        super().__init__('yolov8_person_detector')

        self.declare_parameter('image_topic', '/camera/image_raw')
        self.declare_parameter('annotated_image_topic', '/detections/image')
        self.declare_parameter('detection_topic', '/detections/people')
        self.declare_parameter('model_path', 'yolov8n.pt')
        self.declare_parameter('confidence', 0.35)
        self.declare_parameter('device', 'cpu')
        self.declare_parameter('target_class_name', 'person')
        self.declare_parameter('publish_annotated_image', True)

        self.image_topic = self.get_parameter('image_topic').value
        self.annotated_image_topic = self.get_parameter('annotated_image_topic').value
        self.detection_topic = self.get_parameter('detection_topic').value
        self.model_path = self.get_parameter('model_path').value
        self.confidence = float(self.get_parameter('confidence').value)
        self.device = self.get_parameter('device').value
        self.target_class_name = str(self.get_parameter('target_class_name').value)
        self.publish_annotated_image = bool(
            self.get_parameter('publish_annotated_image').value
        )

        self.bridge = CvBridge()
        self.model = YOLO(self.model_path)

        self.subscription = self.create_subscription(
            Image,
            self.image_topic,
            self._image_callback,
            10,
        )
        self.annotated_publisher = self.create_publisher(
            Image,
            self.annotated_image_topic,
            10,
        )
        self.detection_publisher = self.create_publisher(
            String,
            self.detection_topic,
            10,
        )

        self.get_logger().info(
            f'YOLOv8 carregado ({self.model_path}) observando {self.image_topic}'
        )

    def _extract_person_count(self, result) -> tuple[int, Optional[float]]:
        boxes = getattr(result, 'boxes', None)
        if boxes is None or len(boxes) == 0:
            return 0, None

        classes = boxes.cls.tolist()
        confidences = boxes.conf.tolist()
        names = result.names

        person_scores = [
            conf
            for cls_id, conf in zip(classes, confidences, strict=False)
            if names.get(int(cls_id), '') == self.target_class_name
        ]
        if not person_scores:
            return 0, None

        return len(person_scores), max(person_scores)

    def _image_callback(self, msg: Image) -> None:
        try:
            frame_bgr = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as exc:
            self.get_logger().warn(f'Falha ao converter imagem ROS: {exc}')
            return

        try:
            results = self.model.predict(
                source=frame_bgr,
                conf=self.confidence,
                device=self.device,
                verbose=False,
            )
        except Exception as exc:
            self.get_logger().error(f'Falha ao executar YOLOv8: {exc}')
            return

        result = results[0]
        person_count, best_confidence = self._extract_person_count(result)

        detection_msg = String()
        if person_count > 0:
            detection_msg.data = (
                f'person_detected=true count={person_count} best_confidence={best_confidence:.3f}'
            )
            self.get_logger().info(detection_msg.data)
        else:
            detection_msg.data = 'person_detected=false count=0'

        self.detection_publisher.publish(detection_msg)

        if not self.publish_annotated_image:
            return

        annotated_bgr = result.plot()
        try:
            annotated_msg = self.bridge.cv2_to_imgmsg(annotated_bgr, encoding='bgr8')
            annotated_msg.header = msg.header
            self.annotated_publisher.publish(annotated_msg)
        except Exception as exc:
            self.get_logger().warn(f'Falha ao publicar imagem anotada: {exc}')


def main() -> None:
    rclpy.init()
    node = Yolov8PersonDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()