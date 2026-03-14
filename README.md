# p3at_simulation

Guia rapido para instalar dependencias, configurar ambiente, compilar e executar a simulacao do P3AT com ROS 2 Jazzy e Gazebo Harmonic.

## 1. Requisitos

- Ubuntu 24.04
- ROS 2 Jazzy instalado em /opt/ros/jazzy
- Workspace em /home/ubuntu24/ros2_jazzy

## 2. Instalacao de dependencias

Instale os pacotes necessarios para o launch atual:

    sudo apt update
    sudo apt install -y \
      ros-jazzy-xacro \
      ros-jazzy-ros-gz \
      ros-jazzy-teleop-twist-keyboard

Observacao:
- ros-jazzy-ros-gz e a integracao oficial ROS 2 Jazzy com Gazebo Harmonic.
- Esse meta pacote inclui, entre outros, ros_gz_sim e ros_gz_bridge.

## 3. Configuracao do ambiente

Em cada novo terminal, carregue os ambientes nesta ordem:

    source /opt/ros/jazzy/setup.bash
    source /home/ubuntu24/ros2_jazzy/install/setup.bash

Opcional para automatizar o ROS 2 base no bash:

    echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
    source ~/.bashrc

## 4. Compilacao do workspace

Na raiz do workspace:

    cd /home/ubuntu24/ros2_jazzy
    source /opt/ros/jazzy/setup.bash
    colcon build
    source install/setup.bash

Para compilar somente este pacote:

    colcon build --packages-select p3at_simulation

## 5. Executar a simulacao

Com ambiente carregado:

    ros2 launch p3at_simulation p3at_gazebo.launch.py


## 6. Publicacao de velocidade em /cmd_vel

Movimento para frente continuo a 10 Hz:

    ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.3, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}" -r 10

Giro no proprio eixo a 10 Hz:

    ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.6}}" -r 10

Parada imediata (envio unico):

    ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"

Monitorar topico:

    ros2 topic echo /cmd_vel

## 7. Controle por teclado (opcional)

    ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/cmd_vel

## 9. Ordem recomendada de uso no dia a dia

1. Abrir terminal
2. source /opt/ros/jazzy/setup.bash
3. source /home/ubuntu24/ros2_jazzy/install/setup.bash
4. Subir simulacao com ros2 launch
5. Publicar comandos em /cmd_vel por outro terminal com os mesmos source
