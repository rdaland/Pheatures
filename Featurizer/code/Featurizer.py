import argparse

from Poset import Poset
from collections import defaultdict, deque
from enum import Enum
from os import path

# This code requires boolean matrix functionality, which numpy provides
# set this value to True if you have numpy installed
# otherwise, use our slower native Python implementation
USE_NUMPY = False
if USE_NUMPY:
    import numpy as np
    ARRAY = np
else:
    import Array
    ARRAY = Array.SimpleBoolArray

DEFAULT_ROOTNAME = "feature_output"

class Specification(Enum):
    PRIVATIVE = 0
    COMPLEMENTARY = 1
    INFERENTIAL_COMPLEMENTARY = 2
    FULL = 3

FEATURIZATION_MAP = {
    'privative': Specification.PRIVATIVE,
    'complementary': Specification.COMPLEMENTARY,
    'inferential_complementary': Specification.INFERENTIAL_COMPLEMENTARY,
    'full': Specification.FULL
}

class Featurizer():
    def __init__(self, input_classes, alphabet,
                 specification=Specification.COMPLEMENTARY, verbose=False,
                 rootname=DEFAULT_ROOTNAME):
        '''
            Default class constructor that must be given an alphabet and a set
            of input classes.
            
            Input:
                input_classes: A list of sets of segments
                alphabet: A set of all segments used in input_classes
                specification: The Specification indicating the type of
                    featurization to do
                verbose: A bool indicating whether to print extra information
                    during the featurization
        '''
        if specification not in Specification:
            raise Exception("Invalid featural specification '{}'".format(specification))

        self.input_classes = input_classes
        self.alphabet = alphabet
        self.specification = specification
        self.verbose = verbose
        self.rootname = rootname
        self.reset()

    @classmethod
    def from_file(cls, filename, specification=Specification.COMPLEMENTARY,
                  use_numpy=False, verbose=False):
        '''
            An alternative constructor that creates a Featurizer object based on
            the contents of a file. The file should have the following format

            <alphabet>
            <input class 1>
            ...
            <input class n>
            
            <alphabet> and <input class i> are segments separated by spaces.
            Segments do not need to be single characters.
            
            Input:
                filename: A string specifying where to find the input file.
                specification: The type of featurization to do
        '''
        with open(filename, 'r') as f:
            alphabet = set(next(f).rstrip().split(' '))
            classes = []
            for line in f:
                c = set(line.rstrip().split(' '))
                if c:
                    classes.append(c)
        rootname = path.splitext(path.split(filename)[1])[0]
        return Featurizer(
            classes, alphabet, specification, verbose=verbose, 
            rootname=rootname
        )

    def reset(self):
        '''
            Resets the featurization and poset to the state they were in before
            any featurization algorithm was run. If you want to rerun different
            featurization algorithms on the same instance, you'll need to call
            this first.
        '''
        self.class_features = defaultdict(set)
        self.segment_features = defaultdict(set)
        # Initialize to empty feature set for all segments
        for segment in self.alphabet:
            self.segment_features[segment]
        self.feature_num = 1

        # Build an intersectionally closed poset from the input classes
        self.poset = Poset(self.alphabet, self.input_classes)
        self.poset.get_intersectional_closure()

    def set_segment_features(self, c, feature):
        '''
            Adds a feature/value pair to the featural description of every
            segment in a class.
        
            Input:
                c: A set of strings
                feature: A tuple of the form (<feature number>, <value>)
        '''
        for segment in c:
            self.segment_features[segment].update(feature)

    def set_class_features(self, c, features):
        '''
            Adds a feature/value pair to the featural description of a class
        
            Input:
                c: A set of strings
                features
        '''
        self.class_features[tuple(sorted(c))].update(features)

    def get_class_features(self, c):
        '''
            Gets all the feature/values assigned to a class.
            
            Input:
                c: A set of strings
                
            Returns:
                The set of feature/value pairs assigned to c
        '''
        return set.intersection(*[
            self.segment_features.get(x, set()) for x in c
        ])

    def calculate_class_features(self):
        '''Calculate the featural description for each class in the poset'''
        for c in self.poset.classes:
            features = self.get_class_features(c)
            self.set_class_features(c, features)

    def graph_poset(self, filename=None, kw_args=None):
        '''
            Creates a DOT file which describes a graph of the parent/daughter
            relationships in the current intersection closure
            
            Note: you still must compile the DOT file to a graph using
            GraphViz or some other tool
            
            Note: recommended command-line call
            $ dot -Tsvg -O your_DOT_filename.gv
            
            Input:
                filename: the file to write to (preferred extension: .gv)
                kw_args: currently ignored (purpose: control graph style)
            '''
        if not filename:
            inv_map = {v: k for k, v in FEATURIZATION_MAP.items()}
            filename = "../poset_output/{}_{}.gv".format(
                self.rootname, inv_map[self.specification]
            )
        self.poset.graph_poset(filename, kw_args)
    
    def get_feature_transitions(self):
        '''
            This method should only be called after a featurization has been
            generated.
            
            Output:
                M -- a matrix indicating featural relations
                M[i,j] = True ==> class j has a superset of features of class i            
        '''
        N = len(self.poset.classes)
        
        feature_transitions = ARRAY.zeros((N,N))
        for i, cl_i in enumerate(self.poset.classes):
            feats_i = self.get_class_features(cl_i)
            for j, cl_j in enumerate(self.poset.classes):
                if j <= i: continue
                feats_j = self.get_class_features(cl_j)
                ## check whether class j has superset of features of class i
                feature_transitions[i,j] = feats_i.issubset(feats_j)
                feature_transitions[j,i] = feats_j.issubset(feats_i)
        
        return feature_transitions

    def graph_feats(self, filename=None, kw_args=None):
        '''
            Creates a DOT file which describes a graph of the classes
            generated by the current featural system
            
            Note: you still must compile the DOT file to a graph using
            GraphViz or some other tool
            
            Note: recommended command-line call
            $ dot -Tsvg -O your_DOT_filename.gv
            
            Input:
            filename: the file to write to (preferred extension: .gv)
            kw_args: currently ignored (purpose: control graph style)
        '''
        
        #################################################
        ##                    SETUP                    ##
        #################################################
        
        N = len(self.poset.classes)

        if not filename:
            inv_map = {v: k for k, v in FEATURIZATION_MAP.items()}
            filename = "../feats_output/{}_{}.gv".format(
                self.rootname, inv_map[self.specification]
            )
        
        ## write header (clearing old file if it exists)
        with open(filename, 'w') as fout:
            fout.write('// None\ndigraph {\n')
            
        #################################################
        ##                  GET NODES                  ##
        #################################################

        node_string_prefix = '[label="{<segs>'
        node_string_infix = '|<feats>'
        node_string_suffix = '}",shape=record]'
        
        for i, c in enumerate(self.poset.classes):
            features = self.get_class_features(c)
            seg_string = ', '.join(c)
            feat_string = '\\n'.join('{0}F{1}'.format(f[1],f[0]) for f in features)
            
            node_string = '{0} {1} {2} {3} {4}'.format(node_string_prefix,
                                                       seg_string,
                                                       node_string_infix,
                                                       feat_string,
                                                       node_string_suffix)
            with open(filename, 'a') as fout:
                fout.write('\t{0} {1}\n'.format(i, node_string))

        #################################################
        ##                  GET LINKS                  ##
        #################################################

        ## m[i,j] = True iff class j is subset of class i
        m = self.get_feature_transitions()
        feature_daughter = m * ~ARRAY.dot(m, m)
        
        for i in range(N):
            for j in range(N):
                if feature_daughter[i,j]:
                    with open(filename, 'a') as fout:
                        fout.write('\t{0} -> {1}'.format(i,j))

        #################################################
        ##                    WRAPUP                   ##
        #################################################
        
        singletons = [str(i) for i,c in enumerate(self.poset.classes) if len(c)==1]
        singleton_str = ' '.join(singletons)
        with open(filename, 'a') as fout:
            fout.write('\n{rank=same; ')
            fout.write(singleton_str)
            fout.write('}\n}')
            
    def get_segments_for_feature(self, feature):
        '''
            Gets the segments picked out by a feature
            
            Input:
                feature: A tuple of the form (<feature_number>, <value>)
                
            Returns:
                A set of segments
        '''
        segments = set()
        for segment, features in self.segment_features.items():
            if feature in features:
                segments.add(segment)
        return segments

    def get_class_for_features(self, features):
        '''
            Given a set of feature/value pairs, return the class they pick out
            
            Input:
                features: A list of tuples of the form (<feature_number>, <value>)
                
            Returns:
                A set representing the class specified by features
        '''
        feature_segments = [self.alphabet]
        for feature in features:
            segments = self.get_segments_for_feature(feature)
            feature_segments.append(segments)
        return set.intersection(*feature_segments)

    def assert_valid_featurization(self):
        '''Checks that the calculcated features pick out the expected classes'''
        for c, features in self.class_features.items():
            predicted_class = self.get_class_for_features(features)
            if predicted_class != set(c):
                raise Exception(
                    "Invalid featurization: feature set {} associated with class {},"
                    "but produces class {}".format(features, set(c), predicted_class)
                )

    def features_to_csv(self, filename=None):
        '''
            Creates a CSV with classes as rows and corresponding feautral
            descriptors as columns
            
            Input:
                filename: A string specifying where to save the file
        '''
        if not filename:
            inv_map = {v: k for k, v in FEATURIZATION_MAP.items()}
            filename = "../csv_output/{}_{}.csv".format(
                self.rootname, inv_map[self.specification]
            )
        with open(filename, 'w') as f:
            print(',' + ','.join([
                    str(i) for i in range(1, self.feature_num)
                ]),
                file=f
            )
            for key, value in sorted(self.segment_features.items(),
                    key=lambda x: -len(x[0])):
                d = dict(value)
                line = []
                line.append("{}".format(' '.join(key)))
                for i in range(1, self.feature_num):
                    line.append(d.get(i, '0'))
                print(','.join(line), file=f)

    def print_featurization(self):
        '''Print out the classes and their featural specifications.'''
        print('Class features')
        for key, value in sorted(self.class_features.items(),
                                 key=lambda x: -len(x[0])):
            print("{}:\t{}".format(key, sorted(value)))
        print()

    def print_segment_features(self):
        '''Print out the segments and their featural specifications'''
        print("Segment features")
        for key, value in sorted(self.segment_features.items(),
                                 key=lambda x: -len(x[0])):
            print("{}:\t{}".format(key, sorted(value)))
        print() 

    def add_complement_classes(self):
        '''
            For the inferential complementary and full specifications, 
            pre-calculate the full set of complement classes that will be added
            before doing the featurization. This is done using a breadth-first
            search of the poset and adding the complements to the child classes
            simultaneously.
        '''
        bfs_deque = deque([self.alphabet])

        while bfs_deque:
            current_node = bfs_deque.popleft()
            children = self.poset.get_children(current_node)

            # Go through the children of the current node to decide what to 
            # append to the queue
            child_complements = []
            while children:
                child = children.pop(0)
                if (len(self.poset.get_parents(child)) == 1):
                    # If a child only has a single parent, define a complement
                    # class wrt the current class (inferential complementary)
                    #or the alphabet (full)
                    if self.specification == Specification.FULL:
                        complement = self.alphabet - child
                    elif self.specification == Specification.INFERENTIAL_COMPLEMENTARY:
                        complement = current_node - child
                    else:
                        raise(
                            "Complement classes cannot be calculated for "
                            "specification type {}".format(self.specification)
                        )
                    child_complements.append(complement)

            # Add new classes to the poset simultaneously
            self.poset.add_classes(child_complements, update_closure=True)

            # Get the new children of the current parent node and add them to
            # the queue to be processed.
            new_children = self.poset.get_children(current_node)
            bfs_deque.extend(new_children)

    def featurize_classes(self):
        if self.verbose:
            print("Classes to process: {}".format(self.poset.classes))
        '''Featurize the currently calculated poset'''
        incomplete_classes = self.poset.classes.copy()

        while incomplete_classes:
            c = incomplete_classes.pop(0)
            if self.verbose:
                print("Processing class: {}".format(c))
            # We only need to do something if the current class has exactly
            # one parent
            if len(self.poset.get_parents(c)) == 1:
                c_feature = set([(self.feature_num, '+')])
                self.set_segment_features(c, c_feature)

                # In privative specification, we don't consider the complement
                if self.specification != Specification.PRIVATIVE:
                    if self.specification == Specification.FULL:
                        # For full specification we take the complement wrt the
                        # set of all sounds.
                        c1 = self.alphabet - c
                    else:
                        # Otherwise take it wrt the parent set. 
                        parent = self.poset.get_parents(c)[0]
                        c1 = parent - c

                    # We only want to consider the complement for inferential 
                    # complementary underspecification if it's in the input set.
                    if (self.specification != Specification.COMPLEMENTARY
                            or c1 in self.input_classes):
                        # Assign the negative value of the new feature to the 
                        # new class
                        c1_feature = set([(self.feature_num, '-')])
                        self.set_segment_features(c1, c1_feature)

                        incomplete_classes = list(filter(
                            lambda x: x != c1,
                            incomplete_classes
                        ))

                self.feature_num += 1

                if self.verbose:
                    self.print_segment_features()

        self.calculate_class_features()
        self.assert_valid_featurization()

    def get_features_from_classes(self):
        '''
            Calculate the complements added by the featurization if any, and then
            featurize the poset
        '''
        if self.specification in (Specification.INFERENTIAL_COMPLEMENTARY, Specification.FULL):
            self.add_complement_classes()
        self.featurize_classes()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description = "Produce a phonological featurization of a set of input classes."
    )
    parser.add_argument(
        'input_file', type=str, help='Path to the input class file.'
    )
    parser.add_argument(
        '--output_file', type=str, default=None,
        help='Path to csv file to save featurization description in.',
    )
    parser.add_argument(
        '--featurization', type=str, default='complementary',
        help="The featurization type to use. Must be one of 'privative', "
             "'complementary', 'inferential_complementary', or 'full'."
    )
    parser.add_argument(
        '--use_numpy', action="store_true",
        help="Use numpy for matrix calculations. This will make the algorithm "
             "run faster, but requires numpy to be installed on your system."
    )
    parser.add_argument(
        '--poset_file', type=str, default=None,
        help='The path to the file to save the poset graph in.'
    )
    parser.add_argument(
        '--feats_file', type=str, default=None,
        help='The path to the file to save the featurization graph in.'
    )
    parser.add_argument(
        '--verbose', action='store_true',
        help='Prints additional information throughout the course of the featurization.'
    )
    args = parser.parse_args()
    specification = FEATURIZATION_MAP.get(args.featurization, args.featurization)
    featurizer = Featurizer.from_file(
        args.input_file, specification, use_numpy=args.use_numpy,
        verbose=args.verbose
    )
    featurizer.get_features_from_classes()
    featurizer.print_featurization()
    featurizer.print_segment_features()
    featurizer.graph_poset(args.poset_file)
    featurizer.graph_feats(args.feats_file)
    featurizer.features_to_csv(args.output_file)
