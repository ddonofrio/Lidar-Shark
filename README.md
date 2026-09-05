# Lidar-Shark

Lidar-Shark is an interactive top-down 2D LiDAR viewer driven exclusively by the
`lidar-sdk` provider contract. The viewer discovers installed providers through the
SDK and does not import `stl27l_driver`.

## Install and run

From PowerShell, using the two sibling repositories:

```powershell
python -m pip install -e ..\stl27l-driver\sdk
python -m pip install -e .
python -m lidar_shark
```

For a POSIX shell, use the same commands with `../stl27l-driver/sdk` and
`../stl27l-driver` paths.

The deterministic fixture provider is available without hardware:

```powershell
python -m pip install -e ..\stl27l-driver\sdk
python -m pip install -e .\fixture-provider
python -m pip install -e .
python -m lidar_shark
```

## Current viewer behavior

- Provider and source selection are populated from SDK descriptors.
- Acquisition runs outside the Qt UI thread and tolerates normal subscription timeouts and closure.
- The canvas shows valid returns only, with front up and left to the left (`plot_x=-Y/1000`, `plot_y=X/1000`).
- Range coloring, persistence, metric grid, zoom, pan, recenter, cursor coordinates, and point selection are available.
- The configuration dock exposes source configuration and display controls.
- The status line shows scan identity, valid/total samples, stream timing, drops, and selected-point details when available.

## Tests

Run focused tests first, then the complete suite:

```powershell
python -m pytest -q tests/test_orientation.py tests/test_scan_view.py tests/test_acquisition.py
python -m pytest -q
```

The tests use the SDK models and fake sources; they do not validate physical hardware.

Recording, replay, A/B and sector measurements, settings persistence, PNG export, and
provider refresh are not part of the current viewer surface yet.
