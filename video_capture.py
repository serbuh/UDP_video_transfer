# -*- coding: utf-8 -*-
"""
UDP Video Client

Created on Tue Nov 28 16:00:26 2017

@author: Sergey Buh
"""
import cv2
import sys
import numpy as np
import cPickle as pickle
import struct
import socket

# UDP
import UDP_sender

SERVER_ADDR = "127.0.0.1"
SERVER_SEND_VID_PORT = 6001
SERVER_RECV_MSG_PORT = 6002

CLIENT_ADDR = "127.0.0.1"
CLIENT_SEND_MSG_PORT = 5002
CLIENT_RECV_VID_PORT = 5001

MAX_PACKET_SIZE = 1000
MAX_MSG_BUFFER_SIZE = 200

# Timer (for tic(), toc() functions
import Timer

class Capture():
    
    def __init__(self, video_name, max_packet_size):
        self.video_name = video_name        
        # Maximum size of the packet in bytes that can be sent through UDP
        self.max_packet_size = max_packet_size
        
        self.start_video()
        
        cv2.waitKey(1)
        cv2.waitKey(1)
        
        # Get the frame properties
        self.frame_width = self.cap.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)
        self.frame_height = self.cap.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)
        self.frame_count = self.cap.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)
        
        # Initialize UDP video sender
        self.video_sender = UDP_sender.UDP_sender("Video", SERVER_ADDR, SERVER_SEND_VID_PORT, CLIENT_ADDR, CLIENT_RECV_VID_PORT)
        
        # Initialize UDP message receiver
        self.socket_receive_msg = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket_receive_msg.bind((SERVER_ADDR, SERVER_RECV_MSG_PORT))
        self.socket_receive_msg.setblocking(0) # Define a message receiver as a non blocking
        self.run_flag = 0 # define default behaviour if to play video on start or not
        print "-"*20
        print "Message receiver: Running"
        print "-"*20

    def frame_loop(self):
        self.frame_id = 0
        while(True):
            #Timer.Timer.tic()

            
            if(self.listen_for_command() is False): # In case of False returned - Quit command received.
                self.close()
                break
            
            if((self.cap.isOpened()) is False):
                continue # nothing to play. Continue listening for the keys
            
            if self.run_flag == 0: # wait for the run command
                continue

            (ret, frame_orig) = self.cap.read()  # Capture the frame-by-frame
            if frame_orig == None: # No video or video is over
                print "Video capture: End of video"
                self.stop_video()
                continue
            
            
            # Resize the frame
            frame = cv2.resize(frame_orig,(int(self.frame_width/4),int(self.frame_height/4)), interpolation = cv2.INTER_CUBIC)
            
            # Serialize the frame
            serialized_frame = pickle.dumps(frame, pickle.HIGHEST_PROTOCOL)

            print "Frame #{} hash {}".format(self.frame_id, hash(serialized_frame))
            
            
            # Print sizes summary
            serialized_frame_size = len(serialized_frame) # Serialized frame size
            num_of_chunks = -(-serialized_frame_size/self.max_packet_size) # "-(-a/b)" = ceil devision            
            #print "self.frame_id = {0} serialized_frame_size={1}, num_of_chunks={2}".format(self.frame_id, serialized_frame_size, num_of_chunks)
            
            
            # Construct and send Frame Header Packet
            frame_header = struct.pack('BII', 0 ,self.frame_id, num_of_chunks)
            self.video_sender.send(frame_header)

            
            # Construct and send Data Packets of the frame
            for chunk_id in range(num_of_chunks):
                chunk_data = serialized_frame[chunk_id * self.max_packet_size : (chunk_id + 1) * self.max_packet_size]
                chunk_header = struct.pack('BII', 1 ,self.frame_id, chunk_id)
                chunk_packet = chunk_header + chunk_data
                self.video_sender.send(chunk_packet)
            
            # Show frame that was sent
            if (self.show_frame(frame) is False):
                break

            #Timer.Timer.toc("Frame #" + str(self.frame_id))
            self.frame_id = self.frame_id + 1

    def show_frame(self,frame):
        #cv2.imshow('video_orig', frame) # Uncomment it if you want to show the video here
        
        # Stop the capture loop with predefined keyboard key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            self.close()                
            return False
        return True
    
    def listen_for_command(self):
        try:
            control_msg = self.socket_receive_msg.recv(MAX_MSG_BUFFER_SIZE)
            if control_msg == "r": # Run (from the beginning)
                print "(R)estart received"
                self.restart_video()
                self.run_flag = 1
                self.frame_id = 0
            elif control_msg == "c": # Continue
                print "(C)ontinue received"
                self.run_flag = 1
            elif control_msg == "p": # Pause
                print "(P)ause received"
                self.run_flag = 0
            elif control_msg == "s":
                print "(S)top received"
                self.run_flag = 0 # TODO change behaviour of Stop (currently it is like pause)
            elif control_msg == "q":
                print "(Q)uit received"
                return False
                self.close()
            return True
        except:
            return True # no message received - nothing to do
    
    def start_video(self):
        self.cap = cv2.VideoCapture(self.video_name)
        #cv2.namedWindow('video_orig') # Uncomment it if you want to show the video here
        cv2.waitKey(1)
        
    def stop_video(self):
        print "Video capture: Stop"        
        self.cap.release()

    def restart_video(self):
        self.stop_video()
        self.start_video()

    def close(self):
        print "Video capture: Close"
        self.stop_video()
        cv2.destroyAllWindows()        
        self.video_sender.close()
        
# Capture
capture = Capture("DJI_0004.MP4", MAX_PACKET_SIZE)

capture.frame_loop()

#import pdb; pdb.set_trace()
