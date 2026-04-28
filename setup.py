# Copyright 2026 SpacemiT (Hangzhou) Technology Co. Ltd.
#
# SPDX-License-Identifier: Apache-2.0

from setuptools import find_packages, setup
import os
import glob

package_name = 'nav2'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'config'), [f for f in glob.glob('config/*') if os.path.isfile(f)]),
        (os.path.join('share', package_name, 'launch'), glob.glob('launch/*.py')),
        (os.path.join('share', package_name, 'map'), [f for f in glob.glob('map/*') if os.path.isfile(f)]),
        (os.path.join('share', package_name, 'wav'), [f for f in glob.glob('wav/*') if os.path.isfile(f)]),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='robot_team',
    maintainer_email='robot_team@spacemit.com',
    description='TODO: Package description',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'autonomous_patrol = nav2.autonomous_patrol:main',
            'round_trip_grab_task = nav2.round_trip_grab_task:main',
        ],
    },
)
