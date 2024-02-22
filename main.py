import time
import math
import logging
import struct
import argparse
from typing import List, Optional

import numpy as np
import quaternion  
from scipy.spatial.transform import Rotation as R

import traceback
from Header import Header

import rosbag
from proto.memory_cruise_pb2 import TrajInfo, MemoryCruise, BoundaryType, MergeDivergeInfo, MergeDivergeType


kEps = 1e-6


class MemoryCruiseExtractor:
    def __init__(self):
        self.conf_ = type('Conf', (), {
            'cut_dis_ahead': 1000.0,
            'cut_dis_behind': 150.0,
            'min_intersection_dist': 15.0
        })()
        self.memory_cruise_ = MemoryCruise()
        self.memory_path_ = []
        self.resampled_ego_pose_list_ = None
        self.cur_ego_pose_ = None
        self.last_ego_s_ = float('-inf')

def read_rosbag(input_bag, extractor):
    with rosbag.Bag(input_bag, 'r') as bag:
        for topic, msg, t in bag.read_messages(raw=True):
            if topic == '/cp_planning/memory_cruise':
                # print("type msg", type(msg))
                # print(f"Topic: {topic}, Time: {t.to_sec()}")
                traj_info = TrajInfo()
                try:
                    traj_info_header = Header()
                    traj_info_data = traj_info_header.deserialize(msg[1])
                    # msg = msg[1]
                    # bytes_proto_buf = msg[16:len(msg)]
                    traj_info.ParseFromString(traj_info_data.frame_id)

                    # print("timestamp:", traj_info.timestamp)
                    # print("point:", f"x: {traj_info.point.x}, y: {traj_info.point.y}, z: {traj_info.point.z}")
                    # print("s:", traj_info.s)
                    # print("v:", traj_info.v)
                    # print("limit_speed:", traj_info.limit_speed)
                    extractor.update_memory_cruise(traj_info)
                    
            
                except Exception as e:
                    extractor.update_memory_cruise(traj_info)
                    traceback.format_exc()
                    print(f"解析错误: {e}")
        
        # read ego pose topic
        egopose_list = []
        for topic, msg, t in bag.read_messages(topics=['/mla/egopose']):
            # print(f"Topic: {topic}, Time: {t.to_sec()}")

            try:
                egopose_list.append(msg)
            except Exception as e:
                print(f"Skipping a message at {t} due to decode error.")
            
        print("ego pose size:", len(egopose_list))
        print("memory_cruise size:", extractor.memory_cruise_.traj_info.__len__())
        
        return True



def process_memory_cruise(extractor: MemoryCruiseExtractor, frame_index: int):
    print("START MemoryCruiseExtractor::process_memory_cruise(), index frame: ", frame_index)

    cut_memory_cruise = MemoryCruise()
    for start_index in range(extractor.memory_cruise_.traj_info.__len__()):
        traj_info = extractor.memory_cruise_.traj_info[start_index]
        cut_memory_cruise.traj_info.append(traj_info)
    
    return cut_memory_cruise

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Process some bags.')

    parser.add_argument('--input', type=str, required=True,
                            help='Path to the input bag file')
    
    parser.add_argument('--output', type=str, required=True,
                        help='Path to the output bag file')
    args = parser.parse_args()

    extractor = MemoryCruiseExtractor()

    original_bag_path = args.input
    output_bag_path = args.output

    read_succeed = read_rosbag(original_bag_path, extractor)
    print("memory_cruise size://///////////// ",extractor.memory_cruise_.traj_info.__len__())
    print("resampled ego_pose size://///////////// ",extractor.resampled_ego_pose_list_.__len__())
    print("AFTER preprocess memory_cruise size://///////////// ",extractor.memory_cruise_.traj_info.__len__())

    if not read_succeed:
        logging.error("read rosbag FAIL!!!")
    else:
        print("read rosbag succeed!!!")
        with rosbag.Bag(original_bag_path, 'r') as input_bag, rosbag.Bag(output_bag_path, 'w') as output_bag:
            i = 0
            traj_info_1 = TrajInfo()
            for topic, msg, t in input_bag.read_messages(raw=True):
                if topic == '/cp_planning/memory_cruise':
                    print(f"\n ========================= frame <{i}> =========================")                 
                    start_time = time.time()
                    cut_memory_cruise = process_memory_cruise(extractor, i)
                    end_time = time.time()
                    # logging.warning(f"frame index= {i} ==> process_memory_cruise time: {end_time - start_time}")
                    
                    if cut_memory_cruise == None: # TODO: check what to do with None value
                        cut_memory_cruise = MemoryCruise()
                        logging.error("index= ", i, " cut_memory_cruise is None!")
                    
                    serialized_data = cut_memory_cruise.SerializeToString()


                    header_msg = Header()
                    header_msg.seq = i
                    header_msg.stamp = t

                    header_msg.frame_id = serialized_data
                    


                    with open('message.bin', 'wb') as file:
                        file.write(serialized_data)              
                    
                    output_bag.write('/worldmodel/memory_cruise', header_msg, t)
                    output_bag.write('/cp_planning/memory_cruise', msg, t, raw=True)
                    i+=1
                    # break
                elif topic == '/worldmodel/memory_cruise':
                    print(f"\n ================/worldmodel/memory_cruise=====================")   
                    continue
                else:
                    output_bag.write(topic, msg, t, raw=True)
