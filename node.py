import random
import csv
import time

PRINT_STEPS = True

#Packets are dictionary's its fields are send_to, destination, amount_left, and packet_size

class Node:
    def __init__(self, name):
        self.neighbors = {}  # { other_node -> capacity }
        self.lookup_table = {}  # { destination -> (which node this node sends to, total length) }
        self.name = str(name)  # for printing purposes only
        self.send_queue = []  # [ (destination, packet_size) ] holds tuples
        self.in_progress = []  # [ {send_to, destination, amount_left, packet_size} ]
        self.recv_queue = {}  # { (src, dest) -> cur_amount }
        self.dont_do_yet = []  # [ dest ]
        self.tag = 0
        self.flow_count = 0
        self.completed_flows = 0
        self.mean_slowdown_sum = 0

    def __repr__(self):
        return "Node " + str(self.name)

    #What is link 0 and link 1?
    def get_adjacent_nodes(self, network):
        for link in network:
            if link[0] is self or link[1] is self:
                if link[0] is self:
                    self.neighbors[link[1]] = link[2]
                else:  # link[1] is self
                    self.neighbors[link[0]] = link[2]

    #This adds a route to lookup table                
    def add_lookup(self, destination, send_to, path_len):
        self.lookup_table[destination] = (send_to, path_len)

    def route_packets(self):
        #Packet here is a tuple
        #Iterate through send queue
        #Add id to in progress queue
        #add id to en route dict
        for packet_tuple in self.send_queue:
            destination, packet_size, src = packet_tuple
            if destination in self.lookup_table:
                send_to = self.lookup_table[destination][0]
                if send_to is not src:
                    self.in_progress.append(
                        {
                            "send_to": send_to,
                            "destination": destination,
                            "amount_left": packet_size,
                            "packet_size": packet_size,
                            "sent_from": self,
                            "id": self.flow_count,
                            "lifetime": 1,
                            "release_time": time.time()
                        })
                    self.flow_count+=1
                else:
                    print("IMPOSSIBLE TO ROUTE FROM "+str(self)+" TO "+str(destination))

            self.send_queue.remove(packet_tuple)#This loop literally deletes all things from send queue

    #This method is used for network generation
    def has_route_impossibility(self):
        for packet_tuple in self.send_queue:
            destination, packet_size, src = packet_tuple
            if destination not in self.lookup_table:
                return self, destination
        return None

    def process_queue(self):
        iteration_capacity = self.neighbors.copy()
        # transfer what you can
        for packet in (p for p in self.in_progress if p["destination"] not in self.dont_do_yet):
            amount_possible = min(packet["amount_left"], iteration_capacity[packet["send_to"]])
            #Unimportant
            #***
            if amount_possible:#This line is important
                if (self, packet["destination"]) not in packet["send_to"].recv_queue:
                    packet["send_to"].recv_queue[(self, packet["destination"])] = 0
                if packet["amount_left"] - amount_possible == 0:
                    del packet["send_to"].recv_queue[(self, packet["destination"])]
                    packet["send_to"].dont_do_yet.append(packet["destination"])
                    if packet["send_to"] is not packet["destination"]:
                        packet["send_to"].send_queue.append((packet["destination"], packet["packet_size"], packet["sent_from"]))
                #***
                #Importance begins again
                packet["amount_left"] -= amount_possible
                iteration_capacity[packet["send_to"]] -= amount_possible
                if PRINT_STEPS:
                    print("Node "+self.name+" transferred "+str(amount_possible)+" to "+str(packet["send_to"])
                          +" (final dest: "+str(packet["destination"])+", left: "+str(packet["amount_left"])+")")

        # remove completed packets from in progress queue
        #Possible that when put on progress queue they are flows
        for packet in self.in_progress:
            if packet["amount_left"] == 0:
                #Do math
                packet_mean_slowdown = (time.time() - packet["release_time"])/packet["lifetime"]
                self.mean_slowdown_sum += packet_mean_slowdown
                self.completed_flows+=1
                print("Flow mean slowdown " + str(packet_mean_slowdown))
                #Delete
                self.in_progress.remove(packet)
            else:
                #This one lives to see another day
                packet["lifetime"]+=1

    def loop_step(self):
        self.route_packets()
        self.process_queue()

