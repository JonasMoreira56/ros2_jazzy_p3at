import math
import random

import rclpy
from geometry_msgs.msg import Pose
from geometry_msgs.msg import Twist
from rclpy.node import Node
from ros_gz_interfaces.msg import Entity
from ros_gz_interfaces.srv import SetEntityPose


class RandomPersonMotion(Node):
    def __init__(self) -> None:
        super().__init__('random_person_motion')

        self.declare_parameter('person_name', 'pessoa1')
        self.declare_parameter('motion_mode', 'cmd_vel')
        self.declare_parameter('cmd_vel_topic', '/model/pessoa1/cmd_vel')
        self.declare_parameter('set_pose_service', '/world/default/set_pose')
        self.declare_parameter('update_period_sec', 0.05)
        self.declare_parameter('walk_speed_m_s', 0.7)
        self.declare_parameter('turn_std_dev_rad', 0.15)
        self.declare_parameter('max_turn_rate_rad_s', 0.6)
        self.declare_parameter('stop_probability', 0.18)
        self.declare_parameter('min_x', -8.0)
        self.declare_parameter('max_x', 8.0)
        self.declare_parameter('min_y', -8.0)
        self.declare_parameter('max_y', 8.0)
        self.declare_parameter('fixed_z', 0.0)
        self.declare_parameter('start_x', 2.0)
        self.declare_parameter('start_y', 0.0)

        self.person_name = self.get_parameter('person_name').value
        self.motion_mode = self.get_parameter('motion_mode').value
        self.cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        configured_service_name = self.get_parameter('set_pose_service').value
        self.service_name = configured_service_name.strip()
        self.update_period = float(self.get_parameter('update_period_sec').value)
        self.walk_speed = float(self.get_parameter('walk_speed_m_s').value)
        self.turn_std = float(self.get_parameter('turn_std_dev_rad').value)
        self.max_turn_rate = float(self.get_parameter('max_turn_rate_rad_s').value)
        self.stop_probability = float(self.get_parameter('stop_probability').value)
        self.min_x = float(self.get_parameter('min_x').value)
        self.max_x = float(self.get_parameter('max_x').value)
        self.min_y = float(self.get_parameter('min_y').value)
        self.max_y = float(self.get_parameter('max_y').value)
        self.fixed_z = float(self.get_parameter('fixed_z').value)

        self.x = float(self.get_parameter('start_x').value)
        self.y = float(self.get_parameter('start_y').value)
        self.yaw = random.uniform(-math.pi, math.pi)
        self.turn_rate = random.uniform(-0.15, 0.15)

        self.client = None
        self.cmd_pub = None
        if self.motion_mode == 'cmd_vel':
            self.cmd_pub = self.create_publisher(Twist, self.cmd_vel_topic, 10)
            self.get_logger().info(
                f'Movimento aleatorio por cmd_vel iniciado em {self.cmd_vel_topic}'
            )
            self.timer = self.create_timer(self.update_period, self._move_person_cmd_vel)
        else:
            self._connect_set_pose_service()
            self.get_logger().info(
                f'Movimento aleatorio por set_pose iniciado usando {self.service_name}'
            )
            self.timer = self.create_timer(self.update_period, self._move_person_set_pose)

    def _find_set_pose_service(self) -> str:
        service_names = []
        for name, service_types in self.get_service_names_and_types():
            if (
                name.endswith('/set_pose')
                and 'ros_gz_interfaces/srv/SetEntityPose' in service_types
            ):
                service_names.append(name)

        if not service_names:
            return ''

        if '/world/default/set_pose' in service_names:
            return '/world/default/set_pose'

        return sorted(service_names)[0]

    def _connect_set_pose_service(self) -> None:
        while True:
            if self.service_name:
                candidate = self.service_name
            else:
                candidate = self._find_set_pose_service()

            if not candidate:
                self.get_logger().info(
                    'Aguardando descoberta de um servico /world/*/set_pose...'
                )
                rclpy.spin_once(self, timeout_sec=1.0)
                continue

            client = self.create_client(SetEntityPose, candidate)
            if client.wait_for_service(timeout_sec=1.0):
                self.service_name = candidate
                self.client = client
                return

            if self.service_name:
                self.get_logger().info(
                    f'Aguardando servico {self.service_name} para mover {self.person_name}...'
                )
            else:
                self.get_logger().info(
                    f'Servico detectado mas ainda indisponivel: {candidate}'
                )

    def _clamp(self, value: float, min_value: float, max_value: float) -> float:
        return max(min_value, min(max_value, value))

    def _move_person_cmd_vel(self) -> None:
        if self.cmd_pub is None:
            return

        msg = Twist()

        # Pequenas pausas ocasionais deixam o movimento mais humano.
        if random.random() < self.stop_probability:
            msg.linear.x = 0.0
            msg.angular.z = 0.0
        else:
            msg.linear.x = max(0.1, random.gauss(self.walk_speed, 0.12))
            msg.angular.z = max(
                -self.max_turn_rate,
                min(self.max_turn_rate, random.gauss(0.0, self.turn_std)),
            )

        self.cmd_pub.publish(msg)

    def _move_person_set_pose(self) -> None:
        if self.client is None:
            return

        # Dinamica suave: variacao pequena e continua na velocidade angular.
        self.turn_rate += random.gauss(0.0, self.turn_std) * self.update_period
        self.turn_rate = self._clamp(
            self.turn_rate,
            -self.max_turn_rate,
            self.max_turn_rate,
        )
        self.yaw += self.turn_rate * self.update_period
        self.yaw = math.atan2(math.sin(self.yaw), math.cos(self.yaw))

        step = self.walk_speed * self.update_period
        next_x = self.x + math.cos(self.yaw) * step
        next_y = self.y + math.sin(self.yaw) * step

        clamped_x = self._clamp(next_x, self.min_x, self.max_x)
        clamped_y = self._clamp(next_y, self.min_y, self.max_y)

        if clamped_x != next_x or clamped_y != next_y:
            self.yaw += math.pi
            self.turn_rate *= -0.5
            self.yaw = math.atan2(math.sin(self.yaw), math.cos(self.yaw))

        self.x = clamped_x
        self.y = clamped_y

        pose = Pose()
        pose.position.x = self.x
        pose.position.y = self.y
        pose.position.z = self.fixed_z

        half_yaw = self.yaw / 2.0
        pose.orientation.w = math.cos(half_yaw)
        pose.orientation.z = math.sin(half_yaw)

        request = SetEntityPose.Request()
        request.entity.id = 0
        request.entity.name = self.person_name
        request.entity.type = Entity.MODEL
        request.pose = pose
        future = self.client.call_async(request)
        future.add_done_callback(self._on_set_pose_response)

    def _on_set_pose_response(self, future) -> None:
        try:
            response = future.result()
        except Exception as exc:
            self.get_logger().warn(f'Falha ao chamar set_pose: {exc}')
            return

        if not response.success:
            self.get_logger().warn(
                f'set_pose retornou success=False para entidade {self.person_name}'
            )


def main() -> None:
    rclpy.init()
    node = RandomPersonMotion()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
