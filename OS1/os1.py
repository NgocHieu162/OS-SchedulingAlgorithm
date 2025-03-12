import sys
from queue import Queue, PriorityQueue
from dataclasses import dataclass

# Các queue mô phỏng sử dụng resource
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
scheduling_process = []
R1_process = []
R2_process = []
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

def AddingProcess(queue, time, ReEnterProcess=None):
    enterRQ_list = []
    queue_list = list(queue.queue)
    
    # Thêm tiến trình mới có thời gian đến bằng time
    for p in process_list:
        if time == p.AT:
            enterRQ_list.append(p)
            
    if enterRQ_list:
        # Sắp xếp theo last_executed_time, sau đó theo ID
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
    Xử lý IO của resource R1 và R2.
    Nếu tiến trình đang thực hiện IO, giảm thời gian IO 1 đơn vị.
    Khi IO kết thúc, nếu có CPU tiếp theo (CPU2) thì cập nhật remaining_time và đưa tiến trình vào ready queue.
    Đồng thời, lưu lại lịch sử sử dụng resource R1, R2.
    """
    global R1, R2
    ReEnterProcess = []
    ReEnterTime = None
    if not R1.empty():
        r1_process = R1.queue[0]
        if r1_process[0].IO_time != 0:
            r1_process[1] -= 1  # giảm 1 đơn vị thời gian IO
            R1_process.append(r1_process[0].ID)
            if r1_process[1] == 0:
                # IO hoàn thành, lấy tiến trình ra khỏi R1
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
            r2_process[1] -= 1  # giảm 1 đơn vị thời gian IO
            R2_process.append(r2_process[0].ID)
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

##########################################
# THUẬT TOÁN FCFS (First Come First Serve)
##########################################
def fcfs(process_list, np):
    global scheduling_process
    time = 0
    completed = 0
    q = Queue()
    # Vòng lặp chạy đến khi tất cả tiến trình hoàn thành hoặc IO vẫn đang xử lý
    while completed < np or not R1.empty() or not R2.empty():
        ReEnterProcess, ReEnterTime = rProcess(time)
        AddingProcess(q, time)
        if not q.empty():
            curr_Process = q.get()
            # Nếu CPU1 chưa xong, thực hiện CPU1
            if curr_Process.CPU1 > 0:
                burst = curr_Process.CPU1
                for i in range(burst):
                    time += 1
                    scheduling_process.append(str(curr_Process.ID))
                    # Trong quá trình chạy, cập nhật IO nếu có
                    ReEnterProcess, ReEnterTime = rProcess(time)
                    AddingProcess(q, time)
                curr_Process.burst_time += burst
                curr_Process.last_executed_time = time
                curr_Process.CPU1 = 0  # hoàn thành CPU1
                # Nếu có IO sau CPU1
                if curr_Process.IO1 != "-1":
                    io_time = int(curr_Process.IO1.split("(")[0])
                    if curr_Process.IO1[-2] == '1':
                        R1.put([curr_Process, io_time])
                    else:
                        R2.put([curr_Process, io_time])
            # Nếu CPU1 đã xong và có CPU2 chờ thực hiện
            elif curr_Process.CPU2 > 0:
                burst = curr_Process.CPU2
                for i in range(burst):
                    time += 1
                    scheduling_process.append(str(curr_Process.ID))
                    ReEnterProcess, ReEnterTime = rProcess(time)
                    AddingProcess(q, time)
                curr_Process.burst_time += burst
                curr_Process.last_executed_time = time
                curr_Process.CPU2 = 0
                # Nếu có IO sau CPU2 (ít khi xảy ra)
                if curr_Process.IO2 != "-1":
                    io_time = int(curr_Process.IO2.split("(")[0])
                    if curr_Process.IO2[-2] == '1':
                        R1.put([curr_Process, io_time])
                    else:
                        R2.put([curr_Process, io_time])
            if curr_Process.CPU1 == 0 and curr_Process.CPU2 == 0:
                completed += 1
        else:
            scheduling_process.append("_")
            time += 1
            if ReEnterProcess is not None and time == ReEnterTime:
                AddingProcess(q, time, ReEnterProcess)
    calcTime(np)

##########################################
# THUẬT TOÁN SJF (Shortest Job First)
##########################################
def sjf(process_list, np):
    global scheduling_process
    time = 0
    completed = 0
    ready_list = []  # Danh sách các tiến trình sẵn sàng
    # Hàm phụ: trả về burst thời gian hiện hành của tiến trình (CPU1 nếu chưa xong, còn nếu đã xong thì CPU2)
    def current_burst(p):
        return p.CPU1 if p.CPU1 > 0 else (p.CPU2 if p.CPU2 > 0 else float('inf'))
        
    while completed < np or not R1.empty() or not R2.empty():
        ReEnterProcess, ReEnterTime = rProcess(time)
        # Thêm tiến trình mới đến theo thời gian
        for p in process_list:
            if p.AT == time and p not in ready_list:
                ready_list.append(p)
        if ReEnterProcess:
            for p in ReEnterProcess:
                if p not in ready_list:
                    ready_list.append(p)
        # Nếu có tiến trình sẵn sàng, chọn tiến trình có burst nhỏ nhất
        if ready_list:
            ready_list.sort(key=lambda p: (current_burst(p), p.last_executed_time, p.ID))
            curr_Process = ready_list.pop(0)
            burst = current_burst(curr_Process)
            for i in range(burst):
                time += 1
                scheduling_process.append(str(curr_Process.ID))
                ReEnterProcess, ReEnterTime = rProcess(time)
                # Cập nhật thêm các tiến trình đến mới trong suốt thời gian chạy
                for p in process_list:
                    if p.AT == time and p not in ready_list:
                        ready_list.append(p)
                if ReEnterProcess:
                    for p in ReEnterProcess:
                        if p not in ready_list:
                            ready_list.append(p)
            curr_Process.burst_time += burst
            curr_Process.last_executed_time = time
            # Cập nhật trạng thái của tiến trình
            if curr_Process.CPU1 > 0:
                curr_Process.CPU1 = 0
                if curr_Process.IO1 != "-1":
                    io_time = int(curr_Process.IO1.split("(")[0])
                    if curr_Process.IO1[-2] == '1':
                        R1.put([curr_Process, io_time])
                    else:
                        R2.put([curr_Process, io_time])
            elif curr_Process.CPU2 > 0:
                curr_Process.CPU2 = 0
                if curr_Process.IO2 != "-1":
                    io_time = int(curr_Process.IO2.split("(")[0])
                    if curr_Process.IO2[-2] == '1':
                        R1.put([curr_Process, io_time])
                    else:
                        R2.put([curr_Process, io_time])
            if curr_Process.CPU1 == 0 and curr_Process.CPU2 == 0:
                completed += 1
        else:
            scheduling_process.append("_")
            time += 1
            if ReEnterProcess and time == ReEnterTime:
                for p in ReEnterProcess:
                    if p not in ready_list:
                        ready_list.append(p)
    calcTime(np)

##########################################
# Các thuật toán khác đã có: RoundRobin và SRTN
##########################################
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
        setattr(curr_Process, cpu_attr, -1)  # Đánh dấu hoàn thành burst
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
            
            if curr_Process.CPU1 == -1 and curr_Process.CPU2 == -1:  # nếu xong
                completed += 1
            scheduling_process.extend(str(curr_Process.ID) * temp)
        else:
            scheduling_process.append("_")  # CPU idle
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
     
            if curr_Process.CPU1 == -1 and curr_Process.CPU2 == -1:  # nếu xong
                completed += 1
            
            scheduling_process.append(str(curr_Process.ID))
        else:
            scheduling_process.append("_")
            time += 1 
            if ReEnterProcess and time == ReEnterTime:
                AddingProcessSRTN(pq, time, ReEnterProcess)
            
    calcTime(np)
    
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
        f.write(" ".join(map(str, R1_process)) + "\n")
        f.write(" ".join(map(str, R2_process)) + "\n")
        f.write(" ".join(map(str, TT[:np])) + "\n")
        f.write(" ".join(map(str, WT[:np])) + "\n")
        
def main():
    # Nếu chạy từ dòng lệnh, uncomment các dòng dưới đây:
    # if len(sys.argv) != 3:
    #     print("Usage: python scheduler.py <INPUT_FILE> <OUTPUT_FILE>")
    #     sys.exit(1)
    # input_file = sys.argv[1]
    # output_file = sys.argv[2]
    
    input_file = "input.txt"
    output_file = "output.txt"
    
    algorithm, quantum_time, np = read_file(input_file)
    match algorithm:
        case 1:
            fcfs(process_list, np)
        case 2:
            roundRobin(quantum_time, np)
        case 3:
            sjf(process_list, np)
        case 4:
            srtn(np)
    write_file(output_file, np)
   
if __name__ == "__main__":
    main()
