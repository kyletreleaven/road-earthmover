

import itertools

import numpy as np
import networkx as nx

import cvxpy

import matplotlib.pyplot as plt
plt.close('all')


#DELTA = .0001       # there are numerical issues if DELTA == 0.

# just a convenience function
def newvar() :
    var = cvxpy.variable()
    sat = [ cvxpy.geq( var, 0. ) ]
    return var, sat
    

def construct_emd_graph( roadnet, length='length', weight1='weight1', weight2='weight2' ) :
    """
    returns a graph summarizing the problem instance, and the distance itself;
    roadnets are multi-digraph, where edge 'keys' are assumed to be unique,
    i.e., road names; and should be different from node labels too;
    """
    
    # for convenience
    #ROADS = [ key for u,v,key in roadnet.edges_iter( keys=True ) ]
    digraph = nx.DiGraph()
    
    """ insert supply and demand of roads """
    for u,v, road, data in roadnet.edges_iter( keys=True, data=True ) :
        roadlen = data.get( length, 1. )
        assert roadlen >= 0.
        
        # supply layer
        mass = data.get( weight1, 0. )
        if mass > 0. :
            w = roadlen / mass
            out_flow = 0.
            for node in [ u, v ] :
                flowvar, sat = newvar()
                out_flow += flowvar
                #
                cost = .5 * w * cvxpy.square( flowvar )
                digraph.add_edge( (road,'supply'), (node,'layer1'), flow=flowvar, constraints=sat, cost=cost )
                
            sat = [ cvxpy.leq( out_flow, mass ) ]
            digraph.node[ (road,'supply') ]['constraints'] = sat
            #flowvar, sat = newvar()
            #out_flow += flowvar
            #digraph.add_edge( (road,'supply'), 'SUPPLY_SINK', flow=flowvar, constraints=sat )
            #sat = [ cvxpy.equals( out_flow, mass ) ]
            
        # demand layer
        mass = data.get( weight2, 0. )
        if mass > 0. :
            w = roadlen / mass
            in_flow = 0.
            for node in [ u, v ] :
                flowvar, sat = newvar()
                in_flow += flowvar
                #
                cost = .5 * w * cvxpy.square( flowvar )
                digraph.add_edge( (node,'layer2'), (road,'demand'), flow=flowvar, constraints=sat, cost=cost )
                
            sat = [ cvxpy.leq( in_flow, mass ) ]
            digraph.node[ (road,'demand') ]['constraints'] = sat
            #flowvar, sat = newvar()
            #in_flow += flowvar
            #digraph.add_edge( 'DEMAND_SOURCE', (road,'demand'), flow=flowvar, constraints=sat )
            #sat = [ cvxpy.equals( in_flow, mass ) ]
            
    """ insert supply and demand of nodes """
    for u, data in roadnet.nodes_iter( data=True ) :
        # supply layer
        mass = data.get( weight1, 0. )
        if mass > 0. :
            flowvar, sat = newvar()
            #print flowvar, sat
            digraph.add_edge( (u,'supply'), (u,'layer1'), flow=flowvar, constraints=sat )
            
            sat = [ cvxpy.leq( flowvar, mass ) ]
            digraph.node[ (u,'supply') ]['constraints'] = sat
            
        # demand layer
        mass = data.get( weight2, 0. )
        if mass > 0. :
            flowvar, sat = newvar()
            digraph.add_edge( (u,'layer2'), (u,'demand'), flow=flowvar, constraints=sat )
            
            sat = [ cvxpy.leq( flowvar, mass ) ]
            digraph.node[ (u,'demand') ]['constraints'] = sat
            
            
    """ setup the network flow structure """
    #net_graph = nx.DiGraph()                    # "network graph"
    underlying = nx.MultiGraph( roadnet )       # an undirected copy
    APSP = nx.all_pairs_dijkstra_path_length( underlying, weight=length )
    #
    NODES = roadnet.nodes()
    for u,v in itertools.product( NODES, NODES ) :
        try :
            weight = APSP[u][v]
        except :
            continue
        
        flowvar, sat = newvar()
        digraph.add_edge( (u,'layer1'), (v,'layer2'), weight=weight, flow=flowvar, constraints=sat, cost = weight * flowvar )
        
    """ apply flow conservation constraints """
    for u in roadnet.nodes_iter() :
        # supply layer
        out_flows_on_net = [ data['flow'] for _,__,data in digraph.out_edges_iter( (u,'layer1'), data=True ) ]
        LHS = sum( out_flows_on_net )
        
        in_flows_from_roads = [ data['flow'] for _,__,data in digraph.in_edges_iter( (u,'layer1'), data=True ) ]
        RHS = sum( in_flows_from_roads )
        
        sat = [ cvxpy.eq( LHS, RHS ) ]
        digraph.node[ (u,'layer1') ]['constraints'] = sat
        
        # demand layer
        in_flows_from_net = [ data['flow'] for _,__,data in digraph.in_edges_iter( (u,'layer2'), data=True ) ]
        LHS = sum( in_flows_from_net )
        
        out_flows_on_roads = [ data['flow'] for _,__,data in digraph.out_edges_iter( (u,'layer2'), data=True ) ]
        RHS = sum( out_flows_on_roads )
        
        sat = [ cvxpy.eq( LHS, RHS ) ]
        digraph.node[ (u,'layer2') ]['constraints'] = sat
    
    return digraph




def peel_flow( data ) :
    return data.get( 'flow', 0. )

def peel_cost( data ) :
    return data.get( 'cost', 0. )
    
def peel_constraints( data ) :
    return data.get('constraints', [] )


def construct_problem( digraph ) :
    def node_data_iter( graph ) :
        return ( data for _,data in graph.nodes_iter( data=True ) )
    def edge_data_iter( graph ) :
        return ( data for _,__,data in graph.edges_iter( data=True ) )
    def graph_data_iter( graph ) :
        return itertools.chain( node_data_iter( graph ), edge_data_iter( graph ) )
    
    SUPPLY_FLOWS = ( peel_flow( data ) for i,j,data in digraph.edges_iter( data=True ) if i[1] == 'supply' )
    total_flow = sum( SUPPLY_FLOWS )
    
    cost = 0.
    constraints = []
    for data in graph_data_iter( digraph ) :
        cost += peel_cost( data )
        sat = peel_constraints( data )
        constraints.extend( sat )
    
    return total_flow, cost, constraints
        
        
        
        
g = nx.MultiDiGraph()

if False :
    g.add_edge( 0, 1, 'road1', length=2., weight2=.5)
    g.add_edge( 1, 2, 'road2', length=1., weight1=.4)
    g.add_edge( 2, 3, 'road3', length=3., weight2=.1)
    g.add_edge( 3, 0, 'road4', length=5., weight1=.4)
    
else :
    g.add_node( 0, weight1=.7 )
    g.add_edge( 0,1, 'road1', length=1., weight2=.5 )
    g.add_edge( 0,2, 'road2', length=10., weight2=.6 )
    
#g.add_edge( 1, 3, 'road3 ' )

digraph = construct_emd_graph( g )
total_flow, cost, const = construct_problem( digraph )
#const.append( cvxpy.geq( cost, -1000. ) )        # give it a lower bound...

maximize_flow = cvxpy.maximize( total_flow )
prog = cvxpy.program( maximize_flow, const )
prog.solve()
max_flow = total_flow.value
print 'max flow is %f' % max_flow

#DELTA = .0001
DELTA = 0.0001

const2 = [ c for c in const ]
const2.append( cvxpy.geq( total_flow, max_flow - DELTA ) )
minimize_cost = cvxpy.minimize( cost )
prog2 = cvxpy.program( minimize_cost, const2 )

res = prog2.solve()
print 'min cost max flow is %f' % res





