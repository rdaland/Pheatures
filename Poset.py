import graphviz as gv
import os

from collections import deque
from itertools import compress

# See the comment in the SimpleBoolArray class
USE_NUMPY = False

# file constants
DEFAULT_OUTPUT_DIR = "graphs"

# graphing constants
ORIG_CLASS_NODE_SHAPE = "box"
MULTI_PARENT_LINK_STYLE = "dotted"

class SimpleBoolArray():
    """
    This is a simple and very limited class representing a boolean array.
    It is included here for code portability. The interface emulates
    the syntax of numpy arrays. It only implements the subset of functionality
    necessary for this program, so I don't recommend using it elsewhere.

    This is SIGNIFICANTLY slower than the numpy implementation. If performance
    is important to you, you can set the USE_NUMPY variable at the top of
    this file to True to use a numpy implementation instead, which will of 
    course require having numpy installed.
    """
    def __init__(self, shape, data):
        self.shape = shape
        self.data = data

    @classmethod
    def zeros(self, shape, dtype=None):
        return SimpleBoolArray(
            shape, [[False for i in range(shape[0])] for j in range(shape[1])]
        )

    @classmethod
    def dot(self, m1, m2):
        """
        Gets the standard matrix product.
        """
        if m1.shape[1] != m2.shape[0]:
            raise "m1.cols != m2.rows, dot is not defined"
        new_data = []
        for i in range(m1.shape[0]):
            row = []
            for j in range(m2.shape[1]):
                entry = False
                for k in range(m1.shape[1]):
                    entry = entry or (m1[i, k] and m2[k, j])
                row.append(entry)
            new_data.append(row)
        return SimpleBoolArray((m1.shape[0], m2.shape[1]), new_data)      

    def __getitem__(self, key):
        row_idx, col_idx = key
        rows = []
        result = []

        if type(row_idx) == slice:
            row_start = row_idx.start or 0
            row_stop = row_idx.stop or self.shape[0]
            row_step = row_idx.step or 1
            for i in range(row_start, row_stop, row_step):
                rows.append(self.data[i])
        else:
            rows = [self.data[row_idx]]

        for row in rows:
            val = row[col_idx]
            result.extend([val] if type(val) == bool else val)

        return result[0] if len(result) == 1 else result

    def __setitem__(self, key, value):
        if type(key) == tuple:
            self.data[key[0]][key[1]] = value
        else:
            self.data[key] = value

    def __mul__(self, m):
        """
        Does element-wise multiplcation
        """
        if self.shape != m.shape:
            raise "Matrices must be the same shape for multiplication"
        new_data = []
        for i in range(self.shape[0]):
            row = []
            for j in range(self.shape[1]):
                row.append(self[i, j] and m[i, j])
            new_data.append(row)
        return SimpleBoolArray(self.shape, new_data)

    def __invert__(self):
        new_data = []
        for i in range(self.shape[0]):
            row = []
            for j in range(self.shape[1]):
                row.append(not self[i, j])
            new_data.append(row)
        return SimpleBoolArray(self.shape, new_data)

# See the comment in SimpleBoolArray above
if USE_NUMPY:
    import numpy as np
    ARRAY = np
else:
    ARRAY = SimpleBoolArray

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

    def add_class(self, new_class, update_closure=False):
        """
        Adds a new class to the poset and recalculates the subset and 
        daughter matrices.

        Returns False if class was already in the poset, True otherwise
        """
        new_class = set(new_class)

        if new_class in self.classes:
            return False

        if update_closure:
            # Update intersectional closure
            self.get_intersectional_closure(
                existing_closure=self.classes,
                new_classes=[new_class]
            )
        else:
            # Just add class and update matrices
            n = self.subset_matrix.shape[0]
            new_matrix = ARRAY.zeros((n + 1, n + 1), dtype='bool')
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

    def graph_poset(self, filename, title=None):
        """
        Visualizes the parent/daughter relationship of the classes
        in the poset.
        
        DEPRECATED -- SOON TO BE REPLACED BY graph_poset2()
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

    def graph_poset2(self, filename, kw_args=None):
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
