################################################
##      FEATURESET: feature magic             ##
################################################

class FeatureSet:
    """
    A FeatureSet object mediates between segments, features, natural
    classes, and regular expressions. FeatureSets are specified by
    feature files, in the following format:
        <\t>    feat_0  feat_1  feat_2  ... feat_k-1
        seg0    +/0/-   +/0/-   ...
        seg1    ...     ...
        ...                     ...
        segn-1
    The notation +/0/- indicates that the value for seg[i], feature[j]
    must be '+', '0', or '-'. The meanings of these values is discussed
    later. (The '<\t>' indicates a blank tab.)
    
    A segment is represented as a string. For example, the IPA segment
    ETH might be represented as the string 'DH'. The inventory of all
    segments in a FeatureSet is saved in
--->    self.segments <list> -- segmental inventory, lexicographic order

    Conceptually, a feature is a variable, for which particular segments
    have particular values. The names of features are stored in a list,
    in the order in which they occurred in the feature file:
        self.features <list> -- list of feature names, feature file order
        
    Segments are characterized by their feature values. Conjunctions of
    features pick out individual segments or whole classes of segments.    
    For example, the segment 'M' could be characterized as [+sonorant],
    [+labial], [-continuant], [+nasal], and '0'-valued for most other
    features. Since the features have an explicit order/index, the entire
    specification for a segment can be efficiently represented with a
    string of '+', '-', and '0's, with the following semantics:
        '+': the segment has the feature
        '-': the segment lacks the feature, but could have had it
        '0': the feature does not apply to the segment
    Exactly such a representation is stored in the segdict:
--->    self.segdict <dict> -- feature values for each segment
            key: segment <str>
            value: feature values <str>
    
    A natural class is the unique set of segments picked out by a
    conjunction of feature values. For example, the descriptor
    [-sonorant,-continuant] picks out the oral stops (n.b. nasal stops
    are [+sonorant,-continuant]). Natural classes may only be defined
    using '+' and '-' values, formally implementing contrastive and
    privative underspecification. For example, if the feature file assigns
    a '0voice' value to sonorants, then the featural descriptors '+voice'
    and '-voice' will include only non-sonorants. If the feature file
    assigns '+dorsal' to dorsal segments and '0dorsal' to all others,
    the descriptor '-dorsal' will refer to the empty set (which is
    excluded from the list of natural classes). Underneath the hood
    of the FeatureSet code, this is accomplished with an internal
    representation called a FEATSPEC, which is a list of
    (feature index, non-zero value) pairs. The entire set of *distinct*
    natural classes can be efficiently enumerated using this
    representation (see enumerate for details). It is then stored in
--->    self.natclasses <dict>
            key: tuple containing all segments in the natural class
            value: featspec which specified the class
    
    There are internal functions which translate between featspecs
    and the corresponding (human-readable) feature string descriptors:
        str2featspec
        featspec2str
    More usefully to external users, functions which translate between
    the human-readable feature string and the extension of the corresponding
    natural class:
        featureStr2segList
        segList2featureStr
        
    The FeatureSet code is relatively autonomous. If you supply a feature
    file in the correct format, you can initialize the FeatureSet object
    by passing it the filename. It will fill in all the data structures,
    including computing the natural classes, efficiently.

    """
    def __init__(self, featfile = None):
        self.features = []
        self.segments = []
        self.segdict = {}
        self.featdict = {}
        self.natclasses = {}
        if featfile:
            self.readFeatures(featfile)
            self.getclasses()
        
    def readFeatures(self, featfile):
        """Reads in data from feature file. Header row should have initial
        whitespace and then feature names."""
        fin = open(featfile)
        self.features = fin.readline().split()
        for line in fin:
            parse = line.split()
            seg, featvals = parse[0], ''.join(parse[1:])
            self.segments.append(seg)
            self.segdict[seg] = featvals
            for iFeat, featval in enumerate(featvals):
                if featval == '0': continue
                self.featdict[(self.features[iFeat],featval)] = sorted( \
                    self.featdict.get((self.features[iFeat],featval),[])+[seg])
        fin.close()

    def uppertriang(self, featspec):
        """ For enumeration. If input featspec specifies [+FeatureI,-FeatureJ],
        this function will generate all featspecs of the form
        [+FeatureI,-FeatureJ, +/-FeatureK] where K>J. Similarly, if the input
        featspec has 3 featural specifications, the output will be a list of
        4-feature pecifications. Featspecs whose extension matches a class
        that has already been enumerated are pruned immediately, so that the
        entire feature space does not have to be searched. Feature indices
        are determined by the header row in the feature file."""
        return([featspec+[(i,'+')] \
                    for i in range(featspec[-1][0]+1,len(self.features))] + \
               [featspec+[(i,'-')] \
                    for i in range(featspec[-1][0]+1,len(self.features))])

    def getclasses(self, outfile = None):
        """ A featspec is a list of pairs [(i,b[i]), (i+j,b[i+j]), ...] where
            n is a feature index and where b[n] is a feature value (+/-).
        This function searches all featspecs in an order designed to allow for
            efficient paring of redundant featspecs. """
        self.natclasses[tuple(self.segments)] = []
        nextspecs = [[(i,'+')] for i in range(len(self.features))] + \
                [[(i,'-')] for i in range(len(self.features))]
        while nextspecs:
            featspecs, nextspecs = nextspecs, []
            for featspec in featspecs:
                natclass = tuple(sorted(self.getclass(featspec)))
                if natclass in self.natclasses or not natclass: continue
                self.natclasses[natclass] = featspec
                nextspecs += self.uppertriang(featspec)

    def featspec2str(self, featspec):
        'Generates a string representation of the inputted featspec'
        return(','.join([fTuple[1] + self.features[fTuple[0]] \
                for fTuple in featspec]))

    def featureStr2segList(self, featspecStr):
        featspec = []
        for featStr in featspecStr.split(','):
            try: featspec.append((self.features.index(featStr[1:]), featStr[0]))
            except ValueError: pass
        return(self.getclass(featspec))

    def segList2featureStr(self, segList):
        try: return(self.featspec2str(self.natclasses[tuple(sorted(segList))]))
        except KeyError: raise ValueError, "Non-existent natural class %s" %str(segList)

    def saveclasses(self, outfile):
        'Writes natural classes to a file, one per line, segs space-separated.'
        with open(outfile, 'w') as fout:
            for natclass in self.natclasses:
                print >> fout, \
                    self.featspec2str(self.natclasses[natclass]) + \
                            '\t' + ' '.join(natclass)

    def loadclasses(self, infile):
        """Loads natural classes. Expecting each class on its own line,
        with segs sorted and space-separated."""
        with open(infile) as fin:
            for line in fin:
                self.natclasses[tuple(line.split())] = 1

    def getclass(self, featspec):
        'Return the segs that match a featural specification.'
        cur = self.segments
        for item in featspec: cur = self.intersect(cur, \
                self.featdict.get((self.features[item[0]],item[1]),[]))
        return(sorted(cur))
    
    def intersect(self, dict1, dict2):
        'Get keys that are in both dict1 and dict2'
        intersection = {}
        for key in dict1:
            if key in dict2: intersection[key] = 1
        return(intersection)

    def segclasses(self, seg):
        'Get all natural classes to which seg belongs'
        classes = {}
        for natclass in self.natclasses:
            if seg in natclass: classes[natclass] = 1
        return(classes)
    
    def getNatClass2FeatureStrDict(self):
        return(dict([(segTuple,self.featspec2str(self.natclasses[segTuple])) \
                for segTuple in self.natclasses]))
        
    def getFeatureStr2NatClassDict(self):
        return(dict([(self.featspec2str(self.natclasses[segTuple]),segTuple) \
                for segTuple in self.natclasses]))
    
    def REinterpret(self, featREstr):
        ''' pretty sure this function doesn't belong here '''
        featRE = re.compile('\[[^\]]*\]')
        features = featRE.finditer(featREstr)
        lastChar, outBuf = 0, []
        for match in features:
            ## first, add all regular text since last match point
            outBuf.append(featREstr[lastChar:match.start()])
            ## next, calculate the segments for the feature string
            segList = self.featureStr2segList(match.group()[1:-1])
            ## plug those puppies in 'in place of' the feature string
            outBuf.append('('+'|'.join(segList)+')')
            ## and advance the index from the old string
            lastChar = match.end()
        if lastChar < len(featREstr): outBuf.append(featREstr[lastChar:])
        return(''.join(outBuf))
