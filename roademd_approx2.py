
import itertools

import numpy as np
import networkx as nx
import cvxpy

import roadmap_basic as roadmaps

import nxopt




def measurenx_to_approxnx( roadnet, epsilon, length='length', weight1='weight1', weight2='weight2' ) :
    """
    input: a road network, with weights on its elements
    output:
    returns a graph summarizing the network optimization problem instance;
    roadnets are multi-digraph, where edge 'keys' are assumed to be unique,
    i.e., road names; and should be different from node labels too;
    """
    digraph = nx.DiGraph()
    digraph.add_node('s')
    digraph.add_node('t')
    
    """ insert supply and demand of roads """
    for u,v, road, data in roadnet.edges_iter( keys=True, data=True ) :
        roadlen = float( data.get( length, 1 ) )   # float() just in case
        assert roadlen >= 0.
        
        oneway = data.get( 'oneway', False )
        
        surplus = float( data.get( weight1, 0. ) ) - data.get( weight2, 0. )
        deficit = -surplus
        
        """
        split the road into equal-length segments;
        create a node for each segment;
        """
        N = int( np.ceil( roadlen / epsilon ) )
        eps = roadlen / N
        
        if surplus > 0. :
            NODES = [ (road,k,'supply') for k in range(N) ]
            for node in NODES :
                digraph.add_edge( 's', node, flow=cvxpy.variable(), minflow=0., maxflow=surplus/N, w_lo=-eps, w_hi=0. )
                
            SEQ = [ u ] + NODES + [ v ]
            for lnode, rnode in zip( SEQ[:-1], SEQ[1:] ) :
                digraph.add_edge( lnode, rnode, flow=cvxpy.variable(), minflow=0., w_lo=eps, w_hi=eps )
                if not oneway : digraph.add_edge( rnode, lnode, flow=cvxpy.variable(), minflow=0., w_lo=eps, w_hi=eps )
                
        if deficit > 0. :
            NODES = [ (road,k,'demand') for k in range(N) ]
            for node in NODES :
                digraph.add_edge( node, 't', flow=cvxpy.variable(), minflow=0., maxflow=deficit/N, w_lo=-eps, w_hi=0. )
                
            SEQ = [ u ] + NODES + [ v ]
            for lnode, rnode in zip( SEQ[:-1], SEQ[1:] ) :
                digraph.add_edge( lnode, rnode, flow=cvxpy.variable(), minflow=0., w_lo=eps, w_hi=eps )
                if not oneway : digraph.add_edge( rnode, lnode, flow=cvxpy.variable(), minflow=0., w_lo=eps, w_hi=eps )
                
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
    conns = roadmaps.connectivity_graph( roadnet )
    for u, v, data in conns.edges_iter( data=True ) :
        weight = data.get( length, 1 )
        flowvar = cvxpy.variable()
        digraph.add_edge( u, v, flow=cvxpy.variable(), minflow=0., w_lo=weight, w_hi=weight )
    
    """ turn the weights into costs """
    for _,__,data in digraph.edges_iter( data=True ) :
        flowvar = data['flow']
        if 'w_lo' in data : data['cost_lo'] = data['w_lo'] * flowvar
        if 'w_hi' in data : data['cost_hi'] = data['w_hi'] * flowvar
    
    nxopt.attach_flownx_constraints( digraph )
    return digraph      # a flownx








if __name__ == '__main__' :
    import matplotlib.pyplot as plt
    import roademd
    
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
        roadnet.add_edge( 0,2, 'road2', length=2., weight2=.6 )
    else :
        roadnet.add_edge( 0, 1, 'N', length=1., weight2=3. )
        roadnet.add_edge( 1, 2, 'E', length=1., weight1=1000., oneway=True )
        roadnet.add_edge( 2, 3, 'S', length=1., weight1=1. )
        roadnet.add_edge( 3, 0, 'W', length=1., weight2=1. )

        
    #g.add_edge( 1, 3, 'road3 ' )
    res = roademd.EarthMoversDistance( roadnet )
    digraph = measurenx_to_approxnx( roadnet, .015 )
    #total_flow = roademd.flow_on_optNW( digraph )
    
    weights_lo = [ ( (u,v), data.get('w_lo', 0.) ) for u,v,data in digraph.edges_iter( data=True ) ]
    weights_hi = [ ( (u,v), data.get('w_hi', 0.) ) for u,v,data in digraph.edges_iter( data=True ) ]

    costs_lo = [ ( (u,v), data.get('cost_lo', 0.) ) for u,v,data in digraph.edges_iter( data=True ) ]
    costs_hi = [ ( (u,v), data.get('cost_hi', 0.) ) for u,v,data in digraph.edges_iter( data=True ) ]
    
    
    if True :
        res_lo = nxopt.mincost_maxflow( digraph, 'cost_lo' )
        flows = [ ( (u,v), data['flow'].value ) for u,v,data in digraph.edges_iter( data=True ) if data['flow'].value > .0001 ]
        res_hi = nxopt.mincost_maxflow( digraph, 'cost_hi' )
        

        
        #total_flow, cost, const = optNW_statistics( digraph )
        #res = solve_optNW( digraph )
        #max_flow = total_flow.value
        
        #print 'max flow is %f' % max_flow
        #print 'min cost max flow is %f' % res
        
        print res_lo, res, res_hi
        
        
    