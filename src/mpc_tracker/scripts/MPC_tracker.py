#!/usr/bin/env python

import numpy as np
import scipy.sparse as sps
import ipopt
import matplotlib.pyplot as plt
import rospy
# from race.msg import drive_param
from geometry_msgs.msg import PoseStamped
from geometry_msgs.msg import Vector3
from geometry_msgs.msg import Point
from geometry_msgs.msg import Twist
import math
from numpy import linalg as la
from tf.transformations import euler_from_quaternion, quaternion_from_euler

ts = 1
x_goal = 0
y_goal = 0
w_goal = 0 
x_curr = 0
y_curr = 0
w_curr = 0


pub = rospy.Publisher('velocity_omega',Vector3 , queue_size=5)
pub2 = rospy.Publisher('vehicle_Goal',Vector3 , queue_size=5)
pub3 = rospy.Publisher('/catvehicle/cmd_vel', Twist, queue_size=1)
vel_msg = Vector3()
goal_msg = Vector3()
drive_msg = Twist()


def callback1(data):

	#take in the odometry of the vehicle from the localization package.
	global x_curr
	global y_curr
	global w_curr

	qx=data.pose.orientation.x
	qy=data.pose.orientation.y
	qz=data.pose.orientation.z
	qw=data.pose.orientation.w

	quaternion = (qx,qy,qz,qw)
	euler   = euler_from_quaternion(quaternion)

	w_curr     = euler[2] 
	x_curr = data.pose.position.x
	y_curr = data.pose.position.y
	
def callback2(data):

	#take in the goal point to reach from RRT* planner

	global x_goal
	global y_goal
	global w_goal

	x_goal = data.x
	y_goal = data.y
	w_goal = data.z 

def check_omega (w_g):
	global w_curr
	if w_g>3.1:
		return 3.1415
	else:
		return w_curr





class hs071(object):

	#class for optimization of the trajectory

	global ts
	global x_goal
	global y_goal
	global w_goal


	def __init__(self):
		pass

	def objective(self, x):

		#Define the objective function as a return function. 

		return (x_goal - np.sum(x[0]*np.cos(x[1:])*ts) + (y_goal - np.sum(x[0]*np.sin(x[1:])*ts)) + ((x[5]-x[4])+(x[4]-x[3])+(x[3]-x[2])+(x[2]-x[1])+x[1]))
		
	def gradient(self, x):
		#
		# The callback for calculating the gradient
		# #
		return np.array([
					 -	np.sum(np.cos(x[1:])*ts) - np.sum(np.sin(x[1:])*ts), 
					 - (ts * x[0]*np.cos(x[1])) + (ts * x[0]*np.sin(x[1])),
					 - (ts * x[0]*np.cos(x[2])) + (ts * x[0]*np.sin(x[2])),
					 - (ts * x[0]*np.cos(x[3])) + (ts * x[0]*np.sin(x[3])), 
					 - (ts * x[0]*np.cos(x[4])) + (ts * x[0]*np.sin(x[4])), 
					 1 - (ts * x[0]*np.cos(x[5])) + (ts * x[0]*np.sin(x[5]))
					 ])
	
	def constraints(self, x):																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																														
		#
		# The callback for calculating the constraints
		#
		return np.array([x[5]-x[4] , x[4]-x[3] , x[3]-x[2]  ,  x[2]-x[1],  x[5]  , x[1] , x_goal - np.sum(x[0]*np.cos(x[1:])*ts) , y_goal - np.sum(x[0]*np.sin(x[1:])*ts)])
	
	def jacobian(self, x):
		#
		# The callback for calculating the Jacobian
		#
		
		return np.array([0,0,0,0,-1,1,
						0,0,0,-1,1,0,
						0,0,-1,1,0,0, 
						0,-1,1,0,0,0,
						0,0,0,0,0,1,
						0,1,0,0,0,0,
						-np.sum(np.cos(x[1:])*ts) , (ts * x[0]*np.sin(x[1])) , (ts * x[0]*np.sin(x[2])) ,  (ts * x[0]*np.sin(x[3])) , (ts * x[0]*np.sin(x[4])) , (ts * x[0]*np.sin(x[5])),
						- np.sum(np.sin(x[1:])*ts) ,  - (ts * x[0]*np.cos(x[1])) ,  - (ts * x[0]*np.cos(x[2])) , - (ts * x[0]*np.cos(x[3])) , - (ts * x[0]*np.cos(x[4])) , - (ts * x[0]*np.cos(x[5]))])

	
  
	def intermediate(
			self, 
			alg_mod,
			iter_count,
			obj_value,
			inf_pr,
			inf_du,
			mu,
			d_norm,
			regularization_size,
			alpha_du,
			alpha_pr,
			ls_trials
			):

		#
		# Example for the use of the intermediate callback.
		#
		# print("*****************************************")
		# print("Objective value at iteration #%d is - %g" % (iter_count, obj_value))
		pass


def main():
	global x_goal
	global y_goal
	global w_goal

	goal_x = y_goal

	y_goal = x_goal
	x_goal = goal_x

	y_goal = y_goal-10

	# w_curr1 =  check_omega(w_goal)

	w_curr1 = 0

	# x_goal = 10
	# y_goal = -10
	# w_goal = -1.2



	# Define the problem constraints on the optimized variable vector
	x0 = [0, 0, 0, 0, 0 ,0 ]
	
	lb = [0, -3, -3, -3, -3, -3 ]
	ub = [8, 3, 3, 3, 3 , 3 ]


	#define the inequality constraints limit 
	cl = [-0.418, -0.428,-0.428, -0.428, abs(w_goal - w_curr1),-0.4, 0 , 0 ]
	cu = [0.428, 0.428,0.428, 0.428,  abs(w_goal - w_curr1) , +0.4, 100 , 100]

	#define the non linear optimization problem

	nlp = ipopt.problem(
				n=len(x0),
				m=len(cl),
				problem_obj=hs071(),
				lb=lb,
				ub=ub,
				cl=cl,
				cu=cu
				)

	#
	# Set solver options
	#
	#nlp.addOption('derivative_test', 'second-order')
	nlp.addOption(b'mu_strategy', b'adaptive')
	nlp.addOption(b'tol', 1e-7)

	#
	# Scale the problem (Just for demonstration purposes)
	#
	nlp.setProblemScaling(
		obj_scaling=2,
		x_scaling=[1, 1, 1, 1, 1, 1]
		)
	nlp.addOption(b'nlp_scaling_method', b'user-scaling')
	
	#
	# Solve the problem
	#
	x, info = nlp.solve(x0)
	
	# print("Solution of the primal variables: x=%s\n" % repr(x))
	vel = float(x[0])
	omega = float(x[1])
	# vel_msg.x = vel
	# vel_msg.y = omega
	# vel_msg.z = w_curr1

	#publish the message containing the velocity commands. 

	# pub.publish(vel_msg)

	# goal_msg.x = x_goal
	# goal_msg.y = y_goal
	# goal_msg.z = w_goal

	# pub2.publish(goal_msg)

	if vel <0.5:
		vel = 0.5

	drive_msg.linear.x 	= vel
	drive_msg.linear.y 	= 0
	drive_msg.linear.z 	= 0
	drive_msg.angular.z = omega * 1.2
	drive_msg.angular.y = 0 * 1.2
	drive_msg.angular.x = 0 * 1.2

	pub3.publish(drive_msg)


	# print(x_goal)
	# print(y_goal)
	# print(w_goal)


	# print(x)
	# print(vel)
	# print(omega)


	#For plotting Purposes

	# x_coord = np.zeros(6)
	# y_coord = np.zeros(6)
	# xdist=0
	# ydist=0

	# for i in range(len(x)-1):
	#     x_coord[i] 	= xdist
	#     y_coord[i] 	= ydist
	#     xdist 		= xdist + x[0] * np.cos(x[i+1]) *ts
	#     ydist 		= ydist + x[0] * np.sin(x[i+1]) *ts
	# 	x_coord[5] 	= xdist + x[0] * np.cos(x[5]) *ts
	# 	y_coord[5] 	= ydist + x[0] * np.sin(x[5]) *ts

	# print(x_coord)
	# print(y_coord)

	# plt.plot(y_coord,x_coord)
	# plt.show()



	
	# print("Solution of the dual variables: lambda=%s\n" % repr  (info['mult_g']))
	
	# print("Objective=%s\n" % repr(info['obj_val']))


if __name__ == '__main__':
	rospy.init_node('optimizer')
	# rospy.Subscriber('/pf/viz/inferred_pose', PoseStamped, callback1)
	rospy.Subscriber('/get_goal', Point, callback2)
	r = rospy.Rate(40)
	while not rospy.is_shutdown():
		main()
		r.sleep()
