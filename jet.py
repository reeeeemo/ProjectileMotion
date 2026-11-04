import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation

class Jet:
    """Representation of a jet on a linear flight path.
    
    
    """
    def __init__(self, dtype: type):
        self.launch_angle = 30.0
        self.init_vel = 20.0
        self.frame_rate = 60
        self.init_altitude = 50.0
        self.dtype = dtype

        self.init_x = 0.0
        self.current_xy = [0.0, 0.0]

    def plot(self, ax):
        xy0, theta = self.get_init_pos()
        ax.axline((xy0[0], xy0[1]), slope=np.tan(theta), color='g', linestyle=':')

    def animate(self, ax: Axes, fig: Figure):
        xy0, theta = self.get_init_pos()
        dx = self.init_vel * np.cos(theta) / self.frame_rate
        dy = self.init_vel * np.sin(theta) / self.frame_rate
        
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
        
        def inside(x, y):
            return xmin <= x <= xmax and ymin <= y <= ymax
        
        x0, y0 = 0.0, self.init_altitude
        
        x, y = [x0], [y0]
        while inside(x[-1] + dx, y[-1] + dy):
            x.append(x[-1] + dx)
            y.append(y[-1] + dy)
        
        jet, = ax.plot([], [], 'go')
        
        def update(i):
            self.current_xy = (x[i], y[i])
            self.init_x = x[i]
            jet.set_data([x[i]], [y[i]])
            return (jet,)

        return FuncAnimation(fig, update, frames=len(x), interval=1000 / self.frame_rate)

    def reset(self):
        self.current_xy = [0.0, 0.0]
        self.init_x = 0.0

    def get_init_pos(self):
        """Return (xy, angle (radians))"""
        theta = np.radians(self.launch_angle)
        return np.array([
                self.init_x + self.init_vel * np.cos(theta) / self.frame_rate,
                self.init_altitude + (self.init_x * np.tan(theta)) + ((self.init_vel * np.sin(theta)) / self.frame_rate)
            ], dtype=self.dtype), theta