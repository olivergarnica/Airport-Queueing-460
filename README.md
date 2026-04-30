# Airport-Queueing-460
Stochastic Processes modelling different parts airport queues

Passenger arrival -> TSA M/M/s -> gate wait -> boarding by group modified M/M/1 -> departure

person:
id
flight id
gate id
boarding group
arrival to airport time 
#clearance type [std, clear, tsa pre]
tsa queue enter time 
tsa service start time 
tsa service end time 
gate arrival time 
boarding queue enter time 
boarding start time 
boarding end time 
system done time 

flight: 
flight id 
gate id 
plane capacity 
departure time 
boarding open time = departure time - 30 minutes 
number of boarding groups 
passenger list 
boarded passengers 
status 

event: 
time 
event type 
entity id 

tsa checkpoint:
num servers
service rate 
busy servers 
queue 