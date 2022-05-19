import json
import time
from input_types import *
import argparse
import pathlib
import networkx
import random

# Runtime roughly O(#nodes)
# Assignment pointer is a tuple (machine, index) that indexes into assignments
def completion_time(task_graph, assignments, node):
    data = task_graph.nodes[node]
    # print(f"Node: {node} -- Data: {data}")
    assignment_pointer = data['assignment_pointer']
    if assignment_pointer[1] == 0 and data['leaf']:
        return data['duration']
    # max of completion time by moving left in the assignment list ( current person working on previously assigned task )
    # and the max completion time of the subtasks
    goleft = completion_time(task_graph, assignments, assignments[assignment_pointer[0]][assignment_pointer[1] - 1]) \
                 if assignment_pointer[1] > 0 else 0
    childrencompletion = [completion_time(task_graph, assignments, c) for c in task_graph.successors(node)]
    # print(f"Node: {node} -- Data: {data}")
    # print(f"Assignee previous maxpath: {goleft}")
    # for c, time in zip(task_graph.successors(node), childrencompletion):
        # print(f"Child {c} completion: {time}")
    return data['duration'] + \
                max(completion_time(task_graph, assignments, assignments[assignment_pointer[0]][assignment_pointer[1] - 1]) \
                    if assignment_pointer[1] > 0 else 0,
                    max([completion_time(task_graph, assignments, c) for c in task_graph.successors(node)] + [0]))

# We reduce the problem space a little bit by only assigning 
# items in a valid order for O(n) cost
def generate_random_solution(task_graph, operations, employees):
    assignments = {e.name: [] for e in employees}
    # Dictionary from operation name to the number of children that have yet to be picked
    unpicked_children = {o.name: len(o.deps) for o in operations}
    # Nodes which are eligible to be picked ( no more children )
    eligible_tasks = [k for k, v in unpicked_children.items() if v == 0]

    # For each operation, make a choice from my available choices,
    # then remove that choice from my eligible nodes list. Then visit
    # all parents of that node and make sure they know their child was picked.
    # If any parents now have no children remaining, add them to the eligibility list.
    for num_assigned in range(0, len(operations)):
        employee_choice = random.choice(employees)
        task_choice = random.choice(eligible_tasks)
        # assign the task to a random employee
        assignments[employee_choice.name].append(task_choice)
        eligible_tasks.remove(task_choice)
        for p in task_graph.predecessors(task_choice):
          unpicked_children[p] -= 1
          if unpicked_children[p] == 0:
              eligible_tasks.append(p)

    return assignments

# Adds a pointer to the assignment to the graph
def add_assignments_to_graph(task_graph, assignments):
    for employee, tasks in assignments.items():
        for i, task in enumerate(tasks):
            task_graph.nodes[task]['assignment_pointer'] = (employee, i)

# Gets all transitive deps for node passed in
def get_transitive_dependencies(task_graph, node):
    successors = set(task_graph.successors(node))
    if not any(successors):
        return set()
    else:
        ret = successors
        for s in successors:
            ret = ret.union(s)
            ret = ret.union(get_transitive_dependencies(task_graph, s))
        return ret 

# Annotates each task in the task graph with a set of all 
# of its transitive dependencies
def add_transitive_dependencies_to_graph(task_graph):
    for n, data in task_graph.nodes(data=True):
        data['transitive_dependencies'] = get_transitive_dependencies(task_graph, n)

# the high level idea here is: 
# 1) n <- randomly selected node to move
# 2) t <- all transitive children of n
# then, for each P_x ( person x's task list ):
# 1) m <- intersection(t, P_x) 
# 2) iterate P_x, remove tasks from m as you visit, when m is empty the 
# positions iterated over are valid
# In plain english: for each person, i cannot work on the moved task until i've already completed any
# of its transitive dependencies ( otherwise there's a deadlock )
def get_valid_move(task_graph, assignments):
    # first, choose a node at random
    node_to_move, data = random.choice(list(task_graph.nodes(data=True)))
    print("Moving node: " + node_to_move)
    deps = set(data['transitive_dependencies'])
    print(f"Deps: {deps}")
    valid_moves = [] # List of ('Name': position<int>) pairs
    for employee, tasks in assignments.items():
        tmp = deps.intersection(tasks)
        for i, task in enumerate(tasks):
            if not any(tmp):
                valid_moves.append((employee, i)) 
            tmp.discard(task)
    print(valid_moves)

def tabu_search(task_graph, operations, employees, last_task):
    best_completion_time = None
    for i in range(0, 1000):
        assignments = generate_random_solution(task_graph, operations, employees)
        add_assignments_to_graph(task_graph, assignments)
        newtime = completion_time(task_graph, assignments, last_task)
        if not best_completion_time or newtime < best_completion_time:
            best_completion_time = newtime
            best_assignment = assignments
    return best_assignment, best_completion_time

def main(args):
    f = open(args.filepath)
    data = json.load(f)
    operations = [Operation.from_dict(j) for j in data['operations']]
    employees = [Employee.from_dict(dict({'id': i}, **e)) for i, e in enumerate(data['employees'])] 
    num_employees = len(employees)

    # build operations graph 
    task_graph = networkx.DiGraph()
    for operation in operations:
        task_graph.add_node(operation.name, duration=operation.duration, leaf=(not operation.deps))
    for operation in operations:
        for dep in operation.deps:
            task_graph.add_edge(operation.name, dep)

    add_transitive_dependencies_to_graph(task_graph)

    # Find the last task
    last_task = None
    for operation in operations:
        if not any(task_graph.predecessors(operation.name)):
            last_task = operation.name

    best_assignment, best_completion_time = tabu_search(task_graph, operations, employees, last_task)
    print("Best assignment:")
    print(best_assignment)
    print(best_completion_time)
    get_valid_move(task_graph, best_assignment)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process input operations file")
    parser.add_argument('filepath', type=pathlib.Path)
    main(parser.parse_args())
