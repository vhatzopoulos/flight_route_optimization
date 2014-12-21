"""
#----------------------------------------------------------------------
A deterministic algorithm that matches supply to a subset of the available
demand based on geometry-based heuristics.
#----------------------------------------------------------------------
"""
import networkx as nx
import pandas as pd
import smallestEnclosingCircle as sec
import utilities as util
from math import pi
import random

##params
deg2Rad = pi/180.0
ferryPerHour = 1000.0
taxiPerHour = 2000.0
landingCharge = 2500.0
speed = 500.0 #nm/h


#---------------------------------------------------------------
##first find the minimum enclosing circle of the supply coordinates

#store the airport (long,lat)
airports = pd.read_csv('airports.csv',index_col=0)
airportCoords = {} ##dict: AirportCode --> (long,lat)
print "making airport coords..."
for i in range(len(airports.index)):
	
	code = airports.ix[i,"AirportCode"]
	
	#this multiplication is actually the biggest
	#time bottleneck on the problem
	#much better to write the converted coordinates to file and read in
	airports.ix[i,"NLONGITUDE"] *= deg2Rad
	airports.ix[i,"NLATITUDE"] *= deg2Rad
	
	long = airports.ix[i,"NLONGITUDE"]
	lat = airports.ix[i,"NLATITUDE"]
	airportCoords[code] = {'long':-long,'lat':lat}


supply = pd.read_csv('emptyLegs.csv',index_col=0)

supplyCoords =[]
print "finding smallest enclosing circle and centroid for empty legs..."


#longs = []
#lats = []

for i in range(len(supply.index)):

	source = supply.ix[i,"From"]
	target = supply.ix[i,"To"]
	supplyCoords.append((airportCoords[source]['long'],airportCoords[source]['lat']))
	supplyCoords.append((airportCoords[target]['long'],airportCoords[target]['lat']))
	
	"""
	longs.append(airportCoords[source]['long'])
	longs.append(airportCoords[target]['long'])
	lats.append(airportCoords[source]['lat'])
	lats.append(airportCoords[target]['lat'])
	"""

c = sec.make_circle(supplyCoords)    
LONG = c[0]
LAT = c[1]
r = c[2]
r2 = r**2
"""
meanLongSupply = sum(longs) / (1.0*len(longs))
meanLatSupply = sum(lats) / (1.0*len(lats))
"""

#find the (weighted) centroid of empty legs
meanLongSupply = sum([tup[0] for tup in supplyCoords]) / (1.0*len(supplyCoords))
meanLatSupply = sum([tup[1] for tup in supplyCoords]) / (1.0*len(supplyCoords))

#---------------------------------------------------------------
##now start making a supply graph by adding airports in the minimum enclosing circle
supplyGraph = nx.DiGraph()

print "adding airports in smallest enclosing circle for empty legs ..."
for i in range(len(airports.index)):
	
	code = airports.ix[i,"AirportCode"]
	
	long = airportCoords[code]['long']
	lat = airportCoords[code]['lat']
	
	#circle equation
	if  ((long-LONG)**2 + (lat-LAT)**2 <= r2):
		supplyGraph.add_node(airports.ix[i,"AirportCode"],airports.ix[i].to_dict())

##add the supply edges to the graph
print "adding empty leg edges..."

for i in range(len(supply.index)):

	source = supply.ix[i,"From"]
	target = supply.ix[i,"To"]
	
	#only add edges for airports in supply graph
	if source in supplyGraph and target in supplyGraph:
		
		#add edge with data	
		if target not in supplyGraph[source]:		
			supplyGraph.add_edge(source,target,supply=1)	
		#update edge if already there	
		else:
			supplyGraph[source][target]['supply'] += 1
	
#---------------------------------------------------------------
##make the demand graph
watches = pd.read_csv('watches.csv',index_col=0)

##first find subset in graph (smallest enclosing circle)
distances = []

for i in range(len(watches.index)):

	source = watches.ix[i,"FROM"]
	target = watches.ix[i,"TO"]
	
	#if the airports are in the smallest enclosing circle
	#if this route exists as an empty leg append that routes demand
	if source in  supplyGraph and target in supplyGraph:
	
		
		long1 = airportCoords[source]['long']
		lat1 = airportCoords[source]['lat']
		long2 = airportCoords[target]['long']
		lat2 = airportCoords[target]['lat']
		
		midpointLong = ((long1+long2)/2.0)
		midpointLat = ((lat1+lat2)/2.0)
	
		#get the Haversine distance to the centroid of the empty leg points:
		d = util.haversine(midpointLong,midpointLat,meanLongSupply,meanLatSupply)
		distances.append((source,target,{'dist':d}))
		
			
distances.sort(key=lambda tup: tup[2])  #sorts in place

demandGraph = nx.MultiDiGraph()
demandGraph.add_edges_from(distances)

completedTrips = 0
totCost = 0
completed = []

#---------------------------------------------------------------
#go through the edges in a sorted order and take care of the demand that matches empty legs
edges = sorted(demandGraph.edges(data=True),key=lambda edge:edge[2]['dist'],reverse=False)
for edge in edges:
	
	source = edge[0]
	target = edge[1]

	#if the demand matches with an empty leg and there is supply available
	if target in supplyGraph[source] and supplyGraph[source][target]['supply'] > 0:
		long1 = supplyGraph.node[source]['NLONGITUDE']#*(pi/180)
		lat1 = supplyGraph.node[source]['NLATITUDE']#*(pi/180)
		long2 = supplyGraph.node[target]['NLONGITUDE']#*(pi/180)
		lat2 = supplyGraph.node[target]['NLATITUDE']#*(pi/180)
		distance = util.haversine(long1,lat1,long2,lat2)
		time = distance / speed
		cost = time * taxiPerHour
		totCost += cost
		completedTrips += 1
		supplyGraph[source][target]['supply'] -= 1
		completed.append((source,target))
		print source + " " + target + " " + str(cost) + " " +  str(totCost) + " " + str(completedTrips)
		print "executing taxi"
		print "distance: " + str(distance) + " time: " + str(time)  + " cost: " +str(cost) + " totCost: " + str(totCost)
		print "watches completed: " + str(completedTrips)

print "watches completed: " + str(completedTrips)			

#sup = 0
demandGraph.remove_edges_from(completed)

##Try finishing with ferry-taxi or taxi-ferry, i.e. no ferry-taxi-ferry routes
edges = sorted(demandGraph.edges(data=True),key=lambda edge:edge[2]['dist'],reverse=False)
for edge in edges:
	
	passengerSource = edge[0]
	passengerTarget = edge[1]
	
	#1)Is there an empty leg with source equal to the watch source in the same country?
	sameSourceList = [e for e in supplyGraph.edges() if e[0]==passengerSource and supplyGraph.node[e[0]]['CountryCode']==supplyGraph.node[passengerSource]['CountryCode']]
	#1)Is there an empty leg with target equal to the watch target in the same country?
	sameTargetList = [e for e in supplyGraph.edges() if e[1]==passengerTarget and supplyGraph.node[e[1]]['CountryCode']==supplyGraph.node[passengerTarget]['CountryCode']]
	
	if len(sameSourceList)==len(sameTargetList)==0:
		continue # ferry-taxi-ferry needed
		
	distances = []
	
	#if random.random() >= 0.5: #do a taxi-ferry trip
	#execute taxi-ferry or ferry-taxi based on higher availability
	if len(sameSourceList) >= len(sameTargetList): #do a taxi-ferry trip
	
		print "executing taxi-ferry for watch " + passengerSource + "-" + passengerTarget
		print "-------------------------------------------------------------"
		passengerTargetLong = supplyGraph.node[passengerTarget]['NLONGITUDE']
		passengerTargetLat = supplyGraph.node[passengerTarget]['NLATITUDE']
		#distances = []
		
		#for each of the empty leg targets calculate distances with passenger target
		#for ferrying after drop off
		for tup in sameSourceList:
			emptyLegTarget = tup[1]
			
			emptyLegTargetLong = supplyGraph.node[emptyLegTarget]['NLONGITUDE']
			emptyLegTargetLat = supplyGraph.node[emptyLegTarget]['NLATITUDE']
			distances.append((emptyLegTarget,util.haversine(emptyLegTargetLong,emptyLegTargetLat,passengerTargetLong,passengerTargetLat)))
		
		#sort and find minimum distance
		distances.sort(key=lambda tup: tup[1])
		#get code for the airport that minimizes distance
		emptyLegTarget = distances[0][0]

		#execute the flight path
		
		#taxi the passenger
		passengerSourceLong = supplyGraph.node[passengerSource]['NLONGITUDE']
		passengerSourceLat = supplyGraph.node[passengerSource]['NLATITUDE']
		passengerTargetLong = supplyGraph.node[passengerTarget]['NLONGITUDE']
		passengerTargetLat = supplyGraph.node[passengerTarget]['NLATITUDE']
		distance = util.haversine(passengerSourceLong,passengerSourceLat,passengerTargetLong,passengerTargetLat)
		#compute cost
		time = distance / speed
		cost = time * taxiPerHour
		cost += landingCharge
		totCost += cost
		print "1) executing taxi"
		print "distance: " + str(distance) + " time: " + str(time) +" taxiPerHour: " + str(taxiPerHour) + " cost: " +str(cost) + " totCost: " + str(totCost)
		
		#ferry to the empty leg target with the smallest distance - no landing charge as target is part
		#of empty leg
		emptyLegTargetLong = supplyGraph.node[emptyLegTarget]['NLONGITUDE']
		emptyLegTargetLat = supplyGraph.node[emptyLegTarget]['NLATITUDE']
		distance = util.haversine(passengerTargetLong,passengerTargetLat,emptyLegTargetLong,emptyLegTargetLat)
		time = distance / speed
		cost = time * ferryPerHour
		totCost += cost
		
		#reduce supply
		supplyGraph[passengerSource][emptyLegTarget]['supply'] -= 1
		completedTrips +=1
		
		print "2) executing ferry"
		print "distance: " + str(distance) + " time: " + str(time) +" ferryPerHour: " + str(ferryPerHour) + " cost: " +str(cost) + " totCost: " + str(totCost)
		print "watches completed: " + str(completedTrips)
		print '\n'
		
	#if len(sameTargetList) > len(sameSourceList): #do a ferry-taxi trip
	else:
		
		print "executing ferry-taxi for watch " + passengerSource + "-" + passengerTarget
		print "-------------------------------------------------------------"
		
		passengerSourceLong = supplyGraph.node[passengerSource]['NLONGITUDE']
		passengerSourceLat = supplyGraph.node[passengerSource]['NLATITUDE']
		
		#distances = []
		
		#for each of the empty leg sources calculate distances with passenger source
		#for ferrying before pickup
		for tup in sameTargetList:
			emptyLegSource = tup[0]
			emptyLegSourceLong = supplyGraph.node[emptyLegSource]['NLONGITUDE']
			emptyLegSourceLat = supplyGraph.node[emptyLegSource]['NLATITUDE']
			distances.append((emptyLegSource,util.haversine(emptyLegSourceLong,emptyLegSourceLat,passengerSourceLong,passengerSourceLat)))
		
		#sort and find minimum distance
		#print distances
		distances.sort(key=lambda tup: tup[1])
		#get code for the airport that minimizes distance
		emptyLegSource = distances[0][0]
		
		#execute the flight path
		
		#ferry from empty leg source to the passenger source
		passengerSourceLong = supplyGraph.node[passengerSource]['NLONGITUDE']
		passengerSourceLat = supplyGraph.node[passengerSource]['NLATITUDE']
		emptyLegSourceLong = supplyGraph.node[emptyLegSource]['NLONGITUDE']
		emptyLegSourceLat = supplyGraph.node[emptyLegSource]['NLATITUDE']
		distance = util.haversine(passengerSourceLong,passengerSourceLat,emptyLegSourceLong,emptyLegSourceLat)
		
		#compute cost
		time = distance / speed
		cost = time * ferryPerHour
		cost += landingCharge
		totCost += cost
		print "1) executing ferry"
		print "distance: " + str(distance) + " time: " + str(time) +" ferryPerHour: " + str(ferryPerHour) + " cost: " +str(cost) + " totCost: " + str(totCost)
		
		#taxi the passenger to the empty leg target
		emptyLegTargetLong = supplyGraph.node[emptyLegTarget]['NLONGITUDE']
		emptyLegTargetLat = supplyGraph.node[emptyLegTarget]['NLATITUDE']
		distance = util.haversine(passengerSourceLong,passengerSourceLat,emptyLegTargetLong,emptyLegTargetLat)
		
		#compute the cost
		time = distance / speed
		cost = time * taxiPerHour
		totCost += cost
		completedTrips += 1

		#reduce supply
		supplyGraph[emptyLegSource][passengerTarget]['supply'] -= 1

		print "2) executing taxi"
		print "distance: " + str(distance) + " time: " + str(time) +" taxiPerHour: " + str(taxiPerHour) + " cost: " +str(cost) + " totCost: " + str(totCost)
		print "watches completed: " + str(completedTrips)
		print '\n'
			
	#print the remaining supply
	remainingSupply = sum([e[2]['supply'] for e in supplyGraph.edges(data=True)])
	print "remaining supply: " + str(remainingSupply)
	
	#exit when no more supply
	if remainingSupply == 0:
		break