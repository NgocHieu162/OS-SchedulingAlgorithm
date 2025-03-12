import sys
from queue import Queue, PriorityQueue
from dataclasses import dataclass

# Các queue mô phỏng sử dụng resource (dùng cho RR, SRTN không thay đổi)
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
    burst_time: int
    IO_time: int
    remaining_time: int  # ban đầu = CPU1

    def __lt__(self, other):
        return (self.remaining_time, self.last_executed_time, self.ID) < (other.remaining_time, other.last_executed_time, other.ID)

process_list = []

## Output
scheduling_process = []  # lịch sử CPU (theo đơn vị thời gian)
R1_process = []          # lịch sử sử dụng resource R1 (theo đơn vị thời gian)
R2_process = []          # lịch sử sử dụng resource R2 (theo đơn vị thời gian)
TT = [0] * 4
WT = [0] * 4

def read_file(input_file):
    global process_list
    quantum_time = 0
    with open(input_file, "r") as f:
        algorithm = int(f.readline().strip())
        if algorithm == 2: 
            quantum_time = int(f.readline().strip())
        np = int(f.readline().strip())  # số tiến trình
        for i in range(np):
            IO_time = 0
            temp = f.readline().strip().split()
            AT = int(temp[0])
            CPU1 = int(temp[1])
            if len(temp) > 2:
                IO1 = temp[2]
                IO_time += 1
            else:
                IO1 = "-1"
            CPU2 = int(temp[3]) if len(temp) > 3 else -1   
            if len(temp) > 4:
                IO2 = temp[4]
                IO_time += 1
            else:
                IO2 = "-1"
            # Ban đầu, remaining_time = CPU1
            process_list.append(Process(i + 1, AT, CPU1, IO1, CPU2, IO2, 0, 0, IO_time, CPU1))
    return algorithm, quantum_time, np

def calcTime(np):
    global TT, WT
    completion_time = {}
    total_time = len(scheduling_process)
    for i in range(np):
        reversed_list = scheduling_process[::-1]
        for j in range(len(reversed_list)):
            if reversed_list[j] == str(i + 1):
                completion_time[i] = total_time - j
                break
        
    for i in range(np):
        TT[i] = completion_time[i] - process_list[i].AT
        WT[i] = TT[i] - process_list[i].burst_time

def write_file(output_file, np):
    with open(output_file, "w") as f:
        f.write(" ".join(scheduling_process) + "\n")
        f.write(" ".join(R1_process) + "\n")
        f.write(" ".join(R2_process) + "\n")
        f.write(" ".join(map(str, TT[:np])) + "\n")
        f.write(" ".join(map(str, WT[:np])) + "\n")

##############################################################################
# Phiên bản event-driven cho FCFS (First Come First Serve)
##############################################################################
def fcfs_event(process_list, np):
    global scheduling_process, R1_process, R2_process
    time = 0
    completed = 0
    ready_queue = []  # dùng theo thứ tự đến
    curr = None     # tiến trình đang chạy trên CPU

    # Với IO: mỗi resource giữ tuple (process, finish_time) nếu đang bận,
    # và danh sách chờ (waiting list) nếu resource bận.
    io_R1 = None  
    io_R2 = None
    waiting_R1 = []
    waiting_R2 = []

    # Ban đầu, thêm các tiến trình đến lúc 0 vào ready_queue
    for p in process_list:
        if p.AT == 0:
            ready_queue.append(p)

    # Vòng lặp mô phỏng (chạy đến khi tất cả tiến trình hoàn thành và không còn IO)
    while completed < np or curr or ready_queue or io_R1 or io_R2 or waiting_R1 or waiting_R2:
        # Xác định thời điểm sự kiện tiếp theo:
        next_arrival = min([p.AT for p in process_list if p.AT > time], default=float('inf'))
        next_cpu_finish = float('inf')
        if curr:
            burst = curr.CPU1 if curr.CPU1 > 0 else curr.CPU2
            next_cpu_finish = time + burst
        next_io_R1 = io_R1[1] if io_R1 else float('inf')
        next_io_R2 = io_R2[1] if io_R2 else float('inf')
        next_event_time = min(next_arrival, next_cpu_finish, next_io_R1, next_io_R2)
        # Nếu không có sự kiện nào sắp xảy ra:
        if next_event_time == float('inf'):
            # Nếu có tiến trình chờ, bắt đầu ngay lập tức; nếu không, thoát vòng lặp.
            if not curr and ready_queue:
                next_event_time = time
            else:
                break
        delta = int(next_event_time - time)
        
        # Cập nhật lịch sử CPU: nếu CPU bận thì fill bằng ID, ngược lại dấu "_" (idle)
        if curr:
            scheduling_process.extend([str(curr.ID)] * delta)
        else:
            scheduling_process.extend(["_"] * delta)
        # Cập nhật lịch sử IO cho R1 và R2
        if io_R1:
            R1_process.extend([str(io_R1[0].ID)] * delta)
        else:
            R1_process.extend(["_"] * delta)
        if io_R2:
            R2_process.extend([str(io_R2[0].ID)] * delta)
        else:
            R2_process.extend(["_"] * delta)
        
        time = next_event_time

        # Thêm tiến trình đến mới tại thời điểm time
        for p in process_list:
            if p.AT == time:
                ready_queue.append(p)

        # Xử lý sự kiện CPU hoàn thành burst
        if curr and next_cpu_finish == time:
            if curr.CPU1 > 0:
                curr.burst_time += curr.CPU1
                curr.last_executed_time = time
                curr.CPU1 = 0
                # Nếu có IO sau CPU1, đưa vào IO resource phù hợp
                if curr.IO1 != "-1":
                    io_duration = int(curr.IO1.split("(")[0])
                    if curr.IO1[-2] == '1':
                        if not io_R1:
                            io_R1 = (curr, time + io_duration)
                        else:
                            waiting_R1.append(curr)
                    else:
                        if not io_R2:
                            io_R2 = (curr, time + io_duration)
                        else:
                            waiting_R2.append(curr)
                else:
                    if curr.CPU2 > 0:
                        ready_queue.append(curr)
                    else:
                        completed += 1
            elif curr.CPU2 > 0:
                curr.burst_time += curr.CPU2
                curr.last_executed_time = time
                curr.CPU2 = 0
                if curr.IO2 != "-1":
                    io_duration = int(curr.IO2.split("(")[0])
                    if curr.IO2[-2] == '1':
                        if not io_R1:
                            io_R1 = (curr, time + io_duration)
                        else:
                            waiting_R1.append(curr)
                    else:
                        if not io_R2:
                            io_R2 = (curr, time + io_duration)
                        else:
                            waiting_R2.append(curr)
                else:
                    completed += 1
            curr = None

        # Xử lý sự kiện IO hoàn thành trên R1 và R2
        if io_R1 and io_R1[1] == time:
            proc = io_R1[0]
            io_R1 = None
            proc.IO_time -= 1
            if proc.CPU2 > 0:
                ready_queue.append(proc)
            if waiting_R1:
                next_proc = waiting_R1.pop(0)
                duration = int(next_proc.IO1.split("(")[0]) if next_proc.IO1 != "-1" else int(next_proc.IO2.split("(")[0])
                io_R1 = (next_proc, time + duration)
        if io_R2 and io_R2[1] == time:
            proc = io_R2[0]
            io_R2 = None
            proc.IO_time -= 1
            if proc.CPU2 > 0:
                ready_queue.append(proc)
            if waiting_R2:
                next_proc = waiting_R2.pop(0)
                duration = int(next_proc.IO1.split("(")[0]) if next_proc.IO1 != "-1" else int(next_proc.IO2.split("(")[0])
                io_R2 = (next_proc, time + duration)

        # Nếu CPU đang rảnh và ready_queue không rỗng, lấy tiến trình đầu tiên (FCFS) vào CPU
        if not curr and ready_queue:
            curr = ready_queue.pop(0)
    calcTime(np)

def sjf_event(process_list, np):
    global scheduling_process, R1_process, R2_process
    time = 0
    completed = 0
    ready_queue = []  # sẽ được sắp xếp theo burst nhỏ nhất
    curr = None
    io_R1 = None
    io_R2 = None
    waiting_R1 = []
    waiting_R2 = []

    def current_burst(p):
        return p.CPU1 if p.CPU1 > 0 else (p.CPU2 if p.CPU2 > 0 else float('inf'))

    for p in process_list:
        if p.AT == 0:
            ready_queue.append(p)
    ready_queue.sort(key=lambda p: (current_burst(p), p.last_executed_time, p.ID))

    while completed < np or curr or ready_queue or io_R1 or io_R2 or waiting_R1 or waiting_R2:
        next_arrival = min([p.AT for p in process_list if p.AT > time], default=float('inf'))
        next_cpu_finish = float('inf')
        if curr:
            burst = current_burst(curr)
            next_cpu_finish = time + burst
        next_io_R1 = io_R1[1] if io_R1 else float('inf')
        next_io_R2 = io_R2[1] if io_R2 else float('inf')
        next_event_time = min(next_arrival, next_cpu_finish, next_io_R1, next_io_R2)
        # Kiểm tra trường hợp không có sự kiện sắp tới
        if next_event_time == float('inf'):
            if not curr and ready_queue:
                next_event_time = time
            else:
                break
        delta = int(next_event_time - time)
        
        if curr:
            scheduling_process.extend([str(curr.ID)] * delta)
        else:
            scheduling_process.extend(["_"] * delta)
        if io_R1:
            R1_process.extend([str(io_R1[0].ID)] * delta)
        else:
            R1_process.extend(["_"] * delta)
        if io_R2:
            R2_process.extend([str(io_R2[0].ID)] * delta)
        else:
            R2_process.extend(["_"] * delta)
        
        time = next_event_time

        for p in process_list:
            if p.AT == time:
                ready_queue.append(p)
        ready_queue.sort(key=lambda p: (current_burst(p), p.last_executed_time, p.ID))
        
        if curr and next_cpu_finish == time:
            if curr.CPU1 > 0:
                curr.burst_time += curr.CPU1
                curr.last_executed_time = time
                curr.CPU1 = 0
                if curr.IO1 != "-1":
                    io_duration = int(curr.IO1.split("(")[0])
                    if curr.IO1[-2] == '1':
                        if not io_R1:
                            io_R1 = (curr, time + io_duration)
                        else:
                            waiting_R1.append(curr)
                    else:
                        if not io_R2:
                            io_R2 = (curr, time + io_duration)
                        else:
                            waiting_R2.append(curr)
                else:
                    if curr.CPU2 > 0:
                        ready_queue.append(curr)
                    else:
                        completed += 1
            elif curr.CPU2 > 0:
                curr.burst_time += curr.CPU2
                curr.last_executed_time = time
                curr.CPU2 = 0
                if curr.IO2 != "-1":
                    io_duration = int(curr.IO2.split("(")[0])
                    if curr.IO2[-2] == '1':
                        if not io_R1:
                            io_R1 = (curr, time + io_duration)
                        else:
                            waiting_R1.append(curr)
                    else:
                        if not io_R2:
                            io_R2 = (curr, time + io_duration)
                        else:
                            waiting_R2.append(curr)
                else:
                    completed += 1
            curr = None
        if io_R1 and io_R1[1] == time:
            proc = io_R1[0]
            io_R1 = None
            proc.IO_time -= 1
            if proc.CPU2 > 0:
                ready_queue.append(proc)
            if waiting_R1:
                next_proc = waiting_R1.pop(0)
                duration = int(next_proc.IO1.split("(")[0]) if next_proc.IO1 != "-1" else int(next_proc.IO2.split("(")[0])
                io_R1 = (next_proc, time + duration)
        if io_R2 and io_R2[1] == time:
            proc = io_R2[0]
            io_R2 = None
            proc.IO_time -= 1
            if proc.CPU2 > 0:
                ready_queue.append(proc)
            if waiting_R2:
                next_proc = waiting_R2.pop(0)
                duration = int(next_proc.IO1.split("(")[0]) if next_proc.IO1 != "-1" else int(next_proc.IO2.split("(")[0])
                io_R2 = (next_proc, time + duration)
        ready_queue.sort(key=lambda p: (current_burst(p), p.last_executed_time, p.ID))
        if not curr and ready_queue:
            curr = ready_queue.pop(0)
    calcTime(np)


##############################################################################
# Các thuật toán khác (Round Robin và SRTN) giữ nguyên
##############################################################################
def AddingProcess(queue, time, ReEnterProcess=None):
    enterRQ_list = []
    queue_list = list(queue.queue)
    
    # Thêm tiến trình mới có thời gian đến bằng time
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
              
def rProcess(time):
    """
    Xử lý IO của resource R1 và R2 theo đơn vị thời gian (dành cho RR và SRTN).
    """
    global R1, R2
    ReEnterProcess = []
    ReEnterTime = None
    if not R1.empty():
        r1_process = R1.queue[0]
        if r1_process[0].IO_time != 0:
            r1_process[1] -= 1
            R1_process.append(str(r1_process[0].ID))
            if r1_process[1] == 0:
                r1_process = R1.get()[0]
                if r1_process.CPU2 > 0:
                    r1_process.remaining_time = r1_process.CPU2
                    ReEnterProcess.append(r1_process)
                    ReEnterTime = time + 1
                r1_process.IO_time -= 1
        else:
            R1.get()
    else:
        R1_process.append("_")
    
    if not R2.empty():
        r2_process = R2.queue[0]
        if r2_process[0].IO_time != 0:
            r2_process[1] -= 1
            R2_process.append(str(r2_process[0].ID))
            if r2_process[1] == 0:
                r2_process = R2.get()[0]
                if r2_process.CPU2 > 0:
                    r2_process.remaining_time = r2_process.CPU2
                    ReEnterProcess.append(r2_process)
                    ReEnterTime = time + 1
                r2_process.IO_time -= 1
        else:
            R2.get()
    else:
        R2_process.append("_")    
        
    return ReEnterProcess, ReEnterTime

def executeCPU_RR(q, time, curr_Process, quantum_time, cpu_attr, io_attr, ReEnterProcess, ReEnterTime):
    CPU = getattr(curr_Process, cpu_attr)
    temp = min(CPU, quantum_time)

    for i in range(temp):
        time += 1
        if ReEnterProcess is not None and time == ReEnterTime:
            AddingProcess(q, time, ReEnterProcess)
        elif i != temp - 1:
            AddingProcess(q, time)
        if i != temp - 1:
            ReEnterProcess, ReEnterTime = rProcess(time)
            
    curr_Process.burst_time += temp
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
        setattr(curr_Process, cpu_attr, -1)
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
            if curr_Process.CPU1 > 0:
                temp = executeCPU_RR(q, time, curr_Process, quantum_time, "CPU1", "IO1", ReEnterProcess, ReEnterTime)
            elif curr_Process.CPU2 > 0:
                temp = executeCPU_RR(q, time, curr_Process, quantum_time, "CPU2", "IO2", ReEnterProcess, ReEnterTime)
            time += temp   
            
            if curr_Process.CPU1 == -1 and curr_Process.CPU2 == -1:
                completed += 1
            scheduling_process.extend(str(curr_Process.ID) * temp)
        else:
            scheduling_process.append("_")
            time += 1 
            if ReEnterProcess is not None and time == ReEnterTime:
                AddingProcess(q, time, ReEnterProcess)
            
    calcTime(np)
    
def AddingProcessSRTN(pqueue, time, ReEnterProcess=None):
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
            if not any(item[1] == process for item in pqueue_list):
                pqueue.put((process.remaining_time, process))       
                
def executeCPU_SRTN(pq, time, curr_Process, cpu_attr, io_attr):
    curr_Process.burst_time += 1
    setattr(curr_Process, cpu_attr, getattr(curr_Process, cpu_attr) - 1)
    curr_Process.remaining_time = getattr(curr_Process, cpu_attr) - 1
    curr_Process.last_executed_time = time + 1
    
    if getattr(curr_Process, cpu_attr) == 0:
        io_data = getattr(curr_Process, io_attr)
        if io_data != "-1":
            io_time = int(io_data.split("(")[0])
            if io_data[-2] == '1':
                R1.put([curr_Process, io_time])
            else:
                R2.put([curr_Process, io_time])
        setattr(curr_Process, cpu_attr, -1)
    else:
        AddingProcessSRTN(pq, time, [curr_Process])
    
def srtn(np):
    global R1, R2, scheduling_process
    time = 0
    completed = 0
    pq = PriorityQueue()
    while completed < np or not R1.empty() or not R2.empty():
        ReEnterProcess, ReEnterTime = rProcess(time)
        AddingProcessSRTN(pq, time)
        if not pq.empty():
            _, curr_Process = pq.get()
            if curr_Process.CPU1 > 0:
                executeCPU_SRTN(pq, time, curr_Process, "CPU1", "IO1")
            elif curr_Process.CPU2 > 0:
                executeCPU_SRTN(pq, time, curr_Process, "CPU2", "IO2")

            time += 1
            if ReEnterProcess and time == ReEnterTime:
                AddingProcessSRTN(pq, time, ReEnterProcess) 
     
            if curr_Process.CPU1 == -1 and curr_Process.CPU2 == -1:
                completed += 1
            
            scheduling_process.append(str(curr_Process.ID))
        else:
            scheduling_process.append("_")
            time += 1 
            if ReEnterProcess and time == ReEnterTime:
                AddingProcessSRTN(pq, time, ReEnterProcess)
            
    calcTime(np)
    
def main():
    input_file = "Input.txt"
    output_file = "Output.txt"
    
    algorithm, quantum_time, np = read_file(input_file)
    # Sử dụng mô phỏng event-driven cho FCFS và SJF để tăng tốc
    match algorithm:
        case 1:
            fcfs_event(process_list, np)
        case 2:
            roundRobin(quantum_time, np)
        case 3:
            sjf_event(process_list, np)
        case 4:
            srtn(np)
    write_file(output_file, np)
   
if __name__ == "__main__":
    main()
