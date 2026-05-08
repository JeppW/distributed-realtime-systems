import math
import csv
import heapq
from dataclasses import dataclass
from typing import List, Dict
import matplotlib.pyplot as plt
import os
import argparse


@dataclass
class Task:
    id: int
    jitter_input: int
    bcet: int
    wcet: int
    period: int
    deadline: int
    priority: int = 0

    def __lt__(self,other):
        if self.deadline == other.deadline:
            return self.id < other.id
        
        return self.deadline < other.deadline

@dataclass
class Job:
    task_id: int
    arrival: int
    absolute_deadline: int
    remaining: int
    totalExecTime: int


    def __lt__(self, other):
        
        if self.absolute_deadline == other.absolute_deadline:
            return self.task_id < other.task_id
        
        return self.absolute_deadline < other.absolute_deadline


def get_HyperPeriod(tasks):
    return math.lcm(*[task.period for task in tasks])

def get_Jobs_withinHyperPeriod(Tasks, HyperPeriod):
    jobs = []
    sorted_tasks = sorted(Tasks, key=lambda x: x.id)
    for task in sorted_tasks:
        counter = 0
        while(counter * task.period < HyperPeriod):
            arrival_time = counter * task.period
            abs_dl = arrival_time + task.deadline
            jobs.append(Job(task.id,arrival_time,abs_dl,task.wcet,0))
            counter += 1
    return jobs

def check_EDF_scheduability(Ls,tasks):

    for L in Ls:
        processor_demand = sum(math.floor((L + t.period - t.deadline)/t.period) * t.wcet for t in tasks)
        if processor_demand > L:
            return False
    return True


class SchedulabilityAnalysis:
    @staticmethod
    def get_dm_wcrt(tasks: List[Task]) -> Dict[int, int]:
        """Calculates Analytical WCRT for Deadline Monotonic"""
        results = {}
        is_scheduable = True
        sorted_tasks = sorted(tasks) 
        for i, task in enumerate(sorted_tasks):
            r = task.wcet 
            while True:
                interference = sum(math.ceil(r / hp.period) * hp.wcet for hp in sorted_tasks[:i])
                new_r = task.wcet + interference 
                
                if new_r == r:  
                    results[task.id] = r 
                    break

                if new_r > task.deadline: 
                    results[task.id] = new_r
                    is_scheduable = False
                    break
                
                r = new_r
        return results,is_scheduable
    
    
    @staticmethod
    def get_edf_wcrt(tasks,Up):
        """Calculates Analytical WCRT for Earliest Deadline First"""
        is_scheduable = True
        HyperPeriod = get_HyperPeriod(tasks)
        jobs_list = sorted(get_Jobs_withinHyperPeriod(tasks, HyperPeriod), key=lambda job: job.arrival) #sorted by arrival time
        time = 0
        ready_queue = []
        results = {}
        WCRT_perTask = {task.id : [] for task in tasks}

        #before starting anything need to check for feasibility
        if Up == 1:
            Lstar = math.inf
        else:
            Lstar = sum(((t.period - t.deadline)*(t.wcet/t.period)) for t in tasks)/(1- Up)
        #print("Lsart value used for fiding all the L values or the absolutie deadline : " + str(Up))


        L = set()
        reference_value = min(HyperPeriod,Lstar)
        #Find the L's
        for job in jobs_list:
            if job.absolute_deadline <= reference_value:
                L.add(job.absolute_deadline)
        ordered_set = sorted(L)

        if not check_EDF_scheduability(ordered_set,tasks):
            is_scheduable = False


        while(time < HyperPeriod or ready_queue):

            while jobs_list and jobs_list[0].arrival == time:
                heapq.heappush(ready_queue, jobs_list.pop(0))
            
            if ready_queue: ##beause CPU has no tasks to execute at the specific time but the hyperperiod time hasnt passed
                EDF_Job = heapq.heappop(ready_queue)
                EDF_Job.remaining -= 1
                time += 1

                
                if EDF_Job.remaining > 0:
                    heapq.heappush(ready_queue, EDF_Job)
                else:
                    Job_responseTime = time - EDF_Job.arrival
                    WCRT_perTask[EDF_Job.task_id].append(Job_responseTime)

            else:
                if jobs_list:
                    time = jobs_list[0].arrival #jump to the next task arrival time
                else:
                    break #No more work should not be waiting until hyperperiod passes

            
        for key, value in WCRT_perTask.items():
            results[key] = max(value)
        
        return results,is_scheduable


def plot_comparison(tasks, dm_results, edf_results):
    # Prepare the data
    task_ids = [t.id for t in tasks]
    dm_values = [dm_results[t.id] for t in tasks]
    edf_values = [edf_results[t.id] for t in tasks]
    deadlines = [t.deadline for t in tasks]

    plt.figure(figsize=(12, 6))

    # Plot DM Results
    plt.plot(task_ids, dm_values, label='DM WCRT', marker='o', color='blue', linestyle='-')
    
    # Plot EDF Results
    plt.plot(task_ids, edf_values, label='EDF WCRT', marker='s', color='green', linestyle='--')
    
    # Plot Deadlines (The "Failure Line")
    plt.step(task_ids, deadlines, label='Deadline', color='red', where='post', alpha=0.5)

    plt.title('WCRT Comparison: Deadline Monotonic vs. EDF')
    plt.xlabel('Task ID')
    plt.ylabel('Response Time (ms)')
    plt.legend()
    plt.grid(True, which='both', linestyle='--', alpha=0.5)
    
    # Using log sclae 
    plt.yscale('log') 
    
    plt.tight_layout()
    plt.show() 

def get_csv_filepath(dataset, partition, file_num):
    repo_parent = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    roots = {
        "automotive": os.path.join(repo_parent, "TestCases", "automotive-utilDist", "automotive-perDist"),
        "uunifast":   os.path.join(repo_parent, "TestCases", "uunifast-utilDist", "uniform-discrete-perDist"),
    }
    prefixes = {
        "automotive": "automotive",
        "uunifast":   "uniform-discrete",
    }
    base   = roots[dataset]
    prefix = prefixes[dataset]
    return os.path.join(base, "1-core", "25-task", "0-jitter", partition, "tasksets", f"{prefix}_{file_num}.csv")


def main():

    parser = argparse.ArgumentParser(description="Run WCRT Analysis on a Real-Time Task Set.")

    parser.add_argument("--dataset",   default="automotive", choices=["automotive", "uunifast"],
                        help="Dataset to use (default: automotive)")
    parser.add_argument("--partition", default="0.10-util",  choices=[f"{i/100:.2f}-util" for i in range(10, 101, 10)],
                        help="Utilization partition (e.g. 0.10-util)")
    parser.add_argument("--file-num",  type=int, default=1,  choices=range(100),
                        help="File number within the partition (default: 1)")
    parser.add_argument("--file",      type=str, default=None,
                        help="Path to a custom CSV file (overrides --dataset/--partition/--file-num)")

    args = parser.parse_args()

    # Resolve the file path
    if args.file:
        filename = args.file
    else:
        filename = get_csv_filepath(args.dataset, args.partition, args.file_num)

    if not os.path.exists(filename):
        print(f"Error: Could not find the file '{filename}'. Please check the path.")
        return
    
    print(f"\n{'='*60}")
    print(f"Analyzing Task Set: {filename}")
    print(f"{'='*60}\n")

    tasks = []
    
    with open(filename, 'r') as f:
        for r in csv.DictReader(f):
            tasks.append(Task(int(r['TaskID']), int(r['Jitter']), int(r['BCET']), 
                              int(r['WCET']), int(r['Period']), int(r['Deadline'])))
    

    #Check Processor utilization see if if there is feasibility --> Up <= 1.0
    Up = sum((t.wcet/t.period) for t in tasks)

    print(f"Processor Utilization (Up) : {Up:.4f}")

    if Up > 1:
        print("WARNING: Processor is overloaded (Up > 1). Task set cannot be scheduled!")
        return

    print(f"Hyper Period               : {get_HyperPeriod(tasks)}\n")

    print("Calculating Analytical WCRTs (Math)...")
    dm_calculated_wcrt, is_dm_scheduable = SchedulabilityAnalysis.get_dm_wcrt(tasks)
    if not is_dm_scheduable:
        print(" -> RESULT: Task set is NOT schedulable using DM")
    else:
        print(" -> RESULT: Task set IS schedulable using DM")
        


    edf_calculated_wcrt, is_edf_scheduable = SchedulabilityAnalysis.get_edf_wcrt(tasks,Up)
    if not is_edf_scheduable:
        print(" -> RESULT: Task set is NOT schedulable using EDF")
    else:
        print(" -> RESULT: Task set IS schedulable using EDF")
    

    # Output Results
    print("\n+" + "-"*9 + "+" + "-"*11 + "+" + "-"*11 + "+" + "-"*13 + "+" + "-"*13 + "+")
    print(f"| {'Task ID':<7} | {'Period':<9} | {'Deadline':<9} | {'DM WCRT':<11} | {'EDF WCRT':<11} |")
    print("+" + "-"*9 + "+" + "-"*11 + "+" + "-"*11 + "+" + "-"*13 + "+" + "-"*13 + "+")


    for t in tasks:
        calc_dm = dm_calculated_wcrt[t.id]
        calc_edf = edf_calculated_wcrt[t.id]
        
        print(f"| {t.id:<7} | {t.period:<9} | {t.deadline:<9} | {calc_dm:<11} | {calc_edf:<11} |")

    
    print("+" + "-"*9 + "+" + "-"*11 + "+" + "-"*11 + "+" + "-"*13 + "+" + "-"*13 + "+")

    print("\nGenerating Comparison Graph...")
    plot_comparison(tasks, dm_calculated_wcrt, edf_calculated_wcrt)

#Scripts used to calculate all the differen graphs and metrics for Mini-Project 1 

'''
# Scripted used to calculated the number of unschedulable tasksets using DM algorithm 
def main():
    # Path to your folder containing the CSVs
    folder_path = 'output/uunifast-utilDist/uniform-discrete-perDist/1-core/25-task/0-jitter/1.00-util/tasksets/'
    csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
    
    print(f"Scanning {len(csv_files)} files for DM feasibility...\n")
    print(f"{'Filename':<30} | {'Status':<10} | {'Reason'}")
    print("-" * 70)

    failed_count = 0
    for file_path in csv_files:
        tasks = []
        filename = os.path.basename(file_path)
        
        try:
            with open(file_path, 'r') as f:
                for r in csv.DictReader(f):
                    tasks.append(Task(int(r['TaskID']), int(r['Jitter']), int(r['BCET']), 
                              int(r['WCET']), int(r['Period']), int(r['Deadline'])))
            Up = sum((t.wcet/t.period) for t in tasks)
            #print("Processor Utilization: " + str(Up))

            if Up > 1:
                raise Exception("Processor is overloaded and so task set cannot be scheduled!")
            
            is_feasible = SchedulabilityAnalysis.get_dm_wcrt(tasks)
            
            
            if not is_feasible:
                reason = "Not DM schedulable"
                print(f"{filename:<30} | FAIL       | {reason}")
                failed_count += 1
            else:
                # Optional: print passed files too, or just keep it quiet
                # print(f"{filename:<30} | PASS       | -")
                pass

        except Exception as e:
            print(f"{filename:<30} | ERROR      | {str(e)}")

    print("-" * 70)
    print(f"Total Files: {len(csv_files)} | Total DM Failures: {failed_count}")


# Scripted used to calculated the number of unschedulable tasksets using EDF algorithm 
def main():

    # Path to your folder containing the CSVs
    folder_path = 'output/automotive-utilDist/automotive-perDist/1-core/25-task/0-jitter/0.10-util/tasksets/'
    csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
    
    print(f"Scanning {len(csv_files)} files for EDF feasibility...\n")
    print(f"{'Filename':<30} | {'Status':<10} | {'Reason'}")
    print("-" * 70)

    failed_count = 0
    for file_path in csv_files:
        tasks = []
        filename = os.path.basename(file_path)
        
        try:
            with open(file_path, 'r') as f:
                for r in csv.DictReader(f):
                    tasks.append(Task(int(r['TaskID']), int(r['Jitter']), int(r['BCET']), 
                              int(r['WCET']), int(r['Period']), int(r['Deadline'])))
            Up = sum((t.wcet/t.period) for t in tasks)
            #print("Processor Utilization: " + str(Up))

            if Up > 1:
                raise Exception("Processor is overloaded and so task set cannot be scheduled!")
            
            is_feasible = SchedulabilityAnalysis.get_edf_wcrt(tasks,Up)
            
            
            if not is_feasible:
                reason = "Not EDF schedulable"
                print(f"{filename:<30} | FAIL       | {reason}")
                failed_count += 1
            else:
                # Optional: print passed files too, or just keep it quiet
                print(f"{filename:<30} | PASS       | -")
                pass

        except Exception as e:
            print(f"{filename:<30} | ERROR      | {str(e)}")

    print("-" * 70)
    print(f"Total Files: {len(csv_files)} | Total EDF Failures: {failed_count}")

#Script used to make the large-scale analysis to find how many task sets are schedulable using both DM and EDF for each Up directory: 0.10, 0.20, 0.30...
def main():
    folder_path = 'output/uunifast-utilDist/uniform-discrete-perDist/1-core/25-task/0-jitter/0.10-util/tasksets/'
    csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
    
    print(f"Scanning {len(csv_files)} files...\n")

    valid_count = 0      # Total files where Up <= 1
    dm_pass_count = 0    # Total files that pass DM
    edf_pass_count = 0   # Total files that pass EDF

    for file_path in csv_files:
        tasks = []
        try:
            with open(file_path, 'r') as f:
                for r in csv.DictReader(f):
                    tasks.append(Task(int(r['TaskID']), int(r['Jitter']), int(r['BCET']), 
                              int(r['WCET']), int(r['Period']), int(r['Deadline'])))
            
            Up = sum((t.wcet/t.period) for t in tasks)

            valid_count += 1
            # If Up > 1, we just skip it entirely. It doesn't count as a "valid" task set.
            if Up > 1:
                continue
            
            
        
            dm_calculated_wcrt, is_dm_scheduable = SchedulabilityAnalysis.get_dm_wcrt(tasks)
            if is_dm_scheduable:
                dm_pass_count += 1
                
            
            # Check EDF Schedulability
            edf_calculated_wcrt, is_edf_scheduable = SchedulabilityAnalysis.get_edf_wcrt(tasks,Up)
            if is_edf_scheduable:
                edf_pass_count += 1

        except Exception as e:
            print(f"Error reading file: {str(e)}")

    # Calculate the fractions!
    if valid_count > 0:
        dm_fraction = dm_pass_count / valid_count
        edf_fraction = edf_pass_count / valid_count
    else:
        dm_fraction = edf_fraction = 0

    print("-" * 50)
    print(f"Total Valid Files (Up <= 1.0): {valid_count}")
    print(f"DM Schedulable:  {dm_pass_count} out of {valid_count} ({dm_fraction:.2%})")
    print(f"EDF Schedulable: {edf_pass_count} out of {valid_count} ({edf_fraction:.2%})")
    print("-" * 50)

    
#Script used to plot the entire dtaset WCRT distribution
def main():
    # Base folder path for the dataset
    base_folder = 'output/uunifast-utilDist/uniform-discrete-perDist/1-core/25-task/0-jitter/'
    
    util_levels = ['0.10', '0.20', '0.30', '0.40', '0.50', '0.60', '0.70', '0.80', '0.90', '1.00']
    
    # We need a list of lists. Each sub-list will hold ALL the normalized WCRTs for that utilization level.
    all_dm_wcrts = []
    all_edf_wcrts = []

    print("Crunching WCRT distributions for the ENTIRE dataset...")

    for util in util_levels:
        folder_path = os.path.join(base_folder, f"{util}-util/tasksets/")
        csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
        
        current_util_dm = []
        current_util_edf = []

        for file_path in csv_files:
            tasks = []
            try:
                with open(file_path, 'r') as f:
                    for r in csv.DictReader(f):
                        tasks.append(Task(int(r['TaskID']), int(r['Jitter']), int(r['BCET']), 
                                  int(r['WCET']), int(r['Period']), int(r['Deadline'])))
                
                Up = sum((t.wcet/t.period) for t in tasks)

                # Skip invalid overloaded files
                if Up > 1:
                    continue

                dm_calculated_wcrt, is_dm_scheduable = SchedulabilityAnalysis.get_dm_wcrt(tasks)
                edf_calculated_wcrt, is_edf_scheduable = SchedulabilityAnalysis.get_edf_wcrt(tasks,Up)
                
                # Normalize (R_i / D_i) and add them to the current utilization's bucket
                for i, task in enumerate(tasks):
                    current_util_dm.append(dm_calculated_wcrt[i] / task.deadline)
                    current_util_edf.append(edf_calculated_wcrt[i] / task.deadline)

            except Exception:
                pass
        
        # Append the bucket of data to our master lists
        all_dm_wcrts.append(current_util_dm)
        all_edf_wcrts.append(current_util_edf)
        print(f"Processed {util} utilization...")

    print("Data collection complete. Generating Grouped Box Plot...")

    # --- GRAPHING LOGIC ---
    plt.figure(figsize=(12, 6)) # Made it wider to fit all 10 levels beautifully

    # Set up the X-axis positions
    ticks = list(range(1, len(util_levels) + 1))
    pos_dm = [t - 0.18 for t in ticks]  # Shift DM boxes slightly left
    pos_edf = [t + 0.18 for t in ticks] # Shift EDF boxes slightly right

    # Draw DM Boxplots
    plt.boxplot(all_dm_wcrts, positions=pos_dm, widths=0.3, patch_artist=True,
                whis=[0, 100],
                showfliers=False,
                boxprops=dict(facecolor='lightblue', color='blue'),
                medianprops=dict(color='darkblue', linewidth=2))

    # Draw EDF Boxplots
    plt.boxplot(all_edf_wcrts, positions=pos_edf, widths=0.3, patch_artist=True,
                whis=[0, 100],
                showfliers=False,
                boxprops=dict(facecolor='lightcoral', color='red'),
                medianprops=dict(color='darkred', linewidth=2))

    # The critical "Deadline Boundary" line at 1.0
    plt.axhline(y=1.0, color='black', linestyle='--', linewidth=2, label='Deadline Miss Threshold ($R_i / D_i = 1.0$)')

    # Formatting the axes and legend
    plt.xticks(ticks, util_levels)
    plt.xlabel('Processor Utilization ($U_p$)', fontsize=12)
    plt.ylabel('Normalized WCRT ($R_i / D_i$)', fontsize=12)
    plt.title('Evolution of WCRT Distributions Across Utilization Levels (UUniFast Dataset)', fontsize=14)
    plt.grid(True, linestyle=':', alpha=0.7, axis='y')
    
    # Custom legend since boxplot legends are tricky in matplotlib
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='lightblue', edgecolor='blue', label='Deadline Monotonic (DM)'),
        Patch(facecolor='lightcoral', edgecolor='red', label='Earliest Deadline First (EDF)'),
        plt.Line2D([0], [0], color='black', linestyle='--', linewidth=2, label='Deadline Miss Threshold')
    ]
    plt.legend(handles=legend_elements, loc='upper left')

    # Save and show
    plt.savefig('full_dataset_wcrt_distribution.png', dpi=300, bbox_inches='tight')
    print("Graph saved as 'full_dataset_wcrt_distribution.png'!")
    plt.show()
'''

if __name__ == "__main__":
    main()


