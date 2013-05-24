
""" standard python """
import itertools

""" scientific de-facto """
import numpy as np
import scipy as sp

import networkx as nx
import sympy

class GLOBAL :
    x = sympy.Symbol('x')
    y = sympy.Symbol('y')
    

""" mine """
import roadmap_basic as ROAD
import polyglint2d.polyglint2d as pglint


""" general purpose utilities """

def isolate( cont ) :
    for k, i in enumerate( cont ) :
        yield ( i, cont[:k] + cont[k+1:] )


""" helper classes """
    
"""
    poor man's symbolic algebra library, because I can't figure out how to work inequalities in other ones
    I should look into cvxpy for some good example of how to do this right 
"""
    
    
""" utilities """
    
def _compute_options_within( roadnet, road, length_attr ) :
    edge, data = ROAD.obtain_edge( roadnet, road, True )
    u,v,_ = edge ; roadlen = data.get( length_attr, np.inf )
    
    p = ROAD.roadify( roadnet, u, length_attr )
    q = ROAD.roadify( roadnet, v, length_attr )
    alt_dist = ROAD.distance( roadnet, p, q, length_attr )
    K = .5 * ( roadlen + alt_dist )
    
    # cases
    #
    row1 = [
            [ -1., 1. ],        
            [ ]
            ] 
    # x < y ; | x - y | < K
    c = [ -1., 1. ] ; d = 0.
    a = [ -1., 1. ] ; b = .5 * ( roadlen)
    # x < y ; | x - y | > K
    
    # x > y ; | x - y | < K
    
    # x > y ; | x - y | > K

    
    
def _compute_options_between( roadnet, road1, road2, length_attr ) :
    edge1, data1 = ROAD.obtain_edge( roadnet, road1, data_flag=True )
    edge2, data2 = ROAD.obtain_edge( roadnet, road2, data_flag=True )
    
    u1,v1,_ = edge1 ; roadlen1 = data1.get( length_attr, np.inf )
    u2,v2,_ = edge2 ; roadlen2 = data2.get( length_attr, np.inf )
    
    x = GLOBAL.x ; y = GLOBAL.y    
    cost_dict = {
                 u1 : x,
                 v1 : roadlen1 - x,
                 u2 : y,
                 v2 : roadlen2 - y
                 }
    ensure_leq_zero = [
                      -x,               # x >= 0
                      x - roadlen1,     # x <= roadlen1
                      -y,               # y >= 0
                      y - roadlen2      # y <= roadlen2
                      ]
    
    WAYP1 = [ v1 ]
    if not data1.get( 'oneway', False ) : WAYP1.append( u1 )
    WAYP2 = [ u2 ]
    if not data2.get( 'oneway', False ) : WAYP1.append( v2 )
    
    options = []
    for s in WAYP1 :
        p = ROAD.roadify( roadnet, s, length_attr )
        for t in WAYP2 :
            q = ROAD.roadify( roadnet, t, length_attr )
            
            dst = ROAD.distance( roadnet, p, q, length_attr )
            cost = cost_dict[s] + dst + cost_dict[t]
            
            leq = [ o for o in ensure_leq_zero ]    # make a safe copy
            options.append( ( cost, leq ) )
            
    return options




def _get_phases( options ) :
    phases = []
    
    for ( cost, leq ), others in isolate( options ) :
        leq_out = [ o for o in leq ]        # make a safe copy
        for o_cost, _ in others :
            leq_out.append( cost - o_cost )
            
        phases.append( ( cost, leq_out ) )
    return phases


def _phase_to_pglint( cost, ensure_leq_zero ) :
    x = GLOBAL.x ; y = GLOBAL.y 
    d, expr = cost.as_coeff_Add()
    c_x = expr.coeff(x) ; c_y = expr.coeff(y)
    c = np.array([ c_x, c_y ])
    
    nconstr = len(ensure_leq_zero)
    A = np.zeros( ( nconstr, 2 ) )
    b = np.zeros( nconstr )
    
    for i, expr in enumerate( ensure_leq_zero ) :
        minus_b, expr = expr.as_coeff_Add() ; b[i] = -minus_b
        a_x = expr.coeff(x) ; a_y = expr.coeff(y)
        A[i,:] = np.array([ a_x, a_y ])
        
    return ( c, d, A, b )
        

""" algorithms """


def roadEd_conditional( roadnet, road1, road2, length_attr='length' ) :
    if road1 == road2 :
        options = _compute_options_within(roadnet, road1, road2, length_attr)
    else :
        options = _compute_options_between(roadnet, road1, road2, length_attr)
        
    return _get_phases( options )


if __name__ == '__main__' :
    
    roadnet = nx.MultiDiGraph()

    roadnet.add_edge( 0, 1, 'N', length=1., weight2=3. )
    roadnet.add_edge( 1, 2, 'E', length=1., weight1=1000., oneway=False )
    roadnet.add_edge( 2, 3, 'S', length=1., weight1=1. )
    roadnet.add_edge( 3, 0, 'W', length=1., weight2=1. )
    #roadnet.add_node( 0, weight1=.7 )
    #roadnet.add_edge( 0, 1 )
    
    
