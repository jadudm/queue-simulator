import simpy
import math
import random
import sys


class SteppingEnvironment(simpy.Environment):
    # Creating a stepping environment lets me count
    # the number of time steps in the simulation, making it
    # possible to compare the amount of time different models
    # require to execute.
    def __init__(self, initial_time=0):
        super().__init__(initial_time)
        self.total_steps = 0

    def reset(self):
        self.total_steps = 0

    def step(self):
        super().step()
        self.total_steps += 1


class Job:
    # Elch.
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
    # This abstraction allows me to track how long a job takes, which
    # will be dependent on the model being used.
    def work(self, timestep):
        if self.start < 0:
            self.start = timestep
        self.worked += 1
        if self.worked == self.work_units:
            self.end = timestep


class WorkUnit:
    # Also elch.
    WID = 0

    def __init__(self, job, queue_index):
        self.job = job
        self.wid = WorkUnit.WID
        WorkUnit.WID += 1
        self.queue_index = queue_index

# A Manager has a set of Queues that it can send WorkUnits to.
# If I want to change the structure of the system as a whole,
# the Manager is likely going to need to change.

# This may be an abuse of the SimPy framework... I was moving
# kinda fast.


class Manager:
    def __init__(self, env, num_queues, noisy=False):
        self.env = env
        self.next = 0
        # I'm simulating an environment with multiple queues.
        # This lets me set them up as simpy Store objects, which
        # have the machinery inside to manage the contents and
        # play nice with the simulation as a whole.
        self.queues = [simpy.Store(env, math.inf) for _ in range(num_queues)]
        self.noisy = noisy

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
            if self.noisy:
                print(f"Adding J[{wu.job.jid}]WU[{wu.wid}] to Queue[{q_ndx}]")
            shortest_q.put(wu)

    def do_work(self, queue_ndx):
        # print(f"Doing work from Queue[{queue_ndx}]")
        return self.queues[queue_ndx].get()

# Workers are processes. They run forever (or until we stop the sim).
# Here, workers round-robin the queues in the manager.


class RoundRobinWorker:
    def __init__(self, manager, noisy=False):
        self.manager = manager
        self.current_q = 0
        self.noisy = noisy

    def run(self):
        """Running a WorkUnit means we remove it from the queue.
        Assume all WUs run in unit time."""
        while True:
            # Do work from the next queue
            wu = yield self.manager.do_work(self.current_q)
            wu.job.work(self.manager.env.now)
            if self.noisy:
                print(
                    f"[{self.manager.env.now}] Working J[{wu.job.jid}]WU[{wu.wid}] from Queue[{self.current_q}]")
            self.current_q = (self.current_q + 1) % len(self.manager.queues)
            yield self.manager.env.timeout(1)


def simulation(num_queues, num_workers, jobs, noisy=False):
    Job.JID = 0
    WorkUnit.WID = 0
    # Create environment and start processes
    print(f"{num_queues} queue{"s" if num_queues > 1 else ""}, " +
          f"{num_workers} worker{"s" if num_workers > 1 else ""}, " +
          f"{sum([wu.work_units for wu in jobs])} WUs")
    print("--------------")

    env = SteppingEnvironment()
    mgr = Manager(env, num_queues, noisy=noisy)

    # Add a request for 1000 benes, where we process
    # the benes in work units of size 10.
    for job in jobs:
        mgr.add(job)

    # Create worker processes
    for _ in range(num_workers):
        rrw = RoundRobinWorker(mgr, noisy=noisy)
        env.process(rrw.run())

    env.run()

    if noisy:
        print()
    print(f"Simulation time[{env.now}]")
    for job in jobs:
        print(f"Job[{job.jid}] Duration[{job.end - job.start + len(jobs)}]")
    print()

# A job defines the number of benes and the number of benes per work unit.
# Since we're really just interested in WUs (work units), we can pre-define
# a few jobs.


def WU10(): return Job(100, 10)
def WU100(): return Job(1000, 10)
def WU1000(): return Job(10_000, 10)
def WU10000(): return Job(100_000, 10)
def WU100000(): return Job(1_000_000, 10)


if __name__ in "__main__":
    simulation_number = sys.argv[1]
    noisy = sys.argv[2]

    simulation_number = int(simulation_number)

    if "t" in noisy.lower():
        noisy = True
    else:
        noisy = False

    # Q1
    # The first simulation is one queue and one worker.
    # How many time steps do you expect it to take in order
    # to complete all 10 units of work, assuming a worker does
    # one unit of work per clock step?
    match simulation_number:
        case 1:
            simulation(1, 1, [WU10()], noisy=noisy)
        case 2:
            simulation(1, 2, [WU10()], noisy=noisy)
        case 3:
            simulation(1, 5, [WU10()], noisy=noisy)
        case 4:
            simulation(2, 1, [WU10(), WU10()], noisy=noisy)
        case 5:
            simulation(1, 1, [WU10(), WU10()], noisy=noisy)
        case 6:
            simulation(2, 1, [WU10(), WU10()], noisy=noisy)
        case 7:
            simulation(2, 2, [WU10(), WU10()], noisy=noisy)
        case 8:
            simulation(3, 1, [WU10(), WU10(), WU10()], noisy=noisy)
        case 9:
            simulation(1, 3, [WU100000(), WU1000(), WU10000()], noisy=noisy)
