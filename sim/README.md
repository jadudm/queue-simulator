# caveat

> This place is not a place of honor... no highly esteemed deed is commemorated here... nothing valued is here.

<div style="text-align: right;"><a href="https://en.wikipedia.org/wiki/Long-term_nuclear_waste_warning_messages">Long-term nuclear waste warning messages</a></div>

<br/>

This repository neither pretends nor aspires to be a work of art. It does the thing it does, mostly.

# exploring job processing systems

Designing, developing, testing, and maintaining job processing systems is expensive in time. Getting the *model* wrong means that the implementation, no matter how good, will always be fundamentally unfit for purpose. A job processing system that is unfit for purpose leads to disruptions of user experience, either as soft failures (where a system slows down or performs poorly) or hard failures (where the system crashes or loses data). All of these are considered incidents, and carry expensive diagnostic and recovery processes with them. 

("Expensive" means "an entire team is typically stopped and focused on resolving an incident, sometimes for days, while a root cause is ascertained, and the full impact to users is described.")

Because we want to avoid failures in our production systems, a good design process considers the system's needs under light, average, and heavy/extreme load, and we evaluate the model's behavior under these conditions. We can reason about these things (and even formally prove properties of our systems, if we're feeling feisty), but we can also [simulate](https://greenteapress.com/wp/modsimpy/) them. This is often easier, faster, and perhaps more appropriate in an agile, applied context. 

## abstractions FTW

Should we use one queue or two? One worker or two? These questions can be evaluated *in the abstract*. The amount of time it takes to run a query or store the result will be the same regardless of the model. Therefore, we can *reason* about the performance of our models without ever writing a line of code. Assume we have two jobs we want to complete, each of which contains two units of work:

![Four scenarios with workers and queues](scenarios.png)

1. **One worker, one queue**: If we have four units of work on the queue, it will take four units of time to complete all the jobs.
2. **Two workers, one queue**: With four units of work, the entire queue will empty in two units of time: more workers means the work gets done faster.
3. **One worker, two queues**: This does not change the amount of time it takes to complete all of the work, but it does impact the perception of how long it takes to complete individual jobs. If we put one job on each queue, the owners of those jobs will think it took *more* time to complete the work; this configuration appears *slower* than other configurations.
4. **Two workers, two queues**: All four units of work complete in two units of time, *and* the owners of the work believe they were prioritized, because each job completed in two units of time.

## modeling systems

It is possible to model job processing systems in a small number of lines of code. This makes it possible to experiment with *models* as opposed to *implementations*. This allows us to propose a model, and then ask questions about fundamental properties of job processing systems, like **fairness**, **throughput**, **utilization rate**, **average wait time in queue**, **average wait time in system**, 

1. How does the system perform if small jobs come in infrequently?
2. How does the system perform if small and large jobs come in regularly?
   1. What will the user's experience be if they own the small jobs? 
   2. The large jobs?
3. How does the system perform if someone accidentally submits the same job 10,000 times?
   1. What if it is a small job?
   2. Large?
4. If the model scales dynamically, what are the properties of the system...
   1. when it is contracted? 
   2. When it is at it's maximum expansion?

None of these questions require us to actually *build* the system in question. A good model lets us rapidly develop test scenarios (ideally grounded in anticipated and extreme cases of real-world user behavior), test those scenarios, and evaluate how our model will perform under those conditions. If the model performs poorly... *any system we build based on that model will also perform poorly*.

## homework

This folder contains one hacked-together example of a system of queues and workers. It is based on [SimPy](https://simpy.readthedocs.io/en/latest/), a discrete-event simulation framework. This means it does not concern itself with real notions of time, but instead models the world as a series of abstract events. We can then count the number of clock ticks (also events) that it takes to work through a simulation, and in doing so, evaluate system behavior and performance in a consistent, (possibly) repeatable/deterministic manner, even if it is abstracted from the realities of the world.

### set up the environment

I usually like to containerize applications. I skimped.

The makefile creates a venv and installs requirements.

```bash
> make setup
> source venv/bin/activate
> python sim1.py
```

### explore the simulations

There are 9 simulations pre-configured. To run them:

```bash
python sim1.py <simulation number> <is-noisy?>
```

The noisy parameter determines how much printing happens. "t" or "true" will print more detail; "f" or "false" will just print the results.

```bash
python sim1.py 1 t
```

runs the first simulation.

#### simulations

1. 1 queue, 1 worker, 10 work units
2. 1q2w 10WU (abbreviating 1 queue, 2 workers, 10 work units)
3. 1q5w 10WU
4. 2q1w, 10WU per queue
5. 1q1w, two jobs of 10WU each
6. 2q1w, two jobs of 10WU each
7. 2q2w, two jobs of 10WU each
8. 3q1w, three jobs of 10WU each
9. 1q, 3w, three jobs of 100,00 WU, 1000 WU, and 10000 WU

Run each simulation. For each simulation, consider...

1. What is the total time?
2. How long does each job take?
3. If you change the number of workers, how does that impact the simulation?
4. If you change the number of queues?
5. ...

And, for double-extra bonus fun: can you set up a simulation that starts to look like your system? (This initial simulation does not (yet) have the ability to inject work into the queues at specific times... that would let us model more authentic scenarios.)
