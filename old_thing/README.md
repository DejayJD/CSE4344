# NetSimulator
Lets build a network and chill

Run program with `python main.py`

This will use testNetworks.csv file to create a network and then run the simulation.
If you wan't to load your own network you can just change the filename.

If you want a randomly generated network use the `create_network()` function.

To write a network to csv
```python
node_list, network = create_network()
network_to_csv('nwork1.csv', network)
```

To visualize a network stored as a csv file change the filename in graph.py.
Then just run graph.py

Also make sure you have dependencies installed
pip install networkx
pip install matplotlib
