
import itertools

import networkx as nx
import cvxpy

import numpy as np

import roadgeometry.roadmap_basic as roadmap_basic
#import nxopt.nxopt as nxopt    # deprecate!
import nxopt.max_flow_min_cost as flownets 


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
    flowgraph, costgraph = obtainWassersteinProblem( measurenx, length, weight1, weight2 )
    flownets.max_flow_min_cost( flowgraph, costgraph )
    return flownets.totalcost( costgraph ).value


def obtainWassersteinProblem( roadnet, length='length', weight1='weight1', weight2='weight2' ) :
    """
    input: a road network, with weights on its elements
    output:
    returns a graph summarizing the network optimization problem instance;
    roadnets are multi-digraph, where edge 'keys' are assumed to be unique,
    i.e., road names; and should be different from node labels too;
    """
    
    # for convenience
    #ROADS = [ key for u,v,key in roadnet.edges_iter( keys=True ) ]
    class node : pass
    node_s = node() ; node_t = node()
    
    digraph = nx.DiGraph()
    digraph.add_node( node_s )
    digraph.add_node( node_t )
    
    """ insert supply and demand of roads """
    for u,v, road, data in roadnet.edges_iter( keys=True, data=True ) :
        roadlen = data.get( length, 1. )
        assert roadlen >= 0.
        
        oneway = data.get( 'oneway', False )
        
        surplus = data.get( weight1, 0. ) - data.get( weight2, 0. )
        deficit = -surplus
        
        # supply layer
        if surplus > 0. :
            digraph.add_edge( node_s, road, capacity=surplus )
            
            w = roadlen / surplus
            if oneway : ends = [ v ]
            else : ends = [ u, v ]
            for node in ends :
                digraph.add_edge( road, node, decision_weight=w )
                
        # demand layers
        if deficit > 0. :
            digraph.add_edge( road, node_t, capacity=deficit )
            
            w = roadlen / deficit
            if oneway : ends = [ u ]
            else : ends = [ u, v ]
            for node in ends :
                digraph.add_edge( node, road, decision_weight=w )
                
    """ insert supply and demand of nodes """
    for u, data in roadnet.nodes_iter( data=True ) :
        surplus = data.get( weight1, 0. ) - data.get( weight2, 0. )
        deficit = -surplus
        
        # supply layer
        if surplus > 0. :
            digraph.add_edge( node_s, u, capacity=surplus )
        if deficit > 0. :
            digraph.add_edge( u, node_t, capacity=deficit )
            
    """ setup the network flow structure """
    conns = roadmap_basic.connectivity_graph( roadnet, length_in=length )
    for u, v, data in conns.edges_iter( data=True ) :
        w = data.get( 'length', 1 )
        digraph.add_edge( u, v, weight=w )
        
    flowgraph = flownets.obtainFlowNetwork( digraph, node_s, node_t )
    costgraph = flownets.obtainWeightedCosts( flowgraph, digraph )        # cute trick
    
    #return flowgraph, costgraph
    
    for u,v, data in digraph.edges_iter( data=True ) :
        dec_weight = data.get( 'decision_weight', None )
        if dec_weight is None : continue
        #
        fdata = flowgraph.get_edge_data( u, v, 0 )   # key=0, because we have tightly controlled this construction
        flow = fdata.get( 'flow' )
        
        cost = .5 * dec_weight * cvxpy.square( flow )
        #print dec_weight, flow, cost
        
        cdata = costgraph.get_edge_data( u, v, 0 )
        #print cdata
        cdata['cost'] = cost
    
    return flowgraph, costgraph




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
        roadnet.add_edge( 0,2, 'road2', length=10., weight2=.6 )
        
    else :
        roadnet.add_edge( 0, 1, 'N', length=1., weight2=3. )
        roadnet.add_edge( 1, 2, 'E', length=1., weight1=1000., oneway=False )
        roadnet.add_edge( 2, 3, 'S', length=1., weight1=1. )
        roadnet.add_edge( 3, 0, 'W', length=1., weight2=1. )
        #roadnet.add_node( 0, weight1=.7 )
        #roadnet.add_edge( 0, 1 )
        
        
    #g.add_edge( 1, 3, 'road3 ' )
    #print 'max flow is %f' % maxflow
    #print 'min cost max flow is %f' % res
    fgraph, cgraph = obtainWassersteinProblem( roadnet)
    
    flownets.max_flow_min_cost( fgraph, cgraph )
        
        
    
    
