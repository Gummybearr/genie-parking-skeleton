import xhat as hw
import time
import cv2
import config as cfg
#import opidistance3 as dc
import tensorflow as tf
import scipy.misc
import numpy as np
import model

import os
import sys
import signal
import csv
import socket
from pyA20.gpio import gpio
from pyA20.gpio import port

gpio.init()

if __name__ == '__main__':
    sess = tf.InteractiveSession()
    saver = tf.train.Saver()
    saver.restore(sess, "save/model.ckpt")

    start_flag = False
    pleaseStop = 0
    parkingDirection = 1
    parkingCount = 0

    #testing speed variation
    speed_change_flag = False
    getCarFlag=0
    if speed_change_flag:
        cfg.maxturn_speed = cfg.ai_maxturn_speed
        cfg.minturn_speed = cfg.ai_minturn_speed
        cfg.normal_speed_left = cfg.ai_normal_speed_left
        cfg.normal_speed_right = cfg.ai_normal_speed_right

    c = cv2.VideoCapture(0)
    c.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    c.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    #c.set(cv2.CAP_PROP_FPS, 15)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sock.bind(('', 50080))
    print("listening...")
    
    d_flag = False

    waitingVoice = True

    while(True):
        if(waitingVoice):
            data, addr = sock.recvfrom(65535)
            start_flag = True
            waitingVoice = False
            gpio.setcfg(port.PA9, gpio.OUTPUT)
            gpio.output(port.PA9,gpio.HIGH)
        else:
            _,full_image = c.read()
            #full_image = cv2.resize(full_image, (320,240))
            image = scipy.misc.imresize(full_image[cfg.modelheight:], [66, 200]) / 255.0
            image1 = scipy.misc.imresize(full_image[cfg.modelheight:], [66*2, 200*2])

            #cv2.imshow('original',full_image)
            #cv2.imshow("view of AI", cv2.cvtColor(image1, cv2.COLOR_RGB2BGR))
            cv2.imshow("view of AI", full_image)


            wheel = model.y.eval(session=sess,feed_dict={model.x: [image], model.keep_prob: 1.0})
            cfg.wheel = np.argmax(wheel, axis=1)
            #print('wheel value:', cfg.wheel, wheel)
            print('wheel value:', cfg.wheel, model.softmax(wheel))


            k = cv2.waitKey(5)
            if k == ord('q'):  #'q' key to stop program
                break

            """ Toggle Start/Stop motor movement """
            if k == ord('a'):
                if start_flag == False:
                    start_flag = True
                else:
                    start_flag = False
                print('start flag:',start_flag)

            if k == ord('d'):
                if d_flag == False:
                    d_flag = True
                else:
                    d_flag = False:
                print('Parking Mode On')
                
            if start_flag:
                if not d_flag:
                    if cfg.wheel == 0:
                        hw.motor_two_speed(0)
                        hw.motor_one_speed(0)
                        start_flag = False

                    if cfg.wheel == 1:   #left turn
                        hw.motor_two_speed(cfg.minturn_speed)
                        hw.motor_one_speed(cfg.maxturn_speed)

                    if cfg.wheel == 2:
                        hw.motor_two_speed(cfg.normal_speed_left)
                        hw.motor_one_speed(cfg.normal_speed_right)

                    if cfg.wheel == 3:   #right turn
                        hw.motor_two_speed(cfg.maxturn_speed)
                        hw.motor_one_speed(cfg.minturn_speed)
                else:
                    if parkingDirection == 0:
                    if parkingCount < 80:
                        hw.motor_two_speed(cfg.normal_speed_left)
                        hw.motor_one_speed(cfg.normal_speed_right)
                    #Left
                    elif parkingDirection == 1:
                        if parkingCount < 8:
                            hw.motor_two_speed(cfg.minturn_speed)
                            hw.motor_one_speed(cfg.maxturn_speed)
                        elif parkingCount < 20:
                            hw.motor_two_speed(cfg.normal_speed_left)
                            hw.motor_one_speed(cfg.normal_speed_right)
                        elif parkingCount < 27:
                            hw.motor_two_speed(cfg.maxturn_speed)
                            hw.motor_one_speed(cfg.minturn_speed)
                        elif parkingCount < 40:
                            hw.motor_two_speed(cfg.normal_speed_left)
                            hw.motor_one_speed(cfg.normal_speed_right)
                        else:
                            d_flag = False
                            start_flag = False
                    #Right
                    else:
                        if parkingCount < 10:
                            hw.motor_two_speed(cfg.maxturn_speed)
                            hw.motor_one_speed(cfg.minturn_speed)
                        elif parkingCount < 30:
                            hw.motor_two_speed(cfg.normal_speed_left)
                            hw.motor_one_speed(cfg.normal_speed_right)
                        elif parkingCount < 50:
                            hw.motor_two_speed(cfg.minturn_speed)
                            hw.motor_one_speed(cfg.maxturn_speed)
                        elif parkingCOunt < 65:
                            hw.motor_two_speed(cfg.normal_speed_left)
                            hw.motor_one_speed(cfg.normal_speed_right)
                        else:
                            d_flag = False
                            start_flag = False
                    parkingCount+=1
            else:
                hw.motor_one_speed(0)
                hw.motor_two_speed(0)
                gpio.output(port.PA9,gpio.LOW)
                cfg.wheel = 0
                waitingVoice = True
                sock.sendto(str.encode("1"), addr)

gpio.output(port.PA9, gpio.LOW)
hw.motor_clean()
cv2.destroyAllWindows()
