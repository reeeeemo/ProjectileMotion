import numpy as np
import matplotlib.pyplot as plt

class Jet:
    """Representation of a jet on a linear flight path.
    
    
    """
    def __init__(self, dtype: type):
        self.launch_angle = 30.0
        self.init_vel = 20.0
        self.frame_rate = 60
        self.init_altitude = 50.0
        self.dtype = dtype

    def plot(self, ax):
        xy0, theta = self.get_init_pos()
        ax.axline((xy0[0], xy0[1]), slope=np.tan(theta), color='g', linestyle=':')

    def animate(self):
        pass

    def get_init_pos(self):
        """Return (xy, angle (radians))"""
        theta = np.radians(self.launch_angle)
        return np.array([
                self.init_vel * np.cos(theta) / self.frame_rate,
                self.init_altitude + ((self.init_vel * np.sin(theta)) / self.frame_rate)
            ], dtype=self.dtype), theta