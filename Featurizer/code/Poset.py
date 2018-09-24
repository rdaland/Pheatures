import graphviz as gv
import os

from collections import deque
from itertools import compress

# See the comment in the SimpleBoolArray class
USE_NUMPY = False

if USE_NUMPY:
    import numpy as np
    ARRAY = np
else:
    import Array
    ARRAY = Array.SimpleBoolArray

# file constants
DEFAULT_OUTPUT_DIR = "../poset_output"

# graphing constants
ORIG_CLASS_NODE_SHAPE = "box"
MULTI_PARENT_LINK_STYLE = "dotted"

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
        self.input_classes = [set(c) for c in input_classes]
        # input_classes = *original* input classes
        # classes = all classes (after intersectional closure)
        self.classes = [set(c) for c in input_classes]
        if self.alphabet not in self.classes:
            self.classes.append(self.alphabet)
        self.output_dir = output_dir
        self.calculate_matrices()

    def calculate_matrices(self):
        self.subset_matrix = None
        self.daughter_matrix = None
        self.calculate_subset_matrix()
        self.calculate_daughter_matrix()

    def add_classes(self, new_classes, update_closure=False):
        """
        Adds a new class to the poset and recalculates the subset and 
        daughter matrices.

        Returns False if class was already in the poset, True otherwise
        """
        new_classes = [x for x in new_classes if x not in self.classes]

        if update_closure:
            # Update intersectional closure
            self.get_intersectional_closure(
                existing_closure=self.classes,
                new_classes=new_classes
            )
        else:
            # Just add the class to the poset without recalculating the
            # intersectional closure.
            self.classes.extend(new_classes)
            self.calculate_subset_matrix()
            self.calculate_daughter_matrix()

    def calculate_subset_matrix(self):
        """
        Goes through every pair of sets in the inputs and determines whether
        they are in a subset relation. If they are, set their cell in the
        subset matrix to True (so M[j,i] = True means set_i < set_j).
        """
        n = len(self.classes)
        self.subset_matrix = ARRAY.zeros((n, n), dtype='bool')
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
        self.daughter_matrix = m * ~ARRAY.dot(m, m)

    def get_parents(self, c):
        """
        Gets the parents of the provided class
        """
        index = self.classes.index(c)
        parents_col = self.daughter_matrix[:, index]
        return list(compress(self.classes, parents_col))

    def get_children(self, c):
        """
        Gets the children of the provided class
        """
        index = self.classes.index(c)
        children_col = self.daughter_matrix[index, :]
        return list(compress(self.classes, children_col))

    def is_subset(self, c1, c2):
        """
        Returns True if c1 is a subset of c2, False otherwise
        """
        i = self.classes.index(c1)
        j = self.classes.index(c2)
        return self.subset_matrix[j, i]

    def graph_poset(self, filename, kw_args=None):
        '''
        Creates and writes to a DOT file which represents the
        parent/daughter relationships between classes in the poset 
        '''
        
        linebuf = []
        linebuf.append('// None')
        linebuf.append('digraph {')

        # get nodes
        for i, cl in enumerate(self.classes):
            attributes = {'label': '"' + ', '.join(cl) + '"'}
            if cl in self.input_classes:
                attributes['shape'] = ORIG_CLASS_NODE_SHAPE
            attrStr = ','.join([
                '{0}={1}'.format(attr, val) 
                for attr, val in attributes.items()
            ])
            linebuf.append('\t{0} [{1}]'.format(i,attrStr))
        
        # get links
        for i in range(len(self.classes)):
            for j in range(len(self.classes)):
                if self.daughter_matrix[i,j]:
                    attributes = {}
                    if len(self.get_parents(self.classes[j])) > 1:
                        attributes['style'] = MULTI_PARENT_LINK_STYLE
                    attrStr = ','.join([
                        '{0}={1}'.format(attr, val)
                        for attr, val in attributes.items()
                    ])
                    linebuf.append('\t{0} -> {1} [{2}]'.format(i, j, attrStr))
                    
        linebuf.append('}')
        
        with open(filename, 'w') as fout:
            for line in linebuf:
                fout.write(line)
                fout.write('\n')

    def get_intersectional_closure(self, existing_closure=None,
                                   new_classes=None):
        """
        Returns a new Poset object p with the following properties:
            1.  All classes in self are also in p
            2.  The intersections of all subsets of the sets in self
                are also in p
        """
        closure_classes = existing_closure or [self.alphabet]
        class_deque = deque(new_classes) if new_classes else deque(self.classes)

        while class_deque:
            c = class_deque.popleft()
            if c not in closure_classes:
                for cc in closure_classes:
                    intersection = c.intersection(cc)
                    # Don't include the empty set
                    if intersection:
                        class_deque.append(c.intersection(cc))
                closure_classes.append(c)

        self.classes = closure_classes
        self.calculate_matrices()
