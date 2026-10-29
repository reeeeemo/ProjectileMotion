import matplotlib
matplotlib.use("QtAgg")

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation

from PyQt6 import QtCore, QtWidgets, QtGui
from projectile import Projectile
import numpy as np

SCALE = 1000  # 0.001 is 1 tick

class Screen(QtWidgets.QMainWindow):
    """Interactive GUI for displaying 2D Projectile Motion.

    Inherits from QtWidgets.QMainWindow

    Attributes
    ----------
    fig : Figure
        Matplotlib grid for displaying trajectory plotting
    canvas : FigureCanvasQTAgg
        Wrapper for matplotlib grid to PyQt6
    ax : Axes
        Matplotlib ax to draw trajectories
    proj : Projectile
        Class to compute Projectile Motion
    sliders : dict
        All Slider bars
    boxes : dict
        All text boxes
    defaults : dict
        All default values to reset to
    checks : dict
        All checkboxes
    table : QLabel
        Console for displaying all outputs
    anim : FuncAnimation
        Animation function for visual plotting
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Projectile Motion")

        ### setup figure and main classes for config ###
        self.fig = Figure(figsize=(8,5), layout="constrained")
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.ax = self.fig.add_subplot()
        self.proj = Projectile(
            gravity=9.81,
            dtype=np.float32,
            deltatime=0.01,
            wind=np.array([0.0, 0.0], dtype=np.float32)
        )

        ### inputs: slider and text box per val ###
        inputs = [
            ("C_drag", "C (drag coef)", 0.0, 2.0, self.proj.C_drag),
            ("rho", "p (kg/m^3)", 0.0, 3.0, self.proj.rho),
            ("init_vel", "Speed (m/s)", 0.0, 100.0, self.proj.init_vel),
            ("m", "Mass (kg)", 1.0, 20.0, self.proj.m),
            ("launch_angle", "Angle (°)", -90.0, 90.0, self.proj.launch_angle),
            ("init_altitude", "Altitude (m)", 0.0, 100.0, self.proj.init_altitude),
            ("spread", "+/-% Variance", 0.0, 50.0, 10.0),
            ("l", "Object Length", 0, 5.0, self.proj.l),
            ("w", "Object Width", 0, 5.0, self.proj.w),
            ("h", "Object Height", 0, 5.0, self.proj.h)
        ]

        grid = QtWidgets.QGridLayout()
        self.sliders, self.boxes, self.defaults = {}, {}, {}
        for row, (key, lbl, lo, hi, init) in enumerate(inputs):
            s = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
            s.setRange(round(lo * SCALE), round(hi * SCALE))
            s.setValue(round(init * SCALE))

            box = QtWidgets.QDoubleSpinBox()
            box.setDecimals(3)
            box.setRange(lo, hi)
            box.setValue(init)

            s.valueChanged.connect(lambda v, b=box: b.setValue(v / SCALE))
            box.valueChanged.connect(lambda v, sl=s: sl.setValue(round(v * SCALE)))
            s.sliderReleased.connect(self._refresh)
            box.editingFinished.connect(self._refresh)

            grid.addWidget(QtWidgets.QLabel(lbl), row, 0)
            grid.addWidget(s, row, 1)
            grid.addWidget(box, row, 2)
            self.sliders[key], self.boxes[key], self.defaults[key] = s, box, init

        ### add std-dev checkboxes ###
        checks_row = QtWidgets.QHBoxLayout()
        checks_row.addWidget(QtWidgets.QLabel("Applies:"))
        self.checks = {}
        for key, lbl in [("rho", "p"), ("init_altitude", "Altitude"), ("init_vel", "Speed"), ("launch_angle", "Angle")]:
            cb = QtWidgets.QCheckBox(lbl)
            checks_row.addWidget(cb)
            self.checks[key] = cb
            self.checks[key].checkStateChanged.connect(self._refresh)
        checks_row.addStretch()

        ### add console for variable output ###
        self.table = QtWidgets.QLabel()
        self.table.setFont(QtGui.QFont("Consolas", 9))
        self.table.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.table.setStyleSheet("background:#f7f7f7; border:1px solid gray; padding:8px; color:black")

        ### buttons and formatting with widgets ###
        plot_btn = QtWidgets.QPushButton("Animate")
        plot_btn.clicked.connect(self._animate)
        reset_btn = QtWidgets.QPushButton("Reset")
        reset_btn.clicked.connect(self._reset)

        top = QtWidgets.QHBoxLayout()
        top.addWidget(self.canvas, stretch=3)
        top.addWidget(self.table, stretch=1)

        buttons = QtWidgets.QVBoxLayout()
        buttons.addWidget(plot_btn)
        buttons.addWidget(reset_btn)
        buttons.addStretch()

        bottom = QtWidgets.QHBoxLayout()
        bottom.addLayout(grid, stretch=1)
        bottom.addLayout(buttons)

        root = QtWidgets.QVBoxLayout()
        root.addLayout(top, stretch=1)
        root.addLayout(bottom)
        root.addLayout(checks_row)

        central = QtWidgets.QWidget()
        central.setLayout(root)
        self.setCentralWidget(central)

        self._refresh()

    def _reset(self, _):
        """Set all boxes/sliders back to default."""
        for k, b in self.boxes.items():
            b.setValue(self.defaults[k])
        self._refresh()

    def _run(self, proj, **overrides):
        """Run one simulation with temp parameters (flight_time, (x,y) coords)."""
        saved = {k: getattr(proj, k) for k in overrides}
        for k, v in overrides.items():
            setattr(proj, k, v)

        proj.trajectory()
        result = (proj.flight_time, proj.xy.copy())
        for k, v in saved.items():
            setattr(proj, k, v)
        return result

    def _animate(self, *_):
        self._refresh()
        x, y = self.proj.xy.copy()

        line = self.ax.lines[-1]
        line.set_data([], [])

        step = max(1, len(x) // 10)

        def update(i):
            n = min(i * step + 1, len(x))
            line.set_data(x[:n], y[:n])
            return (line,)

        self.anim = FuncAnimation(self.fig, update, frames=len(x)//step + 2, interval=20, repeat=False)

    def _refresh(self, *_):
        """Recompute using all sliders.
        
            Runs a no-drag version for info. Additionally run a 9-simulation spread from -x% to +x%.
            Runs nominal simulation last.
        """
        if getattr(self, "anim", None):
            if self.anim.event_source is not None:
                self.anim.event_source.stop()
        for k, b in self.boxes.items():
            if k != "spread":
                setattr(self.proj, k, round(b.value(), 3))

        t_nd, xy = self._run(self.proj, C_drag=0.0)
        d_nd = xy[0, -1]
        self.proj.plot(self.fig, self.ax, clear=True, linestyle="dotted")

        # simulation spread
        spread_lines = []
        cb_checks = [key for key, cb in self.checks.items() if cb.isChecked()]
        if len(cb_checks):
            pct = self.boxes["spread"].value()
            attrs = [(a, getattr(self.proj, a)) for a in cb_checks]
            factors = np.linspace(1 - pct / 100, 1 + pct / 100, 9)  # -x% to +x%
            kwargs_list = [{a: v * f for a, v in attrs} for f in factors]
            samples = [self._run(self.proj, **kw) for kw in kwargs_list]  # (N, (t, xy))
            times = np.array([t for t, _ in samples])
            xys = [xy for _, xy in samples] # (N, xy)
            dists = np.array([xy[0, -1] for xy in xys])  # (dist,)
            spread_lines = [
                ("lo", pct, dists[0]), ("hi", pct, dists[-1]),
                ("span", dists.min(), dists.max()), ("std", dists.std(), times.std())
            ]

            # plot sim spread
            x_common = np.linspace(0, max(x.max() for x, _ in xys), 300)
            ys = np.array([np.interp(x_common, x, y) for x, y in xys])
            self.ax.fill_between(x_common, ys.min(axis=0), ys.max(axis=0), alpha=0.3)

        # nominal simulation
        self.proj.trajectory()
        t_d, d_d = self.proj.flight_time, self.proj.xy[0][-1]

        def pct_diff(d):
            """Compute difference (%) between given xy displacement and nominal xy displacement."""
            return 100 * (d - d_d) / d_d if abs(d_d) > 1e-9 else float("nan")

        lines = [
            "OUTPUTS",
            "-" * 38,
            "DRAG",
            f"Flight time: {t_d:10.3f}s",
            f"Horizontal Distance: {d_d:10.3f}m"
        ]
        for item in spread_lines:
            if item[0] == "lo":
                lines.append(f"Distance -{item[1]:.0f}% : {item[2]:10.3f}m ({pct_diff(item[2]):+.1f}%)")
            elif item[0] == "hi":
                lines.append(f"Distance +{item[1]:.0f}% : {item[2]:10.3f}m ({pct_diff(item[2]):+.1f}%)")
            elif item[0] == "span":
                lines.append(f" Range -x% - +x%: {item[2] - item[1]:10.3f}m")
            elif item[0] == "std":
                lines.append(f" Std-dev distance: {item[1]:10.3f}m")
                lines.append(f" Std-dev time: {item[2]:10.3f}s")
        lines += [
            "",
            "NO DRAG",
            f"Flight time: {t_nd:10.3f}s",
            f"Distance x: {d_nd:10.3f}m"
        ]
        self.table.setText("\n".join(lines))

        self.proj.plot(self.fig, self.ax, clear=False)
        self.canvas.draw_idle()