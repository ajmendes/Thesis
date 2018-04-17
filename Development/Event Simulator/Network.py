# -*- coding: utf-8 -*-
"""
Towards Performance Modeling of MU-MIMO in CSMA/CA Mesh Networks


    Objectives:
    
        - Measure throughput, the rate of successful message delivery over a communication channel

        - Measure idlea & busy time for each node in a network


    -----------------------------------------------------------

    User sets:
        - Number of Runs
        - Number of Nodes in each run
        - Number of Antennas in each Node
        - Sampling frequency
        - Random number generator seed - 'None' => always different
    
    Paths generated for each node before simulation starts
        - length & path randomized
    
    -----------------------------------------------------------
    
    Simulator:
        [body]:
                 -> Packet_Generator -> Queue_Manager > Transfer_Manager -> Transfer
            Main                                                                            -> Save Data
                 -> Observe    (Stores data each SAMPLING seconds)                                                         
    
    -----------------------------------------------------------

    Aux. library:
    
        Multple generator/probabilistic functions: 
            Nodes & Paths:            
            - path_length  (int)
            - next_jump    (int)
            Timers:
            - interarrival (exp)
            - backoff      (exp)
            - transfer     (exp)
        path_generator
        check_common_nodes
        check_clear
        observe        
        
    -----------------------------------------------------------

@network_model: antonio grilo
@code: antonio

Last edited on 12th April
"""

import simpy                             # DES
import numpy as np                       # Randoms
import copy                              # Utils
import matplotlib.pyplot as plt          # Plots
import xlwt                              # Export to excel


####################
#  Sim. Variables  #

RUNS = 1                            # Number of runs
SIM_TIME = 5000                      # Simulation time for each run
PACKETS = 2500                      # Simulate until X packets
NUMBER_OF_NODES = [4, 2, 3, 3, 4, 4]      # Number of nodes
NUMBER_OF_ANTENNAS = [2, 2, 1, 2, 1, 2]   # Number of Antennas
SAMPLING = 0.5                     # Time between sampling
SEED = [None, 3, 3, 3, 3, 3]                 # Seed for number generators - Keep fixed for debugging


#########################
#  Simulator Functions  #

## Packet Generator:
#
# One process active for each node
# Continuasly generates packets and adds them to the global queue  
#
# Queue entries: [global ID, local ID, origin node, time @ generated, sent {0,1}]
#
# args: (environment, origin node)  

def packet_generator(env, idn, node_queue):   
    
    global packet_id_global
    global queue
    global n_packets_sent
    
    packet_id_local = 0
    #while n_packets_sent < 50:
    while env.now < SIM_TIME:
        yield env.timeout(generate_interarrival() )
        packet_id_global += 1 
        packet_id_local += 1
        id_global = packet_id_global   
        
        timer = '{:1.6f}'.format(env.now)
        sent= 0
        pos = [id_global, packet_id_local, idn, float(timer), sent] 
        queue.append(pos)
        node_queue[idn].append(pos)  
        
        
## Queue Manager:
#
# One process active for each node
# Finds as many packets belonging to node in queue as free antennas 
# Creates a process for each packet to be transfered
#
# args: (environmnent, origin node, antennas as resources)

def queue_manager(env, idn):   
    
    global queue
    global antenna_usage
    global n_packets_sent 
    global path
    global total_wait
    
    #yield env.timeout(2)         # Testing if after getting contention sends all

    while env.now < SIM_TIME:
        
        yield env.timeout(0.001)
        
        if len(queue) <> 0:
          
            common = check_common_nodes(idn)    # Check which antennas are needed
        
            cw = 15             # First ContentionWindow 

            #total_wait[idn] = 0  # Optional - Resets the waiting time before each packet sent
                        
            """
            # Miliseconds
            
            while True:
                yield env.timeout(34E-6)
                total_wait[idn] += 34E-6
                #total_wait[idn] = round(total_wait[idn], 8) 

                if check_clear(common) == True:
                    yield env.timeout(34E-6)
                    
                    total_wait[idn] += 34E-6
                    #total_wait[idn] = round(total_wait[idn], 8) 

                    if check_clear(common) == True:
                        break
                    else:
                        countdown = generate_backoff(cw)
                        while countdown > 0:
                            if check_clear(common) == True:
                                yield env.timeout(34E-6) 
                    
                                total_wait[idn] += 34E-6
                                #total_wait[idn] = round(total_wait[idn], 8) 

                                countdown -= 1
                            else:
                                yield env.timeout(34E-6)
                                        
                                total_wait[idn] += 34E-6
                                #total_wait[idn] = round(total_wait[idn], 8) 

                        if check_clear(common) == True:
                            break
                        else:
                            cw = 2 * cw              
            #
                            
            """  
            # Time Slots
            
            while True:
                yield env.timeout(34)
                total_wait[idn] += 34
                #total_wait[idn] = round(total_wait[idn], 8) 
                if check_clear(common) == True:
                    #yield env.timeout(34)
                    
                    total_wait[idn] += 34
                    #total_wait[idn] = round(total_wait[idn], 8) 

                    if check_clear(common) == True:
                        break
                    else:
                        countdown = generate_backoff(cw)
                        while countdown > 0:
                            if check_clear(common) == True:
                                yield env.timeout(34) 
                    
                                total_wait[idn] += 34
                                #total_wait[idn] = round(total_wait[idn], 8) 

                                countdown -= 1
                            else:
                                yield env.timeout(34)
                                        
                                total_wait[idn] += 34
                                #total_wait[idn] = round(total_wait[idn], 8) 

                        if check_clear(common) == True:
                            break
                        else:
                            cw = 2 * cw            
            #
            
            
            
            # Only acts if next in queue source is node
            for i in range( len(queue) ):
                if queue[i][4] == 0:
                    next_in_queue = queue[i][0]
                    break
                
            # Current antenna usage
            free_antennas = copy.copy(antenna_usage)  # Free antennas in path
            in_path = []    
            for jump in path[idn]:
                in_path.append(free_antennas[jump])                  
                
                
            # Find next - then n_free_antennas next
            for i in range( len(queue) ):
                if queue[i][2] == idn and queue[i][0] == next_in_queue:
                    j = i
                    
    ############## RTS HERE ?!        ###############             
                    
                    while j < len(queue):
                        
                        
                        """
                        Send as many packets as free antennas on source node
                        
                        """
                        if any(antenna is 0 for antenna in in_path):
                            break
                        
                        if queue[j][2] == idn and queue[j][4] == 0:
                            env.process(transfer_manager(env, queue[j][2], queue[j][0]))
                            queue[j][4] = 1
                            
                            for k in range(len(in_path)): 
                                in_path[k] -= 1      
                        j += 1
                    break
                
                
##  Transfer Management Function:
#
# Requests an Antenna from each node in Path and adds a Transfer process 
#
# args: (environment, origin node, global packet id, antennas as resources)
                
def transfer_manager(env, idn, packet_id):   
    
    global n_packets_sent 
    global path
    global antenna_usage
    
    for jump in path[idn]: 
        antenna_usage[jump] -= 1        
    
    yield env.process(transfer(env, idn, packet_id)) 
    n_packets_sent += 1 
    


##  Transfer Function:
#
# Iterates through a packet's path, yields a transfer time for each jump
#
# args: (environment, origin node, antennas requests, global ID)
def transfer(env, idn, packet_id):   # Fica so o yield env.timeout
   
    global path
    global antenna_usage
    global line    
    
    print
    line += 1        
    here = line
    
    global order
    order.append(packet_id)    
    
    

    """
    RECEBE UM PACOTE PARA ENVIAR

    for jump in path:
        if both have antenna: send
        else break
    
    """    
    
    # Writes packets to excel in send order (for all ws.writes in this function)
    ws.write(here + 1 , 4  ,str('{:.6f}'.format(env.now)), time_values)
    ws.write(here + 1, 3, str(packet_id), integers) 
    for i in range(len(path[idn])-1):
        if i == 0:
             print 'Packet: {} - Start Node: {} - Sent at \t\t{:.6f}  ' .format(packet_id, path[idn][i], env.now)
             yield env.timeout( generate_transfer_time() )
        else:
             #print ' - Packet: {} - Node: {} - Sent at \t\t{:.3f}  ' .format(packet_id, path[idn][i], env.now)
             yield env.timeout( generate_transfer_time() )
        print ' - Packet: {} - Node: {} - Received at \t\t{:.6f} ' .format(packet_id, path[idn][i+1], env.now)
        #ws.write(here + 1, 5  , str('{:.6f}'.format(env.now)), time_values)

        #antenna_usage[ path[idn][i] ] += 1                  # This line and the next free up antennas each jump
    #antenna_usage[ path[idn][i+1] ] += 1
    ws.write(here + 1, 5  , str('{:.6f}'.format(env.now)), time_values)

    for jump in path[idn]:                                   # This line and the next free up antennas after path
        antenna_usage[jump] += 1        


####################
#  Aux. Functions  #

## Generator/Probabilistic Functions (names self-explanatory)
def generate_path_length(max_size):
    return np.random.randint(1, max_size)       
       
def generate_next_jump(n_nodes):
    return np.random.randint(n_nodes)


def generate_interarrival():
    return 35
    return float('{0:.6f}'.format(np.random.exponential(1./3))) # 1/lambda

def generate_backoff(cw):
    #return 1
    return np.random.randint(0, cw+1)

def generate_transfer_time():
    #return 1
    return float('{0:.6f}'.format(np.random.exponential(1./3)))





## Defining Paths
# Random size, random path through nodes
def generate_path(node, n_nodes):  #  args: (origin node, number of nodes)
    global path
    way = []

    way.append(node)  # Path at node x starting at x        
    path_length = generate_path_length(n_nodes) # Path length
    for i in range( path_length ):
        next_jump = generate_next_jump(n_nodes)
        while (next_jump in way):
            next_jump = generate_next_jump(n_nodes)
        way.append(next_jump)
    path.append(way)
    
    
# Find common nodes between path and antennas vectors
def check_common_nodes(idn):
    common = []
    for i in range(len(antenna_usage)):
        for l in range(len(path[idn])):
            if path[idn][l] == i:
                 common.append(i)
    return common

    
# Check if path clear (free antennas)
def check_clear(common):
    clear = True    
    for node in common:
        if antenna_usage[ node ] == 0:
            clear = False
            break
    return clear


################
#   Analysis   #

# Keeps count of stats. Adds a new entry every SAMPLING seconds
def observe(env):
    global n_packets_sent
    global total_wait
        
    while True:
        time = '{:1.3f}'.format(env.now)
        obs_time.append(float(time))
        
        packets_sent.append(n_packets_sent)
        
        aux = copy.copy(total_wait)         
        wait.append(aux)
        
        yield env.timeout(SAMPLING)
        

    
    
# Opens Excell Workbook & set font style
wb = xlwt.Workbook()
header = xlwt.easyxf('font: bold on; align:  vert centre, horiz center')
time_values = xlwt.easyxf(' align:  vert centre, horiz right', num_format_str='#,##0.0000000')
integers = xlwt.easyxf('align: vert centre, horiz centre;', num_format_str='#,##0')

# Run simulation as many times as RUNS
for run in range(RUNS):
    
    # Workbook
    name = 'Run '+ str(run+1)
    ws = wb.add_sheet(name, cell_overwrite_ok=False)
    
    # Set/Reset observation variables    
    obs_time = []
    packets_sent = []
    n_packets_sent = 0
    wait = []
    total_wait = []
    for i in range(NUMBER_OF_NODES[run]):
        total_wait.append(0)
            
    # Random number generator seed - set on header, by user, for each run
    np.random.seed(SEED[run])
    
    # Creates simpy simulation environment
    env = simpy.Environment()
    
    # Either randomizes the number of nodes and antennas in each node or takes
    # those set on header.
    # Number of antennas and resources stored in lists.
    # Path randomized for each node
    
    #n_nodes = np.random.randint(2, NUMBER_OF_NODES + 1)     # Random number of Nodes
    n_nodes = NUMBER_OF_NODES[run]                           # Set by user for each run
    
    n_antennas = []       # Number of Antennas/Node
    global antenna_usage  # Defines a global vector for the antennas in use
    antenna_usage = []    # Know if there are antennas available  
    
    global path  # Defines a global path variable that can be read anywhere
    path = []
    
    
    for i in range(n_nodes):
        #n_antennas.append(np.random.randint(1,4))           # Random number of Antennas
        n_antennas.append(NUMBER_OF_ANTENNAS[run])           # Set by user for each run
        #n_antennas.append(NUMBER_OF_ANTENNAS[i])             # Single run - different number of antennas
        antenna_usage.append(n_antennas[i])
        generate_path(i, n_nodes)  
    
    #path = [[0, 1],  [1, 0], [2, 0],  [3, 4],  [4, 5],  [5, 5]]

    #path = [[0, 1], [1, 0], [4, 5], [4, 5], [4, 5], [4, 5]]
    
    print '-----\nNumber of Nodes: {}\nNumber of Antennas: {}\n-----'.format(n_nodes, n_antennas)
    print 'Paths:', path, '\n', '----' 
    
    
    global queue  # Defining a global package queue [global_id; local_id; origin; time]
    queue = []
    
    global packet_id_global  
    packet_id_global = 0
    
    global order
    order = []    
    
    global line
    line = 0    
    
    # Each node adds two processes to the environment 
    #    - Packet generation - stores them in a global queue
    #    - Queue management - find their packet and send as many as free antennas
    node_queue = [ ]
    for i in range(n_nodes):
        node_queue.append([])
    
    
    for idn in range(n_nodes):
        env.process(packet_generator(env, idn, node_queue))    
        env.process(queue_manager(env, idn))
    
    # Add observation process to the environment
    env.process(observe(env))
    
    # Run environment untill SIM_TIME
    env.run(until = SIM_TIME)    
 
  
    for i in range(len(order)):
       if order[i] <> i+1:
           print '\nNot in order'
           break

  
  

    # ANALYSIS #
    ############

    # Plot data sett
    plt.figure()
    plt.step(obs_time, packets_sent, where = 'post')
    plt.xlabel('Time')
    plt.ylabel('#.Sent')
    
    plt.figure()
    plt.step(obs_time, wait, where = 'post')
    plt.xlabel('Time')
    plt.ylabel('Total Idle Time')
    
    print '\n\nTotal idle time per node: ',total_wait
    
    
    
    # Store in workbook    
    ws.write(0, 0, 'Time', header)
    ws.write(0, 1, '#.Sent', header)
   
    ws.write(0, 4, 'Order[sent]', header)
    ws.write(1, 3, 'Packt ID', header)
    ws.write(1, 4, 'Sent.@', header)
    ws.write(1, 5, 'Rcvd.@', header)    
    
    rng = len(obs_time)
    for i in range( rng ):
        ws.write(i+1, 0, obs_time[i], time_values)    
        ws.write(i+1, 1, packets_sent[i], integers)
       
    ws.write(0, 6, 'Node', header)
    ws.write(0, 7, '#.Antennas', header)   
    for i in range(n_nodes):
        ws.write(i+1, 6, str(i), integers)   
        ws.write(i+1, 7, str(n_antennas[i]), integers)   
    
    col = 9
    i = 0
    while i < n_nodes:
        ws.write(0, col, 'Path Node '+str(i), header)
        ws.write(1, col, str(path[i]), integers)
        ws.write(4, col, 'Node '+ str(i), header)
        ws.write(5, col, 'Packt ID ', header)
        ws.write(5, col+1, 'Gen.@', header)

        rng = len(node_queue[i])
        for j in range(rng):
            ws.write(j+6, col, str(node_queue[i][j][0]), integers)
            ws.write(j+6, col+1, str(node_queue[i][j][3]), time_values)
        col += 3
        i += 1
    
# Save workbook after last run    
wb.save('Simulation.xls')



