
""" standard python """
import itertools

""" scientific de-facto """
import numpy as np
import scipy as sp

import networkx as nx
import sympy


""" setiptah dependencies """
#import polyglint2d.polyglint2d as pglint
import setiptah.roadgeometry.roadmap_basic as ROAD
import setiptah.polyglint2d as pglint

""" local dependencies """




class GLOBAL :
    x = sympy.Symbol('x')
    y = sympy.Symbol('y')
    


""" general purpose utilities """

def isolate( cont ) :
    for k, i in enumerate( cont ) :
        yield ( i, cont[:k] + cont[k+1:] )


""" problem specific utilities """

""" "options" generators, in each of three interesting cases """

def _options_roads_eq_ygeqx( roadnet, road, length_attr ) :
    edge, data = ROAD.obtain_edge( roadnet, road, data_flag=True )
    u,v,_ = edge ; roadlen = data.get( length_attr, np.inf )
    p = ROAD.roadify( roadnet, u, length_attr )
    q = ROAD.roadify( roadnet, v, length_attr )
    
    x = GLOBAL.x ; y = GLOBAL.y
    options = [ y - x ]
    if not data.get( 'oneway', False ) :
        sojourn_cost = x + ROAD.distance( roadnet, p, q, length_attr ) + roadlen - y    # a path using the rest of the network 
        options.append( sojourn_cost )
        
    return options


def _options_roads_eq_yleqx( roadnet, road, length_attr ) :
    edge, data = ROAD.obtain_edge( roadnet, road, data_flag=True )
    u,v,_ = edge ; roadlen = data.get( length_attr, np.inf )
    p = ROAD.roadify( roadnet, u, length_attr )
    q = ROAD.roadify( roadnet, v, length_attr )
    
    x = GLOBAL.x ; y = GLOBAL.y
    sojourn_cost = roadlen - x + ROAD.distance( roadnet, q, p, length_attr ) + y    # a path using the rest of the network 
    options = [ sojourn_cost ]
    if not data.get( 'oneway', False ) :
        options.append( x - y )
    return options


def _options_roads_neq( roadnet, road1, road2, length_attr ) :
    edge1, data1 = ROAD.obtain_edge( roadnet, road1, data_flag=True )
    u1,v1,_ = edge1 ; roadlen1 = data1.get( length_attr, np.inf )
    edge2, data2 = ROAD.obtain_edge( roadnet, road2, data_flag=True )
    u2,v2,_ = edge2 ; roadlen2 = data2.get( length_attr, np.inf )
    
    x = GLOBAL.x ; y = GLOBAL.y    
    cost_dict = {
                 '<-s' : x,
                 's->' : roadlen1 - x,
                 '->t' : y,
                 't<-' : roadlen2 - y
                 }
    
    options = []
    # paths through endpoints
    WAYP1 = [ ( 's->', v1 ) ]
    if not data1.get( 'oneway', False ) : WAYP1.append( ( '<-s', u1 ) )
    WAYP2 = [ ( '->t', u2 ) ]
    if not data2.get( 'oneway', False ) : WAYP2.append( ( 't<-', v2 ) )
    
    for s,u in WAYP1 :
        p = ROAD.roadify( roadnet, u, length_attr )
        for t,v in WAYP2 :
            q = ROAD.roadify( roadnet, v, length_attr )
            
            dst = ROAD.distance( roadnet, p, q, length_attr )
            cost = cost_dict[s] + dst + cost_dict[t]
            options.append( cost )
            
    return options










def _zonify_options( options ) :
    zones = []
    for cost, others in isolate( options ) :
        ensure_leq_zero = [ cost - o_cost for o_cost in others ]
        zones.append( ensure_leq_zero )
    return zones




def _compute_phases( roadnet, road1, road2, length_attr ) :
    edge1, data1 = ROAD.obtain_edge( roadnet, road1, data_flag=True )
    roadlen1 = data1.get( length_attr, np.inf )
    edge2, data2 = ROAD.obtain_edge( roadnet, road2, data_flag=True )
    roadlen2 = data2.get( length_attr, np.inf )
    
    res = []
    
    x = GLOBAL.x ; y = GLOBAL.y
    canvas = [
                -x,                 # x >= 0
                x - roadlen1,       # x <= roadlen1
                -y,                 # y >= 0
                y - roadlen2        # y <= roadlen2
            ]
    
    """ there are three "interesting" cases """
    if road1 == road2 :
        # case 1: road1 == road2, y >= x
        options = _options_roads_eq_ygeqx( roadnet, road1, length_attr )
        zones = _zonify_options( options )
        for zone in zones :
            zone.extend( canvas )
            zone.append( x - y )
        phases = zip( options, zones )
        res.extend( phases )
        
        # case 2: road1 == road2, y <= x
        options = _options_roads_eq_yleqx( roadnet, road1, length_attr )
        zones = _zonify_options( options )
        for zone in zones :
            zone.extend( canvas )
            zone.append( y - x )
        phases = zip( options, zones )
        res.extend( phases )
        
    else :
        # case 3: road1 != road2
        options = _options_roads_neq( roadnet, road1, road2, length_attr )
        zones = _zonify_options( options )
        for zone in zones :
            zone.extend( canvas )
        phases = zip( options, zones )
        res.extend( phases )
        
    return res









""" the utilities below are in a working state """

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







""" main algorithm """

def roadEd_conditional( roadnet, road1, road2, length_attr='length' ) :
    edge1, data1 = ROAD.obtain_edge( roadnet, road1, data_flag=True )
    roadlen1 = data1.get( length_attr, np.inf )
    edge2, data2 = ROAD.obtain_edge( roadnet, road2, data_flag=True )
    roadlen2 = data2.get( length_attr, np.inf )
    
    phases = _compute_phases( roadnet, road1, road2, length_attr='length' )
    pglints = [ _phase_to_pglint( c, constr ) for c,constr in phases ]
    # somewhere we need to normalize!
    vals = [ pglint.integrate( c, d, A, b ) for c, d, A, b in pglints ]
    
    return sum( vals ) / roadlen1 / roadlen2




def roadEd( roadnet, distr1, distr2=None, length_attr='length' ) :
    """
    distr1 may be a pmf over road pairs, or over roads;
    if distr2 is not present then distr1 is assumed to be the joint pmf ( i.e., over (source,target) road pairs ) ;
    if distr2 is present, then source and target are assumed i.i.d.,
        distr1 is the pmf over source roads, and distr2 is the pmf over target roads
    """
    if distr2 is not None : raise 'not implemented yet'
    
    return np.sum([ prob * roadEd_conditional( roadnet, road1, road2, length_attr ) for (road1,road2), prob in distr1.iteritems() ]) 






""" self test """
if __name__ == '__main__' :
    import random
    import probability as roadprob
    
    """ unit test """
    
    if True :
        roadnet = nx.MultiDiGraph()
        
        roadnet.add_edge( 0, 1, 'N', length=1., weight2=3. )
        roadnet.add_edge( 1, 2, 'E', length=2., weight1=1000., oneway=True )
        roadnet.add_edge( 2, 3, 'S', length=1., weight1=1. )
        roadnet.add_edge( 3, 0, 'W', length=1., weight2=1. )
        #roadnet.add_node( 0, weight1=.7 )
        #roadnet.add_edge( 0, 1 )
        
    else :
        g = nx.erdos_renyi_graph( 15, .3 )
        g = nx.connected_component_subgraphs( g )[0]
        
        roadnet = nx.MultiDiGraph()
        def roadmaker() :
            for i in itertools.count() : yield 'road%d' % i, np.random.exponential()
        road_iter = roadmaker()
        
        for i, ( u,v,data ) in enumerate( g.edges_iter( data=True ) ) :
            label, length = road_iter.next()
            roadnet.add_edge( u, v, label, length=length )
            
        nodes = roadnet.nodes()
        for i in range( 5 ) :
            u = random.choice( nodes )
            v = random.choice( nodes )
            label, length = road_iter.next()
            roadnet.add_edge( u, v, label, length=length, oneway=True )
            
            
    
    if True :
        distr = {}
        distr[('W','E')] = 1./5
        distr[('N','E')] = 1./5
        distr[('W','S')] = 3./5
        
        Ed = roadEd( roadnet, distr, length_attr='length' )
        print 'Ed computed %f' % Ed
        
        pairs = [ roadprob.samplepair( roadnet, distr ) for i in range(20000) ]
        dst = [ ROAD.distance( roadnet, p, q, 'length' ) for p,q in pairs ]
        Ed_emp = np.mean( dst )
        print 'Ed empirical %f' % Ed_emp
        
        
    else :
        ROADS = ['N', 'S', 'E', 'W' ]
        #PAIRS = itertools.product( ROADS, ROADS )
        #PAIRS = [ ('E','E') ]
        edges = [ name for _,__,name in roadnet.edges( keys=True ) ]
        #PAIRS = [ ( random.choice(edges), random.choice(edges) ) for i in range(5) ]
        for road1, road2 in PAIRS :
            Ed_cond = roadEd_conditional( roadnet, road1, road2 )
            #
            pairs = [ sample( roadnet, { (road1, road2) : 1.} ) for i in range(20000) ]
            dst = [ ROAD.distance( roadnet, p, q, 'length' ) for p,q in pairs ]
            Ed_emp = np.mean( dst )
            #
            print '(%s,%s) -> Ed computed %f, empirical %f' % ( road1, road2, Ed_cond, Ed_emp )
            
        
        