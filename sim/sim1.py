import simpy
import math
import random

class SteppingEnvironment(simpy.Environment):
    def __init__(self, initial_time=0):
        super().__init__(initial_time)
        self.total_steps = 0

    def step(self):
        super().step()
        self.total_steps += 1

# I'd like to know when a job is first worked, and when it finishes.
class Job:
    JID = 0
    def __init__(self, benes, benes_per_wu):
        self.jid = Job.JID
        Job.JID += 1
        self.work_units = benes // benes_per_wu
        self.start = -1
        self.worked = 0
        self.end = -1
    # When a job is worked, we increment the 
    # units worked.
    def work(self, timestep):
        if self.start < 0:
            self.start = timestep
        self.worked += 1
        if self.worked == self.work_units:
            self.end = timestep
        

class WorkUnit:
    WID = 0
    def __init__(self, job, queue_index):
        self.job = job
        self.wid = WorkUnit.WID
        WorkUnit.WID += 1
        self.queue_index = queue_index

# A Manager has a set of Queues that it can send WorkUnits to.
class Manager:
    def __init__(self, env, num_queues):
        self.env = env
        self.next = 0
        self.queues = [simpy.Store(env) for _ in range(num_queues)]

    # This is an important part of the simulation. How we add work to 
    # queues (if there are multiple queues) matters a lot to the model/sim.
    def add(self, job):
        """Add to the queue with the fewest items."""
        least = math.inf
        shortest_q = None
        q_ndx = 0
        for ndx, q in enumerate(self.queues):
            if len(q.items) < least:
                least = len(q.items)
                q_ndx = ndx
                shortest_q = q
        # Add all the work units to the queue
        for _ in range(job.work_units):
            wu = WorkUnit(job, q_ndx)
            print(f"Adding J[{wu.job.jid}]WU[{wu.wid}] to Queue[{q_ndx}]")
            shortest_q.put(wu)
    
    def do_work(self, queue_ndx):
        # print(f"Doing work from Queue[{queue_ndx}]")
        return self.queues[queue_ndx].get()

# Workers are processes. They run forever (or until we stop the sim).
# Here, workers round-robin the queues in the manager.
class RoundRobinWorker:
    def __init__(self, manager):
        self.manager = manager
        self.current_q = 0
        
    def run(self):
        """Running a WorkUnit means we remove it from the queue.
        Assume all WUs run in unit time."""
        while True:
            # Do work from the next queue
            wu = yield self.manager.do_work(self.current_q)
            wu.job.work(self.manager.env.now)
            print(f"[{self.manager.env.now}] Working J[{wu.job.jid}]WU[{wu.wid}] from Queue[{self.current_q}]")            
            self.current_q = (self.current_q + 1) % len(self.manager.queues)
            yield self.manager.env.timeout(1)
    

        
def simulation(num_queues, num_workers, jobs):
    Job.JID = 0
    WorkUnit.WID = 0
    # Create environment and start processes
    print(f"{num_queues} queue{"s" if num_queues > 1 else ""}, " +
          f"{num_workers} worker{"s" if num_workers > 1 else ""}, " +
          f"{sum([wu.work_units for wu in jobs])} WUs")
    print("--------------")
    
    env = SteppingEnvironment()
    mgr = Manager(env, num_queues)
    
    # Add a request for 1000 benes, where we process
    # the benes in work units of size 10.
    for job in jobs:
        mgr.add(job)
        
    # Create worker processes
    for _ in range(num_workers):
        rrw = RoundRobinWorker(mgr)
        env.process(rrw.run())
    
    env.run()
    
    print(f"Steps[{env.total_steps}] Time[{env.now}]")
    for job in jobs:
        print(f"Job[{job.jid}] Duration[{job.end - job.start + len(jobs)}]")
    print()

if __name__ in "__main__":
    simulation(1, 1, [Job(100, 10)])
    simulation(1, 2, [Job(100, 10)])
    simulation(1, 5, [Job(100, 10)])
    simulation(2, 1, [Job(100, 10), Job(100, 10)])
    simulation(1, 1, [Job(1000, 10), Job(1000, 10)])
    simulation(2, 1, [Job(1000, 10), Job(1000, 10)])
    simulation(2, 2, [Job(1000, 10), Job(1000, 10)])
    simulation(3, 1, [Job(1000, 10), Job(1000, 10), Job(1000, 10)])
    simulation(1, 3, [Job(1000, 10), Job(1000, 10), Job(1000, 10)])
    simulation(8, 16, [Job(1_000_000, 10), Job(10_000, 10), Job(100_000, 10)])