import networkx
from tabu_search.input_types import Operation

class TabuGraph:
    graph: networkx.DiGraph
    assignment_pointers: dict[str, tuple[str, int]] # "A" -> ('Frank': 0)
    assignments: dict[str, list[str]] # {'John': ["B"], 'Frank': ["A", "C"]}
    assignment_aware_transitive_deps: dict[str, list[str]] # {"A": ["B", "C"]}, etc.
    last_task: str

    def __init__(self, g: networkx.DiGraph):
        self.assignment_pointers = dict()
        self.assignments = dict()
        self.assignment_aware_transitive_deps = dict()
        self.graph = g
        for node in self.graph.nodes:
            if not any(self.graph.predecessors(node)):
                    self.last_task = node
        assert(self.last_task)

    def update_assignment_aware_transitive_dependencies(self, node):
        data = self.graph.nodes[node]
        assignment_pointer = self.assignment_pointers[node]
        if assignment_pointer[1] == 0 and data['leaf']:
            return set()
        # my dependencies are my task children + anything left of me in my individual assignment list
        deps = set()
        if assignment_pointer[1] > 0:
            left_of_me = self.assignments[assignment_pointer[0]][assignment_pointer[1] - 1]
            deps = set(left_of_me)
            deps = deps.union(self.update_assignment_aware_transitive_dependencies(left_of_me))
        for c in self.graph.successors(node):
            deps.add(c)
            deps = deps.union(self.update_assignment_aware_transitive_dependencies(c))
        return deps

    def update_transitive_deps(self):
        for n in self.graph.nodes:
            self.assignment_aware_transitive_deps[n] = self.update_assignment_aware_transitive_dependencies(n)

    def update_assignments(self, new_assignments):
        self.assignments = new_assignments
        self.assignment_pointers.clear()
        self.assignment_aware_transitive_deps.clear()
        for employee, assignment_list in self.assignments.items():
            for i, assignment in enumerate(assignment_list):
                self.assignment_pointers[assignment] = (employee, i)

        self.update_transitive_deps()

    def node_completion_time(self, node):
        data = self.graph.nodes[node]
        assignment_pointer = self.assignment_pointers[node]
        if assignment_pointer[1] == 0 and data['leaf']:
            return data['duration']
        # max of completion time by moving left in the assignment list ( current person working on previously assigned task )
        # and the max completion time of the subtasks
        return data['duration'] + \
                    max(self.node_completion_time(self.assignments[assignment_pointer[0]][assignment_pointer[1] - 1]) \
                        if assignment_pointer[1] > 0 else 0,
                        max([self.node_completion_time(c) for c in self.graph.successors(node)] + [0]))

    def completion_time(self):
        return self.node_completion_time(self.last_task)

    def get_valid_moves(self):
        moves = []
        # for each node, find out all the valid positions i can put it in
        valid_moves = set()
        for n in self.graph.nodes:
            deps = self.assignment_aware_transitive_deps[n]
            assignment_pointer = self.assignment_pointers[n]
           
            may_place_on_end = True
            for employee, tasks in self.assignments.items():
                tmp = deps.intersection(tasks)
                i = 0
                for i, task in enumerate(tasks):
                    if task == n:
                        continue
                    if not any(tmp):
                        valid_moves.add((n, (assignment_pointer, (employee, i))))
                    tmp.discard(task)
                    if n in self.assignment_aware_transitive_deps[task]:
                        may_place_on_end = False
                        break
                if not any(tmp) and may_place_on_end:
                    valid_moves.add((n, (assignment_pointer, (employee, i + 1))))
        return valid_moves

def build_graph(operations: list[Operation]):
    g = networkx.DiGraph()
    for operation in operations:
        g.add_node(operation.name, duration=operation.duration, leaf=(not operation.deps))
    for operation in operations:
        for dep in operation.deps:
            g.add_edge(operation.name, dep)
    return TabuGraph(g)
