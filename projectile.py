import numpy as np

class Projectile:
    """2D Projectile Motion calculator.

        Parameters
        ----------
        gravity : float
            Gravity in m/s^2
        dtype : type
            Precision value to use for calculations
        deltatime : float
            Deltatime for simulation
        wind : np.ndarray
            Headwind velocity

        Attributes
        ----------
        _g : float
            Gravity in m/s^2
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
        launch_angle : float
            Initial launched angle of object in degrees
        max_time : int
            Time frame to drop object before early cutoff
        xy : np.ndarray
            Current XY displacement points after a trajectory
        heading : np.ndarray
            Current heading per timestep after a trajectory
        t : np.ndarray
            Array of all timesteps to fit deltatime
        elapsed : int
            Elapsed timesteps of a trajectory run
    """
    def __init__(
            self, 
            gravity: float = 9.81, 
            dtype: type = np.float32, 
            deltatime: float = 0.01, 
            wind: np.ndarray = None,
         ):
        ### projectile constants ###
        self._g = gravity
        self._dtype = dtype
        self._dt = deltatime
        self._wind = wind if wind is not None else np.zeros(2, dtype=self._dtype)
        
        ### projectile changeable vars ###
        self.m = 5.0
        self.rho = 1.225
        self.C_drag = 0.5
        self.l = 2.0
        self.h = 0.5
        self.w = 1.0

        self.init_altitude = 50.0
        self.init_vel = 20.0
        self.launch_angle = 30.0
        self.max_time = 1000

        ### per-iteration variables to output ###
        self.max_time_scaled = max(int(np.ceil(self.max_time / self._dt)) + 1, 2)
        self._xy = np.zeros((self.max_time_scaled, 2), dtype=self._dtype)
        self._heading = np.zeros(self.max_time_scaled, dtype=self._dtype)
        self.t = np.arange(self.max_time_scaled, dtype=self._dtype) * self._dt
        self.elapsed = 0

    def trajectory(self):
        """Compute a projectile motion calculation in 2D with drag."""
        ### v0x = v0 * cos0 || v0y = v0 * sin0 ###
        theta = np.radians(self.launch_angle)
        vx, vy = self.init_vel * np.cos(theta), self.init_vel * np.sin(theta)

        ### allocate memory for all variables for euler dynamics ###
        self._xy[0, :] = (0.0, self.init_altitude)
        self._heading[0] = theta
        px, py, self.elapsed = 0.0, self.init_altitude, 1

        ### semi-implicit euler dynamics for 2d projectile motion ###
        while py >= 0.0 and self.elapsed < self.t.shape[0] - 1:  
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

            self._xy[self.elapsed, :] = (px, py)
            theta = np.arctan2(vy, vx)
            self._heading[self.elapsed] = theta.copy()
            self.elapsed += 1

    def plot(
            self, 
            fig, 
            ax, 
            clear: bool = True, 
            linestyle: str = "solid"
         ):
        """Plot the most recent trajectory."""
        x, y = self.xy
        if clear: 
            ax.clear()
            xpad = max(0.05 * (x.max() - x.min()), 1.0)
            ypad = max(0.1 * (y.max() - y.min()), 1.0)
            ax.set_xlim(x.min() - xpad, x.max() + xpad)
            ax.set_ylim(min(0, y.min()), y.max() + ypad)

        ax.plot(x, y, linestyle=linestyle)
        ax.scatter(x[0], y[0], c='green')
        ax.scatter(x[-1], y[-1], c='red')

        ax.set_ylabel("Height (m)")
        ax.set_xlabel("Distance (m)")
        return fig

    @property
    def flight_time(self):
        return self.t[self.elapsed - 1]

    @property
    def xy(self):
        return self._xy[:self.elapsed].T

    @property
    def heading(self):
        return self._heading[:self.elapsed]
