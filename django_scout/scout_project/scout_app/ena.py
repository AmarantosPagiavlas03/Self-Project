import simpy
import numpy as np
import random
import scipy.stats as st

# Parameters
mu1 = 1.0      # Service rate for machine 1
mu2 = 1.1      # Service rate for machine 2
mu3 = 0.9      # Service rate for machine 3
B1 = 5         # Buffer capacity between machine 1 and 2
B2 = 5         # Buffer capacity between machine 2 and 3

def machine1(env, buffer1, service_rate, stats):
    """Machine 1: produces jobs to buffer1 if there is space."""
    while True:
        # Time to produce a job
        yield env.timeout(np.random.exponential(1 / service_rate))
        # This yield will block if buffer1 is full
        yield buffer1.put(1)
        stats['machine1_count'] += 1

def machine2(env, buffer1, buffer2, service_rate, stats):
    """Machine 2: takes a job from buffer1, processes it, and puts it into buffer2."""
    while True:
        # Wait until there is a job in buffer1
        yield buffer1.get(1)
        yield env.timeout(np.random.exponential(1 / service_rate))
        # Block if buffer2 is full
        yield buffer2.put(1)
        stats['machine2_count'] += 1

def machine3(env, buffer2, service_rate, stats):
    """Machine 3: takes a job from buffer2, processes it, and then the job leaves the system."""
    while True:
        yield buffer2.get(1)
        yield env.timeout(np.random.exponential(1 / service_rate))
        stats['machine3_count'] += 1

def run_replication(total_time, warmup, seed=None):
    """
    Runs one replication of the simulation.
    The simulation runs until total_time. Only counts after the warmup period are used.
    Returns the throughput (jobs per time unit) for each machine.
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    env = simpy.Environment()
    # Create buffers with capacities and initial level 0
    buffer1 = simpy.Container(env, capacity=B1, init=0)
    buffer2 = simpy.Container(env, capacity=B2, init=0)

    # Dictionary to store job counts for each machine
    stats = {'machine1_count': 0, 'machine2_count': 0, 'machine3_count': 0}

    # Start the machine processes
    env.process(machine1(env, buffer1, mu1, stats))
    env.process(machine2(env, buffer1, buffer2, mu2, stats))
    env.process(machine3(env, buffer2, mu3, stats))

    # Record the counts at the end of the warmup period
    warmup_counts = {}
    def record_warmup():
        yield env.timeout(warmup)
        warmup_counts['machine1'] = stats['machine1_count']
        warmup_counts['machine2'] = stats['machine2_count']
        warmup_counts['machine3'] = stats['machine3_count']
    env.process(record_warmup())

    # Run the simulation until total_time
    env.run(until=total_time)

    measurement_time = total_time - warmup
    # Compute throughput for each machine over the measurement period
    t1 = (stats['machine1_count'] - warmup_counts['machine1']) / measurement_time
    t2 = (stats['machine2_count'] - warmup_counts['machine2']) / measurement_time
    t3 = (stats['machine3_count'] - warmup_counts['machine3']) / measurement_time

    return t1, t2, t3

# Simulation parameters for replications
total_time = 100000    # total simulation time (including warmup)
warmup = 10000         # warmup period
replications = 30     # number of independent replications

throughputs1 = []
throughputs2 = []
throughputs3 = []

# Run replications (using different seeds for variability)
for i in range(replications):
    t1, t2, t3 = run_replication(total_time, warmup, seed=i)
    throughputs1.append(t1)
    throughputs2.append(t2)
    throughputs3.append(t3)

# Compute sample means and standard deviations
mean_t1 = np.mean(throughputs1)
mean_t2 = np.mean(throughputs2)
mean_t3 = np.mean(throughputs3)

std_t1 = np.std(throughputs1, ddof=1)
std_t2 = np.std(throughputs2, ddof=1)
std_t3 = np.std(throughputs3, ddof=1)

# Compute 95% confidence intervals using the t-distribution
alpha = 0.05
t_crit = st.t.ppf(1 - alpha/2, replications - 1)

ci_t1 = t_crit * std_t1 / np.sqrt(replications)
ci_t2 = t_crit * std_t2 / np.sqrt(replications)
ci_t3 = t_crit * std_t3 / np.sqrt(replications)

print("Machine 1 Throughput: {:.4f} jobs/unit time (95% CI: [{:.4f}, {:.4f}])".format(mean_t1, mean_t1 - ci_t1, mean_t1 + ci_t1))
print("Machine 2 Throughput: {:.4f} jobs/unit time (95% CI: [{:.4f}, {:.4f}])".format(mean_t2, mean_t2 - ci_t2, mean_t2 + ci_t2))
print("Machine 3 Throughput: {:.4f} jobs/unit time (95% CI: [{:.4f}, {:.4f}])".format(mean_t3, mean_t3 - ci_t3, mean_t3 + ci_t3))
