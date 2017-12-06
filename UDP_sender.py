# -*- coding: utf-8 -*-
"""
UDP Video Server

Created on Tue Nov 28 16:00:26 2017

@author: Sergey
"""
import socket
import time


#SERVER_ADDR = "127.0.0.1"
#SERVER_SEND_VID_PORT = 6001
#SERVER_RECV_MSG_PORT = 6002

#CLIENT_ADDR = "127.0.0.1"
#CLIENT_SEND_MSG_PORT = 5002
#CLIENT_RECV_VID_PORT = 5001

class UDP_sender:
    
    def __init__(self,  msg_type, from_addr, from_port, to_addr, to_port):
        self.msg_type = msg_type        
        self.from_addr = from_addr
        self.from_port = from_port
        self.to_addr = to_addr
        self.to_port = to_port
        self.socket_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	self.socket_send.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 33445566) # Define bigger buffer size in RAM (Important!). Otherwise packets are lost
	self.socket_send.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 33445566) # Define bigger buffer size in RAM (Important!). Otherwise packets are lost
	print "-"*20
	print "{} sender: Running".format(msg_type)
        
    def send_loop_example(self):
        i = 0
        while True:
            msg = "msg(" + str(i) + ")"
            
            print "Sending " + str(self.msg_type) + ": " + msg
            self.send(msg)
            
            time.sleep(0.5)
            i = i + 1

    def send(self, msg):
        #print "Sending: " + msg
        self.socket_send.sendto(msg, (self.to_addr, self.to_port))
        
    def close(self):
        self.socket_send.close()


# Sending example (use within Capture)
#sender = UDP_sender("msg1", SERVER_ADDR, SERVER_SEND_VID_PORT, CLIENT_ADDR, CLIENT_RECV_VID_PORT)
#msg = "msg to send"
#sender.send(msg)
#sender.close()

#import pdb; pdb.set_trace()
