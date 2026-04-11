# ros2_jazzy_p3at

Workspace ROS 2 Jazzy para simulacao do P3AT no Gazebo Harmonic, com:

- pacote principal `p3at_simulation` (launch, URDF/Xacro, meshes, bridge ROS <-> Gazebo)
- nos de controle ROS2 (`teleop_keyboard`, `rotate_controller`, `speed_controller`)
- script de validacao do ambiente Gym/ROS2 (`test_gym_p3at_ros2_updated.py`)

## Requisitos

- Ubuntu 24.04
- ROS 2 Jazzy instalado em `/opt/ros/jazzy`
- Gazebo Harmonic via integracao `ros_gz`

Instalacao de dependencias:

```bash
sudo apt update
sudo apt install -y \
    ros-jazzy-xacro \
    ros-jazzy-robot-state-publisher \
    ros-jazzy-geometry-msgs \
    ros-jazzy-nav-msgs \
    ros-jazzy-ros-gz \
    ros-jazzy-ros-gz-sim \
    ros-jazzy-ros-gz-bridge \
    ros-jazzy-ros-gz-interfaces \
    ros-jazzy-teleop-twist-keyboard
```

## Estrutura do projeto

- `src/p3at_simulation`: pacote ROS2 principal
- `src/p3at_simulation/launch/p3at_gazebo.launch.py`: launch da simulacao
- `src/p3at_simulation/p3at_simulation/teleop.py`: teleop por teclado (node ROS2)
- `src/p3at_simulation/p3at_simulation/rotate_controller.py`: rotacao por angulo alvo
- `src/p3at_simulation/p3at_simulation/speed_controller.py`: controle para objetivo `(x, y)` usando odometria
- `test_gym_p3at_ros2_updated.py`: teste de integracao do ambiente Gym ROS2

## Configuracao do ambiente

Na raiz do workspace (`/home/ubuntu24/ros2_jazzy_p3at`):

```bash
cd /home/ubuntu24/ros2_jazzy_p3at
source /opt/ros/jazzy/setup.bash
source venv_ros2/bin/activate
```

Depois do build, carregue tambem:

```bash
source install/setup.bash
```

## Build

Build completo:

```bash
cd /home/ubuntu24/ros2_jazzy_p3at
source /opt/ros/jazzy/setup.bash
colcon build
source install/setup.bash
```

Build apenas do pacote principal:

```bash
colcon build --packages-select p3at_simulation
source install/setup.bash
```

## Executar simulacao

```bash
ros2 launch p3at_simulation p3at_gazebo.launch.py
```

Esse launch inicia:

- Gazebo (`ros_gz_sim`)
- `robot_state_publisher`
- spawn do P3AT
- spawn de uma pessoa no cenario
- node `random_person_motion`
- `ros_gz_bridge` para `/cmd_vel`, `/odom`, `/scan`, `/camera/image_raw`, `/tf`

## Comandos de movimento

Publicar comando de avance continuo:

```bash
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
    "{linear: {x: 0.3, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}" -r 10
```

Publicar giro:

```bash
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
    "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.6}}" -r 10
```

Parar o robo:

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
    "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

## Controladores ROS2 incluidos

Teleop por teclado do pacote:

```bash
ros2 run p3at_simulation teleop_keyboard
```

Rotacao unica por angulo alvo:

```bash
ros2 run p3at_simulation rotate_controller --ros-args \
    -p angle_deg:=90.0 \
    -p angular_speed_deg_s:=30.0 \
    -p clockwise:=true
```

Controle para ponto alvo via odometria:

```bash
ros2 run p3at_simulation speed_controller --ros-args \
    -p goal_x:=3.0 \
    -p goal_y:=3.0 \
    -p linear_speed_m_s:=0.5 \
    -p angular_speed_rad_s:=0.3
```

## Teste do ambiente Gym ROS2

Com ambiente Python ativo:

```bash
python test_gym_p3at_ros2_updated.py
```

Esse script valida registro do ambiente `p3at-v2-ros2`, imports, dependencias e artefatos esperados.

## Boas praticas de versionamento

- nao versionar ambientes virtuais (`venv_ros2/`)
- nao versionar artefatos de build (`build/`, `install/`, `log/`)

## Fluxo recomendado (resumo)

1. Abrir terminal na raiz do workspace.
2. `source /opt/ros/jazzy/setup.bash`
3. `source venv_ros2/bin/activate`
4. `colcon build` (quando houver mudancas)
5. `source install/setup.bash`
6. `ros2 launch p3at_simulation p3at_gazebo.launch.py`
7. Em outro terminal com os mesmos `source`, executar controle/teleop.
