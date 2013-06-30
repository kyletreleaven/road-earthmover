

from signaling import Signal, Message




class Vehicle :
    def __init__(self) :
        self.ready = Signal()
        
    def set_environment(self, f_dist ) :
        self.f_dist = f_dist
        
    def set_location(self, location ) :
        self.location = location
        
    def join_sim(self, sim ) :
        self.sim = sim
        self.sim.schedule( self.ready_at )
        
    """ signaloid """
    def ready_at(self) : self.ready( self.location )
    
    """ slot """
    def receive_demand(self, demand ) :
        p, q = demand
        time = self.sim.get_time()
        print 'got demand at %f: (%s, %s)' % ( time, repr(p), repr(q) )
        
        self.pick = p ; self.delv = q
        
        dist_curr_to_pick = self.f_dist( self.location, p )
        print 'moving to pickup, there in %f' % dist_curr_to_pick
        self.sim.schedule( self.arrived_at_pickup, dist_curr_to_pick )
        
    """ auto slot """
    def arrived_at_pickup(self) :
        self.location = self.pick
        time = self.sim.get_time()
        print 'arrived to pickup at %f' % time
        
        q = self.delv
        dist_pick_to_delv = self.f_dist( self.location, q )
        print 'moving to delivery, there in %f' % dist_pick_to_delv
        self.sim.schedule( self.delivered, dist_pick_to_delv )
        
    """ auto slot """
    def delivered(self) :
        self.location = self.delv
        time = self.sim.get_time()
        print 'delivered at %f' % time
        
        self.ready_at()







