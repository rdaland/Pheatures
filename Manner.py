from Poset import *
from cluster_to_features import *

## uyghur1: 'a' is a back, non-round vowel
## uyghur2: 'a' is a non-back, non-round vowel
## uyghur3: 'a' is a back, round vowel
## uyghur4: 'a' is a non-back, round vowel

all_vowels = set(['i', 'y', 'e', '@', 'u', 'o', 'a'])
front_vowels = set(['i', 'y', 'e', '@'])
back_vowels = set(['u', 'o', 'a'])
round_vowels = set(['y', '@', 'u', 'o'])
high_vowels = set(['i', 'y', 'u'])
frnt_unrnd_vowels = set(['i', 'e'])
nonlow_vowels = set(['i', 'y', 'e', '@', 'u', 'o'])

classes_uyghur = [all_vowels,
                   front_vowels,
                   back_vowels,
                   round_vowels,
                   high_vowels,
                   frnt_unrnd_vowels,
                   nonlow_vowels,
                   set(['i']), set(['y']),  set(['u']),
                   set(['e']), set(['@']), set(['o']),
                                            set(['a'])
                   ]

for spec in Specification:
    captionStr = 'Doing Uyghur: '+str(spec)
    spacer = len(captionStr)+6
    print()
    print('*'*spacer)
    print('** {0} **'.format(captionStr))
    print('*'*spacer)
    
    uyghur_feats = Featurizer(input_classes = classes_uyghur,
                              alphabet = all_vowels,
                              specification = spec)
    uyghur_feats.get_features_from_classes()
    uyghur_feats.print_featurization()

    print()


