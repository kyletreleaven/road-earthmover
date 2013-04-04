
import itertools

import numpy as np
import networkx as nx
import cvxpy

import roadmap_basic as roadmaps

from nxopt import newvar




def measurenx_to_approxnx( roadnet, epsilon, length='length', weight1='weight1', weight2='weight2' ) :
    """
    input: a road network, with weights on its elements
    output:
    returns a graph summarizing the network optimization problem instance;
    roadnets are multi-digraph, where edge 'keys' are assumed to be unique,
    i.e., road names; and should be different from node labels too;
    """
    digraph = nx.DiGraph()
    SUPPLY = []
    DEMAND = []
    
    """ insert supply and demand of roads """
    for u,v, road, data in roadnet.edges_iter( keys=True, data=True ) :
        surplus = float( data.get( weight1, 0. ) ) - data.get( weight2, 0. )
        deficit = -surplus
        
        """
        split the road into equal-length segments;
        create a node for each segment;
        record boundary points, and mass contained
        """
        roadlen = float( data.get( length, 1 ) )   # float() just in case
        assert roadlen >= 0.
        N = int( np.ceil( roadlen / epsilon ) )
        #print road, N
        eps = roadlen / N
        bd = np.linspace( 0, roadlen, N+1 )
        bd = [ roadmaps.RoadAddress( road, x ) for x in bd ]
        for i, boundary in enumerate( zip( bd[:-1], bd[1:] ) ) :
            if surplus > 0. :
                node = (road,i,'supply')
                digraph.add_node( node, boundary=boundary, mass=surplus/N )
                SUPPLY.append( node )
            if deficit > 0. :
                node = (road,i,'demand')
                digraph.add_node( node, boundary=boundary, mass=deficit/N )
                DEMAND.append( node )
    
    """ ...and nodes """
    for u, data in roadnet.nodes_iter( data=True ) :
        surplus = data.get( weight1, 0. ) - data.get( weight2, 0. )
        deficit = -surplus
        if surplus > 0. :
            boundary = [ roadmaps.roadify( roadnet, u, weight=length ) ]
            node = (u,'supply')
            digraph.add_node( node, boundary=boundary, mass=surplus )
            SUPPLY.append( node )
        if deficit > 0. :
            boundary = [ roadmaps.roadify( roadnet, v, weight=length ) ]
            node = (u,'demand')
            digraph.add_node( node, boundary=boundary, mass=deficit )
            DEMAND.append( node )
            
            
    """ generate flow edges """
    for u, v in itertools.product( SUPPLY, DEMAND ) :
        bd_u = digraph.node[u]['boundary']
        bd_v = digraph.node[v]['boundary']
        options = [ pair for pair in itertools.product( bd_u, bd_v ) ]
        options = [ roadmaps.distance( roadnet, p, q, weight=length ) for p,q in options ]
        #options = [ np.inf ]
        w = min( options )
        W = max( options )
        
        # all flows are generated here
        flowvar, sat = newvar()
        digraph.add_edge( u, v, flow=flowvar, constraints=sat,
                          cost_lo = w * flowvar, cost_hi = W * flowvar )
        
    """ record network constraints """
    for u in SUPPLY :
        out_flows = [ peel_flow( data ) for _,__,data in digraph.out_edges_iter( u, data=True ) ]
        out_flow = sum( out_flows )
        data = digraph.node[u]
        capacity = data['mass']
        sat = [ cvxpy.leq( out_flow, capacity ) ]
        data['constraints'] = sat
        
    for v in DEMAND :
        in_flows = [ peel_flow( data ) for _,__,data in digraph.in_edges_iter( v, data=True ) ]
        in_flow = sum( in_flows )
        data = digraph.node[v]
        capacity = data['mass']
        sat = [ cvxpy.leq( in_flow, data['mass'] ) ]
        data['constraints'] = sat
        
    return digraph      # a flow network




def peel_flow( data ) :
    return data.get( 'flow', 0. )

def peel_cost( data ) :
    return data.get( 'cost', 0. )
    
def peel_constraints( data ) :
    return data.get('constraints', [] )





if __name__ == '__main__' :
    import matplotlib.pyplot as plt
    plt.close('all')
    
    roadnet = nx.MultiDiGraph()
    
    if False :
        g.add_edge( 0, 1, 'road1', length=2., weight1=0.+OFFSET, weight2=.5+OFFSET)
        g.add_edge( 1, 2, 'road2', length=1., weight1=.4)
        g.add_edge( 2, 3, 'road3', length=3., weight2=.1)
        g.add_edge( 3, 0, 'road4', length=5., weight1=.4)
        
    else :
        OFFSET = 10.
        roadnet.add_node( 0, weight1=.7 )
        roadnet.add_edge( 0,1, 'road1', length=1., weight1=0.+OFFSET, weight2=.5+OFFSET )
        roadnet.add_edge( 0,2, 'road2', length=2., weight2=.6 )
        
        
    #g.add_edge( 1, 3, 'road3 ' )
    res = roademd.EarthMoversDistance( roadnet )
    
    digraph = measurenx_to_approxnx( roadnet, .015 )
    #total_flow = roademd.flow_on_optNW( digraph )
    res_lo = roademd.mincost_maxflow( digraph, 'cost_lo' )
    res_hi = roademd.mincost_maxflow( digraph, 'cost_hi' )
    
    #total_flow, cost, const = optNW_statistics( digraph )
    #res = solve_optNW( digraph )
    #max_flow = total_flow.value
    
    #print 'max flow is %f' % max_flow
    #print 'min cost max flow is %f' % res
    
    print res_lo, res, res_hi
    
    
    