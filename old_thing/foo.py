    for i in range(0, 10):    
        packets_to_send = generate_packets(network, node_list, 100)#New set of packets each itera        #Fill the send queue
#        for packet in packets_to_send:
 #           send_packet(*(packet[1:]))

        #Add node in case of impossibility
        for node in node_list:
            result = node.has_route_impossibility()
            if result is not None:
                source, dest = result
                network.append(create_link(source, dest, False))
            #Clear node's send queue
            #node.send_queue = []
            network.append(node.name, random.random

    #packets_to_send = generate_packets(network, node_list, 100)
    #set_up_network(node_list, network)

    #send_packets(node_list, packets_to_send)
 #   network_to_csv("nwork2.csv", network)

    for i in range(0, 100):
        packets_to_send = generate_packets(network, node_list, 100)

        #Add packets to send queue
        for packet in packets_to_send:
            send_packet(*(packet[1:]))
            
        for node in node_list:
            result = node.has_route_impossibility()
            if result is not None:
                src, dest = result
                print("impossibility")
                n1 = get_node_from_node_list(src, node_list)
                n2 = get_node_from_node_list(dest, node_list)
                network.append(create_link(n1, n2, False))
            else:
                print("no impossibles")
            node.send_queue = []

