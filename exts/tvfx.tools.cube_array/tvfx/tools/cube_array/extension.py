from functools import partial

from pxr import Gf, UsdGeom, Usd
from pxr.Usd import Stage

import omni.ext
import omni.kit.commands
import omni.ui as ui
import omni.usd

from timeit import default_timer as dt

# PYTHON 3.7.12

def create_uint_slider(axis:str, min=0, max=50, default=1) -> ui.UIntSlider:
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
    global cubes
    # Get Active Prim
    space = space_slider.model.get_value_as_float()*100
    stage:Stage = omni.usd.get_context().get_stage()
    selection = omni.usd.get_context().get_selection().get_selected_prim_paths()
    if not selection:
        return
    selected_xform = xform or stage.GetPrimAtPath(selection[0])
    
    # Ensure PointInstancer
    if not selected_xform or selected_xform.GetPrim().GetTypeName() != "PointInstancer":
        return

    # Get XYZ values
    x_count = x_slider.model.get_value_as_int()
    y_count = y_slider.model.get_value_as_int()
    z_count = z_slider.model.get_value_as_int()

    ids = []
    positions = []
    # Create Cube Array
    for i in range(x_count):
        x = i*100+space*i
        for j in range(y_count):
            y = j*100+space*j
            for k in range(z_count):
                b = j*x_count
                c = k*y_count*x_count
                n = (i+b+c)
                positions.append((x, y, k*100+space*k))
                ids.append(0)
    
    instancer = UsdGeom.PointInstancer(selected_xform.GetPrim())
    instancer.CreateProtoIndicesAttr()
    instancer.CreatePositionsAttr()
    instancer.GetProtoIndicesAttr().Set(ids)
    instancer.GetPositionsAttr().Set(positions)

def on_space_change(x_slider:ui.UIntSlider,y_slider:ui.UIntSlider,z_slider:ui.UIntSlider, space_slider:ui.UIntSlider, _b:float, xform:UsdGeom.Xform=None):
    space = space_slider.model.get_value_as_float()*100
    stage:Stage = omni.usd.get_context().get_stage()
    
    # Get Active Selection
    selection = omni.usd.get_context().get_selection().get_selected_prim_paths()
    if not selection:
        return
    selected_xform = xform or stage.GetPrimAtPath(selection[0])

    # Ensure PointInstancer
    if not selected_xform or selected_xform.GetPrim().GetTypeName() != "PointInstancer":
        return

    # Get XYZ Values
    x_count = x_slider.model.get_value_as_int()
    y_count = y_slider.model.get_value_as_int()
    z_count = z_slider.model.get_value_as_int()

    ids = []
    positions = []
    # Translate Cubes
    for i in range(x_count):
        x = i*100+space*i
        for j in range(y_count):
            y = j*100+space*j
            for k in range(z_count):
                b = j*x_count
                c = k*y_count*x_count
                n = (i+b+c)
                positions.append((x, y, k*100+space*k))
                ids.append(0)
    
    instancer = UsdGeom.PointInstancer(selected_xform.GetPrim())
    instancer.CreateProtoIndicesAttr()
    instancer.CreatePositionsAttr()
    instancer.GetProtoIndicesAttr().Set(ids)
    instancer.GetPositionsAttr().Set(positions)
                

class MyExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        print("[tvfx.tools.cube_array] MyExtension startup")

        self._window = ui.Window("My Window", width=300, height=300)
        with self._window.frame:
            with ui.VStack():
                # Create Slider Row
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
                
                # Add Functions on Change
                x_slider.model.add_value_changed_fn(partial(on_slider_change, x_slider,y_slider,z_slider,space_slider))
                y_slider.model.add_value_changed_fn(partial(on_slider_change, x_slider,y_slider,z_slider,space_slider))
                z_slider.model.add_value_changed_fn(partial(on_slider_change, x_slider,y_slider,z_slider,space_slider))
                space_slider.model.add_value_changed_fn(partial(on_space_change, x_slider,y_slider,z_slider,space_slider))

                # Create Array Xform Button
                def create_array_holder(x_slider:ui.UIntSlider,y_slider:ui.UIntSlider,z_slider:ui.UIntSlider, space_slider:ui.UIntSlider):
                    C:omni.usd.UsdContext = omni.usd.get_context()
                    stage:Stage = C.get_stage()
                    cube_array:UsdGeom.PointInstancer = UsdGeom.PointInstancer.Define(stage, stage.GetDefaultPrim().GetPath().AppendPath("Cube_Array"))
                    proto_container = stage.OverridePrim(cube_array.GetPath().AppendPath("Prototypes"))
                    cube = UsdGeom.Cube.Define(stage,proto_container.GetPath().AppendPath("Cube"))
                    cube.CreateSizeAttr(100)
                    cube_array.CreatePrototypesRel()
                    cube_array.GetPrototypesRel().AddTarget(cube.GetPath())
                    omni.kit.commands.execute(
                        'SelectPrimsCommand',
                        old_selected_paths=[],
                        new_selected_paths=[str(cube_array.GetPath())],
                        expand_in_stage=True
                    )

                    on_slider_change(x_slider, y_slider, z_slider, space_slider,None, xform=cube_array)
                create_array_button = ui.Button(text="Create Array")
                create_array_button.set_clicked_fn(partial(create_array_holder, x_slider,y_slider,z_slider,space_slider))

    def on_shutdown(self):
        print("[tvfx.tools.cube_array] MyExtension shutdown")
        stage:Stage = omni.usd.get_context().get_stage()
