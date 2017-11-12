import numpy as np
import graphviz as gv

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

intersection = lambda s1, s2: (element for element in s1 if element in s2)
complement = lambda s, U: (element for element in U if element not in s)

class poset(dict):

    def __init__(self, infile = None):
        self.order = None
        self.named_classes = None
        self.subset_matrix = None
        self.intersect_matrix = None
        self.digraph = None
        
        if infile: self.read_classes_from_file(infile)

    def read_classes_from_file(self, infile):
        '''
        Expecting format:
        each class is listed on its own line
        optional: name field, followed by a tab character
        class: a space-separated sequence of segments
        '''

        with open(infile) as fin:
            firstline = fin.readline().rstrip().split('\t')
            self.named_classes = (len(firstline) == 2)
            
            seg_list = tuple(sorted(firstline[-1].split()))
            name = 1
            if self.named_classes: name = firstline[0]
            self[seg_list] = name
            
            for line in fin:
                parse = line.rstrip().split('\t')
                seg_list = tuple(sorted(parse[-1].split()))
                if self.named_classes: name = parse[0]
                else: name += 1
                self[seg_list] = name

        ## establish a canonical order for node indices to index
        self.order = self.keys()
        self.order.sort(key=len, reverse=True)

    def write_classes_to_file(self, outfile):
        with open(outfile, 'w') as fout:
            for nat_class in self.order:
                fout.write('{0}\t{1}\n'.format(self[nat_class], ' '.join(nat_class)))

    def display_classes(self):
        for nat_class in self.order:
            print '{0:20}\t{1}'.format(self[nat_class], nat_class)

    def get_subset_matrix(self):
        N = len(self)
        self.subset_matrix = np.zeros((N,N), dtype='bool')
        for iClass, sup_class in enumerate(self.order):
            for jClass, sub_class in enumerate(self.order):
                # ignore improper subsethood
                if iClass == jClass: continue
                self.subset_matrix[iClass, jClass] = is_subset(sub_class, sup_class)
        return(self.subset_matrix)

    def get_parents(self):
        'Assumes subset_matrix is up to date'
        if self.subset_matrix == None: self.get_subset_matrix()
        return(self.subset_matrix * ~ np.dot(self.subset_matrix, self.subset_matrix))
        # M[i,j] = 1 <==> j is a subset of i
        # M^2[i,j] ==> j is a subset of some k which is a subset of i
        # (M * ~M^2) ==> j is a subset of i, and there is no k such that
        #                j is a subset of k and k is a subset of i
    
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
            nodetext = '{' + ', '.join(nat_class) + '}'
            self.graph.node(nodename, label=nodetext)
        
        ## add an edge for every pair (i,j) where i is a parent of j
        parent_matrix = self.get_parents()
        for coords, val in np.ndenumerate(parent_matrix):
            if val: self.graph.edge(str(coords[0]), str(coords[1]))

        return(self.graph)
                
    
    def intersectional_closure(self):
        pass

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
