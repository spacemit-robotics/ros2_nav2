# Copyright 2026 SpacemiT (Hangzhou) Technology Co. Ltd.
#
# SPDX-License-Identifier: Apache-2.0

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    custom_nav_dir = get_package_share_directory('nav2')

    nav2_launch = os.path.join(get_package_share_directory('nav2_bringup'), 'launch', 'navigation_launch.py')


    # Configuration parameters for navigation
    param_dir = os.path.join(custom_nav_dir, 'config')
    param_file = LaunchConfiguration('params', default=os.path.join(param_dir, 'rgbd_nav2_params.yaml'))

    return LaunchDescription([

        DeclareLaunchArgument(
            'params',
            default_value=param_file,
            description='Full path to param file to load'),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                [nav2_launch]),
            launch_arguments={
                'use_sim_time': use_sim_time,
                'params_file': param_file}.items(),
        ),

    ])
