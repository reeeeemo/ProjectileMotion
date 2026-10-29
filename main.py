from screen import Screen
from projectile import Projectile
import numpy as np

if __name__ == "__main__":
    proj = Projectile(
        gravity=9.81,
        dtype=np.float32,
        deltatime=0.01,
        wind=np.array([0.0, 0.0], dtype=np.float32)
    )
    gui = Screen(proj=proj)
    gui.run()