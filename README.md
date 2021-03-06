flight_route_optimization
=========================
Attached are three data sources:
emptylegs - a list supply : available positioning flights (/empty legs), and the costs of taking that exact flight
watches - a list of demand : who wants to travel from different airports
airports - a list of worldwide airports, with geo-coordinates
We want to calculate the most profitable use of these empty legs to service our demand. We call these options “ghost legs”. The price of a ghost leg is a combination of:
“ferry” costs to get to the pickup point from the empty legs departure point (if different) and from the drop off point to the arrival airport of the empty leg (if different)
“taxi” costs to fly the person on the journey they want to take
landing charges at the pickup and drop off points, if different to those of the empty leg
For this test iteration you can make the following assumptions:
The flying time is a simple function of the nm distance between the two points and a speed of 500nm/h
We’re only trying to fly a single “taxi” route, rather than multiple, from each empty leg
The landing charges are £2500 at each airport that’s not part of the empty leg
The total distance for the ghost leg (ferry + taxi + ferry) should be no more than double the empty leg distance
Ferry costs are £1000 per hour for all aircraft
Taxi costs are £2000 per hour for all aircraft
Feel free to use any languages/tools that you think would be appropriate. We expect you to report back with your findings and solutions in a way you feel is appropriate - at this stage we value the process of how you solve the problem as much as the solution itself so make sure you include as much info as possible. We’d expect you to include some source code and steps to follow to reproduce your findings.


