# queue simulator

This is a model for queued work. It attemps to demonstrate a fair but efficient queuing model for environments where the work:

1. **is easily chunked**. It is assumed that all jobs can be broken into multiple work units without any loss of fidelity for the job itself. For example, it might be a query for millions of rows of data where each row needs to be processed in the same way before being written to another database or file. The order of work does not matter, and the work is not differentiated on a per-row basis.
2. **is highly variable**. Some jobs may represent 10M or more work units; others might be 1000 units. So, multiple powers of ten stand between the smallest and largest jobs. We do not want large jobs to starve small jobs or visa versa.
3. **is spikey**. Jobs come in when they come in; large jobs might be consistent (e.g. weekly), but truly, large and small jobs come in without a great deal of consistency.

## running the model

```
pip install -r requirements
python queues.py
```

Or, using Docker:

```
make build
make run
```

This will run a Plotly Dash server that can be accessed at [http://127.0.0.1:8050](http://127.0.0.1:8050).

This simulates 8 queues with 64 workers, where the queues initially have workloads of 50K, 500, 5K, 300, 2K, 100, and 35K units (respectively).

```
realistic = {
    "queues":  ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8"],
    "jobs":    [50_000, 500, 5000, 0, 300, 2000, 100, 35_000],
    "workers": [16, 4, 8, 4, 8, 8, 4, 8]}
```

## non-models

There are several queueing models that do not work well for this kind of workload. FIFO and SJF (shortest-job-first) can easily lead to either 1) starvation of short jobs or 2) starvation of long jobs. Similarly, trying to use priority can easily lead to priority inversion or starvation, where high-priority jobs starve low-priority jobs.

In terms of "non-models," we start by considering a single queue and a single worker.

```                       
     ┌───┬───┬───┬───┐    
  Q1 │   │   │   │   │    
     └───┴───┴───┴───┘    
                   ▲      
                   │      
                   W1     
```

This is a FIFO queue; as new work is added, it goes to the end of the queue.  Hence, a short job landing behind a long job might take a very, very long time to run. That is, a job of 1M work units could end up with several 1K work-unit jobs behind it, and they would *effectively* be starved.

```
     ┌───┐ ┌───┬───┬───┬───┬───┬───┬───┐     
  Q1 │   │ │   │   │   │   │   │   │   │     
     └───┘ └───┴───┴───┴───┴───┴───┴───┘     
                                     ▲       
                                     │       
                                     W1      
```

We could add short jobs to the front, but then enough short jobs could  ultimately starve the long. (This would be akin to treating short jobs as "high priority," and could be considered an example of priority inversion.)

We could add a second queue. As new jobs are added, we always add them to the shortest queue. In this way, long-running jobs might monopolize a single queue, but short jobs can come through on the second queue.

```                                    
       ┌───┬───┬───┬───┬───┬───┬───┐  
    Q1 │   │   │   │   │   │   │   │  
       └───┴───┴───┴───┴───┴───┴───┘  
                                  ▲    
                                  │    
                                  W1   
                                            
       ┌───┐ ┌───┬───┐                      
    Q2 │   │ │   │   │                      
       └───┘ └───┴───┘                      
                   ▲                        
                   │                        
                   W2                       
```


This looks promising, but has the same problems as a single FIFO queue. It is possible that another large job could land, and we now have two queues running large jobs. Small jobs arriving would, again, be starved out by the two large jobs on the two queues.

## addressing throughput

There are two things we can do. 

1. **Round-robin the workers**. Instead of one worker per queue, we instead round-robin the workers. 
2. **"Enough" queues**. We should have enough queues to always have room for a short job. Or, we should always have more queues than we expect to have large jobs.

These two solutions help as follows.

### round-robin workers

In the case of "one worker per queue," we can't see how this helps. But, if we have N queues and M workers, where M = Nx8, we can now see how a large number of workers, migrating through the queues, will both 1) quickly finish small jobs, and 2) focus on large jobs when nothing else is left.

Using just two queues as an example, consider the case where a small job is about to finish:

```
      ┌───┬───┬───┬───┐  
   Q1 │   │   │   │   │  
      └───┴───┴───┴───┘  
                    ▲    
                    │    
                    W1   
                         
      ┌───┐              
   Q2 │   │              
      └───┘              
         ▲               
         │               
         W2              
```

After W2 finishes Q2, we now have one queue with four work units left, and an empty queue. In the subsequent work steps, both W1 and W2 will work on Q1, because there is no other work to round-robin to. Work on the large job now happens at twice the rate it did before.

```
    ┌───┬───┐
 Q1 │   │   │
    └───┴───┘
          ▲  
          │  
          W1 
          W2 
```

### more queues than anticipated large jobs

```
     ┌───┬───┬───┬───┐ 
  Q1 │   │   │   │   │ 
     └───┴───┴───┴───┘ 
                   ▲   
                   │   
                   W1  
     ┌───┐             
  Q2 │   │             
     └───┘             
        ▲              
        │              
        W2             
        W4             
     ┌───┬───┬───┬───┐ 
  Q3 │   │   │   │   │ 
     └───┴───┴───┴───┘ 
                   ▲   
                   │   
                   W3  
                       
                       
  Q4                   
```

If we have *too many* queues, we have created another kind of "priority inversion." That is, even with round-robining, it is possible that many short jobs will fill all of the queues, and the workers will spend most of their time on the short jobs, and only infrequently working the large job. This could be considered either a kind of priority inversion, or "effective starvation" for large jobs on a single queue.

But, by having more queues than we typically anticipate having large jobs, we effectively are leaving one or more queues empty for small jobs. Because workers are not bound to a queue, but instead work round-robin, we know that empty queues have no cost: no workers are "lost" or "idle" on an empty queue.

In this way, if we have N queues and (Nx8) workers, then the following is true. Imagine we have 8 queues (N=8).

1. With jobs in all queues, we will have 64 units of work done on every time step. It will be spread across all of the jobs.
2. As jobs complete, workers will "bunch up." Some queues will see 16 or 32 units of work done in each time step. 
3. When we clear all queues save for long jobs, we will see a 32-to-64x speedup on completion of the large job.

This model has two desirable properties:

1. When a small job lands, it should rapidly complete.
2. When no other small jobs are present, large jobs are worked as rapidly as possible.
3. When more than one job is present, they still leave room for additional small jobs to land and be worked without being starved.

# food for thought

