import graphviz as gv
import numpy as np
import os

from collections import deque
from itertools import combinations, compress

DEFAULT_OUTPUT_DIR = "poset_output"
DEFAULT_GRAPH_FILENAME = "poset_graph.gv"

class Poset():

    def __init__(self, alphabet, input_classes=None,
                 output_dir=DEFAULT_OUTPUT_DIR):
        """
        input_classes: A list of lists or sets.
        output_dir: A string specifying where the graph visualizations
                    should be saved.
        """
        if not input_classes:
            input_classes = []

        self.alphabet = set(alphabet)
        self.classes = [set(c) for c in input_classes] + [self.alphabet]
        self.subset_matrix = None
        self.daughter_matrix = None
        self.output_dir = output_dir
        self.calculate_subset_matrix()
        self.calculate_daughter_matrix()

    def add_class(self, new_class):
        """
        Adds a new class to the poset and recalculates the subset and 
        daughter matrices.

        Returns False if class was already in the poset, True otherwise
        """
        new_class = set(new_class)

        if new_class in self.classes:
            return False

        n = self.subset_matrix.shape[0]
        new_matrix = np.zeros((n + 1, n + 1), dtype='bool')
        new_matrix[0:n, 0:n] = self.subset_matrix

        for i, c in enumerate(self.classes):
            if c.issubset(new_class):
                new_matrix[n, i] = True
            if new_class.issubset(c):
                new_matrix[i, n] = True

        self.subset_matrix = new_matrix
        self.classes.append(new_class)
        self.calculate_daughter_matrix()

        return True

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

    def get_parents(self, c):
        """
        Gets the parents of the provided class
        """
        index = self.classes.index(c)
        parents_col = self.daughter_matrix[:, index]
        return list(compress(self.classes, parents_col))

    def is_subset(self, c1, c2):
        """
        Returns True if c1 is a subset of c2, False otherwise
        """
        i = self.classes.index(c1)
        j = self.classes.index(c2)
        return self.subset_matrix[j, i]

    def graph_poset(self, filename=DEFAULT_GRAPH_FILENAME, title=None):
        """
        Visualizes the parent/daughter relationship of the classes
        in the poset.
        """
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        graph = gv.Digraph(
            comment=str(title),
            filename=os.path.join(self.output_dir, filename),
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
        """
        closure_classes = [self.alphabet]
        class_deque = deque(self.classes)
\
        while class_deque:
            c = class_deque.pop()
            if not c in closure_classes:
                for cc in closure_classes:
                    class_deque.push(c.intersection(cc))
                closure_classes.append(c)

        new_poset = Poset(self.alphabet, closure_classes)

        return new_poset

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
    p.graph_poset(filename="no_intersection_test.gv")
    p2 = p.get_intersectional_closure()
    p2.graph_poset(filename="intersection_test.gv")
