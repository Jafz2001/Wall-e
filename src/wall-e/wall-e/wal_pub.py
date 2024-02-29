# Basic ROS 2 program to publish real-time streaming 
# video from your built-in webcam
# Author:
# - Addison Sears-Collins
# - https://automaticaddison.com
  
# Import the necessary libraries
import rclpy # Python Client Library for ROS 2
from rclpy.node import Node # Handles the creation of nodes
from sensor_msgs.msg import Image # Image is the message type
from cv_bridge import CvBridge # Package to convert between ROS and OpenCV Images
import cv2 # OpenCV library
import torch
from matplotlib import pyplot as plt
import numpy as np
import speech_recognition as sr
import os
import select
import sys

from geometry_msgs.msg import Twist
from rclpy.qos import QoSProfile

if os.name == 'nt':
    import msvcrt
else:
    import termios
    import tty

BURGER_MAX_LIN_VEL = 0.22
BURGER_MAX_ANG_VEL = 2.84

WAFFLE_MAX_LIN_VEL = 0.26
WAFFLE_MAX_ANG_VEL = 1.82

LIN_VEL_STEP_SIZE = 0.01
ANG_VEL_STEP_SIZE = 0.03

TURTLEBOT3_MODEL = os.environ['TURTLEBOT3_MODEL']


def make_simple_profile(output, input, slop):
  if input > output:
    output = min(input, output + slop)
  elif input < output:
    output = max(input, output - slop)
  else:
    output = input

  return output

def constrain(input_vel, low_bound, high_bound):
  if input_vel < low_bound:
    input_vel = low_bound
  elif input_vel > high_bound:
    input_vel = high_bound
  else:
    input_vel = input_vel

  return input_vel

def print_vels(target_linear_velocity, target_angular_velocity):
  print('currently:\tlinear velocity {0}\t angular velocity {1} '.format(target_linear_velocity, target_angular_velocity))


def check_linear_limit_velocity(velocity):
  if TURTLEBOT3_MODEL == 'burger':
    return constrain(velocity, -BURGER_MAX_LIN_VEL, BURGER_MAX_LIN_VEL)
  else:
    return constrain(velocity, -WAFFLE_MAX_LIN_VEL, WAFFLE_MAX_LIN_VEL)


def check_angular_limit_velocity(velocity):
  if TURTLEBOT3_MODEL == 'burger':
    return constrain(velocity, -BURGER_MAX_ANG_VEL, BURGER_MAX_ANG_VEL)
  else:
    return constrain(velocity, -WAFFLE_MAX_ANG_VEL, WAFFLE_MAX_ANG_VEL)



class ImagePublisher(Node):
  """
  Create an ImagePublisher class, which is a subclass of the Node class.
  """
  def __init__(self):
    """
    Class constructor to set up the node
    """
    # Initiate the Node class's constructor and give it a name
    super().__init__('image_publisher')
      
    # Create the publisher. This publisher will publish an Image
    # to the video_frames topic. The queue size is 10 messages.
    self.publisher_ = self.create_publisher(Image, 'video_frames', 10)
    
    path='/home/waffle1/modelV4.pt'
    self.model = torch.hub.load("~/ultralytics_yolov5_master", "custom", path=path, source='local', force_reload=False)
    
    # We will publish a message every 0.1 seconds
    timer_period = 0.1  # seconds
      
    # Create the timer
    self.timer = self.create_timer(timer_period, self.timer_callback)
         
    # Create a VideoCapture object
    # The argument '0' gets the default webcam.
    self.cap = cv2.VideoCapture(0)
         
    # Used to convert between ROS and OpenCV images
    self.br = CvBridge()
    qos = QoSProfile(depth=10)
    node = rclpy.create_node('teleop_keyboard')
    self.pub = node.create_publisher(Twist, 'cmd_vel', qos)
    self.status = 0
    self.target_linear_velocity = 0.0
    self.target_angular_velocity = 0.0
    self.control_linear_velocity = 0.0
    self.control_angular_velocity = 0.0
    self.cont = 0

  def timer_callback(self):
    """
    Callback function.
    This function gets called every 0.1 seconds.
    """
    # Capture frame-by-frame
    # This method returns True/False as well
    # as the video frame.
    ret, frame = self.cap.read()
    results = self.model(frame)
    if ret == True:
      # Publish the image.
      # The 'cv2_to_imgmsg' method converts an OpenCV
      # image to a ROS 2 image message
      self.publisher_.publish(self.br.cv2_to_imgmsg(np.squeeze(results.render())))
 	
    # Display the message on the console
    results_cpu = results.xyxy[0].cpu().numpy()
    if len(results_cpu) != 0:
      self.cont = 0
      print("cubo detectado :D")
      xmin = results_cpu[0][0]
      xmax = results_cpu[0][2]
      point = (((xmin**2)+(xmax**2))**(1/2))/2
      ref = 240
      err = 40
      if point < (ref - err):
        self.target_angular_velocity =\
          check_angular_limit_velocity(self.target_angular_velocity + ANG_VEL_STEP_SIZE)
        self.status = self.status + 1
        print_vels(self.target_linear_velocity, self.target_angular_velocity)
        
      elif point > (ref + err):
        self.target_angular_velocity =\
          check_angular_limit_velocity(self.target_angular_velocity - ANG_VEL_STEP_SIZE)
        self.status = self.status + 1
        print_vels(self.target_linear_velocity, self.target_angular_velocity)
        
      else:  
        self.target_linear_velocity =\
          check_linear_limit_velocity(self.target_linear_velocity + LIN_VEL_STEP_SIZE)
        self.status = self.status + 1
        self.target_angular_velocity = 0.0
        self.control_angular_velocity = 0.0
        print_vels(self.target_linear_velocity, self.target_angular_velocity)
    else:
      print("cubo no detectado >:(")
      self.cont += 1
      if self.cont == 5:
        self.status = 0
        self.target_linear_velocity = 0.0
        self.target_angular_velocity = 0.0
        self.control_linear_velocity = 0.0
        self.control_angular_velocity = 0.0
    twist = Twist()
    self.control_linear_velocity = make_simple_profile(self.control_linear_velocity, self.target_linear_velocity, (LIN_VEL_STEP_SIZE / 2.0))

    twist.linear.x = self.control_linear_velocity
    twist.linear.y = 0.0
    twist.linear.z = 0.0

    self.control_angular_velocity = make_simple_profile(self.control_angular_velocity, self.target_angular_velocity, (ANG_VEL_STEP_SIZE / 2.0))

    twist.angular.x = 0.0
    twist.angular.y = 0.0
    twist.angular.z = self.control_angular_velocity

    self.pub.publish(twist)	
  
def main(args=None):
  
  # Initialize the rclpy library
  rclpy.init(args=args)
  
  # Create the node
  image_publisher = ImagePublisher()
  
  # Spin the node so the callback function is called.
  rclpy.spin(image_publisher)
    
  image_publisher.destroy_node()
  
  # Shutdown the ROS client library for Python
  rclpy.shutdown()
  
if __name__ == '__main__':
  main()
