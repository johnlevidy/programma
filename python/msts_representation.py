import json
from input_types import *
import argparse
import pathlib
import networkx

def main(args):
    f = open(args.filepath)
    data = json.load(f)
    operations = [Operation.from_dict(j) for j in data['operations']]
    employees = [Employee.from_dict(j) for j in data['employees']] 
    num_employees = len(employees)
    
    # build operations graph 
    G = networkx.Graph()
    for operation in operations:
        G.add_node(operation.name)
    for operation in operations:
        for dep in operation.deps:
            G.add_edge(operation.name, dep)
   
    print(f"{G.number_of_nodes()} {G.number_of_edges()} {num_employees}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process input operations file")
    parser.add_argument('filepath', type=pathlib.Path)
    main(parser.parse_args())
