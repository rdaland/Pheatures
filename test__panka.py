from FeatureSet import *

################################################
##      define the language PANKA             ##
################################################

data = ['kim', 'kimi', 'kimta', \
        'tip', 'tibi', 'tipta', \
        'lok', 'logu', 'lokna', \
        'kami', 'kamii', 'kamida', \
        'tuba', 'tubai', 'tubada', \
        'legu', 'leguu', 'leguna']

## write wordforms to file with spaces between segments
## this is not important here, but useful for segmentation
##    when some segments require more than one character
## easier to write a single implementation which assumes
##    the segments are space-separated, even when not needed
with open('panka_data.txt', 'w') as fout:
    for wordform in data:
        print >> fout, ' '.join([c for c in wordform])

#### verify
##with open('panka_data.txt') as fin:
##    for line in fin:
##        print line.rstrip()

################################################
##          featurizing PANKA                 ##
################################################

with open('panka_FEATS.txt','w') as fout:
    print >> fout, '\t'.join(['', 'syl', 'cont', 'son', 'vcd', 'LAB', 'COR', 'DOR', 'high', 'low', 'front', 'back', 'WB'])
    print >> fout, '\t'.join([c for c in '#00000000000+'])
    print >> fout, '\t'.join([c for c in 'a+++0000-+---'])
    print >> fout, '\t'.join([c for c in 'i+++0000+-+--'])
    print >> fout, '\t'.join([c for c in 'e+++0000--+--'])
    print >> fout, '\t'.join([c for c in 'u+++0000+--+-'])
    print >> fout, '\t'.join([c for c in 'o+++0000---+-'])

    print >> fout, '\t'.join([c for c in 'l-++00+00000-'])
    print >> fout, '\t'.join([c for c in 'm--+0+000000-'])
    print >> fout, '\t'.join([c for c in 'n--+00+00000-'])

    print >> fout, '\t'.join([c for c in 'p----+000000-'])
    print >> fout, '\t'.join([c for c in 't----0+00000-'])
    print >> fout, '\t'.join([c for c in 'k----00+0000-'])

    print >> fout, '\t'.join([c for c in 'b---++000000-'])
    print >> fout, '\t'.join([c for c in 'd---+0+00000-'])
    print >> fout, '\t'.join([c for c in 'g---+00+0000-'])

## # verify
## with open('panka_FEATS.txt') as fin:
##     for line in fin:
##         print line.rstrip()


## While each of these decisions is defensible on its own,
## the reader may wonder about the rationale for making
## different decisions for different parts of the grammar?
## Why adopt a 'binary cuts in sonority' scale for manner
## features, privative underspecification for major consonantal
## place, and full specification for vowels? One purpose is to
## demonstrate that the machinery of the feature specification
## is compatible with all of these possibilities; the other
## purpose is to test whether the complementary distribution
## algorithm is in fact sensitive to featurization assumptions.

################################################
##         testing with PANKA                 ##
################################################

print "Reading the feature file in and calculating natural classes...",
feats = FeatureSet('panka_FEATS.txt')
print "Done!\n"

print "Writing all natural classes to panka_NATCLASS.txt, one per line with space-separated segments...", 
feats.saveclasses('panka_NATCLASS.txt')
print "Done!\n"

print "Printing the content of panka_NATCLASS.txt:\n"
with open('panka_NATCLASS.txt') as fin:
    for line in fin:
        print line.rstrip()

## get all natural classes to which 'b' belongs
print "What natural classes does [b] belong to?"
for natclass in feats.segclasses('b'):
    print '\t', ' '.join(natclass)
print

print "Get the natural class corresponding to a featural descriptor"
print "even if it is NOT a canonical descriptor, e.g. +syl,+son,+cont"
print feats.featureStr2segList('+syl,+son,+cont'), '\n'

## get the canonical featural descriptor of a natural class
print "Canonical featural descriptor for natural class {b, d, g}: \t",
print feats.segList2featureStr(['b', 'd', 'g']), '\n'

print "Canonical featural descriptor for natural class {l, m, n}: \t",
print feats.segList2featureStr(['l', 'm', 'n']), '\n'

## FeatureSet correctly rejects an un-natural class
print "Canonical featural descriptor for natural class {l, m}: \t",
#print feats.segList2featureStr(['l', 'm']), '\n'



