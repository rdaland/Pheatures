import graphviz as gv
import numpy as np

from collections import deque
from itertools import combinations
from os.path import join

DEFAULT_OUTPUT_DIR = "poset_output"

class Poset():

    def __init__(self, input_classes=None, output_dir=DEFAULT_OUTPUT_DIR):
        if not input_classes:
            classes = []

        self.classes = [set(c) for c in input_classes]
        self.subset_matrix = None
        self.daughter_matrix = None
        self.output_dir = output_dir
        self.sort_classes()
        self.calculate_subset_matrix()
        self.calculate_daughter_matrix()

    def sort_classes(self):
        """
        Sorts the input classes descending by length
        """
        self.classes.sort(key=len, reverse=True)

    def calculate_subset_matrix(self):
        """
        Goes through every pair of sets in the inputs and determines whether
        they are in a subset relation. If they are, set their cell in the
        subset matrix to True (so M[j,i] = True means set_i < set_j).
        """
        n = len(self.classes)
        self.subset_matrix = np.zeros((n, n), dtype='bool')
        for i, c1 in enumerate(self.classes):
            for j, c2 in enumerate(self.classes[i+1:], start=i+1):
                if c1.issubset(c2):
                    self.subset_matrix[j, i] = True
                if c2.issubset(c1):
                    self.subset_matrix[i, j] = True

    def calculate_daughter_matrix(self):
        """
        Calculate parent/daughter relationship:

        M[i,j] = 1 <==> j is a subset of i
        M^2[i,j] ==> j is a subset of some k which is a subset of i
        (M * ~M^2) ==> j is a subset of i, and there is no k such that
                       j is a subset of k and k is a subset of i

        So self.daughter_matrix will have True for pairs of sets that
        are in a direct parent-daughter relationship.
        """
        m = self.subset_matrix
        self.daughter_matrix = m * ~np.dot(m, m)

    def graph_poset(self, filename='poset_graph.gv', title=None):
        """
        Visualizes the parent/daughter relationship of the classes
        in the poset.
        """
        graph = gv.Digraph(
            comment=str(title),
            filename=join(self.output_dir, filename),
            format='ps'
        )
        for i, cl in enumerate(self.classes):
            graph.node(str(i), ', '.join(cl))

        shape = self.daughter_matrix.shape
        for i in range(shape[0]):
            for j in range(shape[1]):
                if self.daughter_matrix[i, j]:
                    graph.edge(str(i), str(j))

        graph.render()

    def get_intersectional_closure(self):
        """
        Returns a new Poset object p with the following properties:
            1.  All classes in self are also in p
            2.  The intersections of all subsets of the sets in self
                are also in p

        The calculation is done using a modified version of Dijkstra's
        shortest paths algorithm. We start with a queue of *pairs* of
        classes, and reduce the total number of cases that must be 
        considered by capitalizing on two facts (^ is intersection,
        < is subset):
            1.  x ^ y = x ^ y (so only one order needs to be considered)
            2.  if x < y, then x ^ y = y
        Together, these facts make it possible to skip the intersetion
        operation for over half of all classes
        """
        new_classes = self.classes.copy()

        class_pairs = combinations(new_classes, 2)
        class_pair_deque = deque(class_pairs)

        while class_pair_deque:
            c1, c2 = class_pair_deque.pop()

            # Check if one class is a subset of the other
            if c1.issubset(c2) or c2.issubset(c1):
                continue

            # Get the intersection
            intersection = c1.intersection(c2)

            # Check if the intersection is empty or already in our classes
            if not intersection or intersection in new_classes:
                continue

            # We've found a new class!
            for c in new_classes:
                # If any classes aren't in a subset relationship with the new
                # class, add them to the pairs we need to consider.
                if not (c.issubset(intersection) or intersection.issubset(c)):
                    class_pair_deque.appendleft((c, intersection))
            new_classes.append(intersection)

        return Poset(new_classes)

if __name__ == "__main__":

    input_classes_vowels = [
        # Test for round/unround vowel system, which needs a minimum intersection
        # of 3 classes to avoid specifying spurious features.
        # All segments
        set(['i', 'y', 'e', 'E', 'a', 'u', 'U', 'o', 'O']),
        # High vowels
        set(['i', 'u', 'y', 'U']),
        # Mid vowels
        set(['e', 'E', 'o', 'O']),
        # Front vowels
        set(['i', 'e', 'E', 'y']),
        # Back vowels
        set (['u', 'o', 'a', 'O', 'U']),
        # Round vowels
        set(['y', 'E', 'u', 'o']),
        # Unrounded vowels
        set(['i', 'e', 'a', 'U', 'O']),
        # # Individual vowels
        set(['i']),
        set(['u']),
        set(['e']),
        set(['o']),
        set(['a']),
        set(['O']),
        set(['U']),
        set(['y']),
        set(['E'])
    ]

    p = Poset(input_classes_vowels)
    p.graph_poset(filename="no_intersection.gv")
    p2 = p.get_intersectional_closure()
    p2.graph_poset(filename="intersection.gv")
