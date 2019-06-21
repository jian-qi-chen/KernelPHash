#! /usr/bin/env python3
from anytree import Node, RenderTree
from anytree.exporter import DotExporter
import KernelPHash as kph
import re

# read a kernel:0 (text file)
with open('test_cases/test.txt','r') as f:
    k0_txt = f.read()
    
# generate AST (the first element of ast0 is the root node)
ast0 = kph.ASTGen(k0_txt)

# plot the AST to an image AST.png
DotExporter( ast0[0] ).to_picture('AST.png')

# print the tree in terminal
for pre, fill, node in RenderTree( ast0[0] ):
    node_name = re.sub(r'\{[\d]+\}','',node.name) #just to remove the label {n}
    print("%s%s" % (pre,node_name))
    
# print DFS pre-order traversal
text_d = kph.TextGenDFS(ast0, order='pre')
print('\nDFS pre-order:',text_d,'\n')

# show text after changing variable/array names
text_du = kph.UnifyNaming(text_d)
print('After renaming:',text_du,'\n')

# print DFS post-order traversal
text_dpo = kph.TextGenDFS(ast0, order='post')
print('DFS post-order:',text_dpo,'\n')

# print BFS traversal
text_b = kph.TextGenBFS(ast0)
print('BFS:',text_b,'\n')

# get all variable names and frequency(how many times appears in the text) (dictionary var_dict - key: name, value: frequency)
var_dict = kph.VarList(ast0)
print('Varibles:\n',var_dict,'\n')

# get all array names and frequency (dictionary arr_dict - key: name, value: frequency)
arr_dict = kph.ArrList(ast0)
print('arrays:\n',arr_dict,'\n')

# generate hash list from the text of DFS pre-order (by default)
hash0 = kph.PHashGen(ast0)
print('Hash list of test_cases/test.txt:',hash0)

# read another kernel:1 , and generate hash1
with open('test_cases/test1.txt','r') as f:
    k1_txt = f.read()

ast1 = kph.ASTGen(k1_txt)
hash1 = kph.PHashGen(ast1)
print('Hash list of test_cases/test1.txt:',hash1,'\n')

# compare these two hash list ( calculate avg. hamming distance)
hm_dist = kph.HammingDist64(hash0,hash1)
print('Average Hamming Distance:',hm_dist)