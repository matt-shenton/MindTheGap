'''
Implementation of genome graphs.

Data structure : 
g.nodes : dict to store node attributes (seq, name)

g.edges : adjacency list of the nodes. 
       A negative nodeId indicates that the contig is reversed. In that case, 
       the source is the start of the contig, and the target is the end.

'''

import re
from pipeline.genome_graph.utils import reverse_complement
from pipeline.genome_graph.SequenceAlignment import NeedlemanWunsch

class GenomeNode:

       def __init__(self,nodeSeq,nodeName):
              # self.nodeId = nodeId
              self.nodeSeq = nodeSeq
              self.nodeName = nodeName
              # self.active = True  # Alternative way to remove nodes ?
       
       def __eq__(self, other):
              if isinstance(other, GenomeNode):
                     return self.nodeSeq == other.nodeSeq and self.nodeName == other.nodeName 
              return False

       def __ne__(self, other):
              return not self.__eq__(other)

       def __hash__(self):
              return hash((self.nodeSeq, self.nodeName))

class GenomeGraph:

       def __init__(self):
              self.nodes = {}
              self.edges = {}
              self.overlap = 0

       def nNodes(self):
              return(len(self.nodes))
       
       def nEdges(self):
              return(len([j for i in self.edges.values() for j in i])/2)

       def add_node(self,nodeName,nodeSeq):
              newNode = GenomeNode(nodeSeq,nodeName)
              try:
                     assert newNode not in self.nodes.values()
              except AssertionError:
                     print("Node already in graph")
                     
              if len(self.nodes)>0:
                     nodeId = max(self.nodes.keys())+1
              else: 
                     nodeId = 1
              self.nodes[nodeId] = newNode
              self.edges[nodeId] = set()
              self.edges[-nodeId] = set()

       def add_edge(self, src,dst):
              self.edges[src].add(dst)
              self.edges[-dst].add(-src)

       def rem_edge(self,src,dst):
              try:
                     self.edges[src].remove(dst)
                     self.edges[-dst].remove(-src)
              except KeyError:
                     print("Edge not in graph")
              
       def rem_node(self,nodeId):
              try:
                     self.nodes.pop(nodeId)
              except KeyError:
                     print("Node not in graph")

              for n in self.get_neighbors(nodeId).copy():
                     self.rem_edge(-n,-nodeId)

              for n in self.get_neighbors(-nodeId).copy():
                     self.rem_edge(-n,nodeId)

              self.edges.pop(nodeId)
              self.edges.pop(-nodeId)

       def get_neighbors(self,nodeId):
              return(self.edges[nodeId])

       def get_node_seq(self,nodeId):
              if nodeId < 0:
                     nodeSeq = reverse_complement(self.nodes[-nodeId].nodeSeq.strip())
              else:
                     nodeSeq = self.nodes[nodeId].nodeSeq.strip()
              return(nodeSeq)
   
           
       @classmethod
       def read_gfa(self,file):
              
              g = GenomeGraph()
              nodeIds = {}  # Used to retrieve a node Id from a name. Is it useful though?
              nlines = 0
              with open(file) as f:
                     for line in f:
                            nlines += 1
                            if re.match(r"S.*", line):
                                   nodeName = line.split("\t")[1]
                                   nodeSeq = line.split("\t")[2]
                                   g.add_node(nodeName,nodeSeq)
                                   nodeIds[nodeName] = g.nNodes()
                            elif re.match(r"L.*",line):
                                   startName,startDir,endName,endDir,overlap = line.split("\t")[1:]

                                   if g.overlap == 0:
                                          g.overlap = overlap
                                   
                                   startNode = nodeIds[startName]
                                   endNode = nodeIds[endName]

                                   if startDir == "-":
                                          startNode = - startNode
                                   if endDir == "-":
                                          endNode = - endNode

                                   g.add_edge(startNode,endNode)                                  
              return(g)


       ###########  Graph simplification ###########

       def pop_bubble(self,nodeId):
              n1 = self.get_neighbors(nodeId).copy()
              n2 = self.get_neighbors(-nodeId).copy()

              if len(n1)==len(n2)==1:
                     r = self.get_neighbors(-n1.pop())
                     l = self.get_neighbors(-n2.pop())
                     assert -nodeId in r and nodeId in l

                     r_rev = {-i for i in r}

                     inter = l & r_rev
                     assert nodeId in inter

                     if len(inter)>0:
                            toRemove = self.compare_nodes(inter)
                            print(toRemove)
                            for node in toRemove:
                                   print("Redundant node : " + self.nodes[abs(node)].nodeName)
                                   print(node)
                                   self.rem_node(abs(node))

       def pop_all_bubbles(self):
              for node in list(self.nodes):
                     print(node)
                     if node in self.nodes.keys():
                            self.pop_bubble(node)
              


       def compare_nodes(self,nodeSet):
              uniq = set()
              remove = set()
              for node in nodeSet:
                     nodeSeq = self.get_node_seq(node) # Gets rc if node<0
                            
                     if node in uniq:
                            continue
                     foundmatch = False
                     for refNode in uniq:
                            refSeq =  self.get_node_seq(refNode)
                            if refSeq == nodeSeq:
                                   remove.add(node)
                                   foundmatch = True
                            else:
                                   nw = NeedlemanWunsch(refSeq, nodeSeq, 10, -5, -5)
                                   id = nw.getIdentity()
                                   if id > 0.9:
                                          remove.add(node)
                                          foundmatch = True
                                   print(id)
                     if not foundmatch:
                            uniq.add(node)
              return(remove)
