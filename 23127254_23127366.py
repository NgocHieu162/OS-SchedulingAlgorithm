import sys
from queue import Queue, PriorityQueue
from dataclasses import dataclass

R1 = Queue()
R2 = Queue()

## Input
@dataclass
class Process:
    ID: int
    AT: int
    CPU1: int
    IO1: str
    CPU2: int
    IO2: str
    last_executed_time: int
    IO_time: int
    remaining_time: int
    completion_time: int
    
    def __lt__(self, other):
        return (self.remaining_time, self.last_executed_time, self.ID) < (other.remaining_time, other.last_executed_time, other.ID)

process_list = []

## Output
scheduling_process = []
R1_process = []
R2_process = []
TT = [0] * 4
WT = [0] * 4

################ Utility function 
def read_file(input):
    global process_list
    quantum_time = 0
    with open(input, "r") as f:
        algorithm = int(f.readline().strip())
        if algorithm == 2: 
            quantum_time = int(f.readline().strip())
        np = int(f.readline().strip())  #number of processes
        for i in range(np):
            IO_time = 0
            temp = f.readline().strip().split()
            AT = int(temp[0])
            CPU1 = int(temp[1])
            if len(temp) > 2:
                IO1 = temp[2]
                IO_time += 1
            else: IO1 = "-1"
            CPU2 = int(temp[3]) if len(temp) > 3 else -1   
            if len(temp) > 4:
                IO2 = temp[4]
                IO_time += 1
            else: IO2 = "-1"
            process_list.append(Process(i + 1, AT, CPU1, IO1, CPU2, IO2, 0, IO_time, CPU1, 0))
                                    #ID, AT, CPU1, IO1, CPU2, IO2, last_executed_time, IO_Time, remaning_time, completion_time
    return algorithm, quantum_time, np

def AddingProcess(queue, time, ReEnterProcess = None):
    enterRQ_list = []
    queue_list = list(queue.queue)
    
    for p in process_list:
        if time == p.AT:
            enterRQ_list.append(p)
            
    if enterRQ_list:
        enterRQ_list.sort(key=lambda p: (p.last_executed_time, p.ID))
        for p in enterRQ_list:
            if p not in queue_list:
                queue.put(p)
                queue_list.append(p)
                
    if ReEnterProcess:
        for p in ReEnterProcess:
            if p not in queue_list:
                queue.put(p)
                queue_list.append(p)

def AddingProcessPQ(pqueue, time, ReEnterProcess = None):
    enterRQ_list = []
    pqueue_list = list(pqueue.queue)
    for p in process_list:
        if time == p.AT:
            enterRQ_list.append(p)
    
    if ReEnterProcess:
        for p in ReEnterProcess:
            enterRQ_list.append(p) 
               
    if enterRQ_list:
        enterRQ_list.sort(key=lambda p: (p.last_executed_time, p.ID))
        for process in enterRQ_list:
            if not any(p[1] == process for p in pqueue_list):
                pqueue.put((process.remaining_time, process))       
                  
def rProcess(time):
    global R1, R2
    ReEnterProcess = []
    ReEnterTime = None
    if not R1.empty():
        r1_process = R1.queue[0]
        if r1_process[0].IO_time != 0:
            r1_process[1] -= 1 # thời gian IO giảm 1
            R1_process.append(r1_process[0].ID)
            
            if r1_process[1] == 0:
                r1_process = R1.get()[0]
                r1_process.completion_time = time + 1
                if r1_process.CPU2 > 0:
                    r1_process.remaining_time = r1_process.CPU2
                    ReEnterProcess.append(r1_process)
                    ReEnterTime = time + 1
                r1_process.IO_time -= 1
        else: R1.get()
    else: 
        R1_process.append("_")
    
    if not R2.empty():
        r2_process = R2.queue[0]
        if r2_process[0].IO_time != 0:
            r2_process[1] -= 1 # thời gian IO giảm 1
            R2_process.append(r2_process[0].ID)
            
            if r2_process[1] == 0:
                r2_process = R2.get()[0]
                r2_process.completion_time = time + 1
                if r2_process.CPU2 > 0:
                    r2_process.remaining_time = r2_process.CPU2
                    ReEnterProcess.append(r2_process)
                    ReEnterTime = time + 1
                r2_process.IO_time -= 1
        else: R2.get()
    else: 
        R2_process.append("_")    
        
    return ReEnterProcess, ReEnterTime

def calcTT(np):
    global TT 
    for i in range(np):
        TT[i] = process_list[i].completion_time - process_list[i].AT

def calcWT_Queue(q):
    global WT
    queue_list = list(q.queue)
    for p in queue_list:
        WT[p.ID - 1] += 1
        
def calcWT_PQueue(pq):
    global WT
    queue_list = list(pq.queue)
    for p in queue_list:
        WT[p[1].ID - 1] += 1
        
        
def write_file(output, np):
    with open(output, "w") as f:
        f.write(" ".join(scheduling_process) + "\n")  
        f.write(" ".join(map(str, R1_process)) + "\n")
        f.write(" ".join(map(str,R2_process)) + "\n")
        f.write(" ".join(map(str,TT[:np])) + "\n")
        f.write(" ".join(map(str, WT[:np])) + "\n")
################

################ FCFS      
def executeCPU_FCFS(q, time, curr_Process, cpu_attr, io_attr, ReEnterProcess, ReEnterTime):
    CPU = getattr(curr_Process, cpu_attr)

    for i in range(CPU):
        time += 1
        if ReEnterProcess is not None and time == ReEnterTime:
            AddingProcess(q, time, ReEnterProcess)
        elif i !=  CPU - 1: AddingProcess(q, time)
        
        if i != CPU - 1:
            calcWT_Queue(q)
            ReEnterProcess, ReEnterTime = rProcess(time)
            
    curr_Process.last_executed_time = time

    io_data = getattr(curr_Process, io_attr)
    if io_data != "-1":
        io_time = int(io_data.split("(")[0])
        if io_data[-2] == '1':
            R1.put([curr_Process, io_time])
        else:
            R2.put([curr_Process, io_time])
    else: curr_Process.completion_time = time
    
    setattr(curr_Process, cpu_attr, -1)  # Đánh dấu là đã xong
    return CPU 
            
def fcfs(np):
    global R1, R2, scheduling_process
    time = 0
    completed = 0
    q = Queue()
    while completed < np or not R1.empty() or not R2.empty():
        ReEnterProcess, ReEnterTime = rProcess(time)
        AddingProcess(q, time)
        if not q.empty():
            curr_Process = q.get()
            calcWT_Queue(q)
            
            if curr_Process.CPU1 > 0:
                temp = executeCPU_FCFS(q, time, curr_Process, "CPU1", "IO1", ReEnterProcess, ReEnterTime)
            elif curr_Process.CPU2 > 0:
                temp = executeCPU_FCFS(q, time, curr_Process, "CPU2", "IO2", ReEnterProcess, ReEnterTime)
            time += temp   
            
            if curr_Process.CPU1 == -1 and curr_Process.CPU2 == -1: #nếu xong
                completed += 1
                
            scheduling_process.extend(str(curr_Process.ID) * temp)
        else:
            scheduling_process.append("_")  # Nếu hiện tại không có quá trình nào thì append _
            time += 1 
            if ReEnterProcess is not None and time == ReEnterTime:
                AddingProcess(q, time, ReEnterProcess)       
    calcTT(np)
################

################ RoundRobin
def executeCPU_RR(q, time, curr_Process, quantum_time, cpu_attr, io_attr, ReEnterProcess, ReEnterTime):
    CPU = getattr(curr_Process, cpu_attr)
    temp = min(CPU, quantum_time)

    for i in range(temp):
        time += 1
        if ReEnterProcess is not None and time == ReEnterTime:
            AddingProcess(q, time, ReEnterProcess)
        elif i != temp - 1: AddingProcess(q, time)
        
        if i != temp - 1:
            calcWT_Queue(q)
            ReEnterProcess, ReEnterTime = rProcess(time)
            
    curr_Process.last_executed_time = time
    setattr(curr_Process, cpu_attr, CPU - temp)

    if getattr(curr_Process, cpu_attr) == 0:
        io_data = getattr(curr_Process, io_attr)
        if io_data != "-1":
            io_time = int(io_data.split("(")[0])
            if io_data[-2] == '1':
                R1.put([curr_Process, io_time])
            else:
                R2.put([curr_Process, io_time])
        else: curr_Process.completion_time = time
        setattr(curr_Process, cpu_attr, -1)  # Đánh dấu là đã xong
    else:
        AddingProcess(q, time, [curr_Process])

    return temp
     
def roundRobin(quantum_time, np):
    global R1, R2, scheduling_process
    time = 0
    completed = 0
    q = Queue()
    while completed < np or not R1.empty() or not R2.empty():
        ReEnterProcess, ReEnterTime = rProcess(time)
        AddingProcess(q, time)
        if not q.empty():
            curr_Process = q.get()
            calcWT_Queue(q)
            
            if curr_Process.CPU1 > 0:
                temp = executeCPU_RR(q, time, curr_Process, quantum_time, "CPU1", "IO1", ReEnterProcess, ReEnterTime)
            elif curr_Process.CPU2 > 0:
                temp = executeCPU_RR(q, time, curr_Process, quantum_time, "CPU2", "IO2", ReEnterProcess, ReEnterTime)
            time += temp   
            
            if curr_Process.CPU1 == -1 and curr_Process.CPU2 == -1: #nếu xong
                completed += 1
                
            scheduling_process.extend(str(curr_Process.ID) * temp)
        else:
            scheduling_process.append("_")  # Nếu hiện tại không có quá trình nào thì append _
            time += 1 
            if ReEnterProcess is not None and time == ReEnterTime:
                AddingProcess(q, time, ReEnterProcess)        
    calcTT(np)
################
         
################ SJF
    
def executeCPU_SJF(pq, time, curr_Process, cpu_attr, io_attr, ReEnterProcess, ReEnterTime):
    CPU = getattr(curr_Process, cpu_attr)
    
    for i in range(CPU):
        time += 1
        if ReEnterProcess is not None and time == ReEnterTime:
            AddingProcessPQ(pq, time, ReEnterProcess)
        elif i != CPU - 1:
            AddingProcessPQ(pq, time)
        if i != CPU - 1:
            calcWT_PQueue(pq)
            ReEnterProcess, ReEnterTime = rProcess(time)

    curr_Process.last_executed_time = time
    
    io_data = getattr(curr_Process, io_attr)
    if io_data != "-1":
        io_time = int(io_data.split("(")[0])
        if io_data[-2] == "1":
            R1.put([curr_Process, io_time])
        else:
            R2.put([curr_Process, io_time])
    else:
        curr_Process.completion_time = time
        
    setattr(curr_Process, cpu_attr, -1)
    return CPU
    
def sjf(np):
    global R1, R2, scheduling_process
    time = 0
    completed = 0
    pq = PriorityQueue()
    
    while completed < np or not R1.empty() or not R2.empty():
        ReEnterProcess, ReEnterTime = rProcess(time)
        AddingProcessPQ(pq, time)
        if not pq.empty(): 
            _, curr_Process = pq.get()
            calcWT_PQueue(pq)
            
            if curr_Process.CPU1 > 0:
                temp = executeCPU_SJF(pq, time, curr_Process, "CPU1", "IO1", ReEnterProcess, ReEnterTime)
            elif curr_Process.CPU2 > 0:
                temp = executeCPU_SJF(pq, time, curr_Process, "CPU2", "IO2", ReEnterProcess, ReEnterTime)      
            time += temp
        
            if curr_Process.CPU1 == -1 and curr_Process.CPU2 == -1:
                completed += 1 
            
            scheduling_process.extend(str(curr_Process.ID) * temp)
        else:
            scheduling_process.append("_")
            time += 1 
            if ReEnterProcess is not None and time == ReEnterTime:
                AddingProcessPQ(pq, time, ReEnterProcess)
            
    calcTT(np)
################           
    

################ SRTN
                
def executeCPU_SRTN(pq, time, curr_Process, cpu_attr, io_attr):
    setattr(curr_Process, cpu_attr, getattr(curr_Process, cpu_attr) - 1)
    curr_Process.remaining_time = getattr(curr_Process, cpu_attr)
    time += 1
    curr_Process.last_executed_time = time
    
    if getattr(curr_Process, cpu_attr) == 0:
        io_data = getattr(curr_Process, io_attr)
        if io_data != "-1":
            io_time = int(io_data.split("(")[0])
            if io_data[-2] == '1':
                R1.put([curr_Process, io_time])
            else:
                R2.put([curr_Process, io_time])
        else: curr_Process.completion_time = time
        # Đánh dấu xem tiến trình hiện tại có IO lần đầu tiên hay chưa
        setattr(curr_Process, cpu_attr, -1)
    else: AddingProcessPQ(pq, time, [curr_Process])
    
def srtn(np):
    global R1, R2, scheduling_process
    time = 0
    completed = 0
    pq = PriorityQueue()
    while completed < np or not R1.empty() or not R2.empty():
        ReEnterProcess , ReEnterTime = rProcess(time)
        AddingProcessPQ(pq, time)
        if not pq.empty():
            _, curr_Process = pq.get()
            calcWT_PQueue(pq)
            
            if curr_Process.CPU1 > 0:
                executeCPU_SRTN(pq, time, curr_Process, "CPU1", "IO1")
            elif curr_Process.CPU2 > 0:
                executeCPU_SRTN(pq, time, curr_Process, "CPU2", "IO2")
                
            time += 1
            if ReEnterProcess and time == ReEnterTime:
                AddingProcessPQ(pq, time, ReEnterProcess) 
 
            if curr_Process.CPU1 == -1 and curr_Process.CPU2 == -1: #nếu xong
                completed += 1
            
            scheduling_process.append(str(curr_Process.ID))
        else:
            scheduling_process.append("_")  # Nếu hiện tại không có quá trình nào thì append _
            time += 1 
            if ReEnterProcess and time == ReEnterTime:
                AddingProcessPQ(pq, time, ReEnterProcess)
            
    calcTT(np)
################   
    
def main():
    if len(sys.argv) != 3:
        print("Usage: python 23127254_23127366.py <INPUT_FILE> <OUTPUT_FILE>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    algorithm, quantum_time, np = read_file(input_file)
    match algorithm:
        case 1:
            fcfs(np)
        case 2:
            roundRobin(quantum_time, np)
        case 3:
            sjf(np)
        case 4:
            srtn(np)
    write_file(output_file, np)
   
if __name__ == "__main__":
    main()
