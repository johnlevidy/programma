import unittest
import copy
import pprint
from tabu_search.input_types import *
from tabu_search.types import build_graph
import networkx

class GraphUtilTest(unittest.TestCase):
    basic2 = [Operation("A", 1, ["B", "C"], "J1"),
              Operation("B", 3, ["D"], "J1"),
              Operation("C", 4, ["E", "F"], "J1"),
              Operation("D", 2, [], "J1"),
              Operation("E", 2, [], "J1"),
              Operation("F", 1, [], "J1")]

    def test(self):
        graph = build_graph(self.basic2)
        graph.update_assignments({'John': ["F", "E", "D", "C", "B", "A"], 'Frank': []})
        self.assertEqual(graph.completion_time(), 13)
        self.assertEqual(graph.assignment_aware_transitive_deps, \
            {'A': {'C', 'D', 'B', 'F', 'E'}, 'B': {'C', 'D', 'F', 'E'}, 'C': {'E', 'D', 'F'}, 'D': {'E', 'F'}, 'E': {'F'}, 'F': set()})
        graph.update_assignments({'John': ['D', 'E', 'C'], 'Frank': ['F', 'B', 'A']})
        self.assertEqual(graph.completion_time(), 9)
        self.assertEqual(graph.assignment_aware_transitive_deps, \
            {'A': {'B', 'C', 'D', 'F', 'E'}, 'B': {'D', 'F'}, 'C': {'E', 'D', 'F'}, 'D': set(), 'E': {'D'}, 'F': set()})
        graph.update_assignments({'John': ['B', 'C'], 'Frank': ['D', 'E', 'F', 'A']})
        self.assertEqual(graph.completion_time(), 10)
        self.assertEqual(graph.assignment_aware_transitive_deps, \
            {'A': {'B', 'F', 'E', 'C', 'D'}, 'B': {'D'}, 'C': {'B', 'D', 'F', 'E'}, 'D': set(), 'E': {'D'}, 'F': {'E', 'D'}})
        graph.update_assignments({'John': ['E', 'C'], 'Frank': ['D', 'B', 'F', 'A']})
        self.assertEqual(graph.completion_time(), 11)
        self.assertEqual(graph.assignment_aware_transitive_deps, \
            {'A': {'B', 'F', 'E', 'C', 'D'}, 'B': {'D'}, 'C': {'B', 'E', 'D', 'F'}, 'D': set(), 'E': set(), 'F': {'D', 'B'}})

    def test2(self):
        graph = build_graph(self.basic2)
        graph.update_assignments({'John': ['B', 'C'], 'Frank': ['D', 'E', 'F', 'A']})
        self.assertEqual(graph.completion_time(), 10)
        self.assertEqual(graph.assignment_aware_transitive_deps, \
            {'A': {'B', 'F', 'E', 'C', 'D'}, 'B': {'D'}, 'C': {'B', 'D', 'F', 'E'}, 'D': set(), 'E': {'D'}, 'F': {'E', 'D'}})
        pp = pprint.PrettyPrinter(indent=2)

        assignments_before = copy.deepcopy(graph.assignments)
        assignment_pointers_before = copy.deepcopy(graph.assignment_pointers)

        print("Attempting to apply all moves and make sure they are reversible")
        print(assignments_before)
        print(assignment_pointers_before)
        for node, move in graph.get_valid_moves():
            print(f"Applying move: {node}, {move}")
            reverse = graph.apply_move(node, move)
            print(graph.assignments)
            print(f"Reverse: {reverse}")
            graph.apply_move(reverse[0], reverse[1])
            print(graph.assignments)
            self.assertEqual(assignments_before, graph.assignments)
            self.assertEqual(assignment_pointers_before, graph.assignment_pointers)
