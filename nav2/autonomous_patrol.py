#!/usr/bin/env python3

# Copyright 2026 SpacemiT (Hangzhou) Technology Co. Ltd.
#
# SPDX-License-Identifier: Apache-2.0

import math
import os
import threading
import sys
import time
import wave
from typing import List

import cv2
import rclpy
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import PoseStamped, Quaternion
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
import spacemit_audio
from sensor_msgs.msg import Image
from spacemit_audio import AudioPlayer
from std_msgs.msg import Bool



def quaternion_from_yaw(yaw: float) -> Quaternion:
    q = Quaternion()
    q.z = math.sin(yaw / 2.0)
    q.w = math.cos(yaw / 2.0)
    return q



def make_pose(navigator: BasicNavigator, x: float, y: float, yaw: float) -> PoseStamped:
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.header.stamp = navigator.get_clock().now().to_msg()
    pose.pose.position.x = x
    pose.pose.position.y = y
    pose.pose.position.z = 0.0
    pose.pose.orientation = quaternion_from_yaw(yaw)
    return pose



def build_square_waypoints(navigator: BasicNavigator, side_length: float = 1.0) -> List[PoseStamped]:
    return [
        make_pose(navigator, side_length, 0.0, 0.0),
        make_pose(navigator, side_length, -side_length, -math.pi / 2.0),
        make_pose(navigator, 0.0, -side_length, -math.pi),
        make_pose(navigator, 0.0, 0.0, math.pi / 2.0),
    ]


def play_wav_file(file_path: str, device: int = -1) -> bool:
    try:
        with wave.open(file_path, 'rb') as wav_file:
            channels = wav_file.getnchannels()
            sample_rate = wav_file.getframerate()
            sample_width = wav_file.getsampwidth()
            compression = wav_file.getcomptype()
            audio_data = wav_file.readframes(wav_file.getnframes())
    except (OSError, wave.Error) as exc:
        print(f'无法读取 WAV 文件: {exc}')
        return False

    if compression != 'NONE' or sample_width != 2:
        print(f'仅支持 16-bit PCM WAV: {file_path}')
        return False

    spacemit_audio.init(
        sample_rate=sample_rate,
        channels=channels,
        player_device=device,
    )

    with AudioPlayer(device) as player:
        if not player.start(sample_rate=sample_rate, channels=channels):
            print(f'播放设备启动失败: {file_path}')
            return False

        chunk_bytes = 4096 * channels * 2
        for offset in range(0, len(audio_data), chunk_bytes):
            if not player.write(audio_data[offset:offset + chunk_bytes]):
                print(f'播放失败: {file_path}')
                return False

    return True


def play_patrol_error_sound() -> None:
    try:
        wav_path = os.path.join(get_package_share_directory('nav2'), 'wav', 'patrol_error.wav')
        if not os.path.exists(wav_path):
            print(f'告警音频不存在: {wav_path}')
            return
        if not play_wav_file(wav_path):
            print(f'告警音频播放失败: {wav_path}')
    except Exception as exc:
        print(f'播放告警音频异常: {exc}')


def camera_arg_to_source(camera_device: str):
    if camera_device.isdigit():
        return int(camera_device)
    if camera_device.startswith('video') and camera_device[5:].isdigit():
        return f'/dev/{camera_device}'
    return camera_device


class SquareWaypointController:
    def __init__(self, side_length: float = 1.0) -> None:
        self.navigator = BasicNavigator()
        self.side_length = side_length
        self.start_requested = False
        self.stop_requested = False
        self.task_running = False
        self.has_pending_waypoints = False
        self.pending_waypoints: List[PoseStamped] = []
        self.last_feedback_waypoint = -1
        self.camera_device = 'video12'
        self.camera_topic = '/patrol/error_image'
        self.camera_publish_enabled = False
        self.camera_publish_thread: threading.Thread | None = None
        self.camera_publisher = self.navigator.create_publisher(Image, self.camera_topic, 10)

        self.navigator.create_subscription(
            Bool,
            '/square_waypoints_enable',
            self.control_callback,
            10,
        )

    def publish_camera_images(self) -> None:
        source = camera_arg_to_source(self.camera_device)
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            print(f'相机打开失败: {source}')
            return

        try:
            while self.camera_publish_enabled and rclpy.ok():
                ok, frame = cap.read()
                if not ok or frame is None:
                    print(f'相机取帧失败: {source}')
                    break

                msg = Image()
                msg.header.stamp = self.navigator.get_clock().now().to_msg()
                msg.header.frame_id = 'camera'
                msg.height = frame.shape[0]
                msg.width = frame.shape[1]
                msg.encoding = 'bgr8'
                msg.is_bigendian = 0
                msg.step = frame.shape[1] * frame.shape[2]
                msg.data = frame.tobytes()
                self.camera_publisher.publish(msg)
                time.sleep(0.1)
        finally:
            cap.release()
            self.camera_publish_thread = None

    def start_camera_publish(self) -> None:
        if (
            self.camera_publish_enabled
            and self.camera_publish_thread is not None
            and self.camera_publish_thread.is_alive()
        ):
            return

        self.camera_publish_enabled = True
        self.camera_publish_thread = threading.Thread(target=self.publish_camera_images, daemon=True)
        self.camera_publish_thread.start()

    def stop_camera_publish(self) -> None:
        self.camera_publish_enabled = False

    def control_callback(self, msg: Bool) -> None:
        if msg.data:
            self.start_requested = True
            self.stop_requested = False
            self.stop_camera_publish()
            print('收到启动命令')
        else:
            self.stop_requested = True
            self.start_requested = False
            print('收到停止命令')

    def run_waypoints_once(self) -> int:
        if self.has_pending_waypoints and self.pending_waypoints:
            waypoints = list(self.pending_waypoints)
            self.navigator.followWaypoints(waypoints)
            self.pending_waypoints=[]
            self.has_pending_waypoints=False
            print(f'从剩余 {len(waypoints)} 个点继续巡航')
        else:
            waypoints = build_square_waypoints(self.navigator, side_length=self.side_length)
            self.navigator.followWaypoints(waypoints)
            print('从第 1 个点开始执行正方形巡航')


        self.task_running = True
        self.last_feedback_waypoint = -1

        while not self.navigator.isTaskComplete():
            if self.stop_requested:
                remaining_index = max(self.last_feedback_waypoint, 0)
                self.pending_waypoints = list(waypoints[remaining_index:])
                self.has_pending_waypoints = len(self.pending_waypoints) > 0
                self.navigator.cancelTask()
                self.task_running = False
                self.stop_requested = False
                if self.has_pending_waypoints:
                    print(f'收到停止命令，已取消当前巡航任务；保留剩余 {len(self.pending_waypoints)} 个点')
                    threading.Thread(target=play_patrol_error_sound, daemon=True).start()
                    self.start_camera_publish()
                    break
                else:
                    print('收到停止命令，已取消当前巡航任务')
                    break


            feedback = self.navigator.getFeedback()
            if feedback and hasattr(feedback, 'current_waypoint'):
                current_waypoint = feedback.current_waypoint
                self.last_feedback_waypoint = current_waypoint
                print(f'正在前往第 {current_waypoint + 1} / {len(waypoints)} 个点')

            rclpy.spin_once(self.navigator, timeout_sec=0.1)

        self.task_running = False
        result = self.navigator.getResult()

        if len(self.pending_waypoints) > 0:
            print(f'巡航任务已结束，剩余 {len(self.pending_waypoints)} 个点等待下一次启动命令')
            return 1

        if result == TaskResult.SUCCEEDED:
            self.has_pending_waypoints = False
            self.pending_waypoints = []
            print('正方形四点巡航完成，等待下一次启动命令')
            return 0
        if result == TaskResult.CANCELED:
            print('巡航任务已取消，等待下一次启动命令')
            return 1

        self.has_pending_waypoints = False
        self.pending_waypoints = []
        print('巡航任务失败，等待下一次启动命令')
        return 2



def main(args=None) -> int:
    rclpy.init(args=args)
    controller = SquareWaypointController(side_length=1.0)

    cli_args = sys.argv[1:] if args is None else args
    for arg in cli_args:
        if arg.startswith('--camera-device:='):
            controller.camera_device = arg.split(':=', 1)[1] or 'video12'
        elif arg.startswith('--camera-topic:='):
            controller.camera_topic = arg.split(':=', 1)[1] or '/patrol/error_image'
            controller.camera_publisher = controller.navigator.create_publisher(Image, controller.camera_topic, 10)

    try:
        controller.navigator.waitUntilNav2Active()
        print('Nav2 已激活，等待外部向 /square_waypoints_enable 发送 Bool 控制命令')
        print('发送 True 启动正方形巡航，发送 False 停止当前巡航')
        print(f'停止保留航点时将打开相机 {controller.camera_device} 并发布到 {controller.camera_topic}')

        while rclpy.ok():
            rclpy.spin_once(controller.navigator, timeout_sec=0.1)
            if controller.start_requested and not controller.task_running:
                controller.start_requested = False
                controller.run_waypoints_once()

        return 0
    except KeyboardInterrupt:
        if controller.task_running:
            controller.navigator.cancelTask()
        print('收到中断，已取消任务')
        return 130
    finally:
        controller.stop_camera_publish()
        controller.navigator.destroyNode()
        rclpy.shutdown()


if __name__ == '__main__':
    sys.exit(main())
