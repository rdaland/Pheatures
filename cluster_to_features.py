from Poset import Poset
from collections import defaultdict, deque
from enum import Enum
from itertools import chain, combinations

DEFAULT_CSV_FILE = "features.csv"

class Specification(Enum):
    PRIVATIVE = 0
    CONTRASTIVE_UNDER = 1
    CONTRASTIVE = 2
    FULL = 3

class Featurizer():
    def __init__(self, input_classes, alphabet,
                 specification=Specification.CONTRASTIVE_UNDER, verbose=False):
        if specification not in Specification:
            raise("Invalid featural specification '{}'".format(specification))

        self.input_classes = input_classes
        self.alphabet = alphabet
        self.specification = specification
        self.verbose = verbose
        self.reset()

    def reset(self):
        self.class_features = defaultdict(set)
        self.segment_features = defaultdict(set)
        self.feature_num = 1
        # Build an intersectionally closed poset from the input classes
        self.poset = Poset(self.alphabet, self.input_classes)
        self.poset.get_intersectional_closure()

        # Build the list of classes we need to consider
        # if self.specification in (Specification.CONTRASTIVE, Specification.FULL):
        #     self.incomplete_classes = sorted(
        #         self.poset.classes, key=len, reverse=True
        #     )
        # else:
        #     self.incomplete_classes = self.poset.classes.copy()

    def set_segment_features(self, c, features):
        for segment in c:
            self.segment_features[segment].update(features)

    def set_class_features(self, c, features):
        self.class_features[tuple(sorted(c))].update(features)

    def get_class_features(self, c):
        return set.intersection(*[
            self.segment_features.get(x, set()) for x in c
        ])

    def calculate_class_features(self):
        for c in self.poset.classes:
            # Don't attempt to featurize the empty set
            if c:
                features = self.get_class_features(c)
                self.set_class_features(c, features)

    def graph_poset(self):
        self.poset.graph_poset()

    def get_segments_for_feature(self, feature):
        segments = set()
        for segment, features in self.segment_features.items():
            if feature in features:
                segments.update(segment)
        return segments

    def assert_valid_featurization(self):
        for c, features in self.class_features.items():
            if not features:
                predicted_class = self.alphabet
            else:
                feature_segments = []
                for feature in features:
                    segments = self.get_segments_for_feature(feature)
                    feature_segments.append(segments)
                predicted_class = set.intersection(*feature_segments)
            if predicted_class != set(c):
                raise Exception(
                    "Invalid featurization: feature set {} associated with class {},"
                    "but produces class {}".format(features, set(c), predicted_class)
                )

    def features_to_csv(self, filename):
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
        for key, value in sorted(self.segment_features.items(),
                                 key=lambda x: -len(x[0])):
            print("{}:\t{}".format(key, sorted(value)))
        print() 

    def get_features_from_classes(self):
        if self.specification == Specification.CONTRASTIVE:
            self.get_features_from_classes_bfs2()
        else:
            self.get_features_from_classes_unordered()

        self.poset.graph_poset('test')
        self.calculate_class_features()
        self.assert_valid_featurization()

    def get_features_from_classes_bfs2(self):
        # Deque holds tuples of the class, and the class that added it
        bfs_queue = [(self.alphabet, None)]
        processed_classes = []
        while bfs_queue:
            c, c_adder = bfs_queue.pop(0)

            children = zip(
                sorted(
                    self.poset.get_children(c),
                    key=len,
                    reverse=True
                ),
                c
            )
            bfs_queue.extend(children)

            parents = self.poset.get_parents(c)

            if len(parents) == 1 and c not in processed_classes:
                parent = parents[0]

                c_features = set([(self.feature_num, '+')])
                self.set_segment_features(c, c_features)

                c1 = parent - c
                self.poset.add_class(c1, update_closure=True)
                c1_feature = set([(self.feature_num, '-')])
                self.set_segment_features(c1, c1_feature)

                removed_indexes = []
                for i, other_c in enumerate(bfs_queue):
                    if other_c[1] == c_adder and self.poset.is_subset(other_c[0], c1):
                        removed_indexes.append(i)
                bfs_queue = [
                    x for i, x in enumerate(bfs_queue)
                    if i not in removed_indexes
                ]

                self.feature_num += 1
                processed_classes.append(c1)

            processed_classes.append(c)

    def get_features_from_classes_bfs(self):
        bfs_deque = deque([self.alphabet])
        processed_classes = []

        while bfs_deque:
            current_node = bfs_deque.popleft()
            # if current_node == {"a", "^"}:
            #     import pdb; pdb.set_trace()
            children = sorted(
                self.poset.get_children(current_node),
                key=len,
                reverse=True
            )
            updated_children = []
            while children:
                child = children.pop(0)
                if len(self.poset.get_parents(child)) == 1 and child not in processed_classes:
                    child_features = set([(self.feature_num, '+')])
                    self.set_segment_features(child, child_features)

                    complement = current_node - child
                    self.poset.add_class(complement, update_closure=True)
                    complement_feature = set([(self.feature_num, '-')])
                    self.set_segment_features(complement, complement_feature)

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
                    self.feature_num += 1

                updated_children.append(child)
                processed_classes.append(child)
            bfs_deque.extend(updated_children)

    def get_features_from_classes_unordered(self):
        incomplete_classes = self.poset.classes.copy()

        while incomplete_classes:
            c = incomplete_classes.pop(0)
            if len(self.poset.get_parents(c)) == 1:
                c_features = set([(self.feature_num, '+')])
                self.set_segment_features(c, c_features)

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
                        # If the complement is not in the poset, add it and
                        # recalculate the intersectional closure
                        self.poset.add_class(c1, update_closure=True)

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

if __name__ == "__main__":
    # Choose a featurization type
    specification = Specification.CONTRASTIVE

    # A few sample inputs...
    # Input classes are the sunny sounds of Hawaiian.
    classes_hawaiian = [
        # Consonants
        set(['m', 'n', 'p', 'k', '7', 'h', 'w', 'l']),
        # Sonorants
        set(['m', 'n', 'w', 'l']),
        # Approximants
        set(['w', 'l']),
        # Nasal stops
        set(['m', 'n']),
        # Obstruents
        set(['p', 'k', '7', 'h']),
        # Stops
        set(['m', 'n', 'p', 'k', '7']),
        # Oral stops 
        set(['p', 'k', '7']),
        # Glottals
        set(['h', '7']),
        # Bilabials
        set(['w', 'p', 'm']),
        # Coronals
        set(['n', 'l']),
        # Individual consonants
        set(['m']),
        set(['n']),
        set(['p']),
        set(['7']),
        set(['h']),
        set(['w']),
        set(['l']),
        set(['k']),

        # Vowels
        # All vowels
        set(['i', 'u', 'e', 'o', 'a']),
        # High vowels
        set(['i', 'u']),
        # Mid vowels
        set(['e', 'o']),
        # Front vowels
        set(['i', 'e']),
        # Back vowels
        set (['u', 'o', 'a']),
        # Individual vowels
        set(['i']),
        set(['u']),
        set(['e']),
        set(['o']),
        set(['a'])
    ]

    all_sounds_hawaiian = set(
        ['m', 'n', 'p', 'k', '7', 'h', 'w', 'l', 'i', 'e', 'a', 'o', 'u']
    )

    print("Doing Hawaiian...")
    featurizer = Featurizer(classes_hawaiian, all_sounds_hawaiian, specification)
    featurizer.get_features_from_classes()
    featurizer.print_featurization()

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
