#!/usr/bin/env python3

from __future__ import print_function

import roslib; roslib.load_manifest('teleop_twist_keyboard')
import rospy

from geometry_msgs.msg import Twist, Point


import sys, select, termios, tty

msg = """
Reading from the keyboard  and Publishing to Twist!
---------------------------
Moving around:
   u    i    o
   j    k    l
   m    ,    .

For Holonomic mode (strafing), hold down the shift key:
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

a/s : change the lift
d/f : change the yaw
g/h : change the pitch
r: to reset the head 

CTRL-C to quit
"""

moveBindings = {
		'i':(1,0,0,0),
		'o':(1,0,0,-1),
		'j':(0,0,0,1),
		'l':(0,0,0,-1),
		'u':(1,0,0,1),
		',':(-1,0,0,0),
		'.':(-1,0,0,1),
		'm':(-1,0,0,-1),
		'O':(1,-1,0,0),
		'I':(1,0,0,0),
		'J':(0,1,0,0),
		'L':(0,-1,0,0),
		'U':(1,1,0,0),
		'<':(-1,0,0,0),
		'>':(-1,-1,0,0),
		'M':(-1,1,0,0),
		't':(0,0,1,0),
		'b':(0,0,-1,0),
		   }

speedBindings={
		'q':(1.1,1.1),
		'z':(.9,.9),
		'w':(1.1,1),
		'x':(.9,1),
		'e':(1,1.1),
		'c':(1,.9),
		  }

headBindings={
		'a': (1,0,0),
		's': (-1,0,0),
		'd': (0,1,0),
		'f': (0,-1,0),
		'g': (0,0,1),
		'h': (0,0,-1),
		  }

def getKey():
	tty.setraw(sys.stdin.fileno())
	select.select([sys.stdin], [], [], 0)
	key = sys.stdin.read(1)
	termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
	return key


def vels(speed,turn):
	return "currently:\tspeed %s\tturn %s " % (speed,turn)

if __name__=="__main__":
	settings = termios.tcgetattr(sys.stdin)
	
	pub1 = rospy.Publisher('cmd_vel', Twist, queue_size = 1)
	pub2 = rospy.Publisher('head_pos', Point, queue_size = 1)

	rospy.init_node('teleop_twist_keyboard')

	speed = rospy.get_param("~speed", 0.5)
	turn = rospy.get_param("~turn", 1.0)
	x = 0
	y = 0
	z = 0
	th = 0
	status = 0
	
	# head
	lift = 0
	yaw = 50
	pitch = 100

	try:
		print(msg)
		print(vels(speed,turn))
		while(1):
			key = getKey()
			if key in moveBindings.keys():
				x = moveBindings[key][0]
				y = moveBindings[key][1]
				z = moveBindings[key][2]
				th = moveBindings[key][3]
			elif key in speedBindings.keys():
				speed = speed * speedBindings[key][0]
				turn = turn * speedBindings[key][1]

				print(vels(speed,turn))
				if (status == 14):
					print(msg)
				status = (status + 1) % 15
			elif key in headBindings.keys():
				lift += headBindings[key][0]
				if lift < 0: 
					lift = 0
				if lift > 100:
					lift = 100
				yaw += headBindings[key][1]
				if yaw < 0: 
					yaw = 0
				if yaw > 100:
					yaw = 100
				pitch += headBindings[key][2]
				if pitch < 0: 
					pitch = 0
				if pitch > 100:
					pitch = 100
				x = 0
				y = 0
				th = 0
			else:
				x = 0
				y = 0
				z = 0
				th = 0
				if (key == '\x03'):
					break
				elif key == 'r':
					lift = 0
					yaw = 50
					pitch = 100

			twist = Twist()
			twist.linear.x = x*speed; twist.linear.y = y*speed; twist.linear.z = z*speed;
			twist.angular.x = 0; twist.angular.y = 0; twist.angular.z = th*turn
			pub1.publish(twist)

			# head
			point = Point()
			point.x = lift
			point.y = yaw
			point.z = pitch
			pub2.publish(point)

	except Exception as e:
		print(e)

	finally:
		twist = Twist()
		twist.linear.x = 0; twist.linear.y = 0; twist.linear.z = 0
		twist.angular.x = 0; twist.angular.y = 0; twist.angular.z = 0
		pub1.publish(twist)

		termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)