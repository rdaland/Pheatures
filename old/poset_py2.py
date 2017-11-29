import numpy as np
import graphviz as gv
from collections import deque

########################################################
##           some elementary set functions            ##
########################################################

def is_subset(s, S):
    '''
    Returns True if s is a subset of S (including when s==S)
    Assumes s and S are tuples.
    '''
    for element in s:
        if element not in S: return False
    return True

intersect = lambda s1, s2: tuple(element for element in s1 if element in s2)
complement = lambda s, U: tuple(element for element in U if element not in s)

## TODO: refactor so name of class is a 'pretty' form of members
##    unless otherwise specified;

## ALSO need to redo so subset relationship gets stored as a dict
## and presumably intersect will be as well

class poset(dict):

    def __init__(self, infile = None):
        self.order = None
        self.subsets = {}
        self.daughters = {}
        self.intersections = {}
        self.digraph = None
        
        if infile: self.read_classes_from_file(infile)

    def read_classes_from_file(self, infile):
        with open(infile) as fin:
            self.names = {}
            for iLine, line in enumerate(fin):
                parse = line.rstrip().split('\t')
                seg_list = tuple(sorted(parse[-1].split()))
                name = parse[0]
                self[seg_list] = iLine
        self.recalculate()

    def recalculate(self):
        self.canonicalize()
        self.get_subsets()
        
    def canonicalize(self):
        'establish a canonical order, by decreasing length'
        self.order = self.keys()
        self.order.sort(key=len, reverse=True)
        for iClass, nat_class in enumerate(self.order):
            self[nat_class] = iClass

    def get_subsets(self):
        N = len(self)
        try: assert len(self.order)==N
        except AssertionError:
            raise IndexError, 'Length of poset does not match length of indexed sets'
        
        self.subsets = {(jClass, iClass): True \
                            for iClass in range(N) \
                            for jClass in range(N) \
                            if iClass != jClass and \
                            is_subset(self.order[jClass], self.order[iClass])}
        return(self.subsets)
        
    def write_classes_to_file(self, outfile):
        with open(outfile, 'w') as fout:
            for nat_class in self.order:
                fout.write('{0}\t{1}\n'.format(self[nat_class], ' '.join(nat_class)))

    def display_classes(self):
        for nat_class in self.order:
            print('{0:20}\t{1}'.format(self[nat_class], nat_class))

    def get_daughters(self):
        N = len(self.order)
        
        ## convert subset relationship (j,i) --> j is a subset of i
        ## into matrix form M[i,j] = T <==> j SUBSET i
        mSub = np.zeros((N,N), dtype='bool')
        for jClass, iClass in self.subsets:
            mSub[iClass,jClass] = True
        
        ## calculate parent/daughter relationship
        # M[i,j] = 1 <==> j is a subset of i
        # M^2[i,j] ==> j is a subset of some k which is a subset of i
        # (M * ~M^2) ==> j is a subset of i, and there is no k such that
        #                j is a subset of k and k is a subset of i
        mPar = mSub * ~np.dot(mSub,mSub)
        self.daughters = {(jClass, iClass): True \
                             for iClass in range(N) \
                             for jClass in range(N) \
                             if mPar[iClass,jClass]}
        return(self.daughters)
    
    def get_graph(self, graphViz_file = 'poset_graph.gv', title=None):
        ## initialize an empty directed graph
        ## NOTE: still need to pass in some params here
        ## such as letting user save this to .png or sth
        self.graph = gv.Digraph(comment=str(title), \
                                filename = graphViz_file, \
                                format = 'ps')

        ## make a node for every class
        for iClass, nat_class in enumerate(self.order):
            nodename = str(iClass)
            nodetext = ', '.join(nat_class)
            self.graph.node(nodename, label=nodetext)
        
        ## add an edge for every pair (i,j) where j is a daughter of i
        for jClass, iClass in self.get_daughters():
            self.graph.edge(str(iClass), str(jClass))

        return(self.graph)
                
    
    def intersectional_closure(self):
        '''
        Returns a new poset object C with the following properties:
            1. if nat_class in self, nat_class in C
            2. if there exist indices (a1, a2, .., an) such that
                   x = intersect(self[a1], self[a2], ..., self[an])
               then x is in C
        
        The calculation is done using a modified version of Dijkstra's
        shortest paths algorithm. We start with a queue of *pairs* of
        classes, and reduce the total number of cases that must be
        considered by capitalizing on two facts
            1. x ^ y = x ^ y (so only one order need be considered)
            2. if x < y, then x ^ y = y (< is subset, ^ is intersection)
        Together, these facts make it possible to skip the intersection
        operation for over half of all cases.
        '''
        ## initialize new poset
        print('#### intersectional_closure(): ENTERED DEBUG ####')
        C = poset()
        for nat_class in self:
            C[nat_class]=1
        C.canonicalize()
        C.get_subsets()
        print '#### intersectional_closure(): CREATED DEEP COPY OF POSET ####'
        C.display_classes()
        print
        print '#### intersectional_closure(): SUBSET MATRIX ####'
        for jClass, iClass in C.subsets:
            print 'class {0} ({1}) is a subset of class {2} ({3})'.format( \
                      jClass, ' '.join(self.order[jClass]), \
                      iClass, ' '.join(self.order[iClass]))
        print
        ## initialize deque
        ## canonicalized order: i > j  <==> i cannot be a subset of j
        ## thus only consider pairs where j < i
        N = len(C)
        classPairDeque = deque([(jClass, iClass) \
                                for iClass in range(N) \
                                for jClass in range(iClass+1,N)])

        print '#### intersectional_closure(): CREATED classPairDeque ####'
        print classPairDeque
        print
        print '#### intersectional_closure(): ENTERING MAIN LOOP ####'
        ## main loop
        ## efficiently creates all intersections of existing sets
        ## and fills C.intersections, a data structure which keeps track
        ## of which triples obey the intersection relation
        while classPairDeque:
            jClass, iClass = classPairDeque.pop()
            print '\tpopped\t{0}, {1}'.format(jClass, iClass)
            print '\t\tclass {0}:\t{1}'.format(jClass, ' '.join(C.order[jClass]))
            print '\t\tclass {0}:\t{1}'.format(iClass, ' '.join(C.order[iClass]))

            if (jClass, iClass) in C.subsets:
                print '\tclass {0} is a subset of class class {1}, ignoring'.format(jClass, iClass)
                continue

            intersection = intersect(C.order[jClass], C.order[iClass])
            print '\tintersection\t{0}'.format(' '.join(intersection))

            ## efficiency: stop when the intersection is empty (often)
            if len(intersection) == 0:
                print '\t\tempty intersection; ignoring'
                continue

            ## if the intersection is also/already in C
            ## just add that to the dictionary of intersections
            if C.has_key(intersection):
                print '\t\texisting class {0}; adding to intersections and ignoring'.format(C[intersection])
                C.intersections[(iClass, jClass)] = C[intersection]
                C.intersections[(jClass, iClass)] = C[intersection]
                continue
            
            ## if we haven't exited yet, this is a new class!
            ## add it to C and C.order
            ## do bookkeeping on C.subset
            ## and add new pairs to classPairQueue
            N = len(C)
            C[intersection] = N
            C.order.append(intersection)
            print '\t\tnew class found: added class {0} to C and C.order'.format(N)
            print '\t\tadding new class pairs to classPairDeque, and updating C.subsets'
            for iClass in range(N):
                if is_subset(intersection, C.order[iClass]): C.subsets[(N,iClass)] = True
                else: classPairDeque.appendleft((N,iClass))
                
                if is_subset(C.order[iClass], intersection): C.subsets[(iClass,N)] = True
                else: classPairDeque.appendleft((iClass,N))

            ## note that this destroys the guarantee that C's classes are
            ## in the canonical order (of nonincreasing size)
        print '#### intersectional_closure(): EXITED MAIN LOOP ####'
        return(C)
        
if __name__ == "__main__":

    ## defining the poset
    N = poset()
    N.update({('T', 'D', 'V', 'R', 'N'): 'SIGMA', \
              ('V', 'R' ,'N'):           '+son', \
              ('T', 'D'):                '-son', \
              ('V',):                    '+syl', \
              ('R', 'N'):                '+son,-syl', \
              ('R',):                    '+son,-syl,+approx', \
              ('N',):                    '+son,-syl,-approx', \
              ('T',):                    '-vcd', \
              ('D',):                    '-son,+vcd', \
              ('D', 'V', 'R', 'N'):      '+vcd'})
    N.order = sorted(N.keys(), key=len, reverse=True)
    N.write_classes_to_file('TDVRN.txt')

    N = poset('TDVRN.txt')
    print 'Enumerated order:'
    for iClass, nat_class in enumerate(N.order):
        print '\t{0}:\t{1:20}\t{2}'.format(iClass, N[nat_class], ' '.join(nat_class))
    print

    print 'Getting graph and rendering.'
    g = N.get_graph('TDVRN.gv')
    print
    print 'The plot should appear as TDVRN.gv.ps; if it does not,'
    print '  then please execute the following command-line call:'
    print '\tdot -Tps -O TDVRN.gv'
    g.render()
    print
    
    print 'Debugging intersectional closure'
    N2 = N.intersectional_closure()
    print
    print 'Graphing intersectional closure'
    g2 = N2.get_graph('TDVRN_2.gv')
    g2.render()
    
    N3 = poset('vowelHarmony.txt')
    g3 = N3.get_graph('vowelHarmony.gv')
    g3.render()
    
    N4 = N3.intersectional_closure()
    g4 = N4.get_graph('vowelHarmony_2.gv')
    g4.render()
    
    
