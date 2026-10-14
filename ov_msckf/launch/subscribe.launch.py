from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, TextSubstitution
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory, get_package_prefix
import os
import sys

launch_args = [
    DeclareLaunchArgument(name="namespace", default_value="ov_msckf", description="namespace"),
    DeclareLaunchArgument(
        name="ov_enable", default_value="true", description="enable OpenVINS node"
    ),
    DeclareLaunchArgument(
        name="rviz_enable", default_value="false", description="enable rviz node"
    ),
    DeclareLaunchArgument(
        name="config",
        default_value="euroc_mav",
        description="euroc_mav, tum_vi, rpng_aruco...",
    ),
    DeclareLaunchArgument(
        name="config_path",
        default_value="",
        description="path to estimator_config.yaml. If not given, determined based on provided 'config' above",
    ),
    DeclareLaunchArgument(
        name="verbosity",
        default_value="INFO",
        description="ALL, DEBUG, INFO, WARNING, ERROR, SILENT",
    ),
    DeclareLaunchArgument(
        name="use_stereo",
        default_value="true",
        description="if we have more than 1 camera, if we should try to track stereo constraints between pairs",
    ),
    DeclareLaunchArgument(
        name="max_cameras",
        default_value="2",
        description="how many cameras we have 1 = mono, 2 = stereo, >2 = binocular (all mono tracking)",
    ),
    DeclareLaunchArgument(
        name="use_klt",
        default_value="true",
        description="true = FAST + KLT tracking, false = FAST + ORB descriptor matching",
    ),
    DeclareLaunchArgument(
        name="record_timing_information",
        default_value="false",
        description="write per-frame computation times of the estimator to record_timing_filepath",
    ),
    DeclareLaunchArgument(
        name="record_timing_filepath",
        default_value="/tmp/traj_timing.txt",
        description="where record_timing_information writes the timings (absolute path)",
    ),
    DeclareLaunchArgument(
        name="save_total_state",
        default_value="false",
        description="record the total state with calibration and features to a txt file",
    ),
    DeclareLaunchArgument(
        name="filepath_est",
        default_value="/catkin_ws/results/state_estimate.txt",
        description="where save_total_state writes the estimate (absolute path)",
    ),
    DeclareLaunchArgument(
        name="filepath_std",
        default_value="/catkin_ws/results/state_deviation.txt",
        description="where save_total_state writes the standard deviations (absolute path)",
    ),
    DeclareLaunchArgument(
        name="dataset",
        default_value="",
        description="dataset name (e.g. V1_01_easy); loads groundtruth from <ov_data_dir>/<config>/<dataset>.csv",
    ),
    DeclareLaunchArgument(
        name="ov_data_dir",
        default_value="/catkin_ws/src/open_vins/ov_data",
        description="folder with the groundtruth files (ov_data does not install them)",
    ),
    DeclareLaunchArgument(
        name="path_gt",
        default_value="",
        description="path to a groundtruth csv (ASL format). If not given, determined based on 'dataset' above",
    )
]

def launch_setup(context):
    config_path = LaunchConfiguration("config_path").perform(context)
    if not config_path:
        configs_dir = os.path.join(get_package_share_directory("ov_msckf"), "config")
        available_configs = os.listdir(configs_dir)
        config = LaunchConfiguration("config").perform(context)
        if config in available_configs:
            config_path = os.path.join(
                            get_package_share_directory("ov_msckf"),
                            "config",config,"estimator_config.yaml"
                        )
        else:
            return [
                LogInfo(
                    msg="ERROR: unknown config: '{}' - Available configs are: {} - not starting OpenVINS".format(
                        config, ", ".join(available_configs)
                    )
                )
            ]
    else:
        if not os.path.isfile(config_path):
            return [
                LogInfo(
                    msg="ERROR: config_path file: '{}' - does not exist. - not starting OpenVINS".format(
                        config_path)
                    )
            ]
    path_gt = LaunchConfiguration("path_gt").perform(context)
    dataset = LaunchConfiguration("dataset").perform(context)
    if not path_gt and dataset:
        path_gt = os.path.join(
                    LaunchConfiguration("ov_data_dir").perform(context),
                    LaunchConfiguration("config").perform(context),
                    dataset + ".csv"
                )
    if path_gt and not os.path.isfile(path_gt):
        return [
            LogInfo(
                msg="ERROR: groundtruth file: '{}' - does not exist. - not starting OpenVINS".format(
                    path_gt)
                )
        ]
    node1 = Node(
        package="ov_msckf",
        executable="run_subscribe_msckf",
        condition=IfCondition(LaunchConfiguration("ov_enable")),
        namespace=LaunchConfiguration("namespace"),
        output='screen',
        parameters=[
            {"verbosity": LaunchConfiguration("verbosity")},
            {"use_stereo": LaunchConfiguration("use_stereo")},
            {"max_cameras": LaunchConfiguration("max_cameras")},
            {"use_klt": LaunchConfiguration("use_klt")},
            {"record_timing_information": LaunchConfiguration("record_timing_information")},
            {"record_timing_filepath": LaunchConfiguration("record_timing_filepath")},
            {"save_total_state": LaunchConfiguration("save_total_state")},
            {"filepath_est": LaunchConfiguration("filepath_est")},
            {"filepath_std": LaunchConfiguration("filepath_std")},
            {"config_path": config_path},
            {"path_gt": path_gt},
        ],
    )

    node2 = Node(
        package="rviz2",
        executable="rviz2",
        condition=IfCondition(LaunchConfiguration("rviz_enable")),
        arguments=[
            "-d"
            + os.path.join(
                get_package_share_directory("ov_msckf"), "launch", "display_ros2.rviz"
            ),
            "--ros-args",
            "--log-level",
            "warn",
            ],
    )

    return [node1, node2]


def generate_launch_description():
    opfunc = OpaqueFunction(function=launch_setup)
    ld = LaunchDescription(launch_args)
    ld.add_action(opfunc)
    return ld
