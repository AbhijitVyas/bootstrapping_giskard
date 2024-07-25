#!/usr/bin/env python

import rospy
from geometry_msgs.msg import PoseStamped, Vector3Stamped, PointStamped, Quaternion, Point, Vector3
from tf.transformations import quaternion_about_axis, quaternion_from_matrix

from giskardpy.python_interface.python_interface import GiskardWrapper
from giskardpy.utils.tfwrapper import lookup_pose
from typing import List, Dict


class GripperModel:
    def __init__(self, eef_link: str, upright_axis: List[int], second_axis: List[int], rotation_axis: List[int],
                 velocity_threshold: float, effort_threshold: float, effort: float,
                 gripper_pub_topic: str, gripper_joint_state_topic: str, gripper_alibi_joint_name: str,
                 grasp_distance_knowledge: Dict[str, float]):
        self.eef_link = eef_link
        self.upright_axis = Vector3Stamped()
        self.upright_axis.header.frame_id = eef_link
        self.upright_axis.vector = Vector3(*upright_axis)

        self.second_axis = Vector3Stamped()
        self.second_axis.header.frame_id = eef_link
        self.second_axis.vector = Vector3(*second_axis)

        self.rotation_axis = Vector3Stamped()
        self.rotation_axis.header.frame_id = eef_link
        self.rotation_axis.vector = Vector3(*rotation_axis)

        self.velocity_threshold = velocity_threshold
        self.effort_threshold = effort_threshold
        self.effort = effort
        self.pub_topic = gripper_pub_topic
        self.griper_joint_state_topic = gripper_joint_state_topic
        self.alibi_joint_name = gripper_alibi_joint_name

        self.grasp_distance_knowledge = grasp_distance_knowledge


class ObjectGripperModel(GripperModel):
    def __init__(self, grasped_object_name, parent_gripper: GripperModel):
        self.eef_link = grasped_object_name
        self.upright_axis = Vector3Stamped()
        self.upright_axis.header.frame_id = grasped_object_name
        self.upright_axis.vector = Vector3(*[0, 0, 1])

        self.second_axis = Vector3Stamped()
        self.second_axis.header.frame_id = grasped_object_name
        self.second_axis.vector = Vector3(*[1, 0, 0])

        self.rotation_axis = Vector3Stamped()
        self.rotation_axis.header.frame_id = grasped_object_name
        self.rotation_axis.vector = Vector3(*[1, 0, 0])

        self.parent_gripper = parent_gripper


hsrGripperModel = GripperModel('hand_palm_link', [1, 0, 0], [0, 0, 1], [0, 0, 1], 0.1, -1, -180,
                               'hsrb4s/hand_motor_joint_velocity_controller/command',
                               'hsrb4s/joint_states',
                               'hand_motor_joint',
                               grasp_distance_knowledge={'free_cup': 0.04})
pr2LeftGripperModel = GripperModel('l_gripper_tool_frame', [0, 0, 1], [1, 0, 0], [1, 0, 0], 0.1, -0.14, -200,
                                   '/pr2/l_gripper_controller/command',
                                   'pr2/joint_states',
                                   'l_gripper_l_finger_joint',
                                   grasp_distance_knowledge={'free_cup': -0.02})


def openGripper(giskard: GiskardWrapper, gripper: GripperModel):
    if isinstance(gripper, ObjectGripperModel):
        giskard.motion_goals.add_motion_goal(motion_goal_class='CloseGripper',
                                             name='openGripper',
                                             as_open=True,
                                             velocity_threshold=100,
                                             effort_threshold=gripper.parent_gripper.effort_threshold,
                                             effort=100,
                                             pub_topic=gripper.parent_gripper.pub_topic,
                                             joint_state_topic=gripper.parent_gripper.griper_joint_state_topic,
                                             alibi_joint_name=gripper.parent_gripper.alibi_joint_name
                                             )
    else:
        giskard.motion_goals.add_motion_goal(motion_goal_class='CloseGripper',
                                             name='openGripper',
                                             as_open=True,
                                             velocity_threshold=100,
                                             effort_threshold=gripper.effort_threshold,
                                             effort=100,
                                             pub_topic=gripper.pub_topic,
                                             joint_state_topic=gripper.griper_joint_state_topic,
                                             alibi_joint_name=gripper.alibi_joint_name
                                             )
    giskard.motion_goals.allow_all_collisions()
    giskard.add_default_end_motion_conditions()
    giskard.execute()


def closeGripper(giskard: GiskardWrapper, gripper: GripperModel):
    giskard.motion_goals.add_motion_goal(motion_goal_class='CloseGripper',
                                         name='closeGripper',
                                         effort=gripper.effort,
                                         effort_threshold=gripper.effort_threshold,
                                         velocity_threshold=gripper.velocity_threshold,
                                         pub_topic=gripper.pub_topic,
                                         joint_state_topic=gripper.griper_joint_state_topic,
                                         alibi_joint_name=gripper.alibi_joint_name)
    giskard.motion_goals.allow_all_collisions()
    giskard.add_default_end_motion_conditions()
    giskard.execute()


def align_to(giskard: GiskardWrapper, gripper: GripperModel, side: str, object_frame: str, distance=0.3,
             height_offset=0.0,
             second_distance=0.0):
    """
    side: [front, left, right] relative to the object frame from the pov of a robot standing at the origin of the world frame
    axis_align_to_z: axis of the control_frame that will be aligned to the z-axis of the object frame
    object_frame: name of the tf frame to align to
    control_frame: name of a tf frame attached to the robot that should be moved around
    axis_align_to_x: axis of the control_frame that will be aligned to the x-axis of the object frame
    distance: distance between the object and the control frame along the axis resulting from align to [side]
    height_offset: offset between the two frames on the z-axis
    second_distance: offset on the last free axis. When side == [left, right] this is the x axis of the object frame, otherwise it is the y axis.
    """
    goal_normal = Vector3Stamped()
    goal_normal.header.frame_id = object_frame
    goal_normal.vector.z = 1
    giskard.motion_goals.add_align_planes(goal_normal, gripper.eef_link, gripper.upright_axis, 'map',
                                          name='align_upright')
    if gripper.second_axis:
        second_goal_normal = Vector3Stamped()
        second_goal_normal.header.frame_id = object_frame
        second_goal_normal.vector.x = 1
        giskard.motion_goals.add_align_planes(second_goal_normal, gripper.eef_link, gripper.second_axis, 'map',
                                              name='align_second')

    goal_position = PointStamped()
    goal_position.header.frame_id = object_frame
    if side == 'front':
        goal_position.point.x = -distance
        goal_position.point.y = second_distance
        goal_position.point.z = height_offset
    elif side == 'left':
        goal_position.point.x = second_distance
        goal_position.point.y = distance
        goal_position.point.z = height_offset
    elif side == 'right':
        goal_position.point.x = second_distance
        goal_position.point.y = -distance
        goal_position.point.z = height_offset
    giskard.motion_goals.add_cartesian_position(goal_position, gripper.eef_link, 'map')
    giskard.add_default_end_motion_conditions()
    giskard.execute()


def tilt(giskard: GiskardWrapper, gripper: GripperModel, angle: float, velocity: float):
    goal_pose = PoseStamped()
    goal_pose.header.frame_id = gripper.eef_link
    rotation_axis = gripper.rotation_axis
    goal_pose.pose.orientation = Quaternion(
        *quaternion_about_axis(angle, [rotation_axis.vector.x, rotation_axis.vector.y, rotation_axis.vector.z]))
    giskard.motion_goals.add_cartesian_pose(goal_pose, gripper.eef_link, 'map', reference_angular_velocity=velocity)
    # giskard.motion_goals.add_limit_cartesian_velocity(tip_link=gripper.eef_link, root_link='map',
    #                                                   max_angular_velocity=velocity)
    giskard.add_default_end_motion_conditions()
    giskard.execute()


def move_arm(giskard: GiskardWrapper, direction: str, control_frame: str):
    goal_pose = lookup_pose('map', control_frame)
    if direction == 'up':
        goal_pose.pose.position.z += 0.1
    elif direction == 'down':
        goal_pose.pose.position.z -= 0.1
    elif direction == 'left':
        goal_pose.pose.position.y += 0.1
    elif direction == 'right':
        goal_pose.pose.position.y -= 0.1
    elif direction == 'forward':
        goal_pose.pose.position.x += 0.1
    elif direction == 'back':
        goal_pose.pose.position.x -= 0.1

    giskard.motion_goals.add_cartesian_pose(goal_pose=goal_pose, tip_link=control_frame, root_link='map')
    giskard.add_default_end_motion_conditions()
    giskard.execute()


# def put_down(giskard: GiskardWrapper, location: PoseStamped, control_frame: str):
#     giskard.motion_goals.add_cartesian_pose(goal_pose=location, tip_link=control_frame, root_link='map')
#     giskard.add_default_end_motion_conditions()
#     giskard.execute()

def grasp(giskard: GiskardWrapper, gripper: GripperModel, object_name: str, grasp_side: str):
    # Here starts the control
    # Open the gripper. Needs the giskard interface as input, as all the other methods
    openGripper(giskard, gripper)

    # This aligns the control frame to the front of the object frame in a distance of 0.04m.
    align_to(giskard, gripper, grasp_side, object_frame=object_name,
             distance=gripper.grasp_distance_knowledge[object_name])

    # Close the gripper
    closeGripper(giskard, gripper)
    giskard.execute()


def pick_up(giskard: GiskardWrapper, gripper: GripperModel, object_name: str, grasp_side: str):
    # first make an roslaunch giskardpy giskardpy_hsr_mujoco.launchattempt at grasping an object
    grasp(giskard, gripper, object_name, grasp_side)

    # # now, move the arm upward
    move_arm(giskard, 'up', gripper.eef_link)


def put_down(giskard: GiskardWrapper, gripper: GripperModel, goal_pose: PoseStamped):
    # goal_pose = lookup_pose('map', control_frame)
    giskard.motion_goals.add_cartesian_pose(goal_pose=goal_pose, tip_link=gripper.eef_link, root_link='map')
    giskard.add_default_end_motion_conditions()
    giskard.execute()
    # giskard.add_default_end_motion_conditions()
    # open the gripper
    openGripper(giskard, gripper)
    giskard.execute()
    # # now, move the arm upward
    # move_arm(giskard, 'up', robot_eeff)


def attach_to_gripper(giskard: GiskardWrapper, gripper: GripperModel, object_name: str, object_size: tuple):
    cup_pose = PoseStamped()
    cup_pose.header.frame_id = object_name
    cup_pose.pose.position = Point(0, 0, 0)
    cup_pose.pose.orientation.w = 1
    new_name = object_name + '_grasped'
    giskard.world.add_box(new_name, object_size, pose=cup_pose, parent_link=gripper.eef_link)
    return new_name


def get_object_size(object_name: str):
    data = {'free_cup': (0.07, 0.07, 0.18),
            'free_cup2': (0.07, 0.07, 0.18)}
    # instead of reading from the data storage one could get
    # the object size from querying the simulation or a knowledgebase or perception
    if object_name not in data.keys():
        raise Exception('Given object name is unknown')
    return data[object_name]
