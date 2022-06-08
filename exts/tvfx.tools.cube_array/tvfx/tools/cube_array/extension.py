from functools import partial

from pxr import Gf, UsdGeom, Usd
from pxr.Usd import Stage

import omni.ext
import omni.kit.commands
import omni.ui as ui
import omni.usd

from timeit import default_timer as dt

# PYTHON 3.7.12
cubes = {}
def remove_cubes(stage:Stage, cube_list:list):
    if not cube_list:
        return

    for cube_path in cube_list:
        if stage.GetPrimAtPath(cube_path):
            stage.RemovePrim(cube_path)
    cube_list.clear()

def create_uint_slider(axis:str, min=0, max=10, default=1) -> ui.UIntSlider:
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

def on_slider_change(x_slider:ui.UIntSlider,y_slider:ui.UIntSlider,z_slider:ui.UIntSlider, space_slider:ui.UIntSlider, _b:float, xform:UsdGeom.Xform=None):
    # tot = dt()
    global cubes
    space = space_slider.model.get_value_as_float()*100
    stage:Stage = omni.usd.get_context().get_stage()
    selection = omni.usd.get_context().get_selection()
    if not selection:
        return
    selected_xform = xform or stage.GetPrimAtPath(selection.get_selected_prim_paths()[0])

    if not selected_xform or selected_xform.GetTypeName() != "Xform":
        return

    cubes_list:list = cubes.get(str(selected_xform.GetPath()))
    if not cubes_list:
        cubes_list = cubes[str(selected_xform.GetPath())] = []
    remove_cubes(stage, cubes_list)

    x_count = x_slider.model.get_value_as_int()
    y_count = y_slider.model.get_value_as_int()
    z_count = z_slider.model.get_value_as_int()

    # crt = 0
    # trns = 0
    # apnd = 0

    for i in range(x_count):
        x = i*100+space*i
        for j in range(y_count):
            y = j*100+space*j
            for k in range(z_count):
                a = i
                b = j*x_count
                c = k*y_count*x_count
                n = (a+b+c)
                # st = dt()
                new_path = f'Cube_{str(n).rjust(4,"0")}'
                cube_prim: UsdGeom.Cube = UsdGeom.Cube.Define(stage,selected_xform.GetPath().AppendPath(new_path))
                # crt += dt() - st

                # st = dt()
                UsdGeom.XformCommonAPI(cube_prim).SetTranslate((x, y, k*100+space*k))
                cube_prim.GetSizeAttr().Set(100.0)
                # trns += dt() - st

                # st = dt()
                cubes_list.append(cube_prim.GetPath())
                # apnd += dt() - st
    # print(f"Total: {round(dt() - tot,2)}")
    # print(f"  - Create:    {round(crt,2)}")
    # print(f"  - Transform: {round(trns,2)}")
    # print(f"  - Append:    {round(apnd,2)}")

def on_space_change(x_slider:ui.UIntSlider,y_slider:ui.UIntSlider,z_slider:ui.UIntSlider, space_slider:ui.UIntSlider, _b:float, xform:UsdGeom.Xform=None):
    tot = dt()
    global cubes
    space = space_slider.model.get_value_as_float()*100
    stage:Stage = omni.usd.get_context().get_stage()
    
    selection = omni.usd.get_context().get_selection()
    if not selection:
        return

    selected_xform = xform or stage.GetPrimAtPath(selection.get_selected_prim_paths()[0])

    cubes_list:list = cubes.get(str(selected_xform.GetPath()))
    if not cubes_list:
        return

    x_count = x_slider.model.get_value_as_int()
    y_count = y_slider.model.get_value_as_int()
    z_count = z_slider.model.get_value_as_int()

    for i in range(x_count):
        x = i*100+space*i
        for j in range(y_count):
            y = j*100+space*j
            for k in range(z_count):
                a = i
                b = j*x_count
                c = k*y_count*x_count
                n = (a+b+c)
                new_path = f'Cube_{str(n).rjust(4,"0")}'
                cube_prim:Usd.Prim = stage.GetPrimAtPath(selected_xform.GetPath().AppendPath(new_path))

                UsdGeom.XformCommonAPI(cube_prim).SetTranslate((x, y, k*100+space*k))
                

class MyExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        print("[tvfx.tools.cube_array] MyExtension startup")

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
                space_slider.model.add_value_changed_fn(partial(on_space_change, x_slider,y_slider,z_slider,space_slider))
            
                def create_array_holder(x_slider:ui.UIntSlider,y_slider:ui.UIntSlider,z_slider:ui.UIntSlider, space_slider:ui.UIntSlider):
                    C:omni.usd.UsdContext = omni.usd.get_context()
                    stage:Stage = C.get_stage()
                    xform:UsdGeom.Xform = UsdGeom.Xform.Define(stage, stage.GetDefaultPrim().GetPath().AppendPath("Cube_Array"))
                    omni.kit.commands.execute(
                        'SelectPrimsCommand',
                        old_selected_paths=[],
                        new_selected_paths=[str(xform.GetPath())],
                        expand_in_stage=True
                    )

                    on_slider_change(x_slider, y_slider, z_slider, space_slider,None, xform=xform)
                create_array_button = ui.Button(text="Create Array")
                create_array_button.set_clicked_fn(partial(create_array_holder, x_slider,y_slider,z_slider,space_slider))

    def on_shutdown(self):
        global cubes
        print("[tvfx.tools.cube_array] MyExtension shutdown")
        stage:Stage = omni.usd.get_context().get_stage()
        for key in cubes:
            remove_cubes(stage, cubes[key])
