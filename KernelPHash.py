#! /usr/bin/env python3
""" Author: Jianqi Chen, Date: May 2019 """
from anytree import Node
import os, sys, re, math

TEXTGEN = 'preorder' # can be 'preorder', 'postorder' or 'BFS'
PHASH = 'selfmade' #perceptual hash algorithm, 'selfmade' is using TextHash64 function, 'pHashlib' is using pHash C++ library
prevent_overlapped_name = True
node_name_dict = {}
os.system('cd pHash && rm text_ast hash hash.info')
os.system('chmod 744 pHash/text_hash.exe')

def usage():
    print('Please see example.py')

def main(argv):
    from anytree.exporter import DotExporter
    from anytree import RenderTree

    ast_list = []
    for i in range(len(argv)):
        # send in one argument - the name of kernel code file.
        with open(argv[i],'r') as f:
            kernel_txt = f.read()

        ast_nodes = ASTGen(kernel_txt)

        # plot to a PNG image
        DotExporter(ast_nodes[0]).to_picture('AST'+str(i)+'.png')

        # print tree in terminal
        for pre, fill, node in RenderTree(ast_nodes[0]):
            if prevent_overlapped_name == 1:
                node_name = re.sub(r'\{[\d]+\}','',node.name)
            print("%s%s" % (pre,node_name))

        # print DFS pre-order traversal
        text_d = TextGenDFS(ast_nodes, order='pre')
        print('DFS pre-order:',text_d)

        # show text after changing variable/array names
        text_du = UnifyNaming(text_d)
        print('After renaming:',text_du)

        # print BFS traversal
        text_b = TextGenBFS(ast_nodes)
        print('BFS:',text_b)

        ast_list.append(ast_nodes)
    
    # generate hash and compare
    if len(ast_list)>1:
        hash_0 = PHashGen(ast_list[0])
        hash_1 = PHashGen(ast_list[1])
        hm_dist = HammingDist64(hash_0,hash_1)

        print('Hash list of',argv[0],':',hash_0)
        print('Hash list of',argv[1],':',hash_1)
        print('Average Hamming Distance:',hm_dist)


# Generate abstract syntax tree (AST), text is a string of kernel source code
# return a list of nodes in AST. The FIRST element is the root.
def ASTGen(text):
    global keyword, operator
    keyword = ['for','if','else','while','return']
    # operator priority high to low ('{','}' are actually not operators, put them here just for convenience)
    operator = ['{','}','(',')','[',']','.','->','!','~','++','--','*','/','%','+','-','<<','>>','<','<=','>','>=','==','!=','&','^','|','&&','||','?',':','=','+=','-=','*=','/=','%=','>>=','<<=','&=','^=','|=']
    # operators with three letters (need to be processed first when splitting the text)
    operator_3c = list( filter(lambda p: len(p)==3, operator) )
    operator_2c = list( filter(lambda p: len(p)==2, operator) )
    operator_1c = list( filter(lambda p: len(p)==1, operator) )

    text_real =  re.sub(r'\n[ \t\r\n]*\n','\n', re.sub(r'[ \t]*(//.*?[\r\n]+|//.*?$|/\*.*?\*/)','',text,flags=re.S) ) # remove comments, and multiple newlines

    # split the text
    text_s = re.split(r'\s+',text_real)
    text_s = map( lambda p: re.split(r'(;)',p), text_s )
    text_s = sum(text_s,[])
    text_s = list(filter(lambda p: p!='', text_s) )
    
#    for keyw in keyword:
#        new_text_s = []
#        for item in text_s:
#            new_text_s += re.split(r'(\b'+re.escape(keyw)+r'\b)',item)
#        text_s = new_text_s

    for op in operator_3c:
        new_text_s = []
        for item in text_s:
            new_text_s += re.split(r'('+re.escape(op)+r')',item)
        text_s = new_text_s

    for op in operator_2c:
        new_text_s = []
        for item in text_s:
            if not item in operator_3c:
                new_text_s += re.split(r'('+re.escape(op)+r')',item)
            else:
                new_text_s.append(item)
        text_s = new_text_s

    for op in operator_1c:
        new_text_s = []
        for item in text_s:
            if not ( (item in operator_3c) or (item in operator_2c) ):
                new_text_s += re.split(r'('+re.escape(op)+r')',item)
            else:
                new_text_s.append(item)
        text_s = new_text_s

    text_s = list(filter(lambda p: p!='', text_s) )
    # splitting finished

    text_len = len(text_s)
    i = 0
    root_node = Node("Start")
    node_list = [ root_node ]
    while i < text_len:
        node_l, j = SyntaxRule(text_s,i,root_node)
        i = j
        node_list += node_l

    if len( node_list[0].children ) == 1:
        node_list[1].parent = None
        del node_list[0]

    return node_list


# text_list is the list of text of splitted kernel, start_index is the index of text_list to start analyzing, parent_node is the parent node of the starting point.
# return (node_list, j), node_list is the list of node of analyzed text, j is the next index of the end of this analysis.
def SyntaxRule(text_list, start_index, parent_node):
    # this 'for' rule ignores the iterator statements (in the round brackets)
    if text_list[start_index] == 'for':
        node_list = [ Node( NodeName('for'),parent=parent_node) ]
        i = 2
        l_count = 1
        r_count = 0
        while l_count != r_count:
            if text_list[start_index+i] == '(':
                l_count += 1
            elif text_list[start_index+i] == ')':
                r_count += 1
            i += 1
        
        offset = i-1
        node_l, j = SyntaxRule(text_list, start_index+offset+1, node_list[0])
        node_list += node_l
        return (node_list, j)

    # this 'while' rule ignores the iterator statements (in the round brackets)
    elif text_list[start_index] == 'while':
        node_list = [ Node( NodeName('while'),parent=parent_node) ]
        i = 2
        l_count = 1
        r_count = 0
        while l_count != r_count:
            if text_list[start_index+i] == '(':
                l_count += 1
            elif text_list[start_index+i] == ')':
                r_count += 1
            i += 1
        
        offset = i-1
        node_l, j = SyntaxRule(text_list, start_index+offset+1, node_list[0])
        node_list += node_l
        return (node_list, j)

    # standard 'if else' rule, three childs: the first is condition, the second is if statement, the third is else statement
    elif text_list[start_index] == 'if':
        node_list = [ Node( NodeName('if'),parent=parent_node) ]
        i = 2
        l_count = 1
        r_count = 0
        while l_count != r_count:
            if text_list[start_index+i] == '(':
                l_count += 1
            elif text_list[start_index+i] == ')':
                r_count += 1
            i += 1
        
        offset_cond = i-1
        cond_st = text_list[start_index+2 : start_index+offset_cond]
        tree_l = AssignSyntaxRule(cond_st)
        node_l = ConvertNodeList(tree_l, node_list[0]) # condition
        node_list += node_l

        node_l, j = SyntaxRule(text_list, start_index+offset_cond+1, node_list[0]) # if statement
        node_list += node_l

        if text_list[j] == 'else':
            node_l, j = SyntaxRule(text_list, j+1, node_list[0]) # else statement
            node_list += node_l

        return (node_list, j)

    # '{}' rule
    elif text_list[start_index] == '{':
        node_list = [ Node( NodeName('BLOCK'),parent=parent_node) ]
        i = 1
        l_count = 1
        r_count = 0
        while l_count != r_count:
            if text_list[start_index+i] == '{':
                l_count += 1
            elif text_list[start_index+i] == '}':
                r_count += 1
            i += 1

        offset_right_bracket = i-1
        j = start_index + 1
        # while in the curly brackets
        while j < (start_index + offset_right_bracket):
            node_l, j = SyntaxRule(text_list, j, node_list[0])
            node_list += node_l

        return (node_list, start_index+offset_right_bracket+1)

    # 'return' rule
    elif text_list[start_index] == 'return':
        node_list = [ Node( NodeName('return'),parent=parent_node) ]
        node_l, j = SyntaxRule(text_list, start_index+1, node_list[0])
        node_list += node_l

        return (node_list, j)
    
    # assignment rule
    else:
        i = 0
        while text_list[start_index+i] != ';':
            i += 1

        offset_semi_col = i
        assign_st = text_list[start_index : start_index+offset_semi_col]
        tree_list = AssignSyntaxRule(assign_st)
        node_list = ConvertNodeList(tree_list, parent_node)

        return (node_list, start_index+offset_semi_col+1)

# syntax rule for assignment statements, similar to SyntaxRule(), but instead of returning a node list, it return a list show the tree structure that can be convert to a node_list
# Arguments' difference are start index is 0 by default, text_list is only for one statement.
# return value: tree format - [parent_name, [child1 name, [..],[..]], [child2 name,[..],[..]], [..], ..]
def AssignSyntaxRule(text_list):
    if text_list == []:
        return None
    # check form the operators with lowest priority to the operators with highest priority
    if bool( {'+=','-=','*=','/=','%=','>>=','<<=','&=','^=','|='} & set(text_list) ):
        for i,item in enumerate(text_list):
            for sym in ['+','-','*','/','%','>>','<<','&','^','|']:
                if item == (sym+'='):
                    LS = AssignSyntaxRule(text_list[0:i])
                    RS = AssignSyntaxRule(text_list[i+1:])
                    return ['=',LS,[sym,LS,RS]]

    if '=' in text_list:
        i = text_list.index('=')
        LS = AssignSyntaxRule(text_list[0:i])
        RS = AssignSyntaxRule(text_list[i+1:])
        return ['=',LS,RS]

    if '?' in text_list and ':' in text_list:
        for i,item in enumerate(text_list):
            if item == '?':
                quest_ind = i
            if item == ':':
                col_ind = i
        LS = AssignSyntaxRule(text_list[0:quest_ind])
        MS = AssignSyntaxRule(text_list[quest_ind+1:col_ind])
        RS = AssignSyntaxRule(text_list[col_ind+1:])
        return ['if',LS,MS,RS]

    if '||' in text_list:
        i = len(text_list)-1
        while i >= 0:
            # scan from right to left (execution from left to right), make sure not in brackets
            if ( text_list[i] == '||' ) and ( text_list[:i].count('(') == text_list[:i].count(')') ) and  ( text_list[:i].count('[') == text_list[:i].count(']') ):
                LS = AssignSyntaxRule(text_list[0:i])
                RS = AssignSyntaxRule(text_list[i+1:])
                return ['||',LS,RS]
            i -= 1

    if '&&' in text_list:
        i = len(text_list)-1
        while i >= 0:
            if ( text_list[i] == '&&' ) and ( text_list[:i].count('(') == text_list[:i].count(')') ) and  ( text_list[:i].count('[') == text_list[:i].count(']') ):
                LS = AssignSyntaxRule(text_list[0:i])
                RS = AssignSyntaxRule(text_list[i+1:])
                return ['&&',LS,RS]
            i -= 1

    if '|' in text_list:
        i = len(text_list)-1
        while i >= 0:
            if ( text_list[i] == '|' ) and ( text_list[:i].count('(') == text_list[:i].count(')') ) and  ( text_list[:i].count('[') == text_list[:i].count(']') ):
                LS = AssignSyntaxRule(text_list[0:i])
                RS = AssignSyntaxRule(text_list[i+1:])
                return ['|',LS,RS]
            i -= 1

    if '^' in text_list:
        i = len(text_list)-1
        while i >= 0:
            if ( text_list[i] == '^' ) and ( text_list[:i].count('(') == text_list[:i].count(')') ) and  ( text_list[:i].count('[') == text_list[:i].count(']') ):
                LS = AssignSyntaxRule(text_list[0:i])
                RS = AssignSyntaxRule(text_list[i+1:])
                return ['^',LS,RS]
            i -= 1

    if '&' in text_list:
        i = len(text_list)-1
        while i >= 0:
            if ( text_list[i] == '&' ) and ( text_list[:i].count('(') == text_list[:i].count(')') ) and  ( text_list[:i].count('[') == text_list[:i].count(']') ):
                LS = AssignSyntaxRule(text_list[0:i])
                RS = AssignSyntaxRule(text_list[i+1:])
                return ['&',LS,RS]
            i -= 1

    if bool( {'==','!='} & set(text_list) ):
        i = len(text_list)-1
        while i >= 0:
            if ( text_list[i] in ['==','!='] ) and ( text_list[:i].count('(') == text_list[:i].count(')') ) and  ( text_list[:i].count('[') == text_list[:i].count(']') ):
                LS = AssignSyntaxRule(text_list[0:i])
                RS = AssignSyntaxRule(text_list[i+1:])
                return [text_list[i],LS,RS]
            i -= 1

    if bool( {'<','<=','>','>='} & set(text_list) ):
        i = len(text_list)-1
        while i >= 0:
            if ( text_list[i] in ['<','<=','>','>='] ) and ( text_list[:i].count('(') == text_list[:i].count(')') ) and  ( text_list[:i].count('[') == text_list[:i].count(']') ):
                LS = AssignSyntaxRule(text_list[0:i])
                RS = AssignSyntaxRule(text_list[i+1:])
                return [text_list[i],LS,RS]
            i -= 1

    if bool( {'<<','>>'} & set(text_list) ):
        i = len(text_list)-1
        while i >= 0:
            if ( text_list[i] in ['<<','>>'] ) and ( text_list[:i].count('(') == text_list[:i].count(')') ) and  ( text_list[:i].count('[') == text_list[:i].count(']') ):
                LS = AssignSyntaxRule(text_list[0:i])
                RS = AssignSyntaxRule(text_list[i+1:])
                return [text_list[i],LS,RS]
            i -= 1

    if bool( {'+','-'} & set(text_list) ):
        i = len(text_list)-1
        while i >= 0:
            if ( text_list[i] in ['+','-'] ) and ( text_list[:i].count('(') == text_list[:i].count(')') ) and  ( text_list[:i].count('[') == text_list[:i].count(']') ):
                LS = AssignSyntaxRule(text_list[0:i])
                RS = AssignSyntaxRule(text_list[i+1:])
                return [text_list[i],LS,RS]
            i -= 1

    if bool( {'*','/','%'} & set(text_list) ):
        i = len(text_list)-1
        while i >= 0:
            if ( text_list[i] in ['*','/','%'] ) and ( text_list[:i].count('(') == text_list[:i].count(')') ) and  ( text_list[:i].count('[') == text_list[:i].count(']') ):
                LS = AssignSyntaxRule(text_list[0:i])
                RS = AssignSyntaxRule(text_list[i+1:])
                return [text_list[i],LS,RS]
            i -= 1

    if bool( {'!','~','++','--'} & set(text_list) ):
        i = len(text_list)-1
        while i >= 0:
            if ( text_list[i] in ['!','~','++','--'] ) and ( text_list[:i].count('(') == text_list[:i].count(')') ) and  ( text_list[:i].count('[') == text_list[:i].count(']') ):
                LS = AssignSyntaxRule(text_list[0:i])
                RS = AssignSyntaxRule(text_list[i+1:])
                if LS == None:
                    return [text_list[i],RS]
                elif RS == None:
                    return [text_list[i],LS]
                else:
                    print("Error when dealing with '!','~','++','--'")
                    print('text:',text_list)
                    return [-1]
            i -= 1
    
    if bool( {'.','->'} & set(text_list) ):
        i = len(text_list)-1
        while i >= 0:
            if ( text_list[i] in ['.','->'] ) and ( text_list[:i].count('(') == text_list[:i].count(')') ) and  ( text_list[:i].count('[') == text_list[:i].count(']') ):
                LS = AssignSyntaxRule(text_list[0:i])
                RS = AssignSyntaxRule(text_list[i+1:])
                return [LS,text_list[i],RS]
            i -= 1

    if text_list[0] == '[' and text_list[-1] == ']':
        MS = AssignSyntaxRule(text_list[1:-1])
        return ['[ ]',MS]

    if text_list[0] == '(' and text_list[-1] == ')':
        MS = AssignSyntaxRule(text_list[1:-1])
        return MS

    # Array
    if ('[' in text_list) and (']' in text_list) and re.match(r'^[_a-zA-Z][_a-zA-Z0-9]*$',text_list[0]):
        tree_list = [ 'Arr('+text_list[0]+')' ]
        l_count = 0
        r_count = 0
        for i, item in enumerate(text_list):
            if item == '[':
                l_count += 1
                if l_count == 1:
                    l_start = i
            elif item == ']':
                r_count += 1
                if (l_count>0) and (r_count>0) and (l_count==r_count):
                    r_end = i
                    tree_list.append( AssignSyntaxRule(text_list[l_start:r_end+1]) )
                    l_count = 0
                    r_count = 0
        return tree_list

    # Variable
    if ( len(text_list)==1 ) and re.match(r'^[_a-zA-Z][_a-zA-Z0-9]*$',text_list[0]):
        return [ 'Var('+text_list[0]+')' ]

    # Constant
    if ( len(text_list)==1 ) and re.match(r'^[\.0-9]*$',text_list[0]):
        return [ 'Const('+text_list[0]+')' ]

    print('Error: No assignment rule found:',text_list)
    return ['Error']

# convert tree lists (outputs by AssignSyntaxRule()) to node list (the format of the output of SyntaxRule())
def ConvertNodeList(tree_list, parent_node):
    node_list = [ Node( NodeName(tree_list[0]), parent=parent_node) ]
    for child_list in tree_list[1:]:
        node_l = ConvertNodeList(child_list, node_list[0])
        node_list += node_l

    return node_list

# To prevent same name of different nodes (e.g. many name are '+'), add {N} at the end (e.g. instead of '+', use '+{1}'). Set prevent = 1 to enable the function.
def NodeName(name, prevent = prevent_overlapped_name):
    global node_name_dict
    if prevent:
        if not name in node_name_dict:
            node_name_dict[name] = 1
        else:
            node_name_dict[name] += 1

        return name+'{'+str(node_name_dict[name])+'}'
    else:
        return name

# To generate a string from the AST, this function use depth first traversal, order can be 'pre'(preorder) or 'post'(postorder) 
def TextGenDFS(node_list,order='pre'):
    def DFTrav(node,order='pre'):
        nonlocal text
        if order=='pre':
            text += ( ' '+re.sub(r'\{[\d]+\}','',node.name) )

        for child_node in node.children:
            DFTrav(child_node,order=order)

        if order=='post':
            text += ( ' '+re.sub(r'\{[\d]+\}','',node.name) )

        return

    text = ''
    DFTrav(node_list[0], order=order)
    return text[1:]

# To generate a string from the AST, this function use breadth first traversal
def TextGenBFS(node_list):
    text = ''
    queue_b = [ node_list[0] ]

    while bool( queue_b ): # while queue not empty
        text += ( ' '+re.sub(r'\{[\d]+\}','',queue_b[0].name) )
        for child_node in queue_b[0].children:
            queue_b.append(child_node)
        del queue_b[0]

    return text[1:]

# to eliminate the impact of different name of variables and arrays, rename them in the text generated from AST.
def UnifyNaming(text):
    var_l = re.findall(r'Var\(.+?\)',text)
    arr_l = re.findall(r'Arr\(.+?\)',text)

    # remove duplicated elements while maintaining the order
    var_list = []
    for var in var_l:
        if not var in var_list:
            var_list.append(var)

    arr_list = []
    for arr in arr_l:
        if not arr in arr_list:
            arr_list.append(arr)

    # change the name
    new_text = text
    for i, var in enumerate(var_list):
        new_name = str(i)*3
        new_text = new_text.replace(var,'Var('+new_name+')')
    
    for i, arr in enumerate(arr_list):
        new_name = str(i)*3
        new_text = new_text.replace(arr,'Arr('+new_name+')')

    return new_text

# given a AST tree (node_list), return a dictionary of variables, key is variable name, value is frequency.
def VarList(node_list):
    text = TextGenBFS(node_list)
    var_l = re.findall(r'Var\(.+?\)',text)
    var_lm = map(lambda p: p[4:-1], var_l)
    
    var_dict = {}
    for var in var_lm:
        if not var in var_dict:
            var_dict[var] = 1
        else:
            var_dict[var] += 1
            
    return var_dict
    
# similar to VarList(), this one target arrays
def ArrList(node_list):
    text = TextGenBFS(node_list)
    arr_l = re.findall(r'Arr\(.+?\)',text)
    arr_lm = map(lambda p: p[4:-1], arr_l)
    
    arr_dict = {}
    for arr in arr_lm:
        if not arr in arr_dict:
            arr_dict[arr] = 1
        else:
            arr_dict[arr] += 1
            
    return arr_dict

# Generate Perceptual hash from the AST, node_list is a list of nodes in AST
# textgen is the way to generate text form AST, can be 'preorder', 'postorder','BFS'
# phash is the perceptual hash algorithm, 'selfmade' is using TextHash64 function, 'pHashlib' is using pHash C++ library
# returns a list of 32-bit hex hash(string)
def PHashGen(node_list, textgen=TEXTGEN, phash=PHASH):
    if textgen == 'preorder':
        text_ast = TextGenDFS(node_list,order='pre')
    elif textgen == 'postorder':
        text_ast = TextGenDFS(node_list,order='post')
    elif textgen == 'BFS':
        text_ast = TextGenBFS(node_list)
    else:
        print('Error: textgen=',textgen,'not supported')
        return -1

    text_ast = UnifyNaming(text_ast) # change variable/array names

    i = 1
    if phash=='selfmade':
        limit_low = 80
    elif phash=='pHashlib':
        limit_low = 500
        
    while len(text_ast) < limit_low: # avoid the text is too short
        text_ast += text_ast
        i += 1
        
    text_ast += ('101'*i + ' 5656 '*(i>4 and i<8) + '7878'*(i>8 and i<16) + '9090'*(i>16))
    
    if phash=='selfmade':
        hash_v = TextHash64(text_ast)

    elif phash=='pHashlib':
        with open('pHash/text_ast','w') as f:
            f.write(text_ast)
            
        ret_v = os.system('export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$(pwd)/pHash/src && cd pHash && ./text_hash.exe text_ast')
        if ret_v != 0:
            print('Error occur in text_hash.exe')
            return -1

        with open('pHash/hash','r') as f:
            hash_v = f.read().splitlines()

    return hash_v

# Compute the average hamming distance, the return value is a number form 0 to 32. This is a wrapper
def HammingDist(hash1,hash2,printing=False):
    hm_dist1 = HammingDist_avg(hash1,hash2,printing=printing)
    hm_dist2 = HammingDist_avg(hash2,hash1,printing=printing)
    if printing:
        print('hm_dist1 =',hm_dist1)
        print('hm_dist2 =',hm_dist2)
        
    return (hm_dist1+hm_dist2)/2

# Compute the average hamming distance, the return value is a number form 0 to 32
def HammingDist_avg(hash1,hash2,printing=False):
    if printing:
        print('hash1 list:',hash1)
        print('hash2 list:',hash2)

    # use the smallest hamming distance between two hash list as the hamming distance
    hm_dist_list = []
    for h1 in hash1:
        if not h1 in hash2:
            for h2 in hash2:
                cur_hm = HammingDist_real(h1,h2,printing=printing)
                hm_dist_list.append(cur_hm)

    hm_dist = sum(hm_dist_list)/(len(hash1)*len(hash2)) # calculate the average
    if printing:
        print('Overall hamming distance =',hm_dist)

    return hm_dist

# Compute the hamming distance, the return value is a number form 0 to 32, input is two hashes(string)
def HammingDist_real(hash1,hash2,printing=False):
    hash1_b = '{0:b}'.format(int(hash1,16)) #hex to binary
    hash2_b = '{0:b}'.format(int(hash2,16))

    hash1_b = '0'*(32-len(hash1_b))+hash1_b # add zeros
    hash2_b = '0'*(32-len(hash2_b))+hash2_b

    count = 0
    for i in range(32):
        if (hash1_b[i] != hash2_b[i]):
            count += 1

    if printing:
        print('hash1 =',hash1_b,'(',hash1,')')
        print('hash2 =',hash2_b,'(',hash2,')')
        print('hamming distance =',count)

    return count 

# generate a perceptual hash list of a given string textin
def TextHash64(textin):
    hash_list = []
    for i in range(8):
        new_textin = 'dummy '*i+textin
        cur_hash_list = TextHash64_real(new_textin)
        hash_list += cur_hash_list
        
    # reduce hash list size
    target_hd = 0
    while(len(hash_list)>32):
        hashl_len = len(hash_list)
        delete_list = [False]*hashl_len
        
        for i in range(hashl_len):
            if delete_list[i]:
                continue
            if delete_list.count(False)<32:
                continue
            for j in range(i+1,hashl_len):
                if HammingDist64_real(hash_list[i],hash_list[j]) == target_hd:
                    delete_list[j] = True
        
        new_hashl = filter(lambda p: p[1] == False, zip(hash_list,delete_list))
        new_hashl = list(zip(*new_hashl))[0]
        
        hash_list = list(new_hashl)
        target_hd += 1
        
    return hash_list

def TextHash64_real(textin):
    # every paragraph generate a hash value of 64 bits
    win_len = 8 # window length, in number of characters
    para_len = 10 # paragraph length, in number of windows
    
    # align with space
    text_t = textin.split(' ')
    text = ''
    for txt_item in text_t:
        sec_len = math.ceil( len(txt_item)/win_len )*win_len
        new_item = txt_item+' '*(sec_len-len(txt_item))
        text += new_item
    
    txt_len = len(text)
    
    round = int(txt_len/(win_len*para_len)) + 1
    remain_char = txt_len
    hash_list = []
    for i in range(round):
        char_list = [0]*win_len # the list of character value sum, to generate hash
        j = 0
        while remain_char > 0 and j < para_len:
            k = 0
            while remain_char > 0 and k < win_len:
                char_list[k] += ord( text[i*(win_len*para_len)+j*win_len+k] )
                remain_char -= 1
                k += 1
            j += 1
                
        char_list = [ p%256 for p in char_list ]    
        hash_l = [ '%02x' % p for p in  char_list ]
        hash = ''.join(hash_l)
        hash_list.append(hash)
        
    return hash_list
 
# Compute the hamming distance between two hash list
def HammingDist64(hash_list1, hash_list2):
    hm_dist1 = HammingDist64_oneside(hash_list1, hash_list2)
    hm_dist2 = HammingDist64_oneside(hash_list2, hash_list1)
    
    return (hm_dist1+hm_dist2)/2

def HammingDist64_oneside(hash_list1, hash_list2):
    min_hamming_dist_list = []
    
    for hash1 in hash_list1:
        hm_dist_min = 64
        for hash2 in hash_list2:
            cur_hm_dist = HammingDist64_real(hash1, hash2)
            if cur_hm_dist==0:
                hm_dist_min = 0
                break
            elif cur_hm_dist < hm_dist_min:
                hm_dist_min = cur_hm_dist
        
        min_hamming_dist_list.append(hm_dist_min)
    
    # use average minimum hamming distance as the Hamming Distance of two hash list
    avg_min_hd = sum(min_hamming_dist_list)/len(min_hamming_dist_list) 
    return avg_min_hd
    
    
def HammingDist64_real(hash1,hash2):
    hash1_b = '{0:b}'.format(int(hash1,16)) #hex to binary
    hash2_b = '{0:b}'.format(int(hash2,16))

    hash1_b = '0'*(64-len(hash1_b))+hash1_b # add zeros
    hash2_b = '0'*(64-len(hash2_b))+hash2_b

    count = 0
    for i in range(64):
        if (hash1_b[i] != hash2_b[i]):
            count += 1

    return count 

if __name__ == "__main__":
    main(sys.argv[1:])
