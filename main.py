import random
import csv
from node import Node

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
    result[source] = (None, 0)
    node_list = node_list[:]  # make a copy for use in here
    while node_list:
        min_node = None
        min_node_dist = float("inf")

        # find min distanced node
        for node in node_list:
            if result[node][1] < min_node_dist:
                min_node = node
                min_node_dist = result[node][1]
        if min_node:  # check for disconnected graph
            node_list.remove(min_node)
            for neighbor, dist in min_node.neighbors.items():
                new_dist = result[min_node][1] + dist
                if new_dist < result[neighbor][1]:
                    if min_node is source or min_node in source.neighbors:
                        send_to = min_node
                    else:
                        send_to = result[min_node][0]
                    result[neighbor] = (send_to, new_dist)
        else:
            break

    return result

def set_up_network(node_list, network):
    for node in node_list:
        node.get_adjacent_nodes(network)
        paths = calculate_paths(node_list, node)
        for dest, (send_to, path_len) in paths.items():
            if send_to:
                node.add_lookup(dest, send_to if send_to is not node else dest, path_len)
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
        if PRINT_STEPS:
            print("ITERATION "+str(iteration_num+1))
        # send packets if it's their turn
        for packet in packets_to_send[:]:
            if iteration_num == packet[0]:
                send_packet(*(packet[1:]))
                packets_to_send.remove(packet)
        for node in node_list:
            node.loop_step()
        for node in node_list:
            node.dont_do_yet = []
        iteration_num += 1
    print("Simulation took "+str(iteration_num)+" iterations")

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


def main(filename=""):
    #Setup simulation
    if filename:
        node_list, network = load_from_file(filename)
    else:
        node_list, network = create_network(100)

    set_up_network(node_list, network)#Initial network
    network_to_csv("nwork2.csv", network)

    #Robustify the network
    packets_to_send = []

    #Actual network simulation
    packets_to_send = []
    packets_to_send = generate_packets(network, node_list, 100)
    send_packets(node_list, packets_to_send)

    print("---------------------------------------------------")
    print("---------------------------------------------------")

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
    packets_to_send = generate_packets(network, node_list, 100)
    send_packets(node_list, packets_to_send)
    network_to_csv("nwork3.csv", network)

if __name__ == "__main__":
    main()#Use randomly generated network
#    main(filename="nwork.csv")
