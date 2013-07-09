
# built-in
import time
import random

# scientific common
import numpy as np
from scipy.spatial import Delaunay as Tri
import networkx as nx

import matplotlib as mpl
mpl.rcParams['ps.useafm'] = True
mpl.rcParams['pdf.use14corefonts'] = True
mpl.rcParams['text.usetex'] = True

font = {'family' : 'normal',
        'weight' : 'bold',
        'size'   : 22 }
mpl.rc('font', **font)       # oh please, work!


# dev
import mass_transport
#
nxopt = mass_transport.nxopt.nxopt
flownets = mass_transport.nxopt.max_flow_min_cost

from mass_transport import roademd, roademd_approx, roademd_approx2

#import roademd
#import roademd_approx
#import roademd_approx2
#import mass_transport.nxopt.nxopt as nxopt
#import mass_transport.nxopt.max_flow_min_cost as flownets

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



def getcomfoy( sizes ) :
    pass


def publishable( fig) :
    fsize = 25
    fweight = 'bold'
    
    
    























if __name__ == '__main__' :
    import matplotlib.pyplot as plt
    plt.close('all')
    
    roadnet = nx.MultiDiGraph()
    
    if True :
        roadnet.add_edge( 0, 1, 'N', length=1., weight2=1./5)
        roadnet.add_edge( 1, 2, 'E', length=1., weight1=2./5, oneway=False )
        roadnet.add_edge( 2, 3, 'S', length=1., weight1=3./5)
        roadnet.add_edge( 3, 0, 'W', length=1., weight2=4./5)
        
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
    if False :      # fast
        epsilon2 = np.logspace( np.log10(.5), np.log10(1./10), 10 )
        epsilon1 = np.logspace( np.log10(.5), np.log10(1./5), 10 )
    else :          # slow
        epsilon2 = np.logspace( np.log10(.5), np.log10(1./45), 15 )
        epsilon1 = np.logspace( np.log10(.5), np.log10(1./25), 15 )

    """ first, the emd """
    tick = time.time()
    emd_digraph, emd_costgraph = roademd.obtainWassersteinProblem( roadnet )
    flownets.max_flow_min_cost( emd_digraph, emd_costgraph )
    emd = flownets.totalcost( emd_costgraph ).value
    #emd = roademd.EarthMoversDistance( roadnet )
    #emd_digraph = roademd.measurenx_to_flownx( roadnet )
    #emd = nxopt.mincost_maxflow( emd_digraph )
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
    #XLIM = [ 1.1 * mineps, 1.1 * maxeps ]
    #
    nodesline = [ nodes for e in interp ]
    edgesline = [ edges for e in interp ]
    timeline = [ runtime for e in interp ]
    truth = [ emd for e in interp ]
    
    
    """ do some plotting """
    
    """ plotting convenience function """
    import matplotlib.ticker
    
    def fix_axis( ax ) :
        #ax.set_xlim( XLIM )
        ax.invert_xaxis()
        #ax.tick_params( axis='x', which='both', labelbottom='on' )    # I spent way too long trying to get this shitty function to work!
        ax.xaxis.set_major_formatter( matplotlib.ticker.ScalarFormatter() )
        #ax.xaxis.set_minor_formatter( matplotlib.ticker.ScalarFormatter() )
        ax.yaxis.set_major_formatter( matplotlib.ticker.ScalarFormatter() )
        #ax.yaxis.set_minor_formatter( matplotlib.ticker.ScalarFormatter() )
        #ax.relim()
        #ax.autoscale_view()
    
    # resource cost plots
    # nodes
    plt.figure()
    plt.loglog( interp, nodesline, label='Exact', c='k' )
    plt.loglog( epsilon1, nodes1, label='APPROX', c='b', marker='o' )
    plt.loglog( epsilon2, nodes2, label='PATH', c='g', marker='^' )
    ax = plt.gca()
    fix_axis( ax )
    ax.set_xlabel('Fineness of discretization ($\epsilon$)')
    ax.set_ylabel('Number of VERTICES generated')
    ax.legend( fontsize=18 )
    #plt.savefig( 'nodes-generated.pdf' )
    
    # edges
    plt.figure()
    plt.loglog( interp, edgesline, label='Exact', c='k' )
    plt.loglog( epsilon1, edges1, label='APPROX', c='b', marker='o' )
    plt.loglog( epsilon2, edges2, label='PATH', c='g', marker='^' )
    ax = plt.gca()
    fix_axis( ax )
    ax.set_xlabel('Fineness of discretization ($\epsilon$)')
    ax.set_ylabel('Number of EDGES generated')
    ax.legend( fontsize=18 )
    #plt.savefig( 'edges-generated.pdf' )
    
    # runtime
    plt.figure()
    plt.loglog( interp, timeline, label='Exact', c='k' )
    plt.loglog( epsilon1, runtime1, label='APPROX', c='b', marker='o' )
    plt.loglog( epsilon2, runtime2, label='PATH', c='g', marker='^' )
    ax = plt.gca()
    fix_axis( ax )
    ax.set_xlabel('Fineness of discretization ($\epsilon$)')
    ax.set_ylabel('Runtime (sec)')
    ax.legend( fontsize=18 )
    #plt.savefig( 'runtime.pdf' )
    
    
    """ show closeness of approximation and convergence """
    plt.figure()
    plt.semilogx( interp, truth, label='Exact', c='k' )
    plt.semilogx( epsilon1, lowerbound1, c='b', marker='o', label='APPROX' )
    plt.semilogx( epsilon1, upperbound1, c='b', marker='o' )
    plt.semilogx( epsilon2, lowerbound2, c='g', marker='^', label='PATH' )
    plt.semilogx( epsilon2, upperbound2, c='g', marker='^' )
    ax = plt.gca()
    fix_axis( ax )
    ax.set_xlabel('Fineness of discretization ($\epsilon$)')
    ax.set_ylabel('Closeness of approximation')
    ax.legend( fontsize=18 )
    #plt.savefig( 'convergence-in-approx.pdf' )
    
    
    