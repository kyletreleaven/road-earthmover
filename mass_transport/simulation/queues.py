
import numpy as np

from signaling import Signal, Message
import roadgeometry.roadsearch as search



class NNeighDispatcher :
    
    def __init__(self) :
        self.locations = search.PointSet()
        self.demands = {}
        
        self.pending = []
        
    def set_environment(self, roadnet ) :
        self.roadnet = roadnet
        
    def join_sim(self, sim ) :
        self.sim = sim
        
        
    class ServerInterface :
        def __init__(self, parent ) :
            self.parent = parent
            
            """ signal """
            self.demand_out = Signal()
        
        """ slot """
        def request_in(self, location ) :
            self.parent.request_in( self, location )
            
    def spawn_interface(self) :
        return self.ServerInterface( self )
    
    
    """ slot """
    def demand_arrived(self, demand, location ) :
        self.locations.insert( location )
        self.demands[ location ] = demand
        
        self._try_dispatch()
        
    """ slot, collected from interfaces """
    def request_in(self, interface, location ) :
        self.pending.append( ( interface, location ) )
        self._try_dispatch()
        
        
    """ utility """
    def _try_dispatch(self) :
        if len( self.demands ) == 0 or len( self.pending ) == 0 : return
        # otherwise, we have an annihilation!
        
        interface, location = self.pending.pop(0)       # get the next pending request
        
        loc = self.locations.find_nearest( location, self.roadnet, 'length' )
        self.locations.remove( loc )
        dem = self.demands.pop( loc )
        
        msg = Message( interface.demand_out, dem )
        self.sim.schedule( msg )
        
        
        
    