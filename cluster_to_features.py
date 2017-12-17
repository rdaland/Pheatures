from Poset import Poset
from collections import defaultdict
from itertools import chain, combinations

PRIVATIVE = 0
CONTRASTIVE_UNDERSPECIFICATION = 1
CONTRASTIVE = 2
FULL = 3

SPECIFICATIONS = [
    PRIVATIVE, CONTRASTIVE_UNDERSPECIFICATION, CONTRASTIVE, FULL
]

DEFAULT_CSV_FILE = "features.csv"

class Featurizer():
    def __init__(self, input_classes, alphabet,
                 specification=CONTRASTIVE_UNDERSPECIFICATION, verbose=False):
        if specification not in SPECIFICATIONS:
            raise("Invalid featural specification '{}'".format(specification))

        self.input_classes = input_classes
        self.alphabet = alphabet
        self.specification = specification
        self.class_features = defaultdict(set)
        self.verbose = verbose
        self.reset()

    def reset(self):
        self.class_features = defaultdict(set)
        self.feature_num = 0
        # Initialize complete_classes to just be the set of all sounds in the
        # language.
        self.complete_classes = [self.alphabet]

        # Build an intersectionally closed poset from the input classes
        # and take all the resulting classes minus the alphabet
        self.poset = Poset([self.alphabet] + self.input_classes)
        self.poset = self.poset.get_intersectional_closure()
        self.incomplete_classes = [
            c for c in sorted(self.poset.classes, key=len, reverse=True)
            if c not in self.complete_classes
        ]

    def set_class_features(self, c, features):
        self.class_features[tuple(sorted(c))].update(features)

    def get_class_features(self, c):
        return self.class_features[tuple(sorted(c))]

    def percolate_features_down(self, c):
        for cl in self.poset.classes:
            if self.poset.is_subset(cl, c):
                self.set_class_features(cl, self.get_class_features(c))

    def assert_classes_unique(self):
        assert(len(self.class_features)
                == len(set(map(tuple, self.class_features.values()))))

    def graph_poset(self):
        self.poset.graph_poset()

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

    def get_features_from_classes(self):
        while self.incomplete_classes:
            # Check how many parents the largest remaining class has
            c = self.incomplete_classes.pop(0)
            parents = self.poset.get_parents(c)

            # The only case we need to consider explicitly is when a
            # class has only one parent. This means it needs a new
            # feature to ditinguish it from its complement with respect
            # to that parent.
            # Classes with more than one parent will have already received
            # a full featural specification from their ancestors via
            # downward feature percolation, and so we can just mark them
            # as completed
            if len(parents) == 1:
                # Add the new feature assignment and mark this class as
                # complete
                c_features = set([(self.feature_num, '+')])
                self.set_class_features(c, c_features)
                self.complete_classes.append(c)

                # In privative specification, we don't consider the complement
                if self.specification != PRIVATIVE:
                    if self.specification == FULL:
                        # For full specification we take the complement wrt the
                        # set of all sounds.
                        c1 = self.alphabet - c
                    else:
                        # Otherwise take it wrt the parent set. 
                        c1 = parents[0] - c

                    # We only want to consider the complement for contrastive
                    # underspecification if it's in the input set.
                    if (self.specification != CONTRASTIVE_UNDERSPECIFICATION
                            or c1 in self.incomplete_classes):
                        # If the complement is not in the poset, add it and
                        # recalculate the intersectional closure
                        if c1 not in self.poset.classes:
                            class_added = self.poset.add_class(c1)
                            # TODO: Do we need to do this from scratch?
                            self.poset = self.poset.get_intersectional_closure()

                            # Check if the intersectional closure has generated
                            # any new classes
                            new_classes = [
                                s for s in self.poset.classes
                                if s not in self.complete_classes
                                    + self.incomplete_classes
                            ]
                            # If it has, assign them the features of their
                            # parents, since they won't have got these from
                            # downward percolation. This also covers our newly
                            # added class
                            for new_class in new_classes:
                                nc_parents = self.poset.get_parents(new_class)
                                parent_features = set.union(*[
                                        self.get_class_features(x)
                                        for x in nc_parents
                                    ]
                                )
                                self.set_class_features(
                                    new_class, parent_features
                                )

                        # Assign the negative value of the new feature to the 
                        # new class
                        c1_feature = set([(self.feature_num, '-')])
                        self.set_class_features(c1, c1_feature)

                        self.complete_classes.append(c1)

                        # Update incomplete classes. This does two things:
                        # (1) removes the any complement classes we've dealt
                        #     with
                        # (2) adds any new intersectional classes we've
                        #     produced
                        self.incomplete_classes = list(filter(
                            lambda x: x not in self.complete_classes,
                            sorted(self.poset.classes, key=len, reverse=True)
                        ))

                        # Go through each subclass of the complement and assign 
                        # it the same features
                        self.percolate_features_down(c1)

                self.feature_num += 1

                # Go through each subclass of c and assign it the same features
                self.percolate_features_down(c)
            
            self.complete_classes.append(c)

            if self.verbose:
                self.print_featurization()

        # Better have unique descriptions for each class!
        self.assert_classes_unique()

        return self.feature_num, self.class_features

if __name__ == "__main__":
    specification = CONTRASTIVE
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

    classes_test2 = [
        ['R', 'D'],
        ['R'],
    ]

    print("Doing test 2...")
    featurizer = Featurizer(classes_test2, all_sounds_test2, specification)
    featurizer.get_features_from_classes()
    featurizer.print_featurization()
