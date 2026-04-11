#!/usr/bin/env python3

from __future__ import annotations

import select
import sys
import termios
import tty

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node


HELP_MESSAGE = """
Reading from the keyboard and publishing to Twist.
---------------------------
Moving around:
   u    i    o
   j    k    l
   m    ,    .

For holonomic mode, hold shift:
---------------------------
   U    I    O
   J    K    L
   M    <    >

t : up (+z)
b : down (-z)

anything else : stop

q/z : increase/decrease max speeds by 10%
w/x : increase/decrease only linear speed by 10%
e/c : increase/decrease only angular speed by 10%

CTRL-C to quit
"""


MOVE_BINDINGS = {
    'i': (1, 0, 0, 0),
    'o': (1, 0, 0, -1),
    'j': (0, 0, 0, 1),
    'l': (0, 0, 0, -1),
    'u': (1, 0, 0, 1),
    ',': (-1, 0, 0, 0),
    '.': (-1, 0, 0, 1),
    'm': (-1, 0, 0, -1),
    'O': (1, -1, 0, 0),
    'I': (1, 0, 0, 0),
    'J': (0, 1, 0, 0),
    'L': (0, -1, 0, 0),
    'U': (1, 1, 0, 0),
    '<': (-1, 0, 0, 0),
    '>': (-1, -1, 0, 0),
    'M': (-1, 1, 0, 0),
    't': (0, 0, 1, 0),
    'b': (0, 0, -1, 0),
}

SPEED_BINDINGS = {
    'q': (1.1, 1.1),
    'z': (0.9, 0.9),
    'w': (1.1, 1.0),
    'x': (0.9, 1.0),
    'e': (1.0, 1.1),
    'c': (1.0, 0.9),
}


class TeleopKeyboard(Node):
    def __init__(self) -> None:
        super().__init__('teleop_keyboard')

        self.declare_parameter('cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('speed', 0.5)
        self.declare_parameter('turn', 1.0)

        self.cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        self.speed = float(self.get_parameter('speed').value)
        self.turn = float(self.get_parameter('turn').value)

        self.publisher = self.create_publisher(Twist, self.cmd_vel_topic, 10)

    def publish_twist(self, linear: float, angular: float) -> None:
        twist = Twist()
        twist.linear.x = linear
        twist.angular.z = angular
        self.publisher.publish(twist)


def get_key(settings) -> str:
    tty.setraw(sys.stdin.fileno())
    select.select([sys.stdin], [], [], 0)
    key = sys.stdin.read(1)
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


def print_vels(speed: float, turn: float) -> str:
    return f'currently:\tspeed {speed}\tturn {turn} '


def main() -> None:
    rclpy.init()
    node = TeleopKeyboard()
    settings = termios.tcgetattr(sys.stdin)

    x = 0
    y = 0
    z = 0
    th = 0
    status = 0

    try:
        print(HELP_MESSAGE)
        print(print_vels(node.speed, node.turn))

        while rclpy.ok():
            key = get_key(settings)

            if key in MOVE_BINDINGS:
                x, y, z, th = MOVE_BINDINGS[key]
            elif key in SPEED_BINDINGS:
                node.speed *= SPEED_BINDINGS[key][0]
                node.turn *= SPEED_BINDINGS[key][1]
                print(print_vels(node.speed, node.turn))
                if status == 14:
                    print(HELP_MESSAGE)
                status = (status + 1) % 15
            else:
                x = 0
                y = 0
                z = 0
                th = 0
                if key == '\x03':
                    break

            linear = x * node.speed
            angular = th * node.turn
            node.publish_twist(linear, angular)

    except Exception as exc:
        node.get_logger().error(f'Teleop error: {exc}')
    finally:
        node.publish_twist(0.0, 0.0)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()