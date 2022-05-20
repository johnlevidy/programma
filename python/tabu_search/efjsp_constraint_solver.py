import json
import copy
import time
from input_types import *
import argparse
import pathlib
import networkx
import random
from collections import deque

# Runtime roughly O(#nodes)
# Assignment pointer is a tuple (machine, index) that indexes into assignments
def completion_time(task_graph, assignments, node):
    data = task_graph.nodes[node]
    assignment_pointer = data['assignment_pointer']
    if assignment_pointer[1] == 0 and data['leaf']:
        return data['duration']
    # max of completion time by moving left in the assignment list ( current person working on previously assigned task )
    # and the max completion time of the subtasks
    goleft = completion_time(task_graph, assignments, assignments[assignment_pointer[0]][assignment_pointer[1] - 1]) \
                 if assignment_pointer[1] > 0 else 0
    childrencompletion = [completion_time(task_graph, assignments, c) for c in task_graph.successors(node)]
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

# Runtime roughly O(#nodes)
# Assignment pointer is a tuple (machine, index) that indexes into assignments
def get_assignment_aware_transitive_dependencies(task_graph, assignments, node):
    data = task_graph.nodes[node]
    assignment_pointer = data['assignment_pointer']
    if assignment_pointer[1] == 0 and data['leaf']:
        return set()
    # my dependencies are my task children + anything left of me in my individual assignment list
    deps = get_assignment_aware_transitive_dependencies(task_graph, assignments, assignments[assignment_pointer[0]][assignment_pointer[1] - 1]) \
                 if assignment_pointer[1] > 0 else set()
    for c in task_graph.successors(node):
        deps.add(c)
        deps = deps.union(get_assignment_aware_transitive_dependencies(task_graph, assignments, c))
    return deps

# Annotates each task in the task graph with a set of all 
# of its transitive dependencies
def add_transitive_dependencies_to_graph(task_graph, assignments):
    for n, data in task_graph.nodes(data=True):
        data['transitive_dependencies'] = get_assignment_aware_transitive_dependencies(task_graph, assignments, n)

# the high level idea here is: 
# 1) n <- randomly selected node to move
# 2) t <- all transitive children of n
# then, for each P_x ( person x's task list ):
# 1) m <- intersection(t, P_x) 
# 2) iterate P_x, remove tasks from m as you visit, when m is empty the 
# positions iterated over are valid
# In plain english: for each person, i cannot work on the moved task until i've already completed any
# of its transitive dependencies ( otherwise there's a deadlock )
def get_valid_moves(task_graph, assignments):
    moves = []
    deepdata = copy.deepcopy(task_graph.nodes(data=True))
    for node_to_move, data in deepdata:
        deps = data['transitive_dependencies']
        # remove the node to start
        tmp_assignments = copy.deepcopy(assignments)
        tmp_assignments[data['assignment_pointer'][0]].pop(data['assignment_pointer'][1])
        add_assignments_to_graph(task_graph, tmp_assignments)
        add_transitive_dependencies_to_graph(task_graph, tmp_assignments)

        valid_moves = set()
        may_place_on_end = True
        for employee, tasks in tmp_assignments.items():
            tmp = deps.intersection(tasks)
            i = 0
            for i, task in enumerate(tasks):
                # cannot put this after somnething which i'm a dep of
                if not any(tmp):
                    valid_moves.add((employee, i))
                tmp.discard(task) 
                if node_to_move in task_graph.nodes[task]['transitive_dependencies']:
                    may_place_on_end = False 
                    break
            if not any(tmp) and may_place_on_end:
                valid_moves.add((employee, i + 1))

        valid_moves.discard(data['assignment_pointer'])
        valid_moves.discard((data['assignment_pointer'][0], data['assignment_pointer'][1] + 1)) # equivalent to above
        for v in valid_moves:
            moves.append((node_to_move, v))
    return moves

# Applies the move to the graph and assignments, returns new assignments
def apply_move(task_graph, assignments, move):
    print(f"Applying: {move}")
    node_to_move = move[0]
    move = move[1]
    data = task_graph.nodes[node_to_move]
    print(data)
    new_assignments = copy.deepcopy(assignments)
    # mark old position for deletion
    new_assignments[data['assignment_pointer'][0]][data['assignment_pointer'][1]] = None
    new_assignments[move[0]].insert(move[1], node_to_move)
    # delete old position
    new_assignments[data['assignment_pointer'][0]].remove(None)
    return new_assignments

# randomly generate graphs until it looks reasonable
def random_search(task_graph, operations, employees, last_task, iters):
    best_completion_time = None
    for i in range(0, iters):
        assignments = generate_random_solution(task_graph, operations, employees)
        print(assignments)
        add_assignments_to_graph(task_graph, assignments)
        newtime = completion_time(task_graph, assignments, last_task)
        if not best_completion_time or newtime < best_completion_time:
            best_completion_time = newtime
            best_assignment = assignments
    add_assignments_to_graph(task_graph, best_assignment)
    return best_assignment, best_completion_time

# borrowed from: https://en.wikipedia.org/wiki/Tabu_search
# TODO: bad things likely to happen since the task graph here 
# isn't copied, it has old stale assignments on it? 
# Wiki notation is that a "candidate" is a fully rendered set of assignments, not just a candidate _move_
# please interpret below accordingly in place of types ( for now? TODO: mypy? ) 
TABU_TENURE=10
def tabu_search(task_graph, operations, employees, last_task, iters):
    print("Beginning tabu search...")
    assignments = generate_random_solution(task_graph, operations, employees)
    print("Initial assignments: ", assignments)
    add_assignments_to_graph(task_graph, assignments)
    add_transitive_dependencies_to_graph(task_graph, assignments)
    best_candidate = assignments 
    best_candidate_time = completion_time(task_graph, assignments, last_task)
    return_assignments = assignments
    return_time = best_candidate_time
    print("Initial time: ", return_time)

    tabu_list = deque(maxlen=TABU_TENURE)
    tabu_list.append(assignments)

    for i in range(0, iters):
        print(f"Best candidate: {best_candidate}")
        neighborhood = get_valid_moves(task_graph, best_candidate)
        print(neighborhood)
        first = neighborhood.pop()
        print("Using move: ", first)
        print(assignments)
        best_candidate = apply_move(task_graph, assignments, first)
        add_assignments_to_graph(task_graph, assignments)
        best_candidate_time = completion_time(task_graph, best_candidate, last_task)
        print(f"New candidate: {best_candidate} takes time: {best_candidate_time}")

        for neighbor in neighborhood:
            print("Using move: ", neighbor)
            print(assignments)
            candidate = apply_move(task_graph, assignments, neighbor)
            add_assignments_to_graph(task_graph, candidate)
            print(f"Tabu list: {tabu_list}")
            if not candidate in tabu_list:
                t = completion_time(task_graph, candidate, last_task)
                print(f"New candidate: {candidate} takes time: {t}")
                if t < best_candidate_time:
                    best_candidate = candidate
                    best_candidate_time = t
            else:
                print("That's taboo!")
            
        if best_candidate_time < return_time:
            return_assignments = best_candidate
            return_time = best_candidate_time
        print(f"Best so far: {return_time}")

        tabu_list.append(best_candidate)
    return return_assignments, return_time
        

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

    # Find the last task
    last_task = None
    for operation in operations:
        if not any(task_graph.predecessors(operation.name)):
            last_task = operation.name

    iters = 100

    start = time.time()
    best_assignment, best_completion_time = random_search(task_graph, operations, employees, last_task, iters)
    end = time.time()
    print(f"RANDOM {iters} iters in {end - start} found assignment: {best_assignment} with completion time {best_completion_time}")

    # start = time.time()
    # best_assignment, best_completion_time = tabu_search(task_graph, operations, employees, last_task, iters)
    # print(f"TABU {iters} iters in {end - start} found assignment: {best_assignment} with completion time {best_completion_time}")
    # end = time.time()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process input operations file")
    parser.add_argument('filepath', type=pathlib.Path)
    main(parser.parse_args())
