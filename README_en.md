# nav2

## Introduction

Nav2 navigation bringup package providing autonomous navigation capabilities for JDBot K3 differential drive robot. Based on ROS2 Nav2 navigation stack, supporting both 2D LiDAR localization navigation and RGBD depth camera navigation modes.

## Features

**Supported:**
- AMCL-based 2D LiDAR localization navigation
- RTAB-Map based RGBD depth camera navigation
- DWB local path planner
- Configurable costmap parameters

**Not Supported:**
- Mapping functionality (requires SLAM package)
- Multi-robot collaborative navigation

## Quick Start

### Prerequisites

Dependencies:
- nav2_bringup
- nav2_common
- launch / launch_ros

### Build

```bash
source /opt/ros/humble/setup.bash
colcon build --packages-select nav2
source install/setup.bash
```

### Run Examples

**Basic Navigation:**
```bash
ros2 launch nav2 nav2.launch.py map:=/path/to/map.yaml
```

**RGBD Navigation:**
```bash
ros2 launch nav2 nav2_rtabmap_rgbd.launch.py
```

## Detailed Usage

### Directory Structure

```
nav2/
├── config/
│   ├── jdbot_k3_diff.yaml      # Differential drive navigation parameters
│   └── rgbd_nav2_params.yaml   # RGBD navigation parameters
├── launch/
│   ├── nav2.launch.py              # Basic navigation launch
│   └── nav2_rtabmap_rgbd.launch.py # RTAB-Map RGBD navigation launch
└── map/                            # Map files directory
```

### Configuration

**jdbot_k3_diff.yaml** - Optimized parameters for JDBot K3 differential robot:
- AMCL localization: Configured for YDLidar X3 Pro (10 Hz, 0.1-12m range)
- DWB planner: Max velocity 0.5 m/s
- Costmap: Robot radius 0.21m

**rgbd_nav2_params.yaml** - RGBD depth camera navigation parameters

### Launch Arguments

| Parameter | Default | Description |
|-----------|---------|-------------|
| `map` | `map/my_map.yaml` | Path to map file |
| `params` | `config/jdbot_k3_diff.yaml` | Navigation parameters file |
| `use_sim_time` | `false` | Whether to use simulation time |

## FAQ

**Q: Robot localization drifts significantly?**
A: Check LiDAR data quality, adjust AMCL particle count and update frequency parameters.

**Q: Path planning fails?**
A: Verify costmap parameters match actual robot dimensions, check if map is valid.

## Version & Release

| Version | Date | Description |
|---------|------|-------------|
| 0.0.1 | 2026-02 | Initial release |

## Contributing

Issues and Pull Requests are welcome.

## License

Source files in this component are declared as Apache-2.0. The `LICENSE` file in this directory shall prevail.
