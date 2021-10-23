import os
import json 
import sys
from itertools import count
from numpy.core.shape_base import block
import time

block_count = count()
variable_mapping = {}
list_mapping = {}
null_list = []
used_children = set()
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



def build_variable_mapping(targets):
    # variable_mapping = {}
    for obj in targets:
        variables = obj["variables"]
        for var_id in variables:
            variable_mapping[var_id] = variables[var_id]

def build_list_mapping(targets):
    for obj in targets:
        lists = obj["lists"]
        for list_id in lists:
            list_mapping[list_id] = lists[list_id]
        
def get_blocks(targets):
    block_count = count(0,1)
    blocks = []
    build_variable_mapping(targets)
    build_list_mapping(targets)
    used_children = set()
    

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
        if(blockid_map[left_block.block_id] in used_children):
            print("!!!ERROR {}".format(blockid_map[left_block.block_id]))
        blocks[blockid_map[left_block.parent]]["children"].append(blockid_map[left_block.block_id])
        used_children.add(blockid_map[left_block.block_id])

    for inputid in inputid_map:
        # print("##INPUT_MAP {}: {}".format(blocks[inputid_map[inputid]]["type"],blockid_map[inputid]))
        if(blockid_map[inputid] in used_children):
            print("!!!ERROR {}".format(blockid_map[inputid]))
        blocks[inputid_map[inputid]]["children"].append(blockid_map[inputid])
        used_children.add(blockid_map[inputid])

def process_blocks_stacks(blocks,stack,prev_parent_index,blockid_map,blocks_item,visited,visited_first_children,inputid_map):
    while(len(stack)!=0):
        pop_block = stack.pop()
        #print("Popped block {}".format(pop_block.block_id))
        # if(prev_parent_index != -1):
            # print(blocks[prev_parent_index])
        # record current round parent index and 
        cur_parent_index = len(blocks)
        blockid_map[pop_block.block_id] = cur_parent_index
        # blockid_map[cur_parent_index] = pop_block.block_id
        # print("cur parent index {}".format(cur_parent_index))
        shape_block = Sb3OpcodeToShape(pop_block.name)
        if(shape_block == None):
            null_list.append(pop_block.name)
        blocks.append({'type':shape_block,'children':[]})
        ##version 1: parent node also include input children node 
        #if(pop_block.parent!=None):
        ##version 2: parent node not include input children node 
        #!!!(need to create a map for parent next mapping relationship, it's too slow to locate here every time 
        if(pop_block.parent!=None and locate_next_block(blocks_item,pop_block.parent).nextid == pop_block.block_id):
            if(not pop_block.parent in blockid_map):
                visited_first_children.append(pop_block)
                next(block_count)
            else:
                # print("pop_block {}; parent {}".format(pop_block.block_id,blockid_map[pop_block.parent]))
                blocks[blockid_map[pop_block.parent]]["children"].append(next(block_count))
        else:
            next(block_count)

        # print(pop_block.name)
        ##cur_parent_type_index: index of type parent 
        cur_parent_type_index = len(blocks)
        blocks.append({'type':pop_block.name, 'children':[]})
        blocks[cur_parent_index]["children"].append(next(block_count))

        blocks.append({'type':'shadow','value':pop_block.shadow,'children':[]})
        blocks[cur_parent_type_index]["children"].append(next(block_count))
    # "inputs":{'value':[3,[12,"CAS Eyes","dqC)O=B!a/Op`%[4ro%:"],[10,"0"]]},"fields":{"VARIABLE":["EYES Selected Cat","Xi6IgrUvylFSkp(].;mZ"]}
        ## 1. input list mapping 2. consider if we need further breakdown lists 
        if(len(pop_block.inputs)!=0):
            inputs_parent_index = len(blocks)
            blocks.append({'type':'inputs','children':[]})
            blocks[cur_parent_type_index]["children"].append(next(block_count))    
   
            for key in pop_block.inputs:             
                input = pop_block.inputs[key]
                # lens = len(input)
                input_types = input[0]
                input_index_list = []
                # input_index_list length should be number of items under key type 
                # input_index_list.append(len(blocks))
                #cur_input_cur_type_index: type condition XXXX
                cur_input_cur_type_index = len(blocks)
   
                blocks.append({'type':key,'children':[]})
                blocks[inputs_parent_index]["children"].append(next(block_count))
                input_index_list.append(len(blocks))
                blocks.append({'type':input_types,'children':[]})
                blocks[cur_input_cur_type_index]["children"].append(next(block_count))
                if(input_types == 1):    
                    
                    if(type(input[1])!= list):
                      
                        input_block = locate_next_block(blocks_item,input[1])
                        # process_blocks 
                        if(not input_block.block_id in visited):
                            inputid_map[input_block.block_id] = input_index_list[0]
                            stack.append(input_block)
                            visited.append(input_block.block_id)
                            
                    else:  
                        
                        nested_type = input[1][0] 
                        input_index_list.append(len(blocks))
                        # if need a seperate layer for each node start uncomment below and change 0 to 1 ex:{type:10,children:[]}
                        # blocks.append({'type':nested_type,'children':[]})
                        # blocks[input_index_list[0]]["children"].append(next(block_count))
                        
                        for i in range(1,len(input[1])):
                            blocks.append({'type':nested_type,'value':input[1][i],'children':[]})
                            next(block_count)
                            res1 = variable_mapping.get(input[1][i],"")
                            res2 = list_mapping.get(input[1][i],"")
                        if(res1!=""):
                            type_parent = len(blocks)
                            blocks.append({'type':key,'children':[]})
                            blocks[input_index_list[0]]["children"].append(next(block_count))
                            blocks.append({'type':'Vars','value':res1[0],'children':[]})
                            blocks[type_parent]["children"].append(next(block_count))
                            blocks.append({'type':'Vars','value':res1[1],'children':[]})
                            blocks[type_parent]["children"].append(next(block_count))
                        elif (res2!=""):
                            ##element inside need breakdown another layer again since it's a list 
                            type_parent = len(blocks)
                            blocks.append({'type':key,'children':[]})
                            if(type(res2[0]) == list):
                                str1 = " ".join(str(x) for x in res2[0])
                            else:
                                str1 = str(res2[0])
                            if(type(res2[1]) == list):
                                str2 = " ".join(str(x) for x in res2[1])
                            else:
                                str2 = str(res2[1])
                            blocks[input_index_list[0]]["children"].append(next(block_count))
                            blocks.append({'type':'Lists','value':str1,'children':[]})
                            blocks[type_parent]["children"].append(next(block_count))
                            blocks.append({'type':'Lists','value':str2,'children':[]})
                            blocks[type_parent]["children"].append(next(block_count))
                        else:
                            blocks.append({'type':key,'value':input[1][i],'children':[]})
                            blocks[input_index_list[0]]["children"].append(next(block_count)) 
                elif(input_types == 2):

                    input_block = locate_next_block(blocks_item,input[1])
                        # process_blocks 
                    if(not input_block.block_id in visited):
                        inputid_map[input_block.block_id] = input_index_list[0]
                        stack.append(input_block)
                        visited.append(input_block.block_id)
                else:
                    
                    prev_input_index = 1 
                    for j in range(1,3):
                        input_index_list.append(len(blocks))
                        if(type(input[j]) == list):
                            nested_type = input[j][0] 
                            # if need a seperate layer for each node start uncomment below and change j-1 to jex:{type:10,children:[]}
                            # blocks.append({'type':nested_type,'children':[]})
                            # blocks[input_index_list[0]]["children"].append(next(block_count))
                            # print("type 3 {}".format(len(input[j])))
                            for i in range(1,len(input[j])):
                                res1 = variable_mapping.get(input[j][i],"")
                                res2 = list_mapping.get(input[j][i],"")
                                if(res1!=""):
                                    type_parent = len(blocks)
                                    blocks.append({'type':nested_type,'children':[]})
                                    blocks[input_index_list[j-1]]["children"].append(next(block_count))
                                    blocks.append({'type':'Vars','value':res1[0],'children':[]})
                                    blocks[type_parent]["children"].append(next(block_count))
                                    blocks.append({'type':'Vars','value':res1[1],'children':[]})
                                    blocks[type_parent]["children"].append(next(block_count))
                                elif (res2!=""):
                                    ## element inside need breakdown another layer again since it's a list 
                                    type_parent = len(blocks)
                                    blocks.append({'type':nested_type,'children':[]})
                                    blocks[input_index_list[j-1]]["children"].append(next(block_count))
                                    if(type(res2[0]) == list):
                                        str1 = " ".join(str(x) for x in res2[0])
                                    else:
                                        str1 = str(res2[0])
                                    if(type(res2[1]) == list):
                                        str2 = " ".join(str(x) for x in res2[1])
                                    else:
                                        str2 = str(res2[1])
                                    blocks.append({'type':'Lists','value':str1,'children':[]})
                                    blocks[type_parent]["children"].append(next(block_count))
                                    blocks.append({'type':'Lists','value':str2,'children':[]})
                                    blocks[type_parent]["children"].append(next(block_count))
                                else:
                                    blocks.append({'type':nested_type,'value':input[j][i],'children':[]})
                                    blocks[input_index_list[j-1]]["children"].append(next(block_count)) 
  
                            prev_input_index = len(input_index_list)

                        else:           
                            input_block = locate_next_block(blocks_item,input[j])
                                # process_blocks HOW TO ASSIGN THE CHILDREN RELATIONSHIP HERE 
                            if(not input_block.block_id in visited):
                                inputid_map[input_block.block_id] = input_index_list[j-1]
                                stack.append(input_block)
                                visited.append(input_block.block_id)
                                # process_blocks_stacks(blocks,stack4,prev_parent_index,blockid_map,blocks_item,visited)



        if(len(pop_block.fields)!=0):
            fields_parent_index = len(blocks)
            blocks.append({'type':'fields','children':[]})
            blocks[cur_parent_type_index]["children"].append(next(block_count))
            for key in pop_block.fields:
                for field in pop_block.fields[key]:
                    #check if have this key in variable mapping 
                    res1 = variable_mapping.get(field,"")
                    res2 = list_mapping.get(field,"")
                    if(res1!=""):
                        type_parent = len(blocks)
                        blocks.append({'type':key,'children':[]})
                        blocks[fields_parent_index]["children"].append(next(block_count))
                        blocks.append({'type':'Vars','value':res1[0],'children':[]})
                        blocks[type_parent]["children"].append(next(block_count))
                        blocks.append({'type':'Vars','value':res1[1],'children':[]})
                        blocks[type_parent]["children"].append(next(block_count))
                    elif (res2!=""):
                        ## element inside need breakdown another layer again since it's a list 
                        type_parent = len(blocks)
                        blocks.append({'type':key,'children':[]})
                        blocks[fields_parent_index]["children"].append(next(block_count))
                        if(type(res2[0]) == list):
                            str1 = " ".join(str(x) for x in res2[0])
                        else:
                            str1 = str(res2[0])
                        if(type(res2[1]) == list):
                            str2 = " ".join(str(x) for x in res2[1])
                        else:
                            str2 = str(res2[1])
                        blocks.append({'type':'Lists','value':str1,'children':[]})
                        blocks[type_parent]["children"].append(next(block_count))
                        blocks.append({'type':'Lists','value':str2,'children':[]})
                        blocks[type_parent]["children"].append(next(block_count))
                    else:
                        blocks.append({'type':key,'value':field,'children':[]})
                        blocks[fields_parent_index]["children"].append(next(block_count))
        
        # use prev_parent_index to add this children to prev parent 
        prev_parent_index=cur_parent_index              
        # print("prev_parent_index233 {}".format(prev_parent_index))

        #("Popoed block nextid{}".format(pop_block.nextid))
        if(pop_block.nextid != None and not pop_block.nextid in visited):
            next_block = locate_next_block(blocks_item,pop_block.nextid)
            if(next_block!=None):
                stack.append(next_block)
                # print(next_block)
                visited.append(next_block.block_id)
    




def Sb3OpcodeToShape(opcode):
    return {
        'motion_movesteps': 'Stack',
        'motion_turnright': 'Stack',
        'motion_turnleft': 'Stack',
        'motion_pointindirection': 'Stack',
        'motion_pointtowards': 'Stack',
        'motion_gotoxy': 'Stack',
        'motion_goto': 'Stack',
        'motion_glidesecstoxy': 'Stack',
        'motion_changexby': 'Stack',
        'motion_setx': 'Stack',
        'motion_changeyby': 'Stack',
        'motion_sety': 'Stack',
        'motion_ifonedgebounce': 'Stack',
        'motion_setrotationstyle': 'Stack',
        'motion_xposition': 'Reporter',
        'motion_yposition': 'Reporter',
        'motion_direction': 'Reporter',
        'motion_scroll_right': 'Stack',
        'motion_scroll_up': 'Stack',
        'motion_align_scene': 'Stack',
        'motion_xscroll': 'Reporter',
        'motion_yscroll': 'Reporter',
        'looks_sayforsecs': 'Stack',
        'looks_say': 'Stack',
        'looks_thinkforsecs': 'Stack',
        'looks_think': 'Stack',
        'looks_show': 'Stack',
        'looks_hide': 'Stack',
        'looks_hideallsprites': 'Stack',
        'looks_switchcostumeto': 'Stack',
        'looks_nextcostume': 'Stack',
        'looks_switchbackdropto': 'Stack',
        'looks_changeeffectby': 'Stack',
        'looks_seteffectto': 'Stack',
        'looks_cleargraphiceffects': 'Stack',
        'looks_changesizeby': 'Stack',
        'looks_setsizeto': 'Stack',
        'looks_changestretchby': 'Stack',
        'looks_setstretchto': 'Stack',
        'looks_gotofrontback': 'Stack',
        'looks_goforwardbackwardlayers': 'Stack',
        'looks_costumenumbername': 'Reporter',
        'looks_backdropnumbername': 'Reporter',
        'looks_backdrops': 'Reporter',
        'looks_costume': 'Reporter',
        'looks_size': 'Reporter',
        'looks_switchbackdroptoandwait': 'Stack',
        'looks_nextbackdrop': 'Stack',
        'sound_play': 'Stack',
        'sound_playuntildone': 'Stack',
        'sound_stopallsounds': 'Stack',
        'music_playDrumForBeats': 'Stack',
        'music_midiPlayDrumForBeats': 'Deprecated',
        'music_restForBeats': 'Stack',
        'music_playNoteForBeats': 'Stack',
        'music_setInstrument': 'Stack',
        'music_midiSetInstrument': 'Deprecated',
        'sound_changevolumeby': 'Stack',
        'sound_setvolumeto': 'Stack',
        'sound_volume': 'Reporter',
        'sound_sounds_menu': 'Reporter',
        'music_changeTempo': 'Stack',
        'music_setTempo': 'Stack',
        'music_getTempo': 'Reporter',
        'pen_clear': 'Stack',
        'pen_stamp': 'Stack',
        'pen_penDown': 'Stack',
        'pen_penUp': 'Stack',
        'pen_setPenColorToColor': 'Stack',
        'pen_changePenHueBy': 'Stack',
        'pen_setPenHueToNumber': 'Stack',
        'pen_changePenShadeBy': 'Stack',
        'pen_setPenShadeToNumber': 'Stack',
        'pen_changePenSizeBy': 'Stack',
        'pen_setPenSizeTo': 'Stack',
        'videoSensing_videoOn': 'Reporter',
        'event_whenflagclicked': 'Hat',
        'event_whenkeypressed': 'Hat',
        'event_whenthisspriteclicked': 'Hat',
        'event_whenbackdropswitchesto': 'Hat',
        'event_whenbroadcastreceived': 'Hat',
        'event_broadcast': 'Stack',
        'event_broadcastandwait': 'Stack',
        'control_wait': 'Stack',
        'control_repeat': 'C',
        'control_forever': 'C',
        'control_if': 'C',
        'control_if_else': 'C',
        'control_wait_until': 'Stack',
        'control_repeat_until': 'C',
        'control_while': 'C',
        'control_for_each': 'C',
        'control_stop': 'Cap',
        'control_start_as_clone': 'Hat',
        'control_create_clone_of': 'Stack',
        'control_delete_this_clone': 'Cap',
        'control_get_counter': 'Reporter',
        'control_incr_counter': 'Stack',
        'control_clear_counter': 'Stack',
        'control_all_at_once': 'C',
        'sensing_touchingobject': 'Boolean',
        'sensing_touchingobjectmenu': 'Reporter',
        'sensing_touchingcolor': 'Boolean',
        'sensing_coloristouchingcolor': 'Boolean',
        'sensing_distanceto': 'Reporter',
        'sensing_askandwait': 'Stack',
        'sensing_answer': 'Reporter',
        'sensing_keyoptions': 'Reporter',
        'sensing_keypressed': 'Boolean',
        'sensing_mousedown': 'Boolean',
        'sensing_mousex': 'Reporter',
        'sensing_mousey': 'Reporter',
        'sensing_loudness': 'Reporter',
        'sensing_loud': 'Boolean',
        'videoSensing_videoToggle': 'Stack',
        'videoSensing_setVideoTransparency': 'Stack',
        'sensing_timer': 'Reporter',
        'sensing_resettimer': 'Stack',
        'sensing_of': 'Reporter',
        'sensing_current': 'Reporter',
        'sensing_dayssince2000': 'Reporter',
        'sensing_username': 'Reporter',
        'sensing_userid': 'Reporter',
        'operator_add': 'Reporter',
        'operator_subtract': 'Reporter',
        'operator_multiply': 'Reporter',
        'operator_divide': 'Reporter',
        'operator_random': 'Reporter',
        'operator_lt': 'Boolean',
        'operator_equals': 'Boolean',
        'operator_gt': 'Boolean',
        'operator_and': 'Boolean',
        'operator_or': 'Boolean',
        'operator_not': 'Boolean',
        'operator_join': 'Reporter',
        'operator_letter_of': 'Reporter',
        'operator_length': 'Reporter',
        'operator_mod': 'Reporter',
        'operator_round': 'Reporter',
        'operator_mathop': 'Reporter',
        'data_variable': 'Reporter',
        'data_setvariableto': 'Stack',
        'data_changevariableby': 'Stack',
        'data_showvariable': 'Stack',
        'data_hidevariable': 'Stack',
        'data_listcontents': 'Reporter',
        'data_addtolist': 'Stack',
        'data_deleteoflist': 'Stack',
        'data_insertatlist': 'Stack',
        'data_replaceitemoflist': 'Stack',
        'data_itemoflist': 'Reporter',
        'data_lengthoflist': 'Reporter',
        'data_listcontainsitem': 'Boolean',
        'data_showlist': 'Stack',
        'data_hidelist': 'Stack',
        'procedures_definition': 'ProcedureHat',
        'argument_reporter_string_number': 'Parameter',
        'procedures_call': 'Call',
        'wedo2_motorOnFor': 'Stack',
        'wedo2_motorOn': 'Stack',
        'wedo2_motorOff': 'Stack',
        'wedo2_startMotorPower': 'Stack',
        'wedo2_setMotorDirection': 'Stack',
        'wedo2_setLightHue': 'Stack',
        'wedo2_playNoteFor': 'Stack',
        'wedo2_whenDistance': 'Hat',
        'wedo2_whenTilted': 'Hat',
        'wedo2_getDistance': 'Reporter',
        'wedo2_isTilted': 'Boolean',
        'wedo2_getTiltAngle': 'Reporter',
        'argument_reporter_boolean': 'Boolean',
        'control_create_clone_of_menu': 'Reporter',
        'data_deletealloflist': 'Stack',
        'data_itemnumoflist': 'Reporter',
        'event_definition': 'Deprecated',
        'event_whengreaterthan': 'Hat',
        'event_whenstageclicked': 'Hat',
        'makeymakey_menu_KEY': 'Reporter',
        'makeymakey_menu_SEQUENCE': 'Reporter',
        'makeymakey_whenCodePressed': 'Hat',
        'makeymakey_whenMakeyKeyPressed': 'Hat',
        'microbit_menu_gestures': 'Reporter',
        'microbit_whenGesture': 'Hat',
        'motion_glideto': 'Stack',
        'motion_glideto_menu': 'Reporter',
        'motion_goto_menu': 'Reporter',
        'motion_pointtowards_menu': 'Reporter',
        'music_menu_DRUM': 'Reporter',
        'music_menu_INSTRUMENT': 'Reporter',
        'note': 'Reporter',
        'operator_contains': 'Boolean',
        'pen_changePenColorParamBy': 'Stack',
        'pen_menu_colorParam': 'Reporter',
        'pen_setPenColorParamTo': 'Stack',
        'procedures_prototype': 'PrototypeStack',
        'sensing_distancetomenu': 'Reporter',
        'sensing_of_object_menu': 'Reporter',
        'sensing_setdragmode': 'Stack',
        'sound_changeeffectby': 'Stack',
        'sound_cleareffects': 'Stack',
        'sound_seteffectto': 'Stack',
        'text2speech_menu_languages': 'Reporter',
        'text2speech_menu_voices': 'Reporter',
        'text2speech_setLanguage': 'Stack',
        'text2speech_setVoice': 'Stack',
        'text2speech_speakAndWait': 'Stack',
        'videoSensing_menu_ATTRIBUTE': 'Reporter',
        'videoSensing_menu_SUBJECT': 'Reporter',
        'videoSensing_menu_VIDEO_STATE': 'Reporter',
        'videoSensing_whenMotionGreaterThan': 'Hat'
    }.get(opcode, 'Deprecated')




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
        used_children.clear()
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
        
    
