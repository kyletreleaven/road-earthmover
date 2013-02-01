

import itertools

import numpy as np
import networkx as nx

import cvxpy

import matplotlib.pyplot as plt
plt.close('all')


DELTA = .0001       # there are numerical issues if DELTA == 0.

def construct_emd_graph( roadnet, length='length', weight1='weight1', weight2='weight2' ) :
    """
    returns a graph summarizing the problem instance, and the distance itself;
    roadnets are multi-digraph, where edge 'keys' are assumed to be unique,
    i.e., road names; and should be different from node labels too;
    """
    
    # for convenience
    ROADS = [ key for u,v,key in roadnet.edges_iter( keys=True ) ]
    
    """ setup the road flow structure """
    rgraph = nx.DiGraph()       # "road graph"
    #road_graph = nx.DiGraph()
    for u,v, key, data in roadnet.edges_iter( keys=True, data=True ) :
        roadlen = data.get( length, 1. )
        assert roadlen >= 0.
        
        # layer one
        mass = data.get( weight1, 0. )
        if mass > 0. :
            w = roadlen / mass
            
            flowvar = cvxpy.variable()
            sat = [ cvxpy.geq( flowvar, 0. ), cvxpy.leq( flowvar, mass ) ]
            rgraph.add_node( (key,1), weight=w, flowvar=flowvar, constraints=sat )
            
            flow = flowvar
            rgraph.add_edge( (key,1), (u,1), flow=flow, cost=.5 * w * cvxpy.square( flow ) )
            
            flow = mass - flowvar
            rgraph.add_edge( (key,1), (v,1), flow=flow, cost=.5 * w * cvxpy.square( flow ) )
            
        # layer two
        mass = data.get( weight2, 0. )
        if mass > 0. :
            w = roadlen / mass
            
            flowvar = cvxpy.variable()
            sat = [ cvxpy.geq( flowvar, 0. ), cvxpy.leq( flowvar, mass ) ]
            rgraph.add_node( (key,2), weight=w, flowvar=flowvar, constraints=sat )
            
            flow = flowvar
            rgraph.add_edge( (u,2), (key,2), flow=flow, cost=.5 * w * cvxpy.square( flow ) )
            
            flow = mass - flowvar
            rgraph.add_edge( (v,2), (key,2), flow=flow, cost=.5 * w * cvxpy.square( flow ) )
            
    """ setup the network flow structure """
    ngraph = nx.DiGraph()       # "network graph"
    underlying = nx.MultiGraph( roadnet )       # an undirected copy
    APSP = nx.all_pairs_dijkstra_path_length( underlying, weight=length )
    NODES = roadnet.nodes()
    for u,v in itertools.product( NODES, NODES ) :
        try :
            weight = APSP[u][v]
        except :
            continue
        
        flowvar = cvxpy.variable()
        sat = [ cvxpy.geq( flowvar, 0. ) ]      # seems to be needed... it's harmless, but necessary?
        ngraph.add_edge( (u,1), (v,2), weight=weight, flow=flowvar, cost=weight * flowvar, constraints=sat )
        
        
    """ fill in the remaining network constraints """
    for u in roadnet.nodes_iter() :
        # layer one
        out_flows_on_net = [ data['flow'] for _,__,data in ngraph.out_edges_iter( (u,1), data=True ) ]
        LHS = sum( out_flows_on_net )
        
        in_flows_from_roads = [ data['flow'] for _,__,data in rgraph.in_edges_iter( (u,1), data=True ) ]
        RHS = sum( in_flows_from_roads )
        
        sat = [ cvxpy.eq( LHS, RHS ) ]
        sat = [ cvxpy.leq( cvxpy.abs( RHS - LHS ), DELTA ) ]
        ngraph.node[ (u,1) ]['constraints'] = sat
        
        # layer two
        in_flows_from_net = [ data['flow'] for _,__,data in ngraph.in_edges_iter( (u,2), data=True ) ]
        LHS = sum( in_flows_from_net )
        
        out_flows_on_roads = [ data['flow'] for _,__,data in rgraph.out_edges_iter( (u,2), data=True ) ]
        RHS = sum( out_flows_on_roads )
        
        sat = [ cvxpy.eq( LHS, RHS ) ]
        sat = [ cvxpy.leq( cvxpy.abs( RHS - LHS ), DELTA ) ]
        ngraph.node[ (u,2) ]['constraints'] = sat
    
    return rgraph, ngraph




def peel_cost( data ) :
    return data.get('cost', 0. )
    
def peel_constraints( data ) :
    return data.get('constraints', [] )


def construct_problem( road_graph, net_graph ) :
    cost = 0.
    constraints = []
    
    road_graph_node_data = ( data for _,data in road_graph.nodes_iter( data=True ) )
    road_graph_edge_data = ( data for _,__,data in road_graph.edges_iter( data=True ) )
    net_graph_node_data = ( data for _,data in net_graph.nodes_iter( data=True ) )
    net_graph_edge_data = ( data for _,__,data in net_graph.edges_iter( data=True ) )
    iter = itertools.chain( road_graph_node_data, road_graph_edge_data, net_graph_node_data, net_graph_edge_data )
    
    for data in iter :
        c = peel_cost( data )
        sat = peel_constraints( data )
        cost += c
        constraints.extend( sat )
        
    return cost, constraints
        
        
        
        
g = nx.MultiDiGraph()
g.add_edge( 0, 1, 'road1', length=2., weight2=.5)
g.add_edge( 1, 2, 'road2', length=1., weight1=.4 )
g.add_edge( 2, 3, 'road3', length=3., weight2=.1)
g.add_edge( 3, 0, 'road4', length=5., weight1=.2)
#g.add_edge( 1, 3, 'road3 ' )


rgraph, ngraph = construct_emd_graph( g )
cost, const = construct_problem( rgraph, ngraph )
#const.append( cvxpy.geq( cost, -1000. ) )        # give it a lower bound...

obj = cvxpy.minimize( cost )
prog = cvxpy.program( obj, const )
res = prog.solve()








