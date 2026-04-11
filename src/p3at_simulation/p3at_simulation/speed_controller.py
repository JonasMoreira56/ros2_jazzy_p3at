#!/usr/bin/env python3

from __future__ import annotations

import math

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node


def quaternion_to_yaw(x: float, y: float, z: float, w: float) -> float:
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    return math.atan2(siny_cosp, cosy_cosp)


def normalize_angle(angle: float) -> float:
    return math.atan2(math.sin(angle), math.cos(angle))


class SpeedController(Node):
    def __init__(self) -> None:
        super().__init__('speed_controller')

        self.declare_parameter('odom_topic', '/odom')
        self.declare_parameter('cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('goal_x', 3.0)
        self.declare_parameter('goal_y', 3.0)
        self.declare_parameter('linear_speed_m_s', 0.5)
        self.declare_parameter('angular_speed_rad_s', 0.3)
        self.declare_parameter('angle_tolerance_rad', 0.3)
        self.declare_parameter('position_tolerance_m', 0.15)
        self.declare_parameter('control_rate_hz', 10.0)
        self.declare_parameter('shutdown_on_goal', True)

        self.odom_topic = self.get_parameter('odom_topic').value
        self.cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        self.goal_x = float(self.get_parameter('goal_x').value)
        self.goal_y = float(self.get_parameter('goal_y').value)
        self.linear_speed = float(self.get_parameter('linear_speed_m_s').value)
        self.angular_speed = float(self.get_parameter('angular_speed_rad_s').value)
        self.angle_tolerance = float(self.get_parameter('angle_tolerance_rad').value)
        self.position_tolerance = float(self.get_parameter('position_tolerance_m').value)
        self.control_rate_hz = float(self.get_parameter('control_rate_hz').value)
        self.shutdown_on_goal = bool(self.get_parameter('shutdown_on_goal').value)

        if self.control_rate_hz <= 0.0:
            raise ValueError('control_rate_hz deve ser maior que 0')
        if self.linear_speed < 0.0:
            raise ValueError('linear_speed_m_s nao pode ser negativo')
        if self.angular_speed <= 0.0:
            raise ValueError('angular_speed_rad_s deve ser maior que 0')
        if self.position_tolerance <= 0.0:
            raise ValueError('position_tolerance_m deve ser maior que 0')

        self.current_x = 0.0
        self.current_y = 0.0
        self.current_yaw = 0.0
        self.has_odom = False
        self.finished = False

        self.odom_sub = self.create_subscription(
            Odometry,
            self.odom_topic,
            self._on_odom,
            10,
        )
        self.cmd_pub = self.create_publisher(Twist, self.cmd_vel_topic, 10)

        timer_period = 1.0 / self.control_rate_hz
        self.timer = self.create_timer(timer_period, self._on_timer)

        self.get_logger().info(
            'Speed controller iniciado: '
            f'goal=({self.goal_x:.2f}, {self.goal_y:.2f}), '
            f'odom={self.odom_topic}, cmd_vel={self.cmd_vel_topic}'
        )

    def _on_odom(self, msg: Odometry) -> None:
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        self.current_yaw = quaternion_to_yaw(q.x, q.y, q.z, q.w)
        self.has_odom = True

    def _publish(self, linear_x: float, angular_z: float) -> None:
        msg = Twist()
        msg.linear.x = linear_x
        msg.angular.z = angular_z
        self.cmd_pub.publish(msg)

    def _stop_and_finish(self) -> None:
        self._publish(0.0, 0.0)
        self.finished = True
        self.destroy_timer(self.timer)
        self.get_logger().info('Objetivo alcancado. Controlador finalizado.')
        if self.shutdown_on_goal:
            self.destroy_node()
            rclpy.shutdown()

    def _on_timer(self) -> None:
        if self.finished:
            return

        if not self.has_odom:
            return

        inc_x = self.goal_x - self.current_x
        inc_y = self.goal_y - self.current_y
        distance = math.hypot(inc_x, inc_y)

        if distance <= self.position_tolerance:
            self._stop_and_finish()
            return

        angle_to_goal = math.atan2(inc_y, inc_x)
        angle_error = normalize_angle(angle_to_goal - self.current_yaw)

        if abs(angle_error) > self.angle_tolerance:
            direction = 1.0 if angle_error > 0.0 else -1.0
            self._publish(0.0, direction * self.angular_speed)
        else:
            self._publish(self.linear_speed, 0.0)


def main() -> None:
    rclpy.init()
    try:
        node = SpeedController()
    except ValueError as exc:
        temp_node = Node('speed_controller_config_error')
        temp_node.get_logger().error(str(exc))
        temp_node.destroy_node()
        rclpy.shutdown()
        return

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Interrompido pelo usuario, enviando parada.')
        stop = Twist()
        node.cmd_pub.publish(stop)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()