import random
import csv
from node import Node
import time
from copy import deepcopy
from multiprocessing import Pool
from functools import partial

PRINT_STEPS = False

def gen_link(n1, n2, fixed_capacity=0):
    return (n1, n2, 1, fixed_capacity if fixed_capacity else random.randint(1, 10))

#This is currently broken
def create_network(node_list, fixed_capacity=0):
    """
    :param nodes: how many nodes in the network
    :param fixed_capacity: should there be a fixed capacity between nodes (int)
    :return: list of Nodes, list of (node1, node2, capacity of link)
    """
    nodes = len(node_list)
    network = list()
    for i in range(len(node_list)):
        for j in range(i+1, len(node_list)):
            # add paths randomly between nodes
            if (nodes-1) and random.uniform(0, 1) < 1./(nodes-1):
                network.append(gen_link(node_list[i].name, node_list[j].name, fixed_capacity))

    # check if any nodes were left out
    for node in node_list:
        for link in network:
            if node is link[0] or node is link[1]:
                break
            else:
                network.append(gen_link(node.name, random.choice(list(n.name for n in node_list if n is not node)), fixed_capacity))
                
    if PRINT_STEPS:
        print("Created network with "+str(nodes)+" nodes.")
    return network

def calculate_paths(node_table, source, tag=None):
    """
    modified implementation of dijkstra's
    :param node_list:
    :param source:
    :return: { destination -> (first node on path, path length) }
    """
    node_list = node_table.keys()[:]  # make a copy for use in here
    paths = {n: (None, float("inf"), 1) for n in node_list}
    paths[source] = (None, 0, 1)
    if not tag: tag = "default"
    #dijkstra's algorithm
    while node_list:
        min_node = None
        min_node_dist = float("inf")

        # find min distanced node
        for node in node_list:
            if paths[node][1] < min_node_dist:
                min_node = node
                min_node_dist = paths[node][1]
        if min_node:  # check for disconnected graph
            node_list.remove(min_node)
            for neighbor, (dist, capacity) in node_table[min_node].neighbors[tag].items():
                new_dist = paths[min_node][1] + dist
                if new_dist < paths[neighbor][1]:
                    if min_node == source or min_node in node_table[source].neighbors[tag]:
                        send_to = min_node
                    else:
                        send_to = paths[min_node][0]

                    if neighbor in node_table[source].neighbors[tag]:
                        send_to = neighbor
                    paths[neighbor] = (send_to, new_dist, capacity)
        else:
            break

    return paths

def learn_your_neighbors(node_table, network, tag=None):
    for node in node_table.values():
        node.get_adjacent_nodes(network, tag)

def write_lookup_tables(node_table, tag=None):
    for k, v in node_table.iteritems():
        paths = calculate_paths(node_table, k, tag)
        for dest, data in paths.iteritems():
            send_to, weight, capacity = data
            if send_to:
                v.add_lookup(dest, send_to if send_to is not v else dest, tag)
    
def setup_network(node_table, network, tag=None):
    learn_your_neighbors(node_table, network, tag)
    write_lookup_tables(node_table, tag)

def load_from_file(filename):
    network = []
    node_table = {}
    with open(filename) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            n1, n2, weight, capacity = map(int, row)
            if n1 not in node_table: node_table[n1] = Node(n1)
            if n2 not in node_table: node_table[n2] = Node(n2)
            network.append((n1, n2, weight, capacity))
    return node_table, network

def send_packet(src, dest, size, sent_from):
    src.send_queue.append((dest, size, sent_from))

def send_packets(node_table, packets_to_send):
    iteration_num = 0
    for packet in packets_to_send[:]:
        num, src, dest, size = packet
        if iteration_num == num:
            send_packet(node_table[src], dest, size, src)
            packets_to_send.remove(packet)
            
def network_active(node_table):
    for node in node_table.values():
        if node.send_queue or node.in_progress:
            return True

def calculate_global_mean_slowdown(node_table):
    net_mean_slowdown_sum = 0
    count = 0
    for node in node_table.values():
        if node.completed_flows is not 0:
            net_mean_slowdown_sum+=node.mean_slowdown_sum/node.completed_flows
            count+=1
    if count is 0: count = 1
    return net_mean_slowdown_sum/count

def print_results(results):
    global_mean_slowdown, total_time, iterations = results
    print("Simulation took "+str(iterations)+" iterations")
    print("Global mean slowdown: " + str(global_mean_slowdown))
    print("Total simulation time: " + str(total_time) + " seconds")
        
def run_simulation(node_table, packets_to_send, tag=None):
    iteration_num = 0
    start = time.time()
    # MAIN LOOP
    while packets_to_send or network_active(node_table):
        if PRINT_STEPS:
            print("ITERATION "+str(iteration_num+1))
        # send packets if it's their turn
        send_packets(node_table, packets_to_send)
        for node in node_table.values():
            node.loop_step(node_table, tag)
        iteration_num += 1
    end = time.time()
    global_mean_slowdown = calculate_global_mean_slowdown(node_table)
    total = end - start
    for n in node_table.values():
        n.reset_node()
    return (global_mean_slowdown, total, iteration_num)

def generate_packets(node_table, packet_count, precedence={}):
    packets = []
    node_list = node_table.keys()
    for i in range(0, packet_count):
        n1 = random.choice(node_list)
        n2 = random.choice(node_list)
        if n1 not in precedence:
            size = random.randint(1, 10)
            precedence[n1] = size
        else:
            size = precedence[n1]
            noise = random.randint(-1, 1)
            if size + noise <= 10 and size + noise >= 1:
                size = size + noise
        packets.append((0, n1, n2, size))
    return packets, precedence

def random_encoding(node_table):
    encoding = []
    for node in node_table.keys():
        n = random.randint(0, 3)
        if n is 0:
            encoding.append("short")
        elif n is 1:
            encoding.append("mid")
        else:
            encoding.append("long")
    return encoding

def bias_network(node_table, network, tag):
    nwork = []
    for link in network:
        n1, n2, w, c = link
        if node_table[n2].tag is tag:
            w = 0
        nwork.append((n1, n2, w, c))
    return nwork

def setup_tagged_network(node_table, network):
    setup_network(node_table, bias_network(node_table, network, "short"), "short")
    setup_network(node_table, bias_network(node_table, network, "mid"), "mid")
    setup_network(node_table, bias_network(node_table, network, "long"), "long")
    
#Performs deep copy of the node_table and returns modified version
def tagged_node_table(node_table, network, encoding=None):
    node_table2 = deepcopy(node_table)
    
    if not encoding: encoding = random_encoding(node_table2)

    for n, e in zip(node_table2.values(), encoding):
        n.tag = e
            
    setup_tagged_network(node_table2, network)
    return node_table2

def packets_copies(packets, n):
    return [packets[:] for i in range(0, n)]

def gen_encoding_closure(node_table, network):
    def encoding_fn(encoding):
        return tagged_node_table(node_table, network, encoding)
    return encoding_fn

def gen_encoding_partial(node_table, network):
    def encoding_fn(node_table, network, encoding):
        return tagged_node_table(node_table, network, encoding)
    return partial(encoding_fn, node_table, network)

#Fitness function expects two tuples as args
#individual = (encoding, (slowdown, total, iterations))
def evaluate_population(encoding_result_zip, fitness):
    top = encoding_result_zip[0]
    for er in encoding_result_zip:
      top = fitness(top, er)
    return top

def select_top_2(encodings, results, fitness):
    er_zip = zip(encodings, results)
    first = evaluate_population(er_zip, fitness)
    er_zip.remove(first)
    second = evaluate_population(er_zip, fitness)
    return (first, second)

def slowdown_fitness(ind1, ind2):
    mean_slowdown1 = ind1[1][0]
    mean_slowdown2 = ind2[1][0]
    if mean_slowdown1 < mean_slowdown2:
        winner = ind1
    elif mean_slowdown1 > mean_slowdown2:
        winner = ind2
    else:
        winner = ind1
    return winner

def iteration_fitness(ind1, ind2):
    iterations1 = ind1[1][2]
    iterations2 = ind2[1][2]
    if iterations1 < iterations2:
        winner = ind1
    elif iterations1 > iterations2:
        winner = ind2
    else:
        winner = ind1
    return winner

def total_time_fitness(ind1, ind2):
    total_time1 = ind1[1][2]
    total_time2 = ind2[1][2]
    if total_time1 < total_time2:
        winner = ind1
    elif total_time1 > total_time2:
        winner = ind2
    else:
        winner = ind1
    return winner

def genetics(a, b):
   if random.randint(0, 1):
       if random.randint(0, 1):
           return a
       else:
           return b
   else:
       n = random.randint(0, 2)
       if n is 0:
           return "short"
       elif n is 1:
           return "mid"
       else:
           return "long"

def breed(encodingA, encodingB):
    offspring = []
    for a, b in zip(encodingA, encodingB):
        offspring.append(genetics(a, b))
    return offspring
        
#Parents are part of the offspring in order to persist good ideas
def breed_top_2(top_2, num_offspring):
    num_offspring = num_offspring - 2
    parentA = top_2[0][0]
    parentB = top_2[1][0]
    offspring = []
    for i in range(0, num_offspring):
        offspring.append(breed(parentA, parentB))
    offspring.append(parentA)
    offspring.append(parentB)
    return offspring

def evolve(node_table, network, p_root, pop_size, num_generations, fitness_fn):
    encodings = []
    for i in range(0, pop_size):
        encodings.append(random_encoding(node_table))

    encoding_fn = gen_encoding_closure(node_table, network)
    gen_count = 0
    while gen_count < num_generations:
        tagged_ntables = map(encoding_fn, encodings)
        packet_list = packets_copies(p_root, pop_size)
        results = map(lambda table, packets: run_simulation(table, packets, True), tagged_ntables, packet_list)
        top_2 = select_top_2(encodings, results, fitness_fn)
        encodings = breed_top_2(top_2, pop_size)
        gen_count+=1
    #Run eval fns one more time
    tagged_ntables = map(encoding_fn, encodings)
    packet_list = packets_copies(p_root, pop_size)
    results = map(lambda table, packets: run_simulation(table, packets, True), tagged_ntables, packet_list)
    top_2 = select_top_2(encodings, results, fitness_fn)
    return top_2[0]

def evolve_with_changing_data(node_table, network, p_root, pop_size, num_generations, fitness_fn):
    encodings = []
    for i in range(0, pop_size):
        encodings.append(random_encoding(node_table))

    encoding_fn = gen_encoding_closure(node_table, network)
    gen_count = 0
    precedence = {}
    while gen_count < num_generations:
        packets, precedence = generate_packets(node_table, pop_size, precedence)
        tagged_ntables = map(encoding_fn, encodings)
        packet_list = packets_copies(packets, pop_size)
        results = map(lambda table, packets: run_simulation(table, packets, True), tagged_ntables, packet_list)
        top_2 = select_top_2(encodings, results, fitness_fn)
        encodings = breed_top_2(top_2, pop_size)
        gen_count+=1
    #Run eval fns one more time
    tagged_ntables = map(encoding_fn, encodings)
    packet_list = packets_copies(p_root, pop_size)
    results = map(lambda table, packets: run_simulation(table, packets, True), tagged_ntables, packet_list)
    top_2 = select_top_2(encodings, results, fitness_fn)
    return top_2[0]

    
def main(filename=""):
    if filename:
        node_table, network = load_from_file(filename)
    else:
        node_table = {}
        for i in range(10):
            node_table[i] = Node(i)
        network = create_network(node_table.values(), fixed_capacity=1)

    setup_network(node_table, network)

    p_root, precedence = generate_packets(node_table, 1000)

    print("Untagged network")
    not_tagged_data = run_simulation(node_table, p_root[:])
    print_results(not_tagged_data)

    print("Breeding changing data network")
    start = time.time()
    changing_bred = evolve_with_changing_data(node_table, network, p_root, 20, 30, slowdown_fitness)
    end = time.time()
    print("Breeding changing data process took " + str(end - start) + " seconds")
    print("Changing bred output initial")
    print_results(changing_bred[1])
    if not_tagged_data[0] - changing_bred[1][0] > 0:
        print("Bred individual is more fit")
    else:
        print("Bred individual is less fit")

    print("Performance increase by " + str((changing_bred[1][0] / not_tagged_data[0]) * 100) + " %")

    encoding_fn = gen_encoding_closure(node_table, network)
    nt3 = encoding_fn(changing_bred[0])

    untagged_sums = (0, 0, 0)
    changing_sums = (0, 0, 0)
    num_tests = 200
    percentage_average = 0
    for i in range(0, num_tests):
        packets2, precedence = generate_packets(node_table, 1000, precedence)
        untagged_data = run_simulation(node_table, packets2[:])
        changing_data = run_simulation(nt3, packets2[:])
        untagged_sums = map(lambda a, b: a + b, untagged_sums, untagged_data)
        changing_sums = map(lambda a, b: a + b, changing_sums, changing_data)
    print("Average runs with untagged")
    untagged_results = map(lambda a: a / num_tests, untagged_sums)
    print_results(untagged_results)
    print("Average runs with changing")
    tagged_results = map(lambda a: a / num_tests, changing_sums)
    print_results(tagged_results)
    if tagged_results[0] < untagged_results[0]:
        print("GA is " + str((tagged_results[0] / untagged_results[0]) * 100) + " % more performant")
    else:
        print("Average performance of GA is not better")
    
if __name__ == "__main__":
    main(filename="nwork.csv")
    #main()
