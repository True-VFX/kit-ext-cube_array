from functools import partial

from pxr import Gf, UsdGeom
from pxr.Usd import Stage

import omni.ext
import omni.kit.commands
import omni.ui as ui
import omni.usd

# PYTHON 3.7.12

cubes = []
def remove_cubes(stage:Stage):
    for cube_path in cubes:
        print("   -", cube_path)
        if stage.GetPrimAtPath(cube_path):
            stage.RemovePrim(cube_path)
    cubes.clear()

def create_uint_slider(axis:str, min=0, max=100, default=1) -> ui.UIntSlider:
    ui.Label(f"{axis.capitalize()}:",width=20)
    slider = ui.UIntSlider(
        min=min,
        max=max,
        tooltip=f"The number of boxes to create in the {axis.capitalize()} axis"
    )
    slider.model.set_value(default)
    int_field = ui.IntField(width=30)
    int_field.model = slider.model

    return slider

def on_slider_change(x_slider:ui.UIntSlider,y_slider:ui.UIntSlider,z_slider:ui.UIntSlider, space_slider:ui.UIntSlider, _b:float):
    global cubes
    space = space_slider.model.get_value_as_float()*100
    stage:Stage = omni.usd.get_context().get_stage()
    print("Removing Cubes:", len(cubes))
    remove_cubes(stage)

    x_count = x_slider.model.get_value_as_int()
    y_count = y_slider.model.get_value_as_int()
    z_count = z_slider.model.get_value_as_int()

    selected_xform = stage.GetPrimAtPath(omni.usd.get_context().get_selection().get_selected_prim_paths()[0])

    for i in range(x_count):
        x = i*100+space*i
        for j in range(y_count):
            y = j*100+space*j
            for k in range(z_count):
                new_path = f'Cube_{str(len(cubes)).rjust(4,"0")}'
                cube_prim: UsdGeom.Cube = UsdGeom.Cube.Define(stage,selected_xform.GetPath().AppendPath(new_path))

                cube_prim.AddTranslateOp().Set(Gf.Vec3d(x, y, k*100+space*k))
                cube_prim.AddScaleOp().Set(Gf.Vec3d(50, 50, 50))

                cubes.append(cube_prim.GetPath())


class MyExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        print("[zach.testing.omni] MyExtension startup")

        self._window = ui.Window("My Window", width=300, height=300)
        with self._window.frame:
            with ui.VStack():
                with ui.HStack(height=20):
                    x_slider = create_uint_slider("X")
                    y_slider = create_uint_slider("Y")
                    z_slider = create_uint_slider("Z")
                
                ui.Spacer(height=7)
                with ui.HStack(height=20):
                    ui.Label("Space Between:")
                    space_slider = ui.FloatSlider(min=0.0,max=10)
                    space_slider.model.set_value(0.5)
                    space_field = ui.FloatField(width=30)
                    space_field.model = space_slider.model
                    
                x_slider.model.add_value_changed_fn(partial(on_slider_change, x_slider,y_slider,z_slider,space_slider))
                y_slider.model.add_value_changed_fn(partial(on_slider_change, x_slider,y_slider,z_slider,space_slider))
                z_slider.model.add_value_changed_fn(partial(on_slider_change, x_slider,y_slider,z_slider,space_slider))
                space_slider.model.add_value_changed_fn(partial(on_slider_change, x_slider,y_slider,z_slider,space_slider))

    def on_shutdown(self):
        print("[zach.testing.omni] MyExtension shutdown")
        stage:Stage = omni.usd.get_context().get_stage()
        remove_cubes(stage)
