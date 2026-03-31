import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro

def generate_launch_description():

    # Caminho para o diretório de compartilhamento do nosso pacote
    pkg_share_dir = get_package_share_directory('p3at_simulation')
    
    # *** CORREÇÃO CRÍTICA AQUI ***
    # A URI 'model://p3at_simulation' instrui o Gazebo a procurar por um diretório
    # chamado 'p3at_simulation' dentro dos caminhos de GZ_SIM_RESOURCE_PATH.
    # O diretório 'p3at_simulation' está localizado em '.../install/p3at_simulation/share'.
    # Portanto, o GZ_SIM_RESOURCE_PATH deve apontar para '.../install/p3at_simulation/share'.
    # A função get_package_share_directory() retorna '.../share/p3at_simulation',
    # então usamos os.path.dirname() para obter o diretório pai correto.
    gz_resource_path = os.path.dirname(pkg_share_dir)

    set_gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=gz_resource_path
    )
    # *** FIM DA CORREÇÃO ***
    
    # Caminho para o pacote de integração do Gazebo
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    # Iniciar o Gazebo
    start_gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': '-r empty.sdf'}.items(),
    )

    # Processar o arquivo XACRO do robô (que deve usar model://)
    urdf_file_path = os.path.join(pkg_share_dir, 'urdf', 'p3at.xacro')
    robot_description_config = xacro.process_file(urdf_file_path)
    robot_description = {'robot_description': robot_description_config.toxml()}

    # Iniciar o Robot State Publisher
    start_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[robot_description]
    )

    # Spawner para colocar o robô no Gazebo
    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-topic', 'robot_description', '-entity', 'p3at'],
        output='screen'
    )

    # Spawner de uma pessoa usando modelo do Gazebo Fuel
    person_sdf = """
    <sdf version='1.7'>
        <model name='pessoa1'>
            <include>
                <uri>https://fuel.gazebosim.org/1.0/OpenRobotics/models/Walking Person</uri>
            </include>
        </model>
    </sdf>
    """
    spawn_person = Node(
            package='ros_gz_sim',
            executable='create',
            arguments=[
                    '-name', 'pessoa1',
                    '-x', '2.0', '-y', '0.0', '-z', '0.0',
                    '-string', person_sdf
            ],
            output='screen'
    )

    # No que movimenta a pessoa aleatoriamente apos o spawn
    start_random_person_motion = TimerAction(
        period=4.0,
        actions=[
            Node(
                package='p3at_simulation',
                executable='random_person_motion',
                output='screen',
                parameters=[
                    {'person_name': 'pessoa1'},
                    {'motion_mode': 'set_pose'},
                    {'cmd_vel_topic': '/model/pessoa1/cmd_vel'},
                    {'set_pose_service': '/world/empty/set_pose'},
                    {'update_period_sec': 0.05},
                    {'walk_speed_m_s': 0.8},
                    {'turn_std_dev_rad': 0.15},
                    {'max_turn_rate_rad_s': 0.5},
                    {'start_x': 2.0},
                    {'start_y': 0.0},
                    {'fixed_z': 0.0},
                ],
            )
        ],
    )

    # Ponte ROS <=> Gazebo
    start_ros_gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/model/pessoa1/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/world/empty/set_pose@ros_gz_interfaces/srv/SetEntityPose',
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image',
            '/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V'
        ],
        remappings=[('/odom', '/odom')],
        output='screen'
    )

    return LaunchDescription([
        set_gz_resource_path,
        start_gazebo,
        start_robot_state_publisher,
        spawn_entity,
        spawn_person,
        start_random_person_motion,
        start_ros_gz_bridge
    ])
