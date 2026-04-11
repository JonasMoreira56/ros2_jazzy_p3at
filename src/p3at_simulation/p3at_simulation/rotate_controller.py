#!/usr/bin/env python3

from __future__ import annotations

import math

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node


class RotateController(Node):
    def __init__(self) -> None:
        super().__init__('rotate_controller')

        self.declare_parameter('cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('angular_speed_deg_s', 30.0)
        self.declare_parameter('angle_deg', 90.0)
        self.declare_parameter('clockwise', True)
        self.declare_parameter('publish_rate_hz', 20.0)

        cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        angular_speed_deg_s = float(self.get_parameter('angular_speed_deg_s').value)
        angle_deg = float(self.get_parameter('angle_deg').value)
        clockwise = bool(self.get_parameter('clockwise').value)
        publish_rate_hz = float(self.get_parameter('publish_rate_hz').value)

        if angular_speed_deg_s <= 0.0:
            raise ValueError('angular_speed_deg_s deve ser maior que 0')
        if angle_deg <= 0.0:
            raise ValueError('angle_deg deve ser maior que 0')
        if publish_rate_hz <= 0.0:
            raise ValueError('publish_rate_hz deve ser maior que 0')

        self.angular_speed_rad_s = math.radians(angular_speed_deg_s)
        self.target_angle_rad = math.radians(angle_deg)
        self.angular_signal = -1.0 if clockwise else 1.0
        self.duration_sec = self.target_angle_rad / self.angular_speed_rad_s

        self.publisher = self.create_publisher(Twist, cmd_vel_topic, 10)
        self.start_time_sec: float | None = None
        self.finished = False

        timer_period = 1.0 / publish_rate_hz
        self.timer = self.create_timer(timer_period, self._on_timer)

        direction = 'horario' if clockwise else 'anti-horario'
        self.get_logger().info(
            f'Rotacao iniciada: {angle_deg:.2f} deg, '
            f'{angular_speed_deg_s:.2f} deg/s, sentido {direction}, '
            f'duracao estimada {self.duration_sec:.2f}s'
        )

    def _publish_cmd(self, angular_z: float) -> None:
        msg = Twist()
        msg.angular.z = angular_z
        self.publisher.publish(msg)

    def _on_timer(self) -> None:
        if self.finished:
            return

        now_sec = self.get_clock().now().nanoseconds / 1e9
        if self.start_time_sec is None:
            self.start_time_sec = now_sec

        elapsed = now_sec - self.start_time_sec
        if elapsed < self.duration_sec:
            self._publish_cmd(self.angular_signal * self.angular_speed_rad_s)
            return

        self._publish_cmd(0.0)
        self.finished = True
        self.get_logger().info('Rotacao concluida.')
        self.destroy_timer(self.timer)
        self.destroy_node()
        rclpy.shutdown()


def main() -> None:
    rclpy.init()
    try:
        node = RotateController()
    except ValueError as exc:
        temp_node = Node('rotate_controller_config_error')
        temp_node.get_logger().error(str(exc))
        temp_node.destroy_node()
        rclpy.shutdown()
        return

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Interrompido pelo usuario, enviando parada.')
        stop = Twist()
        node.publisher.publish(stop)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()