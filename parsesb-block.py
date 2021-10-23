import os
import json 
import sys
from itertools import count
from numpy.core.shape_base import block
import time

block_count = count()
# variable_mapping = {}
# list_mapping = {}
null_list = []
# used_children = set()
#PARSER RULE 
# BlockGroup := CBlock | CapBlock | HatBlock | StackBlock | ReporterBlock | BooleanBlock | CallBlock;
# Primitive := Variable | Number | String;

# Project: = [Scripts];
# Script := [Blocks];

# CBlock := Block (type=control_if);
# Block (type=control_if) := [fields | next | inputs];
# Input := InputTypeCode + [Block | Primitive];
# Next := BlockGroup;
# Field := ;



class Block:


    def __init__(self,block_id="",name="",nextid="",shadow="",inputs=[],fields=[],parent=None):
        # super().__init__()
        self.block_id = block_id
        self.name = name
        self.nextid = nextid
        self.shadow = shadow
        self.inputs = inputs
        self.fields = fields
        self.parent = parent

      
def get_blocks(targets):
    block_count = count(0,1)
    blocks = []
    # used_children = set()
    

    for obj in targets:
        blocks_item = obj["blocks"]
        process_blocks(blocks,blocks_item)
        
    return blocks

def locate_next_block(blocks_item,id):
    for block_id in blocks_item:
        if(id == block_id):
            searched_block = blocks_item[id]
            return Block(id,searched_block["opcode"],searched_block["next"],searched_block["shadow"],searched_block["inputs"],searched_block["fields"],searched_block["parent"])
    
    return None

def process_blocks(blocks,blocks_item):
    visited = []
    blockid_map = {}
    #index pair that visit children before parent 
    visited_first_children = []
    inputid_map = {}
    for block_id in blocks_item:
    # check if this block is already by previous parent-children relationship 
        if(block_id in visited):
            continue
        #stack of block
        stack = []
        #list of block id visited 
        block = blocks_item[block_id]
        block_name = block["opcode"]
        nextb = block["next"] 
        shadow = False
        inputs = block["inputs"]
        fields = block["fields"]
        parent = block["parent"]
        cur_block = Block(block_id,block_name,nextb,shadow,inputs,fields,parent)
        stack.append(cur_block)
        visited.append(cur_block.block_id)

        prev_parent_index = -1
        process_blocks_stacks(blocks,stack,prev_parent_index,blockid_map,blocks_item,visited,visited_first_children,inputid_map)
    
    # if(len(visited_first_children) != 
    for left_block in visited_first_children:
        # if(blockid_map[left_block.block_id] in used_children):
        #     print("!!!ERROR {}".format(blockid_map[left_block.block_id]))
        blocks[blockid_map[left_block.parent]]["children"].append(blockid_map[left_block.block_id])
        print(blocks[blockid_map[left_block.parent]])
        # used_children.add(blockid_map[left_block.block_id])

    for inputid in inputid_map:
        # print("##INPUT_MAP {}: {}".format(blocks[inputid_map[inputid]]["type"],blockid_map[inputid]))
        # if(blockid_map[inputid] in used_children):
        #     print("!!!ERROR {}".format(blockid_map[inputid]))
        blocks[inputid_map[inputid]]["children"].append(blockid_map[inputid])
        # used_children.add(blockid_map[inputid])

def process_blocks_stacks(blocks,stack,prev_parent_index,blockid_map,blocks_item,visited,visited_first_children,inputid_map):
    while(len(stack)!=0):
        pop_block = stack.pop()
        cur_parent_index = len(blocks)
        blockid_map[pop_block.block_id] = cur_parent_index

        # if(shape_block == None):
        #     null_list.append(pop_block.name)
        # blocks.append({'type':shape_block,'children':[]})
        ##version 1: parent node also include input children node 
        #if(pop_block.parent!=None):
        ##version 2: parent node not include input children node 
        #!!!(need to create a map for parent next mapping relationship, it's too slow to locate here every time 
        if(pop_block.parent!=None):
            if(not pop_block.parent in blockid_map):
                visited_first_children.append(pop_block)
                next(block_count)
            else:
                blocks[blockid_map[pop_block.parent]]["children"].append(next(block_count))
                print('WULALA {}'.format(blocks[blockid_map[pop_block.parent]]))
        else:
            next(block_count)

        print(block_count)
        cur_parent_type_index = len(blocks)
        blocks.append({'type':pop_block.name, 'id':pop_block.block_id,'children':[]})
        # next(block_count)
        # blocks[cur_parent_index]["children"].append(next(block_count))
        print(blocks[cur_parent_index])
        if(len(pop_block.inputs)!=0):
            inputs_parent_index = len(blocks)   
   
            for key in pop_block.inputs:             
                input = pop_block.inputs[key]
                # print("INPUTXXX {}".format(input))
                # lens = len(input)
                input_types = input[0]
                input_index_list = []
                # input_index_list length should be number of items under key type 
                input_index_list.append(len(blocks))
                #cur_input_cur_type_index: type condition XXXX
                cur_input_cur_type_index = len(blocks)
   

                if(input_types == 1):    
                    
                    if(type(input[1])!= list):
                      
                        input_block = locate_next_block(blocks_item,input[1])
                        # process_blocks 
                        if(not input_block.block_id in visited):
                            print("push {} :{}".format(input_block.block_id,input_block.name))
                            # inputid_map[input_block.block_id] = input_index_list[0]
                            stack.append(input_block)
                            visited.append(input_block.block_id)
                            
                elif(input_types == 2):

                    input_block = locate_next_block(blocks_item,input[1])

                    if(not input_block.block_id in visited):
                        # inputid_map[input_block.block_id] = input_index_list[0]
                        stack.append(input_block)
                        visited.append(input_block.block_id)
                else:
                    
                    prev_input_index = 1 
                    for j in range(1,3):
                        # input_index_list.append(len(blocks))
                        if(type(input[j]) != list):        
                            input_block = locate_next_block(blocks_item,input[j])
                            if(not input_block.block_id in visited):
                                # inputid_map[input_block.block_id] = input_index_list[0]
                                stack.append(input_block)
                                visited.append(input_block.block_id)

        
        # use prev_parent_index to add this children to prev parent 
        prev_parent_index=cur_parent_index              
        
        if(pop_block.nextid != None and not pop_block.nextid in visited):
            next_block = locate_next_block(blocks_item,pop_block.nextid)
            if(next_block!=None):
                stack.append(next_block)
                # print(next_block)
                visited.append(next_block.block_id)
    



if __name__ == "__main__":
    start_time = time.time()
    fail_count = 0
    success_count = 0
    read_dir = sys.argv[1]
    write_file = sys.argv[2]
    miss_file = sys.argv[3]
    read_files = [f for f in os.listdir(read_dir) if (os.path.isfile(os.path.join(read_dir, f)) and f.endswith(".json"))]
    total_count= len(read_files)
    print("##total file number{}".format(total_count))
    for read_file in read_files:
        null_list = []
        # used_children.clear()
#         error handling 
        try:
            with open(os.path.join(read_dir, read_file),"r") as f:
                data = json.load(f)
                block_count = count()
                blocks = get_blocks(data["targets"])
            if(len(blocks)>0):
                with open(write_file, 'a') as f:
                    if(fail_count+success_count>0):
                        f.write("\n")
                    json.dump(blocks, f)
                print("###{} parsed successfully".format(read_file))
                success_count +=1 
            with open(miss_file,'a') as fr:
                if(len(null_list) > 0):
                    json.dump(null_list,fr)
        except Exception as e:
            print("###{} has error {}".format(read_file,e))
            fail_count += 1
        if((success_count + fail_count)%100 == 0):
            print("##Current Parsing Success Rate {}: success {}  fail {}".format(success_count/(success_count+fail_count), success_count, fail_count))
    end_time = time.time()    
 
    print("running time {}".format(end_time-start_time))    
    print("##Parsing Success Count {}".format(success_count))
    print("##Parsing Fail Count {}".format(fail_count))
    print("##Parsing Success Rate {}".format(success_count/(success_count+fail_count)))
        
    
