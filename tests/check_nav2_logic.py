#!/usr/bin/env python3

# Copyright 2026 SpacemiT (Hangzhou) Technology Co. Ltd.
#
# SPDX-License-Identifier: Apache-2.0

import importlib.util
import math
import pathlib
import sys
import types


class ClockStub:
    def now(self):
        return self

    def to_msg(self):
        return "stamp"


class LoggerStub:
    def debug(self, message):
        print(f"[debug] {message}")

    def error(self, message):
        print(f"[error] {message}")

    def info(self, message):
        print(f"[info] {message}")

    def warning(self, message):
        print(f"[warning] {message}")


class BasicNavigatorStub:
    def __init__(self):
        self.followed_waypoints = []
        self.cancel_count = 0
        self.task_checks = 0
        self.result = 0

    def cancelTask(self):
        self.cancel_count += 1
        self.result = 1

    def create_publisher(self, *_args, **_kwargs):
        return types.SimpleNamespace(publish=lambda _msg: None)

    def create_subscription(self, *_args, **_kwargs):
        return object()

    def destroyNode(self):
        return None

    def followWaypoints(self, waypoints):
        self.followed_waypoints = list(waypoints)

    def get_clock(self):
        return ClockStub()

    def getFeedback(self):
        return types.SimpleNamespace(current_waypoint=1)

    def get_logger(self):
        return LoggerStub()

    def getResult(self):
        return self.result

    def goToPose(self, target):
        self.target = target

    def isTaskComplete(self):
        self.task_checks += 1
        return self.task_checks > 1

    def waitUntilNav2Active(self):
        return None


class PollerStub:
    def register(self, *_args, **_kwargs):
        return None

    def unregister(self, *_args, **_kwargs):
        return None

    def poll(self, *_args, **_kwargs):
        return []


class SocketStub:
    def bind(self, address):
        self.address = address

    def close(self):
        return None

    def send_string(self, message):
        self.message = message

    def setsockopt(self, *_args, **_kwargs):
        return None


class ContextStub:
    def socket(self, _socket_type):
        return SocketStub()

    def term(self):
        return None



def install_ros_stubs():
    geometry_msgs = types.ModuleType("geometry_msgs")
    geometry_msgs_msg = types.ModuleType("geometry_msgs.msg")

    class Quaternion:
        def __init__(self):
            self.x = 0.0
            self.y = 0.0
            self.z = 0.0
            self.w = 1.0

    class PoseStamped:
        def __init__(self):
            self.header = types.SimpleNamespace(frame_id="", stamp=None)
            self.pose = types.SimpleNamespace(
                position=types.SimpleNamespace(x=0.0, y=0.0, z=0.0),
                orientation=Quaternion(),
            )

    geometry_msgs_msg.PoseStamped = PoseStamped
    geometry_msgs_msg.Quaternion = Quaternion
    geometry_msgs.msg = geometry_msgs_msg
    sys.modules["geometry_msgs"] = geometry_msgs
    sys.modules["geometry_msgs.msg"] = geometry_msgs_msg

    std_msgs = types.ModuleType("std_msgs")
    std_msgs_msg = types.ModuleType("std_msgs.msg")
    std_msgs_msg.Bool = type("Bool", (), {"__init__": lambda self: setattr(self, "data", False)})
    std_msgs.msg = std_msgs_msg
    sys.modules["std_msgs"] = std_msgs
    sys.modules["std_msgs.msg"] = std_msgs_msg

    sensor_msgs = types.ModuleType("sensor_msgs")
    sensor_msgs_msg = types.ModuleType("sensor_msgs.msg")
    sensor_msgs_msg.Image = type("Image", (), {"__init__": lambda self: None})
    sensor_msgs.msg = sensor_msgs_msg
    sys.modules["sensor_msgs"] = sensor_msgs
    sys.modules["sensor_msgs.msg"] = sensor_msgs_msg

    rclpy = types.ModuleType("rclpy")
    rclpy.init = lambda *args, **kwargs: None
    rclpy.ok = lambda: True
    rclpy.shutdown = lambda: None
    rclpy.spin_once = lambda *args, **kwargs: None
    sys.modules["rclpy"] = rclpy

    ament_index_python = types.ModuleType("ament_index_python")
    packages = types.ModuleType("ament_index_python.packages")
    packages.get_package_share_directory = lambda name: f"/tmp/{name}"
    ament_index_python.packages = packages
    sys.modules["ament_index_python"] = ament_index_python
    sys.modules["ament_index_python.packages"] = packages

    robot_navigator = types.ModuleType("nav2_simple_commander.robot_navigator")
    robot_navigator.BasicNavigator = BasicNavigatorStub
    robot_navigator.TaskResult = types.SimpleNamespace(SUCCEEDED=0, CANCELED=1, FAILED=2)
    nav2_simple_commander = types.ModuleType("nav2_simple_commander")
    nav2_simple_commander.robot_navigator = robot_navigator
    sys.modules["nav2_simple_commander"] = nav2_simple_commander
    sys.modules["nav2_simple_commander.robot_navigator"] = robot_navigator

    spacemit_audio = types.ModuleType("spacemit_audio")
    spacemit_audio.init = lambda *args, **kwargs: None
    spacemit_audio.AudioPlayer = object
    sys.modules["spacemit_audio"] = spacemit_audio

    cv2 = types.ModuleType("cv2")
    cv2.VideoCapture = lambda _source: types.SimpleNamespace(
        isOpened=lambda: False,
        release=lambda: None,
    )
    sys.modules["cv2"] = cv2

    zmq = types.ModuleType("zmq")
    zmq.PAIR = 0
    zmq.POLLIN = 1
    zmq.LINGER = 2
    zmq.Context = ContextStub
    zmq.Poller = PollerStub
    sys.modules["zmq"] = zmq


def import_module(module_root, relative_path, module_name):
    module_path = pathlib.Path(module_root) / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def assert_close(actual, expected, message):
    assert math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-9), (
        f"{message}: expected {expected!r}, got {actual!r}"
    )


def check_waypoint_contract(module_root):
    autonomous_patrol = import_module(
        module_root,
        "nav2/autonomous_patrol.py",
        "autonomous_patrol_under_test",
    )

    assert autonomous_patrol.camera_arg_to_source("0") == 0
    assert autonomous_patrol.camera_arg_to_source("video12") == "/dev/video12"
    assert autonomous_patrol.camera_arg_to_source("/tmp/frame.mp4") == "/tmp/frame.mp4"

    navigator = BasicNavigatorStub()
    waypoints = autonomous_patrol.build_square_waypoints(navigator, side_length=2.0)
    expected = [
        (2.0, 0.0, 0.0),
        (2.0, -2.0, -math.pi / 2.0),
        (0.0, -2.0, -math.pi),
        (0.0, 0.0, math.pi / 2.0),
    ]

    assert len(waypoints) == len(expected), "square patrol must contain four waypoints"
    for index, (pose, (x, y, yaw)) in enumerate(zip(waypoints, expected), start=1):
        assert pose.header.frame_id == "map", f"waypoint {index} frame must be map"
        assert_close(pose.pose.position.x, x, f"waypoint {index} x")
        assert_close(pose.pose.position.y, y, f"waypoint {index} y")
        assert_close(pose.pose.position.z, 0.0, f"waypoint {index} z")
        assert_close(pose.pose.orientation.z, math.sin(yaw / 2.0), f"waypoint {index} qz")
        assert_close(pose.pose.orientation.w, math.cos(yaw / 2.0), f"waypoint {index} qw")

    controller = autonomous_patrol.SquareWaypointController(side_length=2.0)
    controller.stop_requested = True
    controller.start_camera_publish = lambda: setattr(controller, "camera_publish_enabled", True)
    autonomous_patrol.play_patrol_error_sound = lambda: None

    result = controller.run_waypoints_once()
    assert result == 1, "stopped patrol should report incomplete task"
    assert controller.navigator.cancel_count == 1, "stopped patrol must cancel navigator task"
    assert controller.has_pending_waypoints, "stopped patrol must keep pending waypoints"
    assert len(controller.pending_waypoints) == 4, "stopped patrol should preserve remaining waypoints"
    assert controller.camera_publish_enabled, "stopped patrol should enable camera publishing on retained waypoints"

    print("NAV2_WAYPOINT_CONTRACT_OK")


def check_zmq_timeout(module_root):
    round_trip = import_module(
        module_root,
        "nav2/round_trip_grab_task.py",
        "round_trip_grab_task_under_test",
    )

    task = round_trip.RoundTripGrabTask(
        point_a_x=0.0,
        point_a_y=0.0,
        point_a_yaw=0.0,
        point_b_x=1.0,
        point_b_y=0.0,
        point_b_yaw=math.pi / 2.0,
        zmq_bind="inproc://ci-test",
        wait_interval_sec=0.001,
    )

    try:
        result = task.wait_for_message("finish grab", timeout_sec=0.0)
        assert result is False, "missing ZMQ completion message must fail by timeout"
        assert_close(task.point_b.pose.orientation.z, math.sin(math.pi / 4.0), "point B qz")
        assert_close(task.point_b.pose.orientation.w, math.cos(math.pi / 4.0), "point B qw")
    finally:
        task.shutdown()

    print("NAV2_ZMQ_TIMEOUT_OK")


def main():
    if len(sys.argv) != 3:
        print("usage: check_nav2_logic.py <waypoint|zmq-timeout> <module_root>", file=sys.stderr)
        return 2

    install_ros_stubs()

    test_name = sys.argv[1]
    module_root = pathlib.Path(sys.argv[2])
    if test_name == "waypoint":
        check_waypoint_contract(module_root)
        return 0
    if test_name == "zmq-timeout":
        check_zmq_timeout(module_root)
        return 0

    print(f"unknown test: {test_name}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())