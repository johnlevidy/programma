import json
from input_types import *
import argparse
import pathlib
import networkx

def main(args):
    f = open(args.filepath)
    data = json.load(f)
    operations = [Operation.from_dict(j) for j in data['operations']]
    employees = [Employee.from_dict(dict({'id': i}, **e)) for i, e in enumerate(data['employees'])] 
    num_employees = len(employees)

    # build operations graph 
    G = networkx.Graph()
    for operation in operations:
        G.add_node(operation.name)
    for operation in operations:
        for dep in operation.deps:
            G.add_edge(operation.name, dep)

    print(f"{G.number_of_nodes()} {G.number_of_edges()} {num_employees}")
    for edge in G.edges():
        print(f"{edge[0]} {edge[1]} J1") # TODO: make this correct instead of J1

    for operation in operations:
        print(f"{num_employees} " + " ".join([f"{employee.id} {operation.duration}" for employee in employees]))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process input operations file")
    parser.add_argument('filepath', type=pathlib.Path)
    main(parser.parse_args())
