from dash import Dash, html, ctx, dcc, callback, Output, Input
import plotly.express as px

app = Dash()

# Requires Dash 2.17.0 or later
app.layout = [
    html.H1(
        children="Queue simulator",
        style={
            "textAlign": "center",
            "color": "black",
            "font-family": "sans-serif"
        },
    ),
    html.Button("Add jobs", id="button_jobs"),
    html.Button("Add workers", id="button_workers"),
    html.Button("Add queue", id="button_queue"),
    dcc.Input(
        id="input_jobs",
        value=1000,
        type="number",
        placeholder="jobs to add",
        min=1,
        max=20_000_000,
        step=1,
    ),
    dcc.Input(
        id="input_workers",
        value=1,
        type="number",
        placeholder="workers to add",
        min=1,
        max=128,
        step=1,
    ),
    dcc.Graph(id="graph-content"),
    dcc.Interval(
        id="ticker",
        # interval is milliseconds between ticks
        # In reality, this might be closer to 2ms/row.
        interval=25,
        n_intervals=0,
    ),
]

# GLOBALS
# The model maniupates state via globals.
# This is the number of jobs added when the jobs button is mashed.
# It gets updated when the input field for jobs is changed.
JOBS_TO_ADD = 1000
# Likewise, we add workers one at a time on button press, unless
# the input field is changed. This holds the value of that field.
WORKERS_TO_ADD = 1


# MODELS
# The FIFO model is a single queue with a single worker
fifo = {"queues": ["Q1"], "jobs": [500], "workers": [1]}

# The FIFO2 model has two queues, but still shows how the first jobs in
# are the first jobs out.
fifo2 = {"queues": ["Q1", "Q2"], "jobs": [500, 500], "workers": [1, 0]}

# SJF shows that the shortest jobs get done first. If a 1000-unit job
# is added, it will land on queue #2, and both the 500- and 1000-unit job
# will finish before the 5000 unit job. However, that job is not starved.
sjf = {"queues": ["Q1", "Q2"], "jobs": [5000, 500], "workers": [1, 1]}

# REALISTIC is a four-queue model that allows for demonstrating what it looks
# like to have 1-2 extremely large jobs and a number of smaller and medium jobs
# with enough queues to balance the work out.
realistic = {"queues":  ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7",  "Q8"],
             "jobs":    [50_000, 500, 5000, 0, 300, 2000, 100, 35_000],
             "workers": [16,   4,    8, 4,   8,    8,   4,      8]}


model = realistic
max_y = max(model["jobs"])


def rotate(l, n):
    return l[n:] + l[:n]


def update():
    global max_y, model
    new_max = max(model["jobs"])
    if new_max > max_y:
        max_y = new_max

    # The model is simulating two things:
    # A worker has no queue affinity. They round-robin after every unit of work.
    # So, a worker works [ Q1, Q2, Q1, Q2, ...]. In this way, a single worker with two queues
    # guarantees that both queues are serviced.
    # This is modeled by rotating the worker list, because workers have afinity based on their
    # index in the worker list.
    model["workers"] = rotate(model["workers"], 1)

    # To simulate work units, we take each worker location and subtract that
    # much work from the queue at the same index. However, if there is no work
    # to be done, then the workers go round-robining forward, looking for something to do.
    # They'll wrap all the way around in an attempt to find work.
    # In reality, when all the queues are empty, they might do this one every second or so.
    for ndx in range(len(model["jobs"])):
        for next in range(len(model["jobs"])):
            new_ndx = (ndx + next) % len(model["jobs"])
            if model["jobs"][new_ndx] > 0:
                model["jobs"][new_ndx] = (
                    model["jobs"][new_ndx] - model["workers"][ndx]
                )
                break

    return model

# Takes the value stored in the WORKERS_TO_ADD value and adds them to
# the zeroth queue. Because workers round-robin, so it does not matter
# if we start them at 0 or somewhere else.


def add_workers(value):
    new_workers = [model["workers"][0] + value] + model["workers"][1:]
    model["workers"] = new_workers
    return model

# There's no real-world example where we casually/dynamically grow the number
# of queues. (Well, there might be.) The number of queues is a complex value to
# dynamically adust. With one queue, we're FIFO. With two, a pair of large jobs starve
# all incoming small jobs. With too many queues, then small jobs could *effectively*
# starve a long-running job. The number of jobs should likely be based on an understanding
# of loads, and the throughput of jobs (not work units) should be evaluated over time.
# Adding them dynamically is mostly a benefit of simulation...


def add_queue():
    global model
    model["queues"].append("Q" + str(len(model["queues"]) + 1))
    model["jobs"].append(0)
    model["workers"].append(1)

# Add work. Looks for the smallest queue, and adds it there.


def add_jobs(n):
    global model
    min_jobs = min(map(lambda q: q, model["jobs"]))
    print(min_jobs, model["jobs"])
    for ndx in range(len(model["jobs"])):
        if model["jobs"][ndx] == min_jobs:
            model["jobs"][ndx] = model["jobs"][ndx] + n
            break

# Draw the chart.


def draw_chart(m):
    return px.bar(m, x="queues", y="jobs", range_y=[0, max_y])

# Utility


def total_jobs(m):
    return sum(model["jobs"])


@callback(
    Output("graph-content", "figure"),
    Input("ticker", "n_intervals"),
    Input("input_jobs", "value"),
    Input("input_workers", "value"),
    Input("button_jobs", "n_clicks"),
    Input("button_workers", "n_clicks"),
    Input("button_queue", "n_clicks"),
    prevent_initial_call=True,
)
def update_graph_live(
    ticks, input_jobs, input_workers, button_jobs, button_workers, button_queue
):
    triggered_id = ctx.triggered_id
    global WORKERS_TO_ADD, JOBS_TO_ADD
    if triggered_id == "ticker":
        next = update()
        return draw_chart(next)
    # Buttons
    elif triggered_id == "button_jobs":
        add_jobs(JOBS_TO_ADD)
        print(model)
        return draw_chart(update())
    elif triggered_id == "button_workers":
        add_workers(WORKERS_TO_ADD)
        print(model)
        return draw_chart(update())
    elif triggered_id == "button_queue":
        add_queue()
        print(model)
        return draw_chart(update())
    # Inputs
    elif triggered_id == "input_workers":
        WORKERS_TO_ADD = input_workers
        return draw_chart(update())
    elif triggered_id == "input_jobs":
        JOBS_TO_ADD = input_jobs
        return draw_chart(update())


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0")
