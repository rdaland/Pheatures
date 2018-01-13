import argparse

from Poset import Poset
from collections import defaultdict, deque
from enum import Enum

# file constants
DEFAULT_CSV_FILE = "features.csv"
DEFAULT_POSET_FILENAME = "poset_graph.gv"
DEFAULT_FEATS_FILENAME = "feats_graph.gv"
DEFAULT_OUTPUT_DIR = "graphs"

class Specification(Enum):
    PRIVATIVE = 0
    CONTRASTIVE_UNDER = 1
    CONTRASTIVE = 2
    FULL = 3

class Featurizer():
    def __init__(self, input_classes, alphabet,
                 specification=Specification.CONTRASTIVE_UNDER, verbose=False):
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
            raise("Invalid featural specification '{}'".format(specification))

        self.input_classes = input_classes
        self.alphabet = alphabet
        self.specification = specification
        self.verbose = verbose
        self.reset()

    @classmethod
    def from_file(cls, filename, specification=Specification.CONTRASTIVE_UNDER):
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
        return Featurizer(classes, alphabet, specification)

    def reset(self):
        '''
            Resets the featurization and poset to the state they were in before
            any featurization algorithm was run. If you want to rerun different
            featurization algorithms on the same instance, you'll need to call
            this first.
        '''
        self.class_features = defaultdict(set)
        self.segment_features = defaultdict(set)
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
            Gets the features required to specify a class
            
            Input:
                c: A set of strings
                
            Returns:
                A set of feature/value pairs that uniquely pick out c
        '''
        return set.intersection(*[
            self.segment_features.get(x, set()) for x in c
        ])

    def calculate_class_features(self):
        'Calculate the featural description for each class in the poset'
        for c in self.poset.classes:
            features = self.get_class_features(c)
            self.set_class_features(c, features)

    def graph_poset(self, filename=DEFAULT_POSET_FILENAME, kw_args=None):
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
        self.poset.graph_poset(filename, kw_args)

    def graph_feats(self, filename=DEFAULT_FEATS_FILENAME, kw_args=None):
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
        pass

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
        'Checks that the calculcated features pick out the expected classes'
        for c, features in self.class_features.items():
            predicted_class = self.get_class_for_features(features)
            if predicted_class != set(c):
                raise Exception(
                    "Invalid featurization: feature set {} associated with class {},"
                    "but produces class {}".format(features, set(c), predicted_class)
                )

    def features_to_csv(self, filename):
        '''
            Creates a CSV with classes as rows and corresponding feautral
            descriptors as columns
            
            Input:
                filename: A string specifying where to save the file
        '''
        with open(filename, 'w') as f:
            print(',' + ','.join([
                    str(i) for i in range(0, self.num_features)
                ]),
                file=f
            )
            for key, value in sorted(self.class_features.items(),
                    key=lambda x: -len(x[0])):
                d = dict(value)
                line = []
                line.append("{}".format(' '.join(key)))
                for i in range(0, self.num_features):
                    line.append(d.get(i, ''))
                print(','.join(line), file=f)

    def print_featurization(self):
        'Print out the classes and their featural specifications.'
        for key, value in sorted(self.class_features.items(),
                                 key=lambda x: -len(x[0])):
            print("{}:\t{}".format(key, sorted(value)))
        print()

    def print_segment_features(self):
        'Print out the segments and their featural specifications'
        for key, value in sorted(self.segment_features.items(),
                                 key=lambda x: -len(x[0])):
            print("{}:\t{}".format(key, sorted(value)))
        print() 

    def add_complement_classes(self):
        '''
            For the contrastive and full specifications, pre-calculate the full
            set of complement classes that will be added before doing the
            featurization. This is done using a breadth-first search of the poset
            Start with the alphabet
        '''
        bfs_deque = deque([self.alphabet])
        processed_classes = []

        while bfs_deque:
            current_node = bfs_deque.popleft()
            # Get the current node's children and sort them from largest to
            # smallest. This is necessary for a minimal featural specification
            children = sorted(
                self.poset.get_children(current_node),
                key=len,
                reverse=True
            )
            updated_children = []

            # Go through the children of the current node to decide what to 
            # append to the queue
            while children:
                child = children.pop(0)
                if (len(self.poset.get_parents(child)) == 1
                        and child not in processed_classes):
                    # If we haven't already processed a child and it only has
                    # a single parent, define a complement class wrt the
                    # current class (contrastive) or the alphabet (full)
                    if self.specification == Specification.FULL:
                        complement = self.alphabet - child
                    elif self.specification == Specification.CONTRASTIVE:
                        complement = current_node - child
                    else:
                        raise(
                            "Complement classes cannot be calculated for "
                            "specification type {}".format(self.specification)
                        )

                    # Add this new class to the poset
                    self.poset.add_class(complement, update_closure=True)

                    # If this new class intervenes between the current node
                    # and any of its children, we want to add the new class
                    # to the queue insted of the children to maintain BFS
                    removed_indexes = []
                    for i, other_child in enumerate(children):
                        if (self.poset.is_subset(other_child, complement)
                                or other_child == complement):
                            removed_indexes.append(i)
                    children = [
                        x for i, x in enumerate(children)
                        if i not in removed_indexes
                    ]

                    updated_children.append(complement)
                    processed_classes.append(complement)

                updated_children.append(child)
                processed_classes.append(child)

            bfs_deque.extend(updated_children)

    def featurize_classes(self):
        'Featurize the currently calculated poset'
        incomplete_classes = self.poset.classes.copy()

        while incomplete_classes:
            c = incomplete_classes.pop(0)
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

                    # We only want to consider the complement for contrastive
                    # underspecification if it's in the input set.
                    if (self.specification != Specification.CONTRASTIVE_UNDER
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
        if self.specification in (Specification.CONTRASTIVE, Specification.FULL):
            self.add_complement_classes()
        self.featurize_classes()

if __name__ == "__main__":
    # Choose a featurization type
    specification = Specification.FULL

    # A few sample inputs...
    # Input classes are the sunny sounds of Hawaiian.
    # This is an example of reading class input from a file.
    print("Doing Hawaiian...")
    featurizer = Featurizer.from_file(
        'sample_inputs/hawaiian.txt', specification
    )
    featurizer.get_features_from_classes()
    featurizer.graph_poset()
    featurizer.print_featurization()

    # An arbitrary vowel space with distinctive rounding, 3-way height,
    # and front/back distinction
    print("Doing vowel space...")
    featurizer = Featurizer.from_file(
        'sample_inputs/vowel_system.txt', specification
    )
    featurizer.get_features_from_classes()
    featurizer.print_featurization()

    # A poset where the full featurization learns fewer classes
    # than the contrastive featuriation
    print("Doing full/contrastive diff 1...")
    featurizer = Featurizer.from_file(
        'sample_inputs/full_contrastive_diff.txt', specification
    )
    featurizer.get_features_from_classes()
    featurizer.print_featurization()

    # A poset that properly does not include the empty set
    print("Doing paper example 1...")
    featurizer = Featurizer.from_file(
        'sample_inputs/paper_example_1.txt', specification
    )
    featurizer.get_features_from_classes()
    featurizer.print_featurization()

    # Vowel system from paper
    print("Doing paper vowels...")
    featurizer = Featurizer.from_file(
        'sample_inputs/paper_vowels.txt', specification
    )
    featurizer.get_features_from_classes()
    featurizer.print_featurization()

    # Class set that requires BFS to work properly with contrastive and
    # full specifications
    print("Doing problematic classes for non-BFS algorithm...")
    featurizer = Featurizer.from_file(
        'sample_inputs/bfs_requirement.txt', specification
    )
    featurizer.get_features_from_classes()
    featurizer.print_featurization()
