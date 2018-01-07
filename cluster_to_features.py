from Poset import Poset
from collections import defaultdict, deque
from enum import Enum
from itertools import chain, combinations

DEFAULT_CSV_FILE = "features.csv"
DEFAULT_GRAPH_FILENAME = "poset_graph.gv"

class Specification(Enum):
    PRIVATIVE = 0
    CONTRASTIVE_UNDER = 1
    CONTRASTIVE = 2
    FULL = 3

class Featurizer():
    def __init__(self, input_classes, alphabet,
                 specification=Specification.CONTRASTIVE_UNDER, verbose=False):
        # Default class constructor that must be given an alphabet and a set
        # of input classes.
        # 
        # Input:
        #   input_classes: A list of sets of segments
        #   alphabet: A set of all segments used in input_classes
        #   specification: The Specification indicating the type of
        #                  featurization to do
        #   verbose: A bool indicating whether to print extra information
        #            during the featurization
        if specification not in Specification:
            raise("Invalid featural specification '{}'".format(specification))

        self.input_classes = input_classes
        self.alphabet = alphabet
        self.specification = specification
        self.verbose = verbose
        self.reset()

    @classmethod
    def from_file(cls, filename, specification=Specification.CONTRASTIVE_UNDER):
        # An alternative constructor that creates a Featurizer object based on
        # the contents of a file. The file should have the following format
        #
        # <alphabet>
        # <input class 1>
        # ...
        # <input class n>
        #
        # <alphabet> and <input class i> are segments separated by spaces.
        # Segments do not need to be single characters.
        #
        # Input:
        #   filename: A string specifying where to find the input file.
        #   specification: The type of featurization to do
        with open(filename, 'r') as f:
            alphabet = set(next(f).rstrip().split(' '))
            classes = []
            for line in f:
                c = set(line.rstrip().split(' '))
                if c:
                    classes.append(c)
        return Featurizer(classes, alphabet, specification)

    def reset(self):
        # Resets the featurization and poset to the state they were in before
        # any featurization algorithm was run. If you want to rerun different
        # featurization algorithms on the same instance, you'll need to call
        # this first.
        self.class_features = defaultdict(set)
        self.segment_features = defaultdict(set)
        self.feature_num = 1

        # Build an intersectionally closed poset from the input classes
        self.poset = Poset(self.alphabet, self.input_classes)
        self.poset.get_intersectional_closure()

    def set_segment_features(self, c, feature):
        # Adds a feature/value pair to the featural description of every
        # segment in a class.
        #
        # Input:
        #   c: A set of strings
        #   feature: A tuple of the form (<feature number>, <value>)
        for segment in c:
            self.segment_features[segment].update(feature)

    def set_class_features(self, c, features):
        # Adds a feature/value pair to the featural description of a class
        #
        # Input:
        #   c: A set of strings
        #   features
        self.class_features[tuple(sorted(c))].update(features)

    def get_class_features(self, c):
        # Gets the features required to specify a class
        # Input:
        #   c: A set of strings
        # Returns:
        #   A set of feature/value pairs that uniquely pick out c
        return set.intersection(*[
            self.segment_features.get(x, set()) for x in c
        ])

    def calculate_class_features(self):
        # Calculate the featural description for each class in the poset
        for c in self.poset.classes:
            features = self.get_class_features(c)
            self.set_class_features(c, features)

    def graph_poset(self, filename=DEFAULT_GRAPH_FILENAME, title=None):
        # Graphs the class poset
        #
        # Input:
        #   filename: A string indicating where to save the file
        #   title: A string providing an optional title for the graph
        self.poset.graph_poset(filename, title)

    def get_segments_for_feature(self, feature):
        # Gets the segments picked out by a feature
        # Input:
        #   feature: A tuple of the form (<feature_number>, <value>)
        # Returns:
        #   A set of segments
        segments = set()
        for segment, features in self.segment_features.items():
            if feature in features:
                segments.add(segment)
        return segments

    def get_class_for_features(self, features):
        # Given a set of feature/value pairs, return the class they pick out
        # Input:
        #   features: A list of tuples of the form (<feature_number>, <value>)
        # Returns:
        #   A set representing the class specified by features
        feature_segments = [self.alphabet]
        for feature in features:
            segments = self.get_segments_for_feature(feature)
            feature_segments.append(segments)
        return set.intersection(*feature_segments)

    def assert_valid_featurization(self):
        # Checks that the calculcated features pick out the expected classes
        for c, features in self.class_features.items():
            predicted_class = self.get_class_for_features(features)
            if predicted_class != set(c):
                raise Exception(
                    "Invalid featurization: feature set {} associated with class {},"
                    "but produces class {}".format(features, set(c), predicted_class)
                )

    def features_to_csv(self, filename):
        # Creates a CSV with classes as rows and corresponding feautral
        # descriptors as columns
        # Input:
        #   filename: A string specifying where to save the file
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
        # Print out the classes and their featural specifications.
        for key, value in sorted(self.class_features.items(),
                                 key=lambda x: -len(x[0])):
            print("{}:\t{}".format(key, sorted(value)))
        print()

    def print_segment_features(self):
        # Print out the segments and their featural specifications
        for key, value in sorted(self.segment_features.items(),
                                 key=lambda x: -len(x[0])):
            print("{}:\t{}".format(key, sorted(value)))
        print() 

    def add_complement_classes(self):
        # For the contrastive and full specifications, pre-calculate the full
        # set of complement classes that will be added before doing the
        # featurization.
        bfs_deque = deque([self.alphabet])
        processed_classes = []

        while bfs_deque:
            current_node = bfs_deque.popleft()
            children = sorted(
                self.poset.get_children(current_node),
                key=len,
                reverse=True
            )
            updated_children = []

            while children:
                child = children.pop(0)
                if (len(self.poset.get_parents(child)) == 1
                        and child not in processed_classes):
                    if self.specification == Specification.FULL:
                        complement = self.alphabet - child
                    elif self.specification == Specification.CONTRASTIVE:
                        complement = current_node - child
                    else:
                        raise(
                            "Complement classes cannot be calculated for "
                            "specification type {}".format(self.specification)
                        )

                    self.poset.add_class(complement, update_closure=True)
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
        # Featurize the currently calculated poset
        incomplete_classes = self.poset.classes.copy()

        while incomplete_classes:
            c = incomplete_classes.pop(0)
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
        # Calculate the complements added by the featurization if any, and then
        # featurize the poset
        if self.specification in (Specification.CONTRASTIVE, Specification.FULL):
            self.add_complement_classes()
        self.featurize_classes()

if __name__ == "__main__":
    # Choose a featurization type
    specification = Specification.FULL

    # A few sample inputs...
    # Input classes are the sunny sounds of Hawaiian.
    # This is an example of reading class input from a file.
    featurizer = Featurizer.from_file('sample_inputs/hawaiian.txt', specification)
    featurizer.get_features_from_classes()
    featurizer.print_featurization()
    featurizer.graph_poset()

    # An arbitrary vowel space with distinctive rounding, 3-way height,
    # and front/back distinction

    classes_vowels = [
        # Test for round/unround vowel system, which needs a minimum intersection
        # of 3 classes to avoid specifying spurious features.
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

    all_sounds_vowels = set(
        ['i', 'y', 'e', 'E', 'a', 'u', 'U', 'o', 'O']
    )

    print("Doing vowel space...")
    featurizer = Featurizer(classes_vowels, all_sounds_vowels, specification)
    featurizer.get_features_from_classes()
    featurizer.print_featurization()

    # A poset where the full featurization learns fewer classes
    # than the contrastive featuriation
    all_sounds_test1 = set(['a', 'b', 'c', 'd', 'e'])
    classes_test1 = [
        set(['a', 'b', 'c', 'd']),
        set(['a', 'b', 'c']),
        set(['d', 'e']),
        set(['a']),
        set(['b']),
        set(['c']),
        set(['d']),
        set(['e']),
    ]

    print("Doing test 1...")
    featurizer = Featurizer(classes_test1, all_sounds_test1, specification)
    featurizer.get_features_from_classes()
    featurizer.print_featurization()

    # A poset that properly does not include the empty set
    all_sounds_test2 = set(
        ['R', 'D', 'T'],
    )

    # classes_test2 = [
    #     ['R', 'D'],
    #     ['R'],
    # ]
    classes_test2 = [
        ['R'],
        ['R', 'D'],
        ['D', 'T'],
        ['T'],
        ['D']
    ]

    print("Doing test 2...")
    featurizer = Featurizer(classes_test2, all_sounds_test2, specification)
    featurizer.get_features_from_classes()
    featurizer.print_featurization()

    all_paper_vowels = set([
        'i', 'y', 'U', 'u', 'e', 'E', '^', 'O', 'a'
    ])
    classes_paper_vowels = [
        set(['E', 'y', 'e', 'i']),
        set(['E', 'O', 'u', 'y']),
        set(['u', 'y', 'i', 'U']),
        *[set([v]) for v in all_paper_vowels]
    ]

    print("Doing paper vowels...")
    featurizer = Featurizer(classes_paper_vowels, all_paper_vowels, specification)
    featurizer.get_features_from_classes()
    featurizer.print_featurization()

    bad_class_all = set([
        'a', 'b', 'c', 'd', 'e', 'f'
    ])
    bad_classes = [
        ['a', 'b'],
        ['a', 'c', 'e', 'f'],
        ['c', 'e', 'f'],
    ]

    print("Doing bad vowels...")
    featurizer = Featurizer(bad_classes, bad_class_all, specification)
    featurizer.get_features_from_classes()
    featurizer.print_featurization()

    bad_class_all_2 = set([
        'a', 'b', 'c', 'd', 'e', 'f'
    ])
    bad_classes_2 = [
        ['a', 'b'],
        ['a', 'c', 'e', 'f'],
        ['c', 'e', 'f'],
        ['b', 'd'],
        ['c', 'd', 'e', 'f'],
        ['a']
    ]

    print("Doing other bad vowels...")
    featurizer = Featurizer(bad_classes_2, bad_class_all_2, specification)
    featurizer.get_features_from_classes()
    featurizer.print_featurization()
    featurizer.graph_poset()
