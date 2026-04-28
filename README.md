# nav2

## 项目简介

Nav2 导航启动包，为 JDBot K3 差速驱动机器人提供自主导航能力。基于 ROS2 Nav2 导航栈，支持 2D 激光雷达定位导航和 RGBD 深度相机导航两种模式。

## 功能特性

**支持：**
- 基于 AMCL 的 2D 激光雷达定位导航
- 基于 RTAB-Map 的 RGBD 深度相机导航
- DWB 局部路径规划器
- 可配置的代价地图参数

**不支持：**
- 建图功能（需配合 SLAM 包使用）
- 多机器人协同导航

## 快速开始

### 环境准备

依赖包：
- nav2_bringup
- nav2_common
- launch / launch_ros

### 构建编译

```bash
source /opt/ros/humble/setup.bash
colcon build --packages-select nav2
source install/setup.bash
```

### 运行示例

**基础导航：**
```bash
ros2 launch nav2 nav2.launch.py map:=/path/to/map.yaml
```

**RGBD 导航：**
```bash
ros2 launch nav2 nav2_rtabmap_rgbd.launch.py
```

## 详细使用

### 目录结构

```
nav2/
├── config/
│   ├── jdbot_k3_diff.yaml      # 差速驱动导航参数
│   └── rgbd_nav2_params.yaml   # RGBD 导航参数
├── launch/
│   ├── nav2.launch.py              # 基础导航启动
│   └── nav2_rtabmap_rgbd.launch.py # RTAB-Map RGBD 导航启动
└── map/                            # 地图文件目录
```

### 配置说明

**jdbot_k3_diff.yaml** - JDBot K3 差速机器人优化参数：
- AMCL 定位：适配 YDLidar X3 Pro（10 Hz，0.1-12m 量程）
- DWB 规划器：最大速度 0.5 m/s
- 代价地图：机器人半径 0.21m

**rgbd_nav2_params.yaml** - RGBD 深度相机导航参数

### 启动参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `map` | `map/my_map.yaml` | 地图文件路径 |
| `params` | `config/jdbot_k3_diff.yaml` | 导航参数文件 |
| `use_sim_time` | `false` | 是否使用仿真时间 |

## 常见问题

**Q: 机器人定位漂移严重？**
A: 检查激光雷达数据质量，调整 AMCL 粒子数和更新频率参数。

**Q: 路径规划失败？**
A: 确认代价地图参数与机器人实际尺寸匹配，检查地图是否有效。

## 版本与发布

| 版本 | 日期 | 说明 |
|------|------|------|
| 0.0.1 | 2026-02 | 初始版本 |

## 贡献方式

欢迎提交 Issue 和 Pull Request。

## License

本组件源码文件头声明为 Apache-2.0，最终以本目录 `LICENSE` 文件为准。
