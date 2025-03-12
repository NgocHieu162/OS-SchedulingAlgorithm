import sys
from queue import Queue, PriorityQueue
from dataclasses import dataclass

#Cac queue mo phong su dung resource
R1 = Queue()
R2 = Queue()

##Input
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
    remaining_time: int #ban dau = CPU1

    def __lt__(self, other):
        return (self.remaining_time, self.last_executed_time, self.ID) < (other.remaining_time,, othe.last_excuted_time, other.ID)

process_list = []

##Output
scheduling_process = []
R1_process = []
R2_process = []
TT = [0] * 4
WT = [0] * 4




