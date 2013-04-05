
import time
import random

import numpy as np
from scipy.spatial import Delaunay as Tri

import networkx as nx

import roademd
import roademd_approx




if __name__ == '__main__' :
    import matplotlib.pyplot as plt
    plt.close('all')
    
    roadnet = nx.MultiDiGraph()
    
    if False :
        roadnet.add_edge( 0, 1, 'road1', length=2., weight1=0.+OFFSET, weight2=.5+OFFSET)
        roadnet.add_edge( 1, 2, 'road2', length=1., weight1=.4)
        roadnet.add_edge( 2, 3, 'road3', length=3., weight2=.1)
        roadnet.add_edge( 3, 0, 'road4', length=5., weight1=.4)
        
    elif False :
        OFFSET = 10.
        roadnet.add_node( 0, weight1=.7 )
        roadnet.add_edge( 0,1, 'road1', length=1., weight1=0.+OFFSET, weight2=.5+OFFSET )
        roadnet.add_edge( 0,2, 'road2', length=2., weight2=.6 )
        
    else :
        def random_road() :
            length = np.random.exponential()
            surplus = np.random.normal()
            if surplus > 0. :
                weight1 = surplus
                weight2 = 0.
            else :
                weight1 = 0.
                weight2 = -surplus
            return length, weight1, weight2
        
        roadnet = nx.MultiDiGraph()
        for k, (i,j) in enumerate([ (0,1), (0,1), (0,2), (1,2) ]) : 
            road = 'road%d' % k
            length, weight1, weight2 = random_road()
            roadnet.add_edge( i,j,road, length=length, weight1=weight1, weight2=weight2 )
        
        
        
        
    """ trials """
    N = 5
    #maxN = 150
    #N = 5
    epsilon = np.logspace( np.log10(.5), np.log10(1./150), N )
    results_lo = np.zeros(N)
    results_hi = np.zeros(N)
    
    #g.add_edge( 1, 3, 'road3 ' )
    res = roademd.EarthMoversDistance( roadnet )
    results = [ res for i in range(N) ]
    
    def display( results, results_lo, results_hi ) :
        plt.semilogx( epsilon, results )
        plt.semilogx( epsilon, results_lo )
        plt.semilogx( epsilon, results_hi )
        plt.show()
    
    
    for k, eps in enumerate( epsilon ) :
        digraph = roademd_approx.measureNW_to_approxNW( roadnet, eps )
        results_lo[k] = roademd.mincost_maxflow( digraph, 'cost_lo' )
        results_hi[k] = roademd.mincost_maxflow( digraph, 'cost_hi' )


        
    #plt.plot( range(N), results )
    #plt.plot( range(N), results_lo )
    #plt.plot( range(N), results_hi )
    
    #total_flow, cost, const = optNW_statistics( digraph )
    #res = solve_optNW( digraph )
    #max_flow = total_flow.value
    
    #print 'max flow is %f' % max_flow
    #print 'min cost max flow is %f' % res
    
