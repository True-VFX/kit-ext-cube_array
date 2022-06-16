from functools import partial

from pxr import UsdGeom, Usd, Sdf, Gf
from pxr.Usd import Stage

import omni.ext
import omni.kit.commands
import omni.ui as ui
import omni.usd


# PYTHON 3.7.12
cubes = {}
def remove_cubes(stage:Stage, cube_list:list):
    if not cube_list:
        return
    omni.kit.commands.execute("DeletePrims", paths=cube_list)
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
    global cubes
    # Get Active Prim
    space = space_slider.model.get_value_as_float()*100
    stage:Stage = omni.usd.get_context().get_stage()
    selection = omni.usd.get_context().get_selection().get_selected_prim_paths()
    if not selection:
        return
    selected_xform = xform or stage.GetPrimAtPath(selection[0])

    # Ensure only to array under Xforms
    if not selected_xform:
        return

    # Remove Existing Cubes: Could be optimized
    cubes_list:list = cubes.get(str(selected_xform.GetPath()))
    if not cubes_list:
        cubes_list = cubes[str(selected_xform.GetPath())] = []
    remove_cubes(stage, cubes_list)

    # Get XYZ values
    x_count = x_slider.model.get_value_as_int()
    y_count = y_slider.model.get_value_as_int()
    z_count = z_slider.model.get_value_as_int()

    # Create Cube Array
    session_layer = stage.GetRootLayer()
    with Usd.EditContext(stage, session_layer):
        with Sdf.ChangeBlock():
            for i in range(x_count):
                x = i*100+space*i
                for j in range(y_count):
                    y = j*100+space*j
                    for k in range(z_count):
                        b = j*x_count
                        c = k*y_count*x_count
                        n = (i+b+c)
                        new_path = f'Cube_{str(n).rjust(4,"0")}'

                        cube = session_layer.GetPrimAtPath(selected_xform.GetPath().AppendPath(new_path)) or Sdf.PrimSpec(session_layer.GetPrimAtPath(selected_xform.GetPath()), new_path, Sdf.SpecifierDef, "Cube")
                        pos = session_layer.GetAttributeAtPath(f"{selected_xform.GetPath().AppendPath(new_path)}.xformOp:translate") or Sdf.AttributeSpec(cube, "xformOp:translate", Sdf.ValueTypeNames.Double3)
                        pos.default = Gf.Vec3d(x, y, k*100+space*k)
                        size = session_layer.GetAttributeAtPath(f"{selected_xform.GetPath().AppendPath(new_path)}.size") or Sdf.AttributeSpec(cube, "size", Sdf.ValueTypeNames.Double)
                        size.default = 100.0
                        op_order = session_layer.GetAttributeAtPath(f"{selected_xform.GetPath().AppendPath(new_path)}.xformOpOrder") or Sdf.AttributeSpec(cube, "xformOpOrder", Sdf.ValueTypeNames.TokenArray)
                        op_order.default  = ["xformOp:translate"]
                        cubes_list.append(cube.path)

def on_space_change(x_slider:ui.UIntSlider,y_slider:ui.UIntSlider,z_slider:ui.UIntSlider, space_slider:ui.UIntSlider, _b:float, xform:UsdGeom.Xform=None):
    global cubes
    space = space_slider.model.get_value_as_float()*100
    stage:Stage = omni.usd.get_context().get_stage()
    
    # Get Active Selection
    selection = omni.usd.get_context().get_selection().get_selected_prim_paths()
    if not selection:
        return
    selected_xform = xform or stage.GetPrimAtPath(selection[0])

    # Ensure Xform
    if not selected_xform:
        return


    cubes_list:list = cubes.get(str(selected_xform.GetPath()))
    if not cubes_list:
        return

    # Get XYZ Values
    x_count = x_slider.model.get_value_as_int()
    y_count = y_slider.model.get_value_as_int()
    z_count = z_slider.model.get_value_as_int()

    # Translate Cubes
    session_layer = stage.GetRootLayer()
    with Usd.EditContext(stage, session_layer):
        with Sdf.ChangeBlock():
            for i in range(x_count):
                x = i*100+space*i
                for j in range(y_count):
                    y = j*100+space*j
                    for k in range(z_count):
                        b = j*x_count
                        c = k*y_count*x_count
                        n = (i+b+c)
                        new_path = f'Cube_{str(n).rjust(4,"0")}'
                        cube_prim:Usd.Prim = stage.GetPrimAtPath(selected_xform.GetPath().AppendPath(new_path))

                        UsdGeom.XformCommonAPI(cube_prim).SetTranslate((x, y, k*100+space*k))
                

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
                    session_layer = stage.GetRootLayer()
                    with Usd.EditContext(stage, session_layer):
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
        self._window.destroy()
        self._window = None
        stage:Stage = omni.usd.get_context().get_stage()
        for key in cubes:
            remove_cubes(stage, cubes[key])
