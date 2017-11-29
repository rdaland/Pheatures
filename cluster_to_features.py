from Poset import Poset
from collections import defaultdict
from itertools import chain, combinations

# Input classes are the sunny sounds of Hawaiian.
input_classes_hawaiian = [
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

input_classes_vowels = [
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

def powerset_generator(classes, max_size=0, min_size=1):
    # Generate power set from largest to smallest.
    if max_size == 0:
        max_size = len(classes) + 1
    for subset in chain.from_iterable(
            combinations(classes, r) 
            for r in range (max_size, min_size, -1)):
        yield subset

def check_intersections(test_class, input_classes, class_features,
                        stop_when_found=True):
    # We obviously don't want to look at all possible intersections, since
    # this is extremely expensive. Instead we start by looking at power sets
    # up to size 2, and then continue to increase the maximum size until the
    # resulting union of features no longer changes.

    # Something to think about: does this actually work? If an increase of max
    # number of sets of intersection doesn't change between n and n+1, does
    # this guarantee it won't change for n+2 or greater?
    max_powerset_size = 2
    prev_union_features = None
    union_features = None

    while True:
        prev_union_features = union_features
        max_powerset_size += 1

        for pset in powerset_generator(input_classes, max_powerset_size):
                if test_class == set.intersection(*pset):
                    found_intersection = True
                    union_features = set.union(
                        *[class_features[tuple(sorted(x))] for x in pset]
                    )
                    # Should we consider multiple possible featural
                    # specifications for the same set?
                    if stop_when_found:
                        break
        if prev_union_features == union_features:
            break

    return union_features

def get_features_from_classes_poset(input_classes, sounds):
    # Initialize complete_classes to just be the set of all sounds in the
    # language.
    complete_classes = [sounds]

    # Build an intersectionally closed poset from the input classes
    # and take all the resulting classes
    poset = Poset([sounds] + input_classes).get_intersectional_closure()
    incomplete_classes = sorted(poset.classes, key=len, reverse=True)

    # A dictionary to associate classes with features.
    class_features = defaultdict(set)

    # Integer labels for learned features
    feature_num = 0

    while incomplete_classes:
        # Check how many parents the largest remaining class has
        c = incomplete_classes.pop(0)
        parents = poset.get_parents(c)

        if not parents:
            # This is the full set of sounds
            class_features[tuple(sorted(c))] = set()

        elif len(parents) == 1:
            # Just one parent, which means it cannot be generated as
            # the intersection of two or more larger classes, which
            # means we need a new feature. Get the complement class
            # wrt its parent and assign +/- feature values arbitrarily
            c1 = parents[0] - c
            c_feature = set([(feature_num, '+')])
            c1_feature = set([(feature_num, '-')])
            feature_num += 1

            # Add the new complement class to the poset and recalculate
            # intersectional closure
            poset.add_class(c1)
            poset = poset.get_intersectional_closure()

            # Get the features of the superclass and combine them with new
            # subclass features
            superclass_features = class_features[
                tuple(sorted(parents[0]))
            ]
            c_features = superclass_features.union(c_feature)
            c1_features = superclass_features.union(c1_feature)

            # Update features for each class and each segment within those classes.
            class_features[tuple(sorted(c))].update(c_features)
            class_features[tuple(sorted(c1))].update(c1_features)

            # Go through each subclass of c and c1 and assign them the same features
            for cl in incomplete_classes:
                if poset.is_subset(cl, c):
                    class_features[tuple(sorted(cl))].update(c_features)
                if poset.is_subset(cl, c1):
                    class_features[tuple(sorted(cl))].update(c1_features)

            # Add c and c1 to classes we've finished with
            complete_classes.append(c)
            complete_classes.append(c1)

            # Update the classes we still need to deal with to be the set of 
            # classes in the new poset that we haven't already dealt with
            incomplete_classes = list(filter(
                lambda x: x not in complete_classes,
                sorted(poset.classes, key=len, reverse=True)
            ))

        else:
            # Class has more than one parent, so we can define its features
            # as the intersection of their features. Get their features and
            # assign them to the class
            union_features = set.union(
                *[class_features[tuple(sorted(x))] for x in parents]
            )
            class_features[tuple(sorted(c))].update(union_features)

            # Assign this class's features to all its subclasses.
            for cl in incomplete_classes:
                if poset.is_subset(cl, c):
                    class_features[tuple(sorted(cl))].update(union_features)
            complete_classes.append(c)

    # Print out the classes and their featural specifications.
    for key, value in sorted(class_features.items(), key=lambda x: len(x[1])):
        print("{}:\t{}".format(key, sorted(value)))

    # Better have unique descriptions for each class!
    assert(len(class_features) == len(set(map(tuple, class_features.values()))))

def get_features_from_classes(input_classes, sounds):
    # Initialize complete_classes to just be the set of all sounds in the
    # language.
    complete_classes = [sounds]

    # Sort input classes from largest to smallest
    incomplete_classes = sorted(input_classes, key=lambda x: -len(x))

    # A dictionary to associate classes with features.
    class_features = defaultdict(set)

    # Integer labels for learned features
    feature_num = 0

    for c in incomplete_classes:
        if c in complete_classes:
            # We've already accounted for this class
            continue

        # Is this class an intersection of two classes we've already
        # accounted for? If it is, it can be defined by the union of
        # their features, and we don't need to add a new feature.
        union_features = check_intersections(c, complete_classes, class_features)
        if union_features:
            # We've found at least one intersection of classes that accounts
            # for this class, so no need to add a new feature, keep going.
            class_features[tuple(sorted(c))].update(union_features)
            for cl in incomplete_classes:
                if cl < c:
                    class_features[tuple(sorted(cl))].update(union_features)
            complete_classes.append(c)
            continue

        # Not an intersection of two existing classes, so we need a new 
        # feature. Find the smallest cluster such that c is a subset of
        smallest_containing_cluster = min(
            [c for c in filter(lambda x: c.issubset(x), complete_classes)],
            key=len
        )

        # Get the complement of c wrt this cluster
        c1 = smallest_containing_cluster - c

        # Arbitrariy associate +/- values of this feature with c and
        # its complement wrt the containing class.
        # TODO: What about privative features?
        c_feature = set([(feature_num, '+')])
        c1_feature = set([(feature_num, '-')])
        feature_num += 1

        # Get the features of the superclass 
        superclass_features = class_features[
            tuple(sorted(smallest_containing_cluster))
        ]
        c_features = superclass_features.union(c_feature)
        c1_features = superclass_features.union(c1_feature)

        # Update features for each class and each segment within those classes.
        class_features[tuple(sorted(c))].update(c_features)
        for cl in incomplete_classes:
            if cl < c:
                class_features[tuple(sorted(cl))].update(c_features)
        class_features[tuple(sorted(c1))].update(c1_features)
        for cl in incomplete_classes:
            if cl < c1:
                class_features[tuple(sorted(cl))].update(c1_features)

        # Mark both classes as accounted for.
        complete_classes.append(c)
        complete_classes.append(c1)

    # Print out the classes and their featural specifications.
    for key, value in sorted(class_features.items(), key=lambda x: len(x[1])):
        print("{}:\t{}".format(key, sorted(value)))

    # Better have unique descriptions for each class!
    assert(len(class_features) == len(set(map(tuple, class_features.values()))))

if __name__ == "__main__":
    # print("Doing Hawaiian...")
    # get_features_from_classes(input_classes_hawaiian, all_sounds_hawaiian)
    
    #print("Doing poset Hawaiian...")
    #get_features_from_classes_poset(input_classes_hawaiian, all_sounds_hawaiian)

    # print("\nDoing vowels...")
    # get_features_from_classes(input_classes_vowels, all_sounds_vowels)

    print("\nDoing poset vowels...")
    get_features_from_classes_poset(input_classes_vowels, all_sounds_vowels)
