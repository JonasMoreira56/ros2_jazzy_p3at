#!/usr/bin/env python3

from __future__ import annotations

import random

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node


class RandomRobotMotion(Node):
    def __init__(self) -> None:
        super().__init__('random_robot_motion')

        self.declare_parameter('cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('linear_speed_m_s', 0.5)
        self.declare_parameter('angular_speed_rad_s', 0.3)
        self.declare_parameter('update_period_sec', 1.0)
        self.declare_parameter('motion_duration_sec', 10.0)

        self.cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        self.linear_speed = float(self.get_parameter('linear_speed_m_s').value)
        self.angular_speed = float(self.get_parameter('angular_speed_rad_s').value)
        self.update_period = float(self.get_parameter('update_period_sec').value)
        self.motion_duration = float(self.get_parameter('motion_duration_sec').value)

        self.publisher = self.create_publisher(Twist, self.cmd_vel_topic, 10)
        self.timer = self.create_timer(self.update_period, self._move_robot)
        
        self.movement_counter = 0
        self.movements_per_cycle = int(self.motion_duration / self.update_period)

        self.get_logger().info(
            f'Movimento aleatorio do robo iniciado em {self.cmd_vel_topic}'
        )

    def _move_robot(self) -> None:
        twist = Twist()

        if self.movement_counter < self.movements_per_cycle:
            z = random.uniform(-self.angular_speed, self.angular_speed)
            twist.linear.x = self.linear_speed
            twist.angular.z = z
            self.get_logger().info(
                f'Movimento: linear_x={twist.linear.x:.2f}, angular_z={twist.angular.z:.2f}'
            )
        else:
            twist.linear.x = 0.0
            twist.angular.z = 0.0
            self.get_logger().info('Parado')

        self.publisher.publish(twist)
        self.movement_counter = (self.movement_counter + 1) % (self.movements_per_cycle * 2)


def main() -> None:
    rclpy.init()
    node = RandomRobotMotion()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
