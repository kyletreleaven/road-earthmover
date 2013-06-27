
import itertools
import random

import numpy as np
import networkx as nx

import matplotlib.pyplot as plt

#import road_Ed, roademd
import nxopt.max_flow_min_cost as FLOW

class Wassnode(object) : pass




def MoversComplexity( lengraph, rategraph, length='length', rate='rate' ) :
    # enroute cost
    enroute_cost = demand_enroute_velocity( lengraph, rategraph, length, rate )
    balance_cost = demand_balance_velocity( lengraph, rategraph, length, rate )
    return enroute_cost + balance_cost
    




def demand_enroute_velocity( lengraph, rategraph, length='length', rate='rate' ) :
    V = 0.
    for u, v, rate_data in rategraph.edges_iter( data=True ) :
        curr_rate = rate_data.get( rate, None )
        if curr_rate is None : continue
        
        dist = nx.dijkstra_path_length( lengraph, u, v, weight=length )
        V += curr_rate * dist
    return V
    
    
def demand_balance_velocity( lengraph, rategraph, length='length', rate='rate' ) :
    flowgraph, costgraph = obtainWassersteinProblem( lengraph, rategraph, length, rate )
    FLOW.max_flow_min_cost( flowgraph, costgraph )
    return FLOW.totalcost( costgraph ).value




def obtainWassersteinProblem( lengraph, rategraph, length='length', rate='rate' ) :
    digraph = nx.DiGraph()
    s = Wassnode() ; t = Wassnode()
    digraph.add_node( s ) ; digraph.add_node( t )
    
    for u, v in lengraph.edges_iter() :
        digraph.add_edge( u, v )
        
    for u in rategraph.nodes_iter() :
        u_supply = rategraph.in_degree( u, rate ) - rategraph.out_degree( u, rate )
        if u_supply > 0. :
            digraph.add_edge( s, u, capacity = u_supply )
        elif u_supply < 0. :
            digraph.add_edge( u, t, capacity = -u_supply )
            
    flowgraph = FLOW.obtainFlowNetwork( digraph, s, t )
    costgraph = FLOW.obtainWeightedCosts( flowgraph, lengraph, weight=length )
    
    return flowgraph, costgraph






def compute_marginals( digraph, rate='rate' ) :
    rate_orig = dict()
    rate_dest = dict()
    for u, data in digraph.nodes_iter( data=True ) :
        rate_orig[u] = digraph.out_degree( u, rate )
        rate_dest[u] = digraph.in_degree( u, rate )
        
    return rate_orig, rate_dest

def compute_surplus( digraph, rate='rate' ) :
    surplus = dict()
    for u, data in digraph.nodes_iter( data=True ) :
        surplus[u] = digraph.out_degree( u, rate ) - digraph.in_degree( u, rate )
        
    return surplus









def randompoint() :
    return np.random.rand(2)

def display( graph, coord='coord' ) :
    map = [ ( u, data.get('coord') ) for u,data in graph.nodes_iter( data=True ) ]
    layout = dict( map )
    
    nx.draw( graph, pos=layout )
    

if True :
    GRAPH = nx.DiGraph()
    
    PLACES = [ 'HOME', 'WORK', 'SHOPPING' ]
    #PLACES = [ 'HOME', 'WORK', 'SHOPPING', 'GYM', 'MOVIE' ]
    for place in PLACES :
        GRAPH.add_node( place, coord=randompoint() )
        
    for o, o_data in GRAPH.nodes_iter( data=True ) :
        o_loc = o_data.get( 'coord' )
        
        for d, d_data in GRAPH.nodes_iter( data=True ) :
            #if d is o : continue
            # this is actually important, max_flow_min_cost chokes without it
            
            # geometry
            d_loc = d_data.get( 'coord' )
            distance = np.linalg.norm( d_loc - o_loc )
            
            # demand
            rate = np.random.exponential()
            
            GRAPH.add_edge( o, d, distance=distance, rate=rate )
            
    enroute_velocity = demand_enroute_velocity( GRAPH, GRAPH, length='distance' )
    balance_velocity = demand_balance_velocity( GRAPH, GRAPH, length='distance' )
    
    #flowgraph, costgraph = obtainWassersteinProblem( DEMAND, DEMAND, length='distance' )
    
    print enroute_velocity, balance_velocity
    
    
    distance_between = lambda u, v : GRAPH.get_edge_data( u, v ).get('distance')
    
    class demand :
        def __init__(self, p, q ) :
            self.pick = p
            self.delv = q
            
    T = 20.
    DEMANDS = []
    for u, v, data in GRAPH.edges_iter( data=True ) :
        n = np.random.poisson( data.get('rate') * T )
        DEMANDS.extend([ demand(u,v) for i in range(n) ])
        
    total_enroute = sum( [ distance_between( dem.pick, dem.delv ) for dem in DEMANDS ] )
    mean_enroute = total_enroute / T
    
    
    
    if True :
        graph = nx.Graph()
        for dem1, dem2 in itertools.product( DEMANDS, DEMANDS ) :
            #if dem2 is dem1 : continue  # those edges aren't in there
            
            dist = distance_between( dem1.delv, dem2.pick )
            graph.add_edge( (dem1,0), (dem2,1), weight = -dist )    # about to do MAX_weight_matching
                
        mate = nx.matching.max_weight_matching( graph, maxcardinality=True )
        total_balance = sum( [ distance_between( dem1.delv, dem2.pick )
                              for ( (dem1,side1), (dem2,side2) ) in mate.iteritems() if side1 == 0 ] )
        mean_balance = total_balance / T
    else :
        mean_balance = None
    
    print mean_enroute, mean_balance
    
        
        
        
    
    
    
    
    
            
            
