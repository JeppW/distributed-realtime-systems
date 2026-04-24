import math
import csv
import random
import heapq
from dataclasses import dataclass
from typing import List, Dict, Optional
import matplotlib.pyplot as plt

import os
import glob




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
    
    # Use log scale if your deadlines vary from 100 to 1,000,000
    plt.yscale('log') 
    
    plt.tight_layout()
    plt.show() 

def main():
    tasks = []
    # Ensure you have your 'task-set-example.csv' in the same directory
    with open('../output/automotive-utilDist/automotive-perDist/1-core/25-task/0-jitter/0.10-util/tasksets/automotive_7.csv', 'r') as f:
        for r in csv.DictReader(f):
            tasks.append(Task(int(r['TaskID']), int(r['Jitter']), int(r['BCET']), 
                              int(r['WCET']), int(r['Period']), int(r['Deadline'])))
    
    #Check Processor utilization see if if there is feasibility

    Up = sum((t.wcet/t.period) for t in tasks)
    print("Processor Utilization: " + str(Up))

    if Up > 1:
        print("Processor is overloaded and so task set cannot be scheduled!")
        return

    print("Hyper Period: " + str(get_HyperPeriod(tasks)))

    print("Calculating Analytical WCRTs (Math)...")
    dm_calculated_wcrt, is_dm_scheduable = SchedulabilityAnalysis.get_dm_wcrt(tasks)
    if not is_dm_scheduable:
        print("Tasks not shedulable using DM ")
        


    edf_calculated_wcrt, is_edf_scheduable = SchedulabilityAnalysis.get_edf_wcrt(tasks,Up)
    if not is_edf_scheduable:
        print("Tasks not shedulable using EDF ")
    

    # Output Results
    print(f"\n{'Task ID':<8} | {'Period':<9} | {'Deadline':<9} | {'WCRT - DM':<9} | {'WCRT - EDF':<9}")
    print("-" * 60)


    for t in tasks:
        calc_dm = dm_calculated_wcrt[t.id]
        calc_edf = edf_calculated_wcrt[t.id]
        
        print(f"{t.id:<8} | {t.period:<9} | {t.deadline:<9} | {calc_dm:<9} | {calc_edf:<9}")

    
    print("\nGenerating Comparison Graph...")
    plot_comparison(tasks, dm_calculated_wcrt, edf_calculated_wcrt)


'''
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
'''
if __name__ == "__main__":
    main()


