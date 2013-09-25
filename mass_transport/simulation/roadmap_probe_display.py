
# built-in
import itertools
import random

# science common
import numpy as np
import scipy as sp
import networkx as nx


if __name__ == '__main__' :
    # plotting
    import matplotlib as mpl
    mpl.rcParams['ps.useafm'] = True
    mpl.rcParams['pdf.use14corefonts'] = True
    mpl.rcParams['text.usetex'] = True
    
    font = {'family' : 'normal',
            'weight' : 'bold',
            'size'   : 22 }
    mpl.rc('font', **font)       # oh please, work!
    
    import matplotlib.pyplot as plt
    plt.close('all')
    
    import pickle
    import argparse
    
    DEFAULT_FILENAME = 'complexity_experiment.dat'
    
    parser = argparse.ArgumentParser()
    parser.add_argument( '--datafile', default=DEFAULT_FILENAME )
    
    ARGS = parser.parse_args()
    data_file = open( ARGS.datafile, 'r' )
    data = pickle.load( data_file )
    data_file.close()
    
    complexity_computed = data['complexity_computed']
    complexity_estimated = data['complexity_estimated']
    
    # wtf is all this about??
    complexity_computed = [ float(repr(x)) for x in complexity_computed ]
    complexity_estimated = [ float(repr(x)) for x in complexity_estimated ]
    
    xmax = max( complexity_computed )
    X = np.linspace(0,xmax,100)
    Y = np.linspace(0,xmax,100)
    
    #plt.scatter( complexity_computed, complexity_estimated, marker='x' )
    plt.scatter( complexity_computed, complexity_estimated )
    plt.plot( X, Y, '--', c='k' )
    plt.xlabel( 'Average Service Time Predicted' )       # miles/demand
    plt.ylabel( 'Average Service Time Observed' )
    plt.show()
    
    
    
    
    
    

