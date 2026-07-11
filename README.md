# Robot Arm Reach Simulator

A simulated robot arm (PyBullet) controlled live via a web dashboard (Flask + WebSockets),
using inverse kinematics to reach a target point in 3D space.

## Folder structure (must match exactly)

```
your_project_folder/
├── app.py
├── requirements.txt
└── templates/
    └── index.html
```

`index.html` MUST sit inside a folder literally named `templates`, next to `app.py`.

## Setup

1. Install dependencies:
   ```
   pip install flask flask-socketio pybullet
   ```

2. Run the app:
   ```
   python app.py
   ```

3. A PyBullet GUI window opens. Leave it open in the background.

4. In your browser, go to:
   ```
   http://localhost:5000
   ```
   (Don't open `index.html` directly as a file — it must be loaded through this URL.)

5. Status text should switch to green "Connected". Drag the X/Y/Z sliders and
   watch the arm move in the PyBullet window.

## Reading the terminal output (this version has built-in diagnostics)

Your `app.py` already prints helpful debug info — use it like this:

**On startup**, you should see:
```
Robot Loaded
Number of joints: 7
0 lbr_iiwa_joint_1
1 lbr_iiwa_joint_2
...
```
This confirms the KUKA arm loaded correctly with 7 joints.

**When the browser connects**, you should see:
```
Browser Connected
```
If this never appears after loading `http://localhost:5000`, the page isn't
reaching your server — double check the URL and that no firewall is blocking
port 5000.

**When you drag a slider**, you should see, once per movement:
```
Received: {'x': 0.62, 'y': 0.2, 'z': 0.5}
```
If this never appears, the browser isn't sending WebSocket events — open your
browser's DevTools (F12) → Console tab and check for red errors.

**Roughly once per second**, the simulation loop prints:
```
Current Target: [0.62, 0.2, 0.5]
```
If this always shows the old default `[0.5, 0.2, 0.5]` even after you've moved
a slider and seen `Received:` print, the shared `target_position` variable
isn't being updated correctly — check `target_lock` usage for typos.

If both `Received:` and `Current Target:` show correct updated values but the
**arm still doesn't visually move**, the issue is in how the computed joint
angles are applied. Compare `joint_positions` length to `num_joints` — for the
KUKA iiwa arm these should both be 7, matching `END_EFFECTOR_INDEX = 6` (the
last joint, index 6, since indexing starts at 0).

## Troubleshooting

### "Internal Server Error" in browser
Check the terminal for the real error, printed right after the page loads.
Usually caused by `templates/index.html` being missing or misplaced.

### Page stuck on "Connecting…"
You opened `index.html` as a local file instead of via the server. Use
`http://localhost:5000` in the address bar, not a `file:///` path.

### Two PyBullet windows open
Caused by Flask's debug auto-reloader. This version already has
`debug=False, use_reloader=False` set, so this shouldn't happen — if it does,
confirm you're running the correct, saved copy of `app.py`.

### Port 5000 already in use
Change the port in `app.py`:
```python
socketio.run(app, host="0.0.0.0", port=5001, debug=False, use_reloader=False)
```
Then visit `http://localhost:5001` instead.

## How it works

- **app.py** runs two things concurrently via threading:
  - A PyBullet physics loop (background thread) that loads a KUKA robot arm,
    repeatedly computes inverse kinematics toward the current target, and
    applies those joint angles with `setJointMotorControlArray`.
  - A Flask + Socket.IO server (main thread) serving the dashboard and
    listening for `update_target` events sent whenever a slider moves.
- **templates/index.html** is the browser dashboard: three range sliders that
  emit an `update_target` WebSocket event on every `input` change, and show
  live connection status.
- A small red sphere marks the current target position in the simulation —
  the arm's end-effector (joint index 6) tries to reach it via IK.

## Key concepts demonstrated

- **URDF**: robot description loaded from PyBullet's built-in `kuka_iiwa/model.urdf`
- **Inverse Kinematics (IK)**: `p.calculateInverseKinematics()` converts a
  target XYZ point into joint angles
- **Joint position control**: `p.setJointMotorControlArray(..., p.POSITION_CONTROL, ...)`
- **Simulation stepping**: `p.stepSimulation()` advances physics one frame at a time
- **Client-server + WebSockets**: browser slider changes are pushed instantly
  to the Python backend, no polling or page reloads
- **Threading + locks**: physics loop and web server run concurrently; the
  `target_lock` prevents both threads from reading/writing `target_position`
  at the exact same instant

## Possible extensions

- Swap the KUKA arm for a CAD model exported to URDF (SW2URDF for SolidWorks,
  Fusion2URDF for Fusion 360)
- Add a virtual camera feed for a perception pipeline
- Replace the IK call with a trained reinforcement learning policy
  (Gymnasium + PyBullet)
- Add obstacle objects and collision-avoidance logic
