import random
import csv
from node import Node
import time

PRINT_STEPS = True

def network_to_csv(filename, network):
    with open(filename, 'w') as out:
        csv_out = csv.writer(out)
        for n1, n2, weight in network:
            csv_out.writerow((n1.name, n2.name, weight))

def calculate_paths(node_list, source):
    """
    modified implementation of dijkstra's
    :param node_list:
    :param source:
    :return: { destination -> (first node on path, path length) }
    """
    result = {n: (None, float("inf")) for n in node_list}
    result[source] = (None, 0)#on initial run through the loop this will be chosen as min_node
    node_list = node_list[:]  # make a copy for use in this function
    while node_list:
        min_node = None
        min_node_dist = float("inf")
        #float("inf") < 2 = False

        # find min distanced node
        # The first node will get set to min_node on initial run
        # Then it goes through whole thing to see which is smaller 
        for node in node_list:
            if result[node][1] < min_node_dist:
                min_node = node
                min_node_dist = result[node][1]
                
        if min_node:  #check for disconnected graph
            node_list.remove(min_node)#Node list minus the minimum node
            #Loop through min nodes neighbors
            for neighbor, dist in min_node.neighbors.items():#The distance data is retrieved from the neighbors
                new_dist = result[min_node][1] + dist
                if new_dist < result[neighbor][1]:#If two steps is better than direct, also mostly float("inf")
                    if min_node is source or min_node in source.neighbors:
                        send_to = min_node
                    else:
                        send_to = result[min_node][0]
                    result[neighbor] = (send_to, new_dist)#This is what is filling results with useful data
                else:
                    continue
        else:#This does not get called every time the function is called
            break
    return result

def set_up_network(node_list, network, tag):
    for node in node_list:
        node.get_adjacent_nodes(network)#Fill up node.neighbors
        #Setting neighbors is when their capacity should be defined
        #The capacity is separate from their distance
        paths = calculate_paths(node_list, node)
        for dest, (send_to, path_len) in paths.items():
            if send_to:
                node.add_lookup(dest, send_to if send_to is not node else dest, tag)
#    if PRINT_STEPS:
#        for node in node_list:
#            for neighbor, path_len in node.neighbors.items():
#                print(str(node)+" -> "+str(neighbor)+": "+str(path_len))

#This function will append to the nodelist
def find_or_create_node(name, node_list, names):
    if name not in names:
        new_node = Node(name)
        names.add(name)
        node_list.append(new_node)
        return new_node
    else:
        for node in node_list:
            if node.name == name:
                return node

#Node list and names could just be condensed to a dictionary
#This would make it faster as it wouldn't need to iterate through the list
def load_from_file(filename):
    node_list = []
    network = []
    names = set()
    with open(filename) as csvfile:
        reader = csv.reader(csvfile)
        for n1, n2, weight in reader:
            node1 = find_or_create_node(n1, node_list, names)
            node2 = find_or_create_node(n2, node_list, names)
            network.append((node1, node2, int(weight)))#Add link to network
    return node_list, network

def send_packet(src, dest, size):
    src.send_queue.append((dest, size, src))

#Detect if any of the nodes still have packets in their queue
def network_active(node_list):
    for node in node_list:
        if node.send_queue or node.in_progress:
            return True

#This is the simulation
def send_packets(node_list, packets_to_send):
    #Start simulation
    iteration_num = 0#Counter variable
    # MAIN LOOP
    while packets_to_send or network_active(node_list):
        # send packets if it's their turn
        for packet in packets_to_send[:]:
            if iteration_num == packet[0]:#If iteration num is time to send
                send_packet(*(packet[1:]))
                packets_to_send.remove(packet)
        for node in node_list:
            node.loop_step()
        for node in node_list:
            node.dont_do_yet = []
        print("Iteration: " + str(iteration_num))
        iteration_num += 1
    print("Simulation took " + str(iteration_num) + " iterations");

def create_link(n1, n2, fixed_capacity):
    return (n1, n2, fixed_capacity if fixed_capacity else random.randint(1, 10))

#This creates the initial network
def create_network(node_count=9, fixed_capacity=0):
    """
    :param nodes: how many nodes in the network
    :param fixed_capacity: should there be a fixed capacity between nodes (int)
    :return: list of Nodes, list of (node1, node2, capacity of link)
    """
    network = []
    node_list = []
    for i in range(node_count):
        node_list.append(Node(i))
    for i in range(len(node_list)):
        for j in range(i+1, len(node_list)):
            # add paths randomly between nodes
            if (node_count-1) and random.uniform(0, 1) < 1./(node_count-1):
                network.append(create_link(node_list[i], node_list[j], fixed_capacity))

    # check if any nodes were left out
    for node in node_list:
        for link in network:
            if node is link[0] or node is link[1]:
                break
        else:
            network.append(create_link(node, random.choice(list(n for n in node_list if n is not node)), fixed_capacity))

    if PRINT_STEPS:
        print("Created network with "+str(node_count)+" nodes.")
    return node_list, network

def generate_packets(network, node_list, num_packets):
    #Generate packets to be sent
    packets_to_send = []
    for i in range(0, num_packets):
        n1 = int(random.choice(node_list).name)
        n2 = int(random.choice(node_list).name)
        #(iteration#, source, dest, size)
        packets_to_send.append((0, random.choice(node_list), random.choice(node_list), 10))
    return packets_to_send

#Robustify the network
#This takes a couple of seconds
def generate_robust_network(node_list, network):
    packets_to_send = []
    for i in range(0, 5):
        packets_to_send = generate_packets(network, node_list, 100)

        #Add packets to send queue
        for packet in packets_to_send:
            send_packet(*(packet[1:]))

        for node in node_list:
            result = node.has_route_impossibility()
            if result is not None:
                src, dest = result
                if dest is not None:
                    network.append(create_link(src, dest, False))
            node.send_queue = []
        set_up_network(node_list, network)

def randomly_partition(network):
    num_chunks = 3
    chunked_nwork = []
    for i in range(0, num_chunks):
        chunked_nwork.append([])

    nwork_copy = network[:]
    for link in nwork_copy[:]:
        index = random.randint(0, num_chunks-1)
        chunked_nwork[index].append(link)
        nwork_copy.remove(link)
    return chunked_nwork

def node_list_from_nwork(network):
    node_list = []
    names = set()
    for n1, n2, w in network:
        node1 = find_or_create_node(n1, node_list, names)
        node2 = find_or_create_node(n2, node_list, names)
    return node_list

def randomly_tag_nodes(nodelist):
    for node in nodelist:
        tag = random.randint(0, 3)
        if tag is 0:
            node.tag = tag
        elif tag is 1:
            node.tag = tag
        else:
            node.tag = tag

def calculate_global_mean_slowdown(nodelist):
    net_mean_slowdown_sum = 0
    count = 0
    for node in nodelist:
        if node.completed_flows is not 0:
            net_mean_slowdown_sum+=node.mean_slowdown_sum/node.completed_flows
            count+=1
    return net_mean_slowdown_sum/count

def run_simulations(network, node_list, num_runs):
    #Run network simulation
    count = 0
    for i in range(0, num_runs):
        start = time.time()
        packets_to_send = []
        packets_to_send = generate_packets(network, node_list, 100)
        send_packets(node_list, packets_to_send)
        end = time.time()
        total = end - start
        print("Simulation took: " + str(total) + " secs")
        count += total
        print("Global mean slowdown: " + str(calculate_global_mean_slowdown(node_list)))
        
    print("Average duration of simulation: " + str(count/num_runs))

def bias_network(tag, network):
    for link in network:
        n1, n2, weight = link
        if n2.tag is tag:
            weight = 0
        link = (n1, n2, weight)
        
def main(filename=""):
    #Setup simulation
    if filename:
        node_list, network = load_from_file(filename)
    else:
        node_list, network = create_network(100)

    randomly_tag_nodes(node_list)
    start = time.time()
    #Modify the network for each type of flow
    long_nwork = network[:]
    bias_network("long", long_nwork)
    set_up_network(node_list, long_nwork, "long")#Initial network
    mid_nwork = network[:]
    bias_network("mid", mid_nwork)
    set_up_network(node_list, mid_nwork, "mid")#Initial network
    short_nwork = network[:]
    bias_network("short", short_nwork)
    set_up_network(node_list, short_nwork, "short")#Initial network
    end = time.time()
    print("Time to set up network: " + str(end - start))

    #Set iteration capacity hack
    #This reuses the network proper without bias to set iteration_capacity
    #This is not the same as distances between nodes
    #Needs to be run anytime the network is setup
    #This includes when it is reset up
    for node in node_list:
        node.get_adjacent_nodes(network)
    
    run_simulations(network, node_list, 10)
    
if __name__ == "__main__":
    #main()#Use randomly generated network
    main(filename="nwork.csv")
