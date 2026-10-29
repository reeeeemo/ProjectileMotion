import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, TextBox, CheckButtons
from projectile import Projectile
import numpy as np

class Screen:
    """Interactive GUI for displaying 2D Projectile Motion.
    
    
    """
    def __init__(self, proj: Projectile):
        self.fig = plt.figure(figsize=(10,7))
        self.ax = self.fig.add_axes([0.06, 0.45, 0.6, 0.5])
        self.proj = proj

        ### setup table + error toggle ###
        self.table = self.fig.text(
            0.7, 0.95, "", va="top", family="monospace", fontsize=9,
            bbox=dict(boxstyle="round,pad=0.6", facecolor="#f7f7f7", edgecolor="gray")
        )
        self.check = CheckButtons(self.fig.add_axes([0.78, 0.26, 0.18, 0.06]), ["Show +/-% spread"])

        ### inputs: slider and text box per val ###
        inputs = [
            ("C_drag", "C (drag coef)", 0.0, 2.0, proj.C_drag),
            ("rho", "p (kg/m^3)", 0.0, 3.0, proj.rho),
            ("init_vel", "Speed (m/s)", 0.0, 100.0, proj.init_vel),
            ("m", "Mass (kg)", 1.0, 20.0, proj.m),
            ("launch_angle", "Angle (°)", -90.0, 90.0, proj.launch_angle),
            ("init_altitude", "Altitude (m)", 0.0, 200.0, proj.init_altitude),
            ("spread", "+/-% speed", 0.0, 50.0, 10.0),
        ]
        self.sliders, self.boxes = {}, {}
        for row, (key, lbl, lo, hi, init) in enumerate(inputs):
            y0 = 0.33 - row * 0.045
            s = Slider(self.fig.add_axes([0.14, y0, 0.25, 0.03]), lbl, lo, hi, valinit=init)
            s.valtext.set_visible(False)
            tb = TextBox(self.fig.add_axes([0.61, y0, 0.08, 0.03]), "", initial=f"{init:.3f}")
            self.sliders[key], self.boxes[key] = s, tb
            self.sliders[key].on_changed(self._on_slider(key))
            self.boxes[key].on_submit(self._on_text(key))
        self.check.on_clicked(lambda _: self._refresh())

        ### setup reset button ###
        reset_btn = Button(self.fig.add_axes([0.85, 0.06, 0.1, 0.04]), "Reset")
        reset_btn.on_clicked(self._reset)

    def run(self):
        self._refresh()
        plt.show()
    
    def _set_box(self, k, v):
        tb = self.boxes[k]
        tb.eventson = False
        tb.set_val(f"{v:.3f}")
        tb.eventson = True

    def _on_slider(self, k):
        def cb(v):
            self._set_box(k, v)
            self._refresh()
        return cb

    def _on_text(self, k):
        """Update textbox value with new user-inputted value if correct."""
        def cb(txt):
            s = self.sliders[k]
            try:
                val = float(txt)
            except ValueError:
                self._set_box(k, s.val)
                return
            s.set_val(float(np.clip(round(val, 3), s.valmin, s.valmax)))
        return cb

    def _reset(self, _):
        for k, s in self.sliders.items():
            s.eventson = False
            s.reset()
            s.eventson = True
            self._set_box(k, s.val)
        self._refresh()

    def _run(self, proj, **overrides):
        """Run one simulation with temp parameters (flight_time, distance_x)."""
        saved = {k: getattr(proj, k) for k in overrides}
        for k, v in overrides.items():
            setattr(proj, k, v)

        proj.trajectory()
        x, _ = proj.xy
        result = (proj.flight_time, x[-1])
        for k, v in saved.items():
            setattr(proj, k, v)
        return result

    def _refresh(self):
        """Recompute using all sliders.
        
            Runs a no-drag version for info. Additionally run a 9-simulation spread from -x% to +x%.
            Runs nominal simulation last.
        """
        for key, s in self.sliders.items():
            if key != "spread":
                setattr(self.proj, key, round(s.val, 3))

        t_nd, d_nd = self._run(self.proj, C_drag=0.0)

        # simulation spread
        spread_lines = []
        if self.check.get_status()[0]:
            pct = self.sliders["spread"].val
            v0 = self.proj.init_vel
            speeds = np.linspace(v0 * (1 - pct / 100), v0 * (1 + pct / 100), 9)  # -x% to +x%
            samples = np.array([self._run(self.proj, init_vel=v) for v in speeds])
            times, dists = samples[:, 0], samples[:, 1]
            spread_lines = [
                ("lo", pct, dists[0]), ("hi", pct, dists[-1]),
                ("span", dists[0], dists[-1]), ("std", dists.std(), times.std())
            ]

        # nominal simulation
        self.proj.trajectory()
        t_d, d_d = self.proj.flight_time, self.proj.xy[0][-1]

        def pct_diff(d):
            """Compute difference between given xy displacement and nominal xy displacement."""
            return 100 * (d - d_d) / d_d if abs(d_d) > 1e-9 else float("nan")

        lines = [
            "OUTPUTS",
            "-" * 38,
            "DRAG",
            f"Flight time   :   {t_d:10.3f}s",
            f"Distance x    :   {d_d:10.3f}m"
        ]
        for item in spread_lines:
            if item[0] == "lo":
                lines.append(f"Distance -{item[1]:.0f}% v    :   {item[2]:10.3f}m ({pct_diff(item[2]):+.1f}%)")
            elif item[0] == "hi":
                lines.append(f"Distance +{item[1]:.0f}% v   :   {item[2]:10.3f}m ({pct_diff(item[2]):+.1f}%)")
            elif item[0] == "span":
                lines.append(f" Range -x%..+x%    :   {item[2] - item[1]:10.3f}m")
            elif item[0] == "std":
                lines.append(f" Std-dev distance    :   {item[1]:10.3f} m")
                lines.append(f" Std-dev time    :    {item[2]:10.3f} s")
        lines += [
            "",
            "NO DRAG",
            f"Flight time   :   {t_nd:10.3f}s",
            f"Distance x    :   {d_nd:1.3f}m"
        ]
        self.table.set_text("\n".join(lines))

        self.proj.plot(self.fig, self.ax)
        self.fig.canvas.draw_idle()