import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Slider, Button
from projectile import Projectile

def main():
    ### setup projectile class and figures ###
    proj = Projectile(
        gravity=9.81,
        dtype=np.float32,
        deltatime=0.01,
        wind=np.array([0, 0], dtype=np.float32)
    )
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_axes([0.08, 0.40, 0.88, 0.55])

    ### initial values ###
    x, y, h = proj.trajectory()
    proj.plot(fig, ax, x, y, h)
    #line, = ax.plot(x, y, "b-")
    #ax.set_xlabel("Distance (m)")
    #ax.set_ylabel("Height (m)")
    #ax.grid(True)

    ### setup variable slides ###
    def slider_ax(row):
        return fig.add_axes([0.2, 0.28 - row * 0.045, 0.6, 0.03])

    s_angle = Slider(slider_ax(0), "Angle (°)", -90, 90, valinit=proj.launch_angle)
    s_vel = Slider(slider_ax(1), "Speed (m/s)", 0, 100, valinit=proj.init_vel)
    s_alt = Slider(slider_ax(2), "Altitude (m)", 0, 200, valinit=proj.init_altitude)
    s_mass = Slider(slider_ax(3), "Mass (kg)", 0.1, 20, valinit=proj.m)
    s_cd = Slider(slider_ax(4), "Drag coef", 0, 2, valinit=proj.C_drag)
    sliders = [s_angle, s_vel, s_alt, s_mass, s_cd]

    def update(_):
        proj.launch_angle = s_angle.val
        proj.init_vel = s_vel.val
        proj.init_altitude = s_alt.val
        proj.m = s_mass.val
        proj.C_drag = s_cd.val

        x, y, h = proj.trajectory()
        proj.plot(fig, ax, x, y, h)
        #line.set_data(x, y)
        fig.canvas.draw_idle()

    for s in sliders:
        s.on_changed(update)

    reset_btn = Button(fig.add_axes([0.85, 0.05, 0.1, 0.04]), "Reset")
    reset_btn.on_clicked(lambda _: [s.reset() for s in sliders])

    plt.show()

if __name__ == "__main__":
    main()