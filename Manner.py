from Poset import *
from Featurizer import *

sigma = set(['V', 'G', 'L', 'N', 'T'])
son = set(['V', 'G', 'L', 'N'])
aprx = set(['V', 'G', 'L'])
ncont = set(['N', 'T'])
syl = set(['V'])
glid = set(['G'])
liq = set(['L'])
nas = set(['N'])
vcls = set(['T'])

classes = [sigma, son, aprx, ncont,
           syl, glid, liq, nas, vcls]

'''
for spec in Specification:
    captionStr = 'Doing manner: '+str(spec)
    spacer = len(captionStr)+6
    print()
    print('*'*spacer)
    print('** {0} **'.format(captionStr))
    print('*'*spacer)
    
    feats = Featurizer(input_classes = classes,
                       alphabet = sigma,
                       specification = spec)
    feats.get_features_from_classes()
    feats.print_featurization()

    print()
'''

feats = Featurizer(input_classes = classes,
                   alphabet = sigma,
                   specification = Specification.CONTRASTIVE_UNDER)
feats.get_features_from_classes()
feats.print_featurization()
feats.poset.graph_poset2('manner_underspec.gv')










