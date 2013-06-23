
import itertools

import networkx as nx
import cvxpy

import numpy as np

import roadgeometry.roadmap_basic as roadmap_basic
import nxopt.nxopt as nxopt    # deprecate!


""" utilities """

def roadnet_APSP( roadnet, length='length' ) :
    digraph = nx.MultiDiGraph()
    for i,j,key,data in roadnet.edges_iter( keys=True, data=True ) :
        edgelen = data.get( length, 1 )
        digraph.add_edge( i,j,key, weight=edgelen )
        if not data.get( 'oneway', False ) :
            digraph.add_edge( j,i,key, weight=edgelen )
    return nx.all_pairs_dijkstra_path_length( digraph )




""" exported functionality """

def EarthMoversDistance( measurenx, length='length', weight1='weight1', weight2='weight2', DELTA=None ) :
    digraph = measurenx_to_flownx( measurenx, length, weight1, weight2 )
    return nxopt.mincost_maxflow( digraph, cost='cost', DELTA=DELTA )


def measurenx_to_flownx( roadnet, length='length', weight1='weight1', weight2='weight2' ) :
    """
    input: a road network, with weights on its elements
    output:
    returns a graph summarizing the network optimization problem instance;
    roadnets are multi-digraph, where edge 'keys' are assumed to be unique,
    i.e., road names; and should be different from node labels too;
    """
    
    # for convenience
    #ROADS = [ key for u,v,key in roadnet.edges_iter( keys=True ) ]
    digraph = nx.DiGraph()
    digraph.add_node('s')
    digraph.add_node('t')
    
    """ insert supply and demand of roads """
    for u,v, road, data in roadnet.edges_iter( keys=True, data=True ) :
        roadlen = data.get( length, 1. )
        assert roadlen >= 0.
        
        oneway = data.get( 'oneway', False )
        
        surplus = data.get( weight1, 0. ) - data.get( weight2, 0. )
        deficit = -surplus
        
        # supply layer
        if surplus > 0. :
            w = roadlen / surplus
            id = ( road, 'supply' )
            digraph.add_edge( 's', id, flow=cvxpy.variable(), minflow=0., maxflow=surplus )
            
            if oneway : ends = [ v ]
            else : ends = [ u, v ]
            for node in ends :
                flowvar = cvxpy.variable()
                cost = .5 * w * cvxpy.square( flowvar )
                digraph.add_edge( id, node, flow=flowvar, minflow=0., cost=cost )
                
        # demand layers
        if deficit > 0. :
            w = roadlen / deficit
            id = ( road, 'demand' )
            digraph.add_edge( id, 't', flow=cvxpy.variable(), minflow=0., maxflow=deficit )
            
            if oneway : ends = [ u ]
            else : ends = [ u, v ]
            for node in ends :
                flowvar = cvxpy.variable()
                cost = .5 * w * cvxpy.square( flowvar )
                digraph.add_edge( node, id, flow=flowvar, minflow=0., cost=cost )
                
                
    """ insert supply and demand of nodes """
    for u, data in roadnet.nodes_iter( data=True ) :
        surplus = data.get( weight1, 0. ) - data.get( weight2, 0. )
        deficit = -surplus
        
        # supply layer
        if surplus > 0. :
            digraph.add_edge( 's', u, flow=cvxpy.variable(), minflow=0., maxflow=surplus )
        if deficit > 0. :
            digraph.add_edge( u, 't', flow=cvxpy.variable(), minflow=0., maxflow=deficit )
            
            
            
    """ setup the network flow structure """
    conns = roadmap_basic.connectivity_graph( roadnet )
    for u, v, data in conns.edges_iter( data=True ) :
        weight = data.get( length, 1 )
        flowvar = cvxpy.variable()
        cost = weight * flowvar
        digraph.add_edge( u, v, weight=weight, flow=flowvar, minflow=0., cost=cost )
    
    nxopt.attach_flownx_constraints( digraph )
    return digraph      # a flownx
    
    
    
    
if __name__ == '__main__' :
    import matplotlib.pyplot as plt
    plt.close('all')
    
    
    roadnet = nx.MultiDiGraph()
    
    if False :
        g.add_edge( 0, 1, 'road1', length=2., weight1=0.+OFFSET, weight2=.5+OFFSET)
        g.add_edge( 1, 2, 'road2', length=1., weight1=.4)
        g.add_edge( 2, 3, 'road3', length=3., weight2=.1)
        g.add_edge( 3, 0, 'road4', length=5., weight1=.4)
        
    elif False :
        OFFSET = 10.
        roadnet.add_node( 0, weight1=.7 )
        roadnet.add_edge( 0,1, 'road1', length=1., weight1=0.+OFFSET, weight2=.5+OFFSET )
        roadnet.add_edge( 0,2, 'road2', length=10., weight2=.6 )
        
    else :
        roadnet.add_edge( 0, 1, 'N', length=1., weight2=3. )
        roadnet.add_edge( 1, 2, 'E', length=1., weight1=1000., oneway=False )
        roadnet.add_edge( 2, 3, 'S', length=1., weight1=1. )
        roadnet.add_edge( 3, 0, 'W', length=1., weight2=1. )
        #roadnet.add_node( 0, weight1=.7 )
        #roadnet.add_edge( 0, 1 )
        
        
    #g.add_edge( 1, 3, 'road3 ' )
    digraph = measurenx_to_flownx( roadnet )
    if True :
        maxflow = nxopt.maxflow( digraph )
        #total_flow, total_cost, constr = flownx_to_opt( digraph )
        res = nxopt.mincost_maxflow( digraph )
        
        flows = [ ( (u,v), data['flow'].value ) for u,v,data in digraph.edges_iter( data=True ) ]
        
        print 'max flow is %f' % maxflow
        print 'min cost max flow is %f' % res
        
        
        
    
    
