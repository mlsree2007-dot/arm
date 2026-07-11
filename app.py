import threading
import time

import pybullet as p
import pybullet_data

from flask import Flask, render_template
from flask_socketio import SocketIO

# -----------------------
# Flask + SocketIO
# -----------------------

app = Flask(__name__)
app.config["SECRET_KEY"] = "robot"

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading"
)

# -----------------------
# Shared Target Position
# -----------------------

target_lock = threading.Lock()

target_position = {
    "x": 0.5,
    "y": 0.2,
    "z": 0.5
}

END_EFFECTOR_INDEX = 6


# -----------------------
# Simulation Thread
# -----------------------

def run_simulation():

    physics = p.connect(p.GUI)

    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, -9.81)

    p.loadURDF("plane.urdf")

    robot = p.loadURDF(
        "kuka_iiwa/model.urdf",
        basePosition=[0, 0, 0],
        useFixedBase=True
    )

    num_joints = p.getNumJoints(robot)

    print("Robot Loaded")
    print("Number of joints:", num_joints)

    for i in range(num_joints):
        print(i, p.getJointInfo(robot, i)[1].decode())

    # Target Marker

    marker_visual = p.createVisualShape(
        shapeType=p.GEOM_SPHERE,
        radius=0.03,
        rgbaColor=[1, 0, 0, 1]
    )

    marker = p.createMultiBody(
        baseMass=0,
        baseVisualShapeIndex=marker_visual
    )

    last_print = time.time()

    while p.isConnected():

        with target_lock:
            target = [
                target_position["x"],
                target_position["y"],
                target_position["z"]
            ]

        p.resetBasePositionAndOrientation(
            marker,
            target,
            [0, 0, 0, 1]
        )

        joint_positions = p.calculateInverseKinematics(
            robot,
            END_EFFECTOR_INDEX,
            target
        )

        p.setJointMotorControlArray(
            bodyUniqueId=robot,
            jointIndices=list(range(num_joints)),
            controlMode=p.POSITION_CONTROL,
            targetPositions=joint_positions[:num_joints]
        )

        if time.time() - last_print > 1:
            print("Current Target:", target)
            last_print = time.time()

        p.stepSimulation()
        time.sleep(1 / 240)


# -----------------------
# Flask Routes
# -----------------------

@app.route("/")
def index():
    return render_template("index.html")


# -----------------------
# Socket Events
# -----------------------

@socketio.on("connect")
def on_connect():
    print("Browser Connected")


@socketio.on("disconnect")
def on_disconnect():
    print("Browser Disconnected")


@socketio.on("update_target")
def update_target(data):

    print("Received:", data)

    with target_lock:
        target_position["x"] = float(data["x"])
        target_position["y"] = float(data["y"])
        target_position["z"] = float(data["z"])


# -----------------------
# Main
# -----------------------

if __name__ == "__main__":

    sim = threading.Thread(
        target=run_simulation,
        daemon=True
    )

    sim.start()

    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=False,
        use_reloader=False
    )