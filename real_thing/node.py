import time
PRINT_STEPS = False

class Node:
    def __init__(self, name):
        self.neighbors = {"short":{}, "mid":{}, "long":{}, "default":{}}  # { other_node -> (weight, capacity) }
        self.lookup_table = {"short":{}, "mid":{}, "long":{}, "default":{}}
        self.name = name
        self.send_queue = list() 
        self.in_progress = list()
        self.completed_flows = 0
        self.mean_slowdown_sum = 0
        self.tag = ""

    def __repr__(self):
        return "Node " + str(self.name)

    def reset_node(self):
        self.send_queue = []
        self.in_progress = []
        self.completed_flows = 0
        self.mean_slowdown_sum = 0

    #Neighbors
    def get_adjacent_nodes(self, network, tag=None):
        if not tag: tag = "default"
        neighbors = self.neighbors[tag]
        for n1, n2, weight, capacity in network:
            if n1 is self.name or n2 is self.name:
                if n1 is self.name:
                    neighbors[n2] = (weight, capacity)
                else:  # n2 is self
                    neighbors[n1] = (weight, capacity)

    def add_lookup(self, destination, send_to, tag=None):
        if not tag: tag = "default"
        self.lookup_table[tag][destination] = send_to

    def tag_packet(self, size):
        tag = None
        if size <= 3:
            tag = "short"
        elif size > 3 and size <= 6:
            tag = "mid"
        elif size > 6:
            tag = "long"
        else:
            tag = "default"
        return tag

    def route_packets(self, tag=None):
        for packet in self.send_queue[:]:
            dest, size, src = packet
            if not tag:
                p_tag = "default"
            else:
                p_tag = self.tag_packet(size)
                
            if dest in self.lookup_table[p_tag]:
                send_to = self.lookup_table[p_tag][dest]
                if send_to is not src:
                    self.in_progress.append(
                        {
                            "send_to": send_to,
                            "destination": dest,
                            "amount_left": size,
                            "packet_size": size,
                            "sent_from": self.name,
                            "lifetime": 1,
                            "release_time": time.time(),
                            "tag": p_tag
                        })
                else:
                    print("CYCLE DETECTED, PACKET HAS BEEN DROPPED")
            else:
                if self.name is not dest:
                    if PRINT_STEPS: print("IMPOSSIBLE TO ROUTE FROM "+str(self.name)+" TO "+str(dest))
            self.send_queue.remove(packet)

    #Neighbors        
    def process_queue(self, node_table):
        # transfer what you can
        for packet in (p for p in self.in_progress):
            p_tag = packet["tag"]
            amount_possible = min(packet["amount_left"], self.neighbors[p_tag][packet["send_to"]][1])
            if amount_possible:
                if packet["amount_left"] - amount_possible == 0:  # it finishes sending on this iteration
                    if packet["send_to"] is not packet["destination"]:
                        node_table[packet["send_to"]].send_queue.append((packet["destination"], packet["packet_size"], packet["sent_from"]))
                packet["amount_left"] -= amount_possible
                if PRINT_STEPS:
                    print("Node "+str(self.name)+" transferred "+str(amount_possible)+" to "+str(packet["send_to"])
                          +" (final dest: "+str(packet["destination"])+", left: "+str(packet["amount_left"])+")")

        # remove completed packets from queue
        for packet in self.in_progress[:]:
            if packet["amount_left"] == 0:
                #Calculate mean slowdown of the flow
                flow_mean_slowdown = (time.time() - packet["release_time"])/packet["lifetime"]
                self.mean_slowdown_sum += flow_mean_slowdown
                self.completed_flows+=1
                self.in_progress.remove(packet)
            else:
                packet["lifetime"]+=1

    def loop_step(self, node_table, tag=None):
        self.route_packets(tag)
        self.process_queue(node_table)
