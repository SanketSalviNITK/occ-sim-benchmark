"""Pinhole camera + planar LED panel geometry -> homography (panel mm -> image px)."""
import numpy as np
from dataclasses import dataclass

@dataclass
class CameraIntrinsics:
    f_px: float = 1000.0      # focal length in pixels (~smartphone 1080p main camera)

def panel_corners_mm(n=8, pitch_mm=8.0):
    s = n * pitch_mm
    return np.array([[0, 0], [s, 0], [s, s], [0, s]], float)

def project_panel(distance_m, yaw_deg=0.0, pitch_deg=0.0, roll_deg=0.0, n=8, pitch_mm=8.0, cam=CameraIntrinsics()):
    """Panel centred on optical axis at distance d, rotated by yaw/pitch/roll (deg).
    Returns 4 image-plane corners (px, origin at principal point) for panel corners."""
    s = n * pitch_mm
    P = np.c_[panel_corners_mm(n, pitch_mm) - s / 2, np.zeros(4)]  # mm, panel plane z=0
    y, p, r = np.radians([yaw_deg, pitch_deg, roll_deg])
    Ry = np.array([[np.cos(y), 0, np.sin(y)], [0, 1, 0], [-np.sin(y), 0, np.cos(y)]])
    Rx = np.array([[1, 0, 0], [0, np.cos(p), -np.sin(p)], [0, np.sin(p), np.cos(p)]])
    Rz = np.array([[np.cos(r), -np.sin(r), 0], [np.sin(r), np.cos(r), 0], [0, 0, 1]])
    X = (Rz @ Ry @ Rx @ P.T).T + np.array([0, 0, distance_m * 1000.0])
    return cam.f_px * X[:, :2] / X[:, 2:3]
