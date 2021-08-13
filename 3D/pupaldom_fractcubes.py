# metadata struct
bl_info = {
    "name": "Generátor fráktálových kostek (Sponge)",
    "description": "Fractal Cubes generator",
    "author": "Dominik Pupala",
    "version": (1, 0, 0),
    "blender": (2, 91, 0),
    "location": "View3D > Add > Mesh > FractCubes",
    "category": "Add Mesh"
}

# imports
import bpy
import random

class MyFractCubes(bpy.types.Operator):
    bl_idname = "object.fract_cubes"
    bl_label = "Fractal Cubes"
    bl_options = {'REGISTER', 'UNDO'}
    
    size = bpy.props.FloatProperty(
        name='Size', 
        description='Size of single fractal cube', 
        default=2, 
        min=0, 
        step=1
    )
    
    location = bpy.props.FloatVectorProperty(
        name='Location', 
        description='Location of fractal cube', 
        default=(1.0, 1.0, 1.0)
    )
    
    iterations = bpy.props.IntProperty(
        name='Iterations', 
        description='Number of iterations', 
        default=3, 
        min=1, 
        max=6, 
        step=1
    )
    
    rows = bpy.props.IntProperty(
        name='Rows', 
        description='Number of rows', 
        default=1, 
        min=1, 
        step=1
    )
    
    columns = bpy.props.IntProperty(
        name='Columns', 
        description='Number of columns', 
        default=1, 
        min=1, 
        step=1
    )
    
    offset = bpy.props.FloatProperty(
        name='Offset', 
        description='Offset between cubes', 
        default=0.2, 
        min=0, 
        step=1
    )
        
    def execute(self, context):
        object = self.construct(self.iterations, self.size, self.location)
        
        if (self.rows * self.columns != 1):
            self.generate(object)
            bpy.ops.object.join()
        
        return {'FINISHED'}
    
    def generate(self, object):
        c = self.colormix()
        
        for i in range(0, self.rows):
            for j in range(0, self.columns):
                if (i == j == 0): continue # skip already existing object
            
                temp = object.copy()
                temp.data = object.data.copy()
                temp.data.materials.append(c[2] if random.random() < 0.031 else c[1] if random.random() > 0.491 else c[0])
                temp.location = (
                    temp.location[0] + i * (self.size + self.offset), 
                    temp.location[1] + j * (self.size + self.offset), 
                    temp.location[2] + random.random() * self.size * 17 / 13
                )
                
                bpy.context.scene.collection.objects.link(temp)
        
        object.data.materials.append(c[2] if random.random() < 0.031 else c[1] if random.random() > 0.491 else c[0])
        object.location[2] = object.location[2] +  random.random() * self.size * 17 / 13
        
        return bpy.context.object
    
    def colormix(self):
        base = bpy.data.materials.new("Base")
        base.use_nodes = True
        base.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.13, 0.03, 0.07, 1)
        
        high = bpy.data.materials.new("High")
        high.use_nodes = True
        high.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.97, 0.87, 0.93, 1)
        
        rare = bpy.data.materials.new("Rare")
        rare.use_nodes = True
        rare.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.69, 0.06, 0.31, 1)
        
        return (base, high, rare)
    
    def construct(self, iterations, size, location):
        # the smallest cube is mesh primitive
        if iterations == 1:
            bpy.ops.mesh.primitive_cube_add(location=location, size=size)
            bpy.context.object.name = 'FractCube'
            return bpy.context.object
        
        # get smaller cube via recursive construction of fractal cube
        cube = self.construct(iterations - 1, size / 3, (location[0] - size / 3, location[1] - size / 3, location[2] - size / 3))
        
        # create larger cube
        for x in range(0, 3):
            for y in range(0, 3): 
                for z in range(0, 3):
                    if (x == y == z == 0): continue # skip already existing cube
                    if (x == y == 1) or (x == z == 1) or (y == z == 1): continue # skip non edge cubes
                    
                    temp = cube.copy()
                    temp.data = cube.data.copy()
                    temp.location = (
                        temp.location[0] + x * size / 3, 
                        temp.location[1] + y * size / 3, 
                        temp.location[2] + z * size / 3
                    )
                    
                    bpy.context.scene.collection.objects.link(temp)
        
        # unify larger cube
        bpy.ops.object.join() 
        
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        bpy.ops.mesh.remove_doubles() # merge double vertices
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
            
        return bpy.context.object
        


classes = [MyFractCubes]

def menu_func(self, context):
    self.layout.operator(MyFractCubes.bl_idname)

def register():
    for c in classes: 
        bpy.utils.register_class(c)
    
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)
    
def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)

    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)
    
if __name__ == "__main__":
    register()