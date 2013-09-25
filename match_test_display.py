
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
    
    DEFAULT_FILENAME = 'checkmatch.dat'
    
    parser = argparse.ArgumentParser()
    parser.add_argument( '--datafile', default=DEFAULT_FILENAME )
    
    ARGS = parser.parse_args()
    data_file = open( ARGS.datafile, 'r' )
    data = pickle.load( data_file )
    data_file.close()
    
    
    enroute_predict = data['enroute_predict']
    enroute_compute = data['enroute_compute']
    balance_predict = data['balance_predict']
    balance_compute = data['balance_compute']

    # wtf is all this about??
    for stuff in [ enroute_predict, enroute_compute, balance_predict, balance_compute ] :
        stuff[:] = [ float(repr(x)) for x in stuff ]
        
    plt.figure()
    plt.subplot(1,2,1)
    plt.scatter( enroute_predict, enroute_compute )
    xmin, xmax, ymin, ymax = plt.axis()
    x = np.linspace(xmin,xmax,1000)
    plt.plot(x,x,'--')
    plt.gca().set_aspect('equal')
    plt.title( 'Average Conveyance Time' )
    plt.xlabel('Predicted')
    plt.ylabel('Observed')
    
    plt.subplot(1,2,2)
    plt.scatter( balance_predict, balance_compute )
    xmin, xmax, ymin, ymax = plt.axis()
    x = np.linspace(xmin,xmax,1000)
    plt.plot(x,x,'--')
    plt.gca().set_aspect('equal')
    plt.title( 'Average Empty Time' )
    plt.xlabel('Predicted')
    plt.ylabel('Observed')
    plt.show()


    
    

