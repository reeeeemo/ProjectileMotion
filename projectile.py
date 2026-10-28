import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import uuid
from pathlib import Path

SAVE_PATH = Path("./figures/")
SAVE_PATH.mkdir(parents=True, exist_ok=True)

class Projectile:
    """2D Projectile Motion calculator.

        Parameters
        ----------
        gravity : float
            Gravity in m/s
        dtype : type
            Precision value to use for calculations
        deltatime : float
            Deltatime for simulation
        wind : np.ndarray
            Headwind velocity

        Attributes
        ----------
        _g : float
            Gravity in m/s
        _dtype : type
            Precision value to use for calculations
        _dt : float
            Deltatime for simulation
        _wind : np.ndarray
            Headwind velocity
        m : float
            Mass of object
        rho : float
            Air density
        C_drag : float
            Drag coefficient
        l : float
            Length of object
        h : float
            Height of object
        w : float
            Width of object
        init_altitude : float
            Initial altitude of launched object
        init_vel : float
            Initial velocity of launched object
        launch_angle : int
            Initial launched angle of object in degrees
        max_time : int
            Time frame to drop object before early cutoff
    """
    def __init__(
            self, 
            gravity: float = 9.81, 
            dtype: type = np.float32, 
            deltatime: float = 0.01, 
            wind: np.ndarray = None,
         ):
        # projectile constants
        self._g = gravity
        self._dtype = dtype
        self._dt = deltatime
        self._wind = wind if wind is not None else np.zeros(2, dtype=self._dtype)
        
        # projectile changeable vars
        self.m = 5.0
        self.rho = 1.225
        self.C_drag = 0.5
        self.l = 2.0  # length
        self.h = 0.5  # height 
        self.w = 1.0  # width

        self.init_altitude = 50.0
        self.init_vel = 20.0
        self.launch_angle = 30
        self.max_time = 30

    def trajectory(self):
        """Return the points on a path following projectile motion in 2D.

                Returns:
                (x, y) points on a projectile path 
        """
        ### v0x = v0 * cos0 || v0y = v0 * sin0 ###
        theta = np.radians(self.launch_angle)
        vx, vy = self.init_vel * np.cos(theta), self.init_vel * np.sin(theta)

        ### allocate memory for all variables for euler dynamics ###
        n = max(int(np.ceil(self.max_time / self._dt)) + 1, 2)
        x, y = np.zeros(n, dtype=self._dtype), np.zeros(n, dtype=self._dtype)
        heading = np.zeros(n, dtype=self._dtype)
        t = np.zeros(n, dtype=self._dtype)

        x[0], y[0], heading[0] = 0.0, self.init_altitude, theta
        px, py, i = 0.0, self.init_altitude, 1

        ### semi-implicit euler dynamics for 2d projectile motion ###
        while py >= 0.0 and i < n - 1:  
            # compute exposed surface area based on current heading
            cos_theta = np.abs(np.cos(theta))
            sin_theta = np.abs(np.sin(theta))
            esa_x = ( self.w * (self.l * sin_theta + self.h * cos_theta) )
            esa_y = ( self.w * (self.l * cos_theta + self.h * sin_theta) )
            drag_x = self.rho * self.C_drag * esa_x
            drag_y = self.rho * self.C_drag * esa_y

            # rel velocities w/ wind
            v_rel_x = vx + self._wind[0]
            v_rel_y = vy + self._wind[1]
            speed = np.sqrt(v_rel_x**2 + v_rel_y**2)

            # accelerations
            ax = -(drag_x / (2 * self.m)) * speed * v_rel_x
            ay = -self._g - (drag_y / (2 * self.m)) * speed * v_rel_y

            # update velocities / positions (semi-implciit euler :p)
            vx += ax * self._dt
            vy += ay * self._dt
            px += vx * self._dt
            py += vy * self._dt

            x[i] = px
            y[i] = py
            theta = np.arctan2(vy, vx)
            heading[i] = theta.copy()
            t[i] = i * self._dt
            i += 1
        return x[:i], y[:i], heading[:i]

    def plot(self, fig, ax, x, y, heading):
        """Plot and save a given trajectory."""
        #id_ = uuid.uuid4()

        ### plot animation ###
        #fig, ax = plt.subplots()

        #ax.set_xlim(0, x.max() * 1.05)
        #ax.set_ylim(0, y.max() * 1.05)
        #path, = ax.plot([], [], "b-")
        #ball, = ax.plot([], [], "ro")

        #def update(i):
        #    """Callback to set array for animation."""
        #    path.set_data(x[:i+1], y[:i+1])
        #    ball.set_data([x[i]], [y[i]])
        #    return path, ball

        #anim = FuncAnimation(fig, update, frames=len(x), interval=20)
        #anim.save(str(SAVE_PATH / f"{str(id_)}_projectile.gif"), writer=PillowWriter(fps=50))

        ### plot static image ###
        #ratio = (y.max() - y.min()) / (x.max() - x.min())
        #fig, ax = plt.subplots(figsize=(10, np.clip(10 * ratio, 4.5, 8)))
        ax.clear()
        xpad = max(0.05 * (x.max() - x.min()), 1.0)
        ypad = max(0.1 * (y.max() - y.min()), 1.0)
        ax.set_xlim(x.min() - xpad, x.max() + xpad)
        ax.set_ylim(min(0, y.min()), y.max() + ypad)
        sx, sy = ax.transData.transform([1, 1]) - ax.transData.transform([0, 0])

        ax.plot(x, y)
        ax.scatter(x[0], y[0], c='green')
        ax.scatter(x[-1], y[-1], c='red')

        # plot heading angle at each interval
        step = max(len(x) // 15, 1)  # every 15 intervals
        L = 20

        for xi, yi, h in zip(x[::step], y[::step], heading[::step]):
            h_screen = np.arctan2(np.sin(h) * sy, np.cos(h) * sx)
            dx, dy = L * np.cos(h_screen) / sx, L * np.sin(h_screen) / sy
            ax.annotate(
                "", xy=(xi + dx, yi + dy), xytext=(xi - dx, yi - dy), annotation_clip=False,
                arrowprops=dict(arrowstyle="-|>", color="k", lw=3)
            )
            ax.annotate(
                f"{np.degrees(h):.0f}°", xy=(xi, yi), xycoords="data", xytext=(4, 6),
                textcoords="offset points", fontsize=8
            )

        fig.suptitle("Projectile Motion")
        ax.set_ylabel("Height (m)")
        ax.set_xlabel("Distance (m)")
        ax.grid(True)
        return fig
        #fig.savefig(str(SAVE_PATH / f"{str(id_)}_projectile.png"))


#### MAIN FUNCTION ####
if __name__ == "__main__":
    proj = Projectile(
        gravity=9.81,
        dtype=np.float32,
        deltatime=0.01,
        wind=np.array([0.0, 0.0]),
    )
    x, y, h = proj.trajectory(
        init_vel=30.0, 
        launch_angle=25.0
    )
    proj.plot(x, y, h)