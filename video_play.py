# -*- coding: utf-8 -*-
"""
UDP Video Client

Created on Tue Nov 28 16:00:26 2017

@author: Sergey Buh
"""
import socket
import time
import cv2
import cPickle as pickle
import numpy as np
import struct
import select

import UDP_sender

SERVER_ADDR = "127.0.0.1"
SERVER_SEND_VID_PORT = 6001
SERVER_RECV_MSG_PORT = 6002

CLIENT_ADDR = "127.0.0.1"
CLIENT_SEND_MSG_PORT = 5002
CLIENT_RECV_VID_PORT = 5001

MAX_PACKET_SIZE = 1000
MAX_BUFFER_SIZE = MAX_PACKET_SIZE*2 #?
MAX_MSG_BUFFER_SIZE = 200
RECEIVE_TIMEOUT_IN_SECONDS = 0.01

class Video_RC:
    
    def __init__(self, video_receiver):
        self.video_receiver = video_receiver
        # Initialize UDP message sender
        self.msg_sender = UDP_sender.UDP_sender("Message", CLIENT_ADDR, CLIENT_SEND_MSG_PORT, SERVER_ADDR, SERVER_RECV_MSG_PORT)
    
    def wait_for_command(self):
        key = cv2.waitKey(1)

        if key == -1: # Nothing pressed
            pass
        elif key == 1048690: # Send (R)un message
            print "(R)estart"
            self.msg_sender.send('r')
        elif key == 1048675:  # Send (C)ontinue message
            print "(C)ontinue"
            self.msg_sender.send('c')
        elif key == 1048688:  # Send (P)ause message
            print "(P)ause"
            self.msg_sender.send('p')
        elif key == 1048691:  # Send (S)top message
            print "(S)top"
            self.msg_sender.send('s')
        elif key == 1048689:  # Send (Q)uit message
            print "(Q)uit"
            self.msg_sender.send('q')
            self.close()
            return False # send stop signal to video receiver
        else:
            print "{} pressed".format(key) # Print value
        return True # continue
    
    def close(self):
        self.msg_sender.close()


class Video_receiver:
    
    def __init__(self):

        # Initialize UDP video receiver
        self.socket_receive = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket_receive.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 33445566) # Define bigger buffer size in RAM (Important!). Otherwise packets are lost
        self.socket_receive.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 33445566) # Define bigger buffer size in RAM (Important!). Otherwise packets are lost
        self.socket_receive.bind((CLIENT_ADDR, CLIENT_RECV_VID_PORT))
        #self.socket_receive.setblocking(0) # Define a video socket as a non-blocling
        
        print "-"*20 + "\n" + "Video receiver: Running"
        # Initialize UDP message sender (inside video_RC)
        self.video_rc = Video_RC(self)
        print "-"*20
        
        cv2.namedWindow('video_recv')
        cv2.waitKey(1)
        
            
    def recv_packet(self):
        msg = self.socket_receive.recv(MAX_BUFFER_SIZE)
        msg_header_packed = msg[0:struct.calcsize('BII')]
        msg_data = msg[struct.calcsize('BII'):]
        msg_header = struct.unpack('BII', msg_header_packed)
        msg_type = msg_header[0]
        msg_id_1 = msg_header[1]
        msg_id_2 = msg_header[2]
        return (msg_type, msg_id_1, msg_id_2, msg_data)
    
    def recv_packet_select(self):
        s = select.select([self.socket_receive], [], [], RECEIVE_TIMEOUT_IN_SECONDS)
        if len(s[0]) != 0:
            msg = self.socket_receive.recv(MAX_BUFFER_SIZE)
            msg_header_packed = msg[0:struct.calcsize('BII')]
            msg_data = msg[struct.calcsize('BII'):]
            msg_header = struct.unpack('BII', msg_header_packed)
            msg_type = msg_header[0]
            msg_id_1 = msg_header[1]
            msg_id_2 = msg_header[2]
            return (msg_type, msg_id_1, msg_id_2, msg_data)
        else:
            return (-1, -1, -1, -1)
    
    def receive_video(self):
        while True:
            # Listen for command (cv2.Waitkey(1) is inside the function)
            if(self.video_rc.wait_for_command() is False): # In case of False returned - Quit command received.
                self.close()
                break
            
            # Get packet
            (msg_type, msg_id_1, msg_id_2, msg_data) = self.recv_packet_select()
            #print "Type={} ID={} ID2={} data={}".format(msg_type, msg_id_1, msg_id_2, msg_data)            
            
            if msg_type == -1:
                pass#; print "Wrong packet sequence. recv_packets did not get any packets (none blocking)"
            elif msg_type == 1:
                pass#; print "Wrong packet sequence. Packets of type 1(chunks) must come after packets of type 2(frames)"
            elif msg_type == 0: # Got the new frame packet (type = 0). Expecting to get the chunks now
                (frame_id_expected, num_of_chunks) = (msg_id_1, msg_id_2)
                
                frame_serialized = ''
                chunk_id_expected = 0
                while chunk_id_expected < num_of_chunks:
                #for chunk_id_expected in range(num_of_chunks):

                    # Get packet
                    (msg_type, frame_id, chunk_id, chunk) = self.recv_packet_select()
                    #print "Type={} ID={} ID2={}".format(msg_type, frame_id, chunk_id) 

                    if msg_type == -1:
                        pass; print "Wrong packet sequence. recv_packets did not get any packets (none blocking)"
                    elif msg_type == 0:
                        pass; print "Wrong packet sequence. Packets of type 0(frame) must come after all the chunks (type 1)"
                    elif msg_type == 1:
                        if chunk_id_expected != chunk_id:
                            print "Frame #{}: Scheiße. Expected chunk {} but received chunk {}".format(frame_id_expected, chunk_id_expected, chunk_id)
                            break
                        frame_serialized += chunk # add received chunk to a frame
                        chunk_id_expected = chunk_id_expected + 1
                    else:
                        print "Frame #{}: Scheiße. expected msg_type is wrong. While expecting chunk {}".format(frame_id_expected, chunk_id_expected)
                        break
                    
                    # Check if the frame is ready to be built
                    if (chunk_id_expected == num_of_chunks):
                        # All chunks are ready. Build the frame
                        try:
                            frame = pickle.loads(frame_serialized)                            
                        except:
                            print "Frame #{}: Got all the chunks, but unpickling failed.".format(frame_id_expected)
                            
                        print "Frame #{}: Show Time! hash {}".format(frame_id_expected, hash(frame.tostring()))
                        self.do_stuff_with_frame(frame)
                        #cv2.waitKey(1)
            else:
                pass#; print "msg_type is not recognized"

    def do_stuff_with_frame(self, frame):
        cv2.imshow('video_recv', frame)

    def receive_loop_simple_example(self):
        i = 0
        while True:
            msg = self.socket_receive.recv(MAX_BUFFER_SIZE)
            print "Receiving: " + msg
            
            time.sleep(0.5)
            i = i + 1

    
    def close(self):
        self.socket_receive.close()
        cv2.destroyAllWindows()
        print "Video play: Windows closed!"


receiver = Video_receiver()
receiver.receive_video()
print "Video play: Bye!"
#import pdb; pdb.set_trace()
