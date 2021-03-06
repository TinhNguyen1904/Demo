# -*- coding: utf-8 -*-
"""HeThongGoiYHoanChinhHT.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/11vJsuwKlunuK2h-fo37p2YGZ-YlvRaAk
"""

#import thu vien
import networkx as nx
import random
import math
import csv
import datetime
from sklearn.metrics import accuracy_score
from sklearn.metrics import f1_score
import multiprocessing as mp
from sklearn.preprocessing import normalize
import numpy as np
import pandas as pd
from sklearn import model_selection as ms
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import mean_squared_error
from math import sqrt
import matplotlib.pyplot as plt
from collections import defaultdict

#Xu ly du lieu
location_geo = dict()
user_checkins = {}
with open('original_data.csv', 'r') as original_data:
    # Doc file CSV
    check_ins = csv.reader(original_data, delimiter='\t')
    for check_in in check_ins:
        # thêm một vị trí làm khóa và làm giá trị
        location_geo[check_in[1]] = (check_in[2], check_in[3])
        # thêm người dùng đăng ký
        user_checkins[(check_in[0], check_in[1])] = 1

with open('preprocessed_data.csv', 'w', newline='') as preprocessed_data:
    checkins_writer = csv.writer(preprocessed_data, delimiter='\t')
    for checkin_info in user_checkins:
        checkin = [checkin_info[0], checkin_info[1], user_checkins[checkin_info]];
        checkins_writer.writerow(checkin)

with open('geo_data.csv', 'w', newline='') as geo_data:
    geo_writer = csv.writer(geo_data, delimiter='\t')
    for lid, geo in location_geo.items():
        geo = [lid, geo[0], geo[1]];
        geo_writer.writerow(geo)

#import dataset
data=pd.read_csv('geo_data.csv')
data.head()

data1=pd.read_csv('preprocessed_data.csv')
data1.head()

!pip install pyspark

from pyspark import SparkContext
sc =SparkContext()

fbCombinedFileName = "dataset_facebook_combined.txt"
fbCombinedFile = sc.textFile(fbCombinedFileName)
fbCombinedFile.take(10)

!pip install pyspark

header = ['user_id', 'location_id', 'frequency']
df = pd.read_csv('preprocessed_data.csv', sep='\t', names=header)
df.head()

n_users = df.user_id.unique().shape[0]
n_locations = df.location_id.unique().shape[0]
print(' Số lượng người dùng = ' + str(n_users))
print(' Số vị trí = ' + str(n_locations))

train_data, test_data = ms.train_test_split(df, test_size=0.30)
print("Du lieu huan luyen:", train_data.shape)
print("Du lieu test:", test_data.shape)

#loc cong tac dua tren item
#Tạo hai ma trận mục người dùng, một ma trận để đào tạo và một ma trận khác để thử nghiệm
train_data_matrix = np.zeros((n_users, n_locations))

for checkin in train_data.itertuples():
    train_data_matrix[checkin[1], checkin[2]] = checkin[3]


test_data_matrix = np.zeros((n_users, n_locations))
#  Độ chính xác 
ground_truth_dic = defaultdict(set)

for checkin in test_data.itertuples():
    test_data_matrix[checkin[1], checkin[2]] = checkin[3]
    ground_truth_dic[int(checkin[1])].add(int(checkin[2]))

def cosine_similarity(train_matrix, kind='user', epsilon=1e-9):
    
    if kind == 'user':
        sim = train_matrix.dot(train_matrix.T) + epsilon
    elif kind == 'location':
        sim = train_matrix.T.dot(train_matrix) + epsilon
    norms = np.array([np.sqrt(np.diagonal(sim))])
    return (sim / norms / norms.T)

item_similarity = cosine_similarity(train_data_matrix, kind='location')

#Du doan
def predict(checkins, similarity, type='user'):
    if type == 'item':
        pred = checkins.dot(similarity)/np.array([np.abs(similarity).sum(axis=1)])
        
    return pred

item_prediction = predict(train_data_matrix, item_similarity, type='item')

def rmse(prediction, ground_truth):
    # dự đoán [ground_truth.nonzero ()] để chỉ xem xét các lần đăng ký dự đoán
    # (xếp hạng) trong tập dữ liệu.
    prediction = prediction[ground_truth.nonzero()].flatten()
    ground_truth = ground_truth[ground_truth.nonzero()].flatten()
    return sqrt(mean_squared_error(prediction, ground_truth))

IB_RMSE = rmse(item_prediction, test_data_matrix)
print('Dua vao Item: ' + str(IB_RMSE))

for i in range(0,3):
  
  for checkin in train_data.itertuples():
      train_data, test_data = ms.train_test_split(df, test_size=0.30)
      train_data_matrix[checkin[1], checkin[2]] = checkin[3]
  test_data_matrix = np.zeros((n_users, n_locations))
  #  Độ chính xác 
  ground_truth_dic = defaultdict(set)
  for checkin in test_data.itertuples():
      test_data_matrix[checkin[1], checkin[2]] = checkin[3]
      ground_truth_dic[int(checkin[1])].add(int(checkin[2]))
  item_similarity = cosine_similarity(train_data_matrix, kind='location')

  #Du doan
  item_prediction = predict(train_data_matrix, item_similarity, type='item')
  IB_RMSE = rmse(item_prediction, test_data_matrix)
  print('Dua vao Item'+ str(i) + str(IB_RMSE))

#lấy đỉnh và cạnh từ tập dữ liệu
def get_vertex1_tuple(entry):
  row = entry.split(' ')
  return int(row[0])

def get_vertex2_tuple(entry):
  row = entry.split(' ')
  return int(row[1])

def get_edge_tuple(entry):
  row = entry.split(' ')
  return int(row[0]),int(row[1])

!pip install pyspark

import pyspark

#tạo đỉnh và cạnh RDD
from pyspark.sql import Row
vertext1RDD = fbCombinedFile.map(get_vertex1_tuple).cache().distinct()
vertext2RDD = fbCombinedFile.map(get_vertex2_tuple).cache().distinct()
vertex1Union2 = vertext1RDD.union(vertext2RDD)
vertexRDD = vertex1Union2.distinct()
vertexCount = vertexRDD.count()
print (vertexCount)
print ('Dinh: %s' % vertexRDD.takeOrdered(5))
edgesRDD = fbCombinedFile.map(get_edge_tuple).cache()
ecount = edgesRDD.count()
print (ecount)
print ('Canh: %s' % edgesRDD.take(5))

!pip install python-igraph

import networkx as np

#import igraph  
import igraph
from igraph import *

#xây dựng biểu đồ với các đỉnh và cạnh từ tập dữ liệu
vertices = vertexRDD.collect()
edges = edgesRDD.collect()
g = Graph(vertex_attrs={"label":vertices}, edges=edges, directed=False)

from functools import reduce

#phân tích tập dữ liệu tổng thể trên biểu đồ đã xây dựng
print (g.is_connected(mode=STRONG))
print (g.farthest_points(directed=False, unconn=True, weights=None))
nwDiameter = g.diameter(directed=False, unconn=True, weights=None)
print (nwDiameter)
print (g.get_diameter(directed=False, unconn=True, weights=None))
nwBetweeness = g.betweenness(vertices=None, directed=False, cutoff=None, weights=None, nobigint=True)
meanNwBetweeness= reduce(lambda x, y: x + y, nwBetweeness) / len(nwBetweeness)
#print (meanNwBetweeness)

#kiểm tra mức độ phân phối của mang facebook
nwDegrees = g.degree()
meanNwDegree= reduce(lambda x, y: x + y, nwDegrees) / len(nwDegrees)
print (meanNwDegree)
from operator import add
nwDegreesRDD = sc.parallelize(nwDegrees)
counts = nwDegreesRDD.map(lambda x: (x, 1)).reduceByKey(add)
output = counts.collect()
for (degree, count) in output:
  print("%s %i" % (degree, count))

#xác định các nút không quan trọng
island_list = []
for v in vertices:
  friends_list = g.neighbors(vertex=v, mode=ALL)
  if (len(friends_list) < 2):
    island_list.append(v)
print (set(island_list))

island_degree_list=[]
for i in island_list:
  island_degree_list.append(g.degree(i))
print  (set(island_degree_list))

#xóa các nút khong quan trong khỏi biểu đồ
g.delete_vertices(island_list)
newVertices = []
newEdges = []
for v in g.vs:
    newVertices.append(v["label"])
for e in g.es:
    newEdges.append(e.tuple) 
print (len(set(vertices)))   
print (len(set(island_list)))    
print (len(set(newVertices)))

#xác định các nút quan trọng
core_node_list = []
core_degree_list = []
for v in g.vs:
  v_degree = g.degree(v)
  if(v_degree > 300): 
    core_node_list.append(v.index)
    core_degree_list.append(v_degree)
print (set(core_node_list))
mean_core_degree = reduce(lambda x, y: x + y, core_degree_list) / len(core_degree_list)
print (mean_core_degree)
#biểu đồ phụ tập trung vào nút "0" được xác định là nút quan trọng
node0_friends_list = g.neighbors(vertex=0, mode=ALL)
freinds_of_friends = g.neighborhood(vertices=0, order=2, mode=ALL)
print (len(node0_friends_list))
print (len(freinds_of_friends))

node0_friends_list.append(0)
node0_alters = []
node0_graph = g.subgraph(node0_friends_list, implementation = "auto")

for e in node0_graph.es:
    print (e.tuple)
    node0_alters.append(e.tuple)

#xác định nhóm trên đồ thị con
cliques_0 = node0_graph.maximal_cliques(min =2 , max =10)
print (cliques_0)

# Phần 2 - Đề xuất Kết bạn dựa trên các cụm được phát hiện
#Extract bộ giá trị từ tập dữ liệu
def returnTuple(entry):
  row = entry.split(' ')
  return int(row[0]),int(row[1]),-1

egoRDD = fbCombinedFile.map(returnTuple)

#Phát hiện bạn bè  cho hai cặp nút bất kỳ từ biểu đồ 
mutualFriends=[]
def generate(x):
  toNodes=[]
  for row in egoRDD.collect():
    if row[0]==x:
      toNodes.append(row[1])
  for i in range(0,len(toNodes)-1):
    mutualFriends.append([toNodes[i],toNodes[i+1],1])
    
prev = -1
  
for row in egoRDD.collect():
  if row[0]!=prev:
    generate(row[0])
  prev=row[0]
  
def predict(entry):
  return (entry[0],entry[1]),entry[2]
  
mutualFriendsRDD =sc.parallelize(mutualFriends)
prediction=mutualFriendsRDD.map(predict)

PredictionRDD = prediction.reduceByKey(lambda a, b: a + b)
sortedRdd=PredictionRDD.sortBy(lambda a: -a[1])
print (sortedRdd.collect())

def getAccuracy(suggestions,friends):
   n=len(friends) 
   correct=0
   for x in range(n):
       if friends[x]==suggestions[x]:
           correct +=1
   return (correct/n) * 100.0

#Chọn một người dùng mà đề xuất kết bạn phải được thực hiện
#Làm lại hoàn thành khoảng 200 người dùng
fromuser=115
#Lọc danh sách bạn bè chung cho người dùng đã chọn
suggestions_115_1 = sortedRdd.filter(lambda x:x[0][0]==fromuser).map(lambda x:(x[0][1],x[1]))
suggestions_115_2 = sortedRdd.filter(lambda x:x[0][1]==fromuser).map(lambda x:(x[0][0],x[1]))
suggestions_115 = suggestions_115_1.union(suggestions_115_2)
suggestions_115_sorted = suggestions_115.sortBy(lambda x:-x[1])
suggestions_115_RDD = suggestions_115_sorted.map(lambda x:x[0])
print (suggestions_115_RDD.collect())

#tất cả bạn bè của người dùng 115
friends_115_1= egoRDD.filter(lambda x:x[0]==fromuser).map(lambda x:x[1])
friends_115_2= egoRDD.filter(lambda x:x[1]==fromuser).map(lambda x:x[0])
friends_115 = friends_115_1.union(friends_115_2)
print (friends_115.collect())

#Đánh giá cho người dùng 115
from array import array
import numpy as np
suggestions=array('q',[116, 111, 41, 149, 138, 114, 20, 112])
friends=array('q',[116, 137, 140, 144, 149, 192, 214, 220, 226, 262, 312, 326, 343, 0, 2, 14, 17, 19, 20, 28, 41])
c=np.intersect1d(suggestions,friends)
print(c)
n=len(friends)
accuracy = len(c)/n *100
print(accuracy)

for fromuser in range (5,200):
  import numpy as np
  #Chọn một người dùng mà đề xuất kết bạn phải được thực hiện
  fromuser= fromuser
  #Lọc danh sách bạn bè chung cho người dùng đã chọn
  suggestions = sortedRdd.filter(lambda x:x[0][0]==fromuser).map(lambda x:(x[0][1],x[1]))
  suggestions = sortedRdd.filter(lambda x:x[0][1]==fromuser).map(lambda x:(x[0][0],x[1]))
  suggestions = suggestions.union(suggestions_115_1)
  suggestions_sorted = suggestions.sortBy(lambda x:-x[1])
  suggestions =suggestions_sorted.map(lambda x:x[0])
  print('Bạn bè được đề nghị ' + str(fromuser) + ':' ,suggestions.collect())
  #tất cả bạn bè của người dùng fromuser
  friends= egoRDD.filter(lambda x:x[0]==fromuser).map(lambda x:x[1])
  friends= egoRDD.filter(lambda x:x[1]==fromuser).map(lambda x:x[0])
  friends= friends.union(friends)
  print('Tất cả bạn bè của ' + str(fromuser) + ':' ,friends.collect())
  c=np.intersect1d(suggestions.collect(),friends.collect())
  print(c)
  n=len(friends.collect())
  accuracy = len(c)/n *100
  print('Đánh giá' + str(fromuser) +':' ,accuracy)
