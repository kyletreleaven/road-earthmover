
import itertools
import random

import numpy as np
import networkx as nx

import matplotlib.pyplot as plt

#import road_Ed, roademd
import mass_transport
import nxopt.max_flow_min_cost as FLOW

#class Wassnode(object) : pass




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
    supplygraph = obtainSupplyGraph( rategraph, rate )
    return EarthMoversDistance( lengraph, supplygraph, length )     # weight1 and weight2 are implicit
    #flowgraph, costgraph = obtainWassersteinProblem( lengraph, rategraph, length, rate )
    #FLOW.max_flow_min_cost( flowgraph, costgraph )
    #return FLOW.totalcost( costgraph ).value




def EarthMoversDistance( lengraph, supplygraph, length='length', weight1='weight1', weight2='weight2' ) :
    # lengraph is a *non*-multi DiGraph
    digraph, s, t = FLOW.obtainCapacityNetwork( lengraph, supplygraph, length, weight1, weight2 )
    #
    flowgraph = FLOW.obtainFlowNetwork( digraph, s, t, capacity='capacity' )
    costgraph = FLOW.obtainWeightedCosts( flowgraph, lengraph, weight=length )
    
    # compute optimal flow
    FLOW.max_flow_min_cost( flowgraph, costgraph )
    
    return FLOW.totalcost( costgraph ).value
    



def obtainSupplyGraph( rategraph, rate='rate' ) :
    digraph = nx.DiGraph()
    for u, u_data in rategraph.nodes_iter( data=True ) :
        u_supply = rategraph.in_degree( u, rate )
        u_demand = rategraph.out_degree( u, rate )
        
        if True :
            digraph.add_node( u, weight1=u_supply, weight2=u_demand )
        else :
            if u_supply > u_demand :
                digraph.add_node( u, weight1 = u_supply - u_demand )
            elif u_supply < u_demand :
                digraph.add_node( u, weight2 = u_demand - u_supply )
        
    # this returns really just a glorified dictionary
    return digraph
    
    
    
    
    
if False :      # remove soon
    # do I even do this anymore?
    def obtainWassersteinProblem( lengraph, rategraph, length='length', rate='rate' ) :
        digraph = nx.DiGraph()
        digraph.add_edges_from( lengraph.edges_iter() )
        
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
    


if __name__ == '__main__' :
    GRAPH = nx.DiGraph()
    
    if False :
        GRAPH.add_edge(0,2,length=5.)
        GRAPH.add_edge(1,3,length=1.)
        GRAPH.add_edge(0,3,length=1.)
        GRAPH.add_edge(3,2,length=1.)
        
        GRAPH.node[0]['weight1'] = 1.
        GRAPH.node[1]['weight1'] = 1.
        GRAPH.node[2]['weight2'] = 1.
        GRAPH.node[3]['weight2'] = 1.
        
        
        print 'EMD: %f' % EarthMoversDistance( GRAPH, GRAPH )
        print 'the answer should be 3. (pretty sure.)'

    else :
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
        
            
        
        
    
    
