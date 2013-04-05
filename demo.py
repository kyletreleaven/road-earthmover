
import time
import random

import numpy as np
from scipy.spatial import Delaunay as Tri

import networkx as nx

import roademd, nxopt
import roademd_approx
import roademd_approx2


"""
Trial data:
    roadnet
    approximation algorithm, resolution (epsilon)
    
Performance metrics:
    size of instance
    runtime of instance
    closeness to the Earth mover's distance
"""




def stopwatch( func, *args, **kwargs ) :
    """ returns the result and duration of a function call """
    start = time.time()
    result = func( *args, **kwargs )
    stop = time.time()
    duration = stop - start
    return result, duration




if __name__ == '__main__' :
    import matplotlib.pyplot as plt
    plt.close('all')
    
    roadnet = nx.MultiDiGraph()
    
    if True :
        roadnet.add_edge( 0, 1, 'N', length=1., weight2=1.)
        roadnet.add_edge( 1, 2, 'E', length=1., weight1=2., oneway=False )
        roadnet.add_edge( 2, 3, 'S', length=1., weight1=3.)
        roadnet.add_edge( 3, 0, 'W', length=1., weight2=4.)
        
        epsilon2 = np.logspace( np.log10(.5), np.log10(1./20), 10 )
        epsilon1 = np.logspace( np.log10(.5), np.log10(1./10), 10 )
        
        
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
        
        
        
        
    """ EXPERIMENT """
    
    """ first, the emd """
    tick = time.time()
    emd_digraph = roademd.measurenx_to_flownx( roadnet )
    emd = nxopt.mincost_maxflow( emd_digraph )
    tock = time.time()
    #
    nodes = len( emd_digraph.nodes() )
    edges = len( emd_digraph.edges() )
    runtime = tock - tick
    
    flows = [ ( (u,v), data['flow'].value ) for u,v,data in emd_digraph.edges_iter( data=True ) if data['flow'].value > .0001 ]

    """ now approx2 """
    N2 = len( epsilon2 )
    
    nodes2 = np.zeros(N2)
    edges2 = np.zeros(N2)
    runtime2 = np.zeros(N2)
    lowerbound2 = np.zeros(N2)
    upperbound2 = np.zeros(N2)
    
    for k, eps in enumerate( epsilon2 ) :
        print 'approx[1]', eps
        tick = time.time()
        approx_digraph = roademd_approx2.measurenx_to_approxnx( roadnet, eps )
        lower = nxopt.mincost_maxflow( approx_digraph, 'cost_lo' )
        tock = time.time()      # only need to time one of them
        #
        upper = nxopt.mincost_maxflow( approx_digraph, 'cost_hi' )
        
        nodes2[k] = len( approx_digraph.nodes() )
        edges2[k] = len( approx_digraph.edges() )
        runtime2[k] = tock - tick
        lowerbound2[k] = lower
        upperbound2[k] = upper
    
    
    """ now approx """
    N1 = len( epsilon1 )
    
    nodes1 = np.zeros(N1)
    edges1 = np.zeros(N1)
    runtime1 = np.zeros(N1)
    lowerbound1 = np.zeros(N1)
    upperbound1 = np.zeros(N1)
        
    if True :
        for k, eps in enumerate( epsilon1 ) :
            print 'approx2', eps
            tick = time.time()
            approx_digraph = roademd_approx.measurenx_to_approxnx( roadnet, eps )
            lower = nxopt.mincost_maxflow( approx_digraph, 'cost_lo' )
            tock = time.time()      # only need to time one of them
            #
            upper = nxopt.mincost_maxflow( approx_digraph, 'cost_hi' )
            
            nodes1[k] = len( approx_digraph.nodes() )
            edges1[k] = len( approx_digraph.edges() )
            runtime1[k] = tock - tick
            lowerbound1[k] = lower
            upperbound1[k] = upper
        
        
    """ show nodes, edges, runtime of loglog plot """
    mineps = min( min(epsilon1), min(epsilon2) )
    maxeps = max( max(epsilon1), max(epsilon2) )
    interp = np.linspace(mineps,maxeps, 10 )
    #
    nodesline = [ nodes for e in interp ]
    edgesline = [ edges for e in interp ]
    timeline = [ runtime for e in interp ]
    truth = [ emd for e in interp ]
    
    plt.figure()
    plt.loglog( interp, nodesline, epsilon1, nodes1, epsilon2, nodes2, c='b' )
    plt.loglog( interp, edgesline, epsilon1, edges1, epsilon2, edges2, c='g' )
    plt.loglog( interp, timeline, epsilon1, runtime1, epsilon2, runtime2, c='k' )
    
    """ show closeness of approximation and convergence """
    plt.figure()
    plt.semilogx( interp, truth, 'k--' )
    plt.semilogx( epsilon1, lowerbound1, epsilon2, lowerbound2, c='b' )
    plt.semilogx( epsilon1, upperbound1, epsilon2, upperbound2, c='r' )
    
    
    