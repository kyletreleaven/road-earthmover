
import numpy as np

from setiptah.eventsim.signaling import Signal, Message
import setiptah.roadgeometry.roadsearch as search


# I think more easily in terms of objects than registers
class token : pass




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
        
        
        
        
class BatchNNeighDispatcher :
    def __init__(self) :
        # batch requests
        self.batch_requests = []
        self.dispatches_pending = []
        
        # service demands
        self.locations = search.PointSet()
        self.demands = {}
        
        # vehicle requests
        self.pending = []
        
        """ signal """
        self.request_batch = Signal()
        
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
    def batch_arrived(self, batch ) :
        # pop a batch request from the queue
        self.batch_requests.pop(0)
        
        # insert the whole batch
        for dem in batch :
            p,_ = dem
            self.locations.insert( p )
            self.demands[ p ] = dem
            
        # schedule the dispatch loop
        if len( self.dispatches_pending ) <= 0 :
            self.dispatches_pending.append( token() )
            self.sim.schedule( self._try_dispatch )
        
    """ slot, collected from interfaces """
    def request_in(self, interface, location ) :
        self.pending.append( ( interface, location ) )
        
        # schedule the dispatch loop
        if len( self.dispatches_pending ) <= 0 :
            self.dispatches_pending.append( token() )
            self.sim.schedule( self._try_dispatch )
        
        
    """ auto-slot, utility """
    def _try_dispatch(self) :
        if len( self.dispatches_pending ) > 0 : self.dispatches_pending.pop(0)
        
        while len( self.pending ) > 0 :
            if len( self.demands ) == 0 : break     # we ran out of demands
            
            # otherwise
            interface, location = self.pending.pop(0)       # get the next pending request
            
            loc = self.locations.find_nearest( location, self.roadnet, 'length' )
            self.locations.remove( loc )
            dem = self.demands.pop( loc )
            
            # signaling
            interface.demand_out( dem )            
            #msg = Message( interface.demand_out, dem )
            #self.sim.schedule( msg )
        
        if len( self.demands ) == 0 and len( self.batch_requests ) <= 0 :
            self.batch_requests.append( token() )   # seriously, i can be an idiot
            self.request_batch()
            #self.sim.schedule( self.request_batch )
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            

            
            
