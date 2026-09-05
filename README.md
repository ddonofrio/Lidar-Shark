# Lidar-Shark

An interactive top-down 2D LiDAR viewer driven exclusively by the `lidar-sdk` provider
contract. Install the SDK and the viewer in the same environment, then run
`python -m lidar_shark`. From PowerShell, using the two sibling repositories:

```powershell
python -m pip install -e ..\stl27l-driver\sdk
python -m pip install -e .
python -m lidar_shark
```

For a dependency-free import check, use `python -m pip install --no-deps -e .`;
running the graphical viewer still requires PySide6 and PyQtGraph. Provider discovery happens through `lidar_sdk.providers`;
the viewer contains no concrete-driver import. The canvas uses `plot_x=-Y/1000` and
`plot_y=X/1000`, so front is up and left is left.
