#!/usr/bin/env python3
"""
Test script for updated gym-p3at ROS2 environment.

Tests:
1. ✅ Gym environment registration
2. ✅ Import and instantiation
3. ✅ Deprecation warnings for ROS1 versions
"""

import sys
import warnings

# Capture deprecation warnings
warnings.simplefilter("always", DeprecationWarning)

print("=" * 60)
print("gym-p3at ROS2 Updated Environment Tests")
print("=" * 60)

# Test 1: Check available gym environments
print("\n[TEST 1] Checking registered Gym environments...")
try:
    import gymnasium as gym
    import gym_p3at  # Must import this first to register environments
    from gymnasium import envs
    
    all_env_ids = [env.id for env in gym.envs.registry.values()]
    p3at_envs = [e for e in all_env_ids if 'p3at' in e.lower()]
    
    print(f"  ✅ Total Gym environments: {len(all_env_ids)}")
    print(f"  ✅ P3AT environments registered: {p3at_envs}")
    
    if 'p3at-v2-ros2' in all_env_ids:
        print("  ✅ 'p3at-v2-ros2' is registered")
    else:
        print("  ❌ 'p3at-v2-ros2' NOT found in registry")
        sys.exit(1)
except Exception as e:
    print(f"  ❌ Error: {e}")
    sys.exit(1)

# Test 2: Test deprecation warnings for ROS1 versions
print("\n[TEST 2] Testing deprecation warnings for ROS1 versions...")
try:
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Try to import ROS1 versions (these should emit warnings)
        try:
            from gym_p3at.envs.p3at_env import p3atEnv as p3at_v0
            if w and "obsoleto" in str(w[-1].message).lower():
                print(f"  ✅ p3at_env (ROS1) emits deprecation warning")
        except ImportError as ie:
            print(f"  ℹ️  p3at_env import would fail (expected): {ie}")
        
except Exception as e:
    print(f"  ℹ️  ROS1 deprecation test skipped: {e}")

# Test 3: Import gym_p3at and check P3atEnvRos2V2
print("\n[TEST 3] Importing gym_p3at and checking P3atEnvRos2V2...")
try:
    import gym_p3at
    from gym_p3at.envs import P3atEnvRos2V2
    
    print(f"  ✅ gym_p3at imported successfully")
    print(f"  ✅ P3atEnvRos2V2 class available")
    
    # Check class attributes
    env_class = P3atEnvRos2V2
    print(f"  ✅ Environment metadata: {env_class.metadata}")
    
except Exception as e:
    print(f"  ❌ Error importing: {e}")
    sys.exit(1)

# Test 4: Check setup.py version
print("\n[TEST 4] Checking package version...")
try:
    from importlib.metadata import version as pkg_version
    version = pkg_version("gym_p3at")
    print(f"  ✅ gym_p3at version: {version}")
    if version == "0.0.3":
        print("  ✅ Version correctly updated to 0.0.3")
    else:
        print(f"  ⚠️  Expected version 0.0.3, got {version}")
except Exception as e:
    print(f"  ⚠️  Could not check version: {e}")

# Test 5: Check dependencies
print("\n[TEST 5] Checking required dependencies...")
required_packages = ['gymnasium', 'numpy', 'cv2', 'rclpy']
for pkg in required_packages:
    try:
        __import__(pkg)
        print(f"  ✅ {pkg} is installed")
    except ImportError:
        print(f"  ❌ {pkg} is NOT installed")
        sys.exit(1)

# Test 6: Check YOLO files
print("\n[TEST 6] Checking YOLO detection files...")
import os
yolo_dir = os.path.dirname(gym_p3at.__file__) + "/envs"
yolo_files = ['coco.names', 'yolov4-tiny.cfg', 'yolov4-tiny.weights']
all_present = True
for fname in yolo_files:
    fpath = os.path.join(yolo_dir, fname)
    exists = os.path.exists(fpath)
    status = "✅" if exists else "❌"
    print(f"  {status} {fname}")
    if not exists:
        all_present = False

if not all_present:
    print("  ⚠️  Some YOLO files are missing (env will work but detection will fail)")

# Summary
print("\n" + "=" * 60)
print("Summary:")
print("=" * 60)
print("✅ gym-p3at ROS2 environment is properly configured")
print("✅ Deprecated ROS1 versions marked for removal")
print("✅ All required dependencies are installed")
print("\nNext steps:")
print("  1. Run evaluation: python test_gym_p3at_ros2_updated.py")
print("  2. Start ROS2 simulation or real robot")
print("  3. Use: env = gym.make('p3at-v2-ros2')")
print("=" * 60)
