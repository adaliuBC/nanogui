# python/example4.py -- Python version of an example application that
# shows how to use the Canvas widget. For a C++ implementation, see
# '../src/example4.cpp'.
#
# NanoGUI was developed by Wenzel Jakob <wenzel@inf.ethz.ch>.
# The widget drawing code is based on the NanoVG demo application
# by Mikko Mononen.
#
# All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE.txt file.

import nanogui
import random
import math
import gc

from nanogui import Canvas, Shader, RenderPass, Screen, Window, \
    GroupLayout, Color, Widget, BoxLayout, Orientation, Alignment, \
    Button, Matrix4f

from nanogui import glfw

from read_obj import *

class MyCanvas(Canvas):
    def __init__(self, parent):
        super(MyCanvas, self).__init__(parent, 1)

        try:
            import numpy as np

            vertex_shader = """
                #version 330
                uniform mat4 model_mat;
                uniform mat4 view_mat;
                uniform mat4 projection_mat;
                in vec3 position;
                in vec3 color;
                out vec4 frag_color;
                in vec3 normal;

                // for reflection model
                out vec3 frag_position;
                out vec3 frag_normal;

                void main() {
                    mat4 mvp = projection_mat * view_mat * model_mat; 
                    gl_Position = mvp * vec4(position, 1.0);
                    frag_position = position;
                    frag_normal = normal;
                    frag_color = vec4(color, 1.0);
                }
                """

            fragment_shader = """
                #version 330
                out vec4 color;
                in vec4 frag_color;

                // for Phong
                in vec3 frag_position;
                in vec3 frag_normal;
                uniform vec3 light_position;
                uniform float light_intensity;
                uniform vec4 light_color;
                uniform vec3 view_position;

                void main() {
                    // ambient
                    float ambient = 0.7;
                    
                    // diffuse
                    float kd = 5.0;
                    vec3 norm = normalize(frag_normal);
                    vec3 light_dir = normalize(light_position - frag_position);
                    float distance = length(light_position - frag_position);
                    float energy_arrive = light_intensity / (distance * distance);
                    float energy_receive = max(dot(norm, light_dir), 0.0);
                    float diffuse = kd * energy_arrive * energy_receive;

                    //specular
                    float ks = 20.0;
                    vec3 view_dir = normalize(view_position - frag_position);
                    vec3 h = normalize(view_dir + light_dir);
                    float p = 32;
                    float energy_specular = pow( max(dot(norm, h), 0.0), p);
                    float specular = ks * energy_arrive * energy_specular;

                    color =  (ambient + diffuse + specular) * light_color * frag_color;
                }
                """

            self.shader = Shader(
                self.render_pass(),
                # An identifying name
                "a_simple_shader",
                vertex_shader,
                fragment_shader
            )

            # read obj file in
            lines = read_file("./teapot2.obj")
            v_positions = lines_to_positions(lines)
            print("vertexes:", v_positions)
            v_normals = lines_to_normals(lines)
            # print("normals:", v_normals)
            v_textures = lines_to_textures(lines)
            # print("textures:", v_textures)
            triangle_vs_inds, triangle_vts_inds, triangle_vns_inds = \
                lines_to_triangles(lines)
            # print("triangle meshes:")
            # print("  vs:\t", triangle_vs_inds)
            # print("  vts:\t", triangle_vts_inds)
            # print("  vns:\t", triangle_vns_inds)

            triangle_v_ind_plate = []
            for triangle_v_inds in triangle_vs_inds:
                triangle_v_ind_plate += triangle_v_inds
            for i in range(len(triangle_v_ind_plate)):
                triangle_v_ind_plate[i] = int(triangle_v_ind_plate[i])
                triangle_v_ind_plate[i] -= 1
            
            self.indices = np.array(triangle_v_ind_plate, dtype=np.uint32)
            self.positions = np.array(v_positions, dtype=np.float32)
            self.normals = np.array(v_normals, dtype=np.float32)

            colors_list = []
            for i in range(len(self.positions)):
                colors_list.append([1, 1, 1])
            self.colors = np.array(
                colors_list,
                dtype=np.float32)

            # Draw a cube
            indices_cube = np.array(
                [3, 2, 6, 6, 7, 3,
                 4, 5, 1, 1, 0, 4,
                 4, 0, 3, 3, 7, 4,
                 1, 5, 6, 6, 2, 1,
                 0, 1, 2, 2, 3, 0,
                 7, 6, 5, 5, 4, 7],
                dtype=np.uint32)

            positions_cube = np.array(
                [[-1, 1, 1], [-1, -1, 1],
                 [1, -1, 1], [1, 1, 1],
                 [-1, 1, -1], [-1, -1, -1],
                 [1, -1, -1], [1, 1, -1]],
                dtype=np.float32)

            normals_cube = np.array(
                [[-1, 1, 1], [-1, -1, 1],
                 [1, -1, 1], [1, 1, 1],
                 [-1, 1, -1], [-1, -1, -1],
                 [1, -1, -1], [1, 1, -1]],
                dtype=np.float32)

            colors_cube = np.array(
                [[0, 1, 1], [0, 0, 1],
                 [1, 0, 1], [1, 1, 1],
                 [0, 1, 0], [0, 0, 0],
                 [1, 0, 0], [1, 1, 0]],
                dtype=np.float32)

            # self.indices = np.append(self.indices, indices_cube)
            # self.positions = np.append(self.positions, positions_cube, axis = 0)
            # self.normals = np.append(self.normals, normals_cube, axis = 0)
            # self.colors = np.append(self.colors, colors_cube, axis = 0)
            
            self.mesh_num = len(self.indices) // 3
            print(self.mesh_num)
                
            light_color = np.array([1, 1, 1, 1], dtype=np.float32)
            
            light_position = np.array([5, 0, 0], dtype = np.float32)
            light_intensity = np.array(1, dtype = np.float32)

            #look_at matrix
            self.view_position = [10, 10, 10]
            self.view_target = [0, 0, 0]
            self.view_up=[0, 1, 0]
            view_position = np.array(self.view_position, dtype = np.float32)
            self.shader.set_buffer("indices", self.indices)
            self.shader.set_buffer("position", self.positions)
            self.shader.set_buffer("normal", self.normals)
            self.shader.set_buffer("color", self.colors)
            self.shader.set_buffer("light_color", light_color)
            self.shader.set_buffer("light_position", light_position)
            self.shader.set_buffer("light_intensity", light_intensity)
            self.shader.set_buffer("view_position", view_position)
            
            self.rotation_plate = 0
            self.rotation_horizontal = 0
            self.rotation_vertical = 0
        
        except ImportError:
            self.shader = None
            pass

    def draw_contents(self):
        if self.shader is None:
            return
        import numpy as np

        view = Matrix4f.look_at(
            origin=self.view_position,
            target=self.view_target,
            up=self.view_up
        )

        model_plate = Matrix4f.rotate(
            [1, 0, 0],
            self.rotation_plate
        )

        model_horizontal = Matrix4f.rotate(
            [0, 1, 0],
            self.rotation_horizontal
        )

        model_vertical = Matrix4f.rotate(
            [0, 0, 1],
            self.rotation_vertical
        )

        size = self.size()
        proj = Matrix4f.perspective(
            fov=25 * np.pi / 180,
            near=0.1,
            far=20,
            aspect=size[0] / float(size[1])
        )

        self.shader.set_buffer("model_mat", (model_plate @ model_horizontal @ model_vertical).T)
        self.shader.set_buffer("view_mat", view.T)
        self.shader.set_buffer("projection_mat", proj.T)
        with self.shader:
            self.shader.draw_array(Shader.PrimitiveType.Triangle,
                                   0, self.mesh_num * 3, indexed=True)


class TestApp(Screen):
    def __init__(self):
        super(TestApp, self).__init__((800, 600), "NanoGUI Test", False)

        window = Window(self, "Canvas widget demo")
        window.set_position((15, 15))
        window.set_layout(GroupLayout())

        self.canvas = MyCanvas(window)
        self.canvas.set_background_color(Color(0.5, 0.5, 0.5, 1.0))
        self.canvas.set_size((400, 400))

        tools = Widget(window)
        tools.set_layout(BoxLayout(Orientation.Horizontal,
                                  Alignment.Middle, 0, 5))

        b0 = Button(tools, "Random Background")
        def cb0():
            self.canvas.set_background_color(Color(random.random(), random.random(), random.random(), 1.0))
        b0.set_callback(cb0)

        b_plate = Button(tools, "Turn Plate")
        def cb_turn_plate():
            # self.canvas.rotation = random.random() * math.pi
            self.canvas.rotation_plate += 0.3
        b_plate.set_callback(cb_turn_plate)

        b_horizontal = Button(tools, "Turn Horizontal")
        def cb_turn_horizontal():
            self.canvas.rotation_horizontal += 0.3
        b_horizontal.set_callback(cb_turn_horizontal)

        b_vertical = Button(tools, "Turn Vertical")
        def cb_turn_vertical():
            self.canvas.rotation_vertical += 0.3
        b_vertical.set_callback(cb_turn_vertical)

        b_zoomin = Button(tools, "+")
        def cb_zoom_in():
            for i in range(len(self.canvas.view_position)):
                self.canvas.view_position[i] -= 1
        b_zoomin.set_callback(cb_zoom_in)
        
        b_zoomout = Button(tools, "-")
        def cb_zoom_out():
            for i in range(len(self.canvas.view_position)):
                self.canvas.view_position[i] += 1
        b_zoomout.set_callback(cb_zoom_out)

        # bottons for move the obj
        b_up = Button(tools, "up")
        def cb_up():
            for i in range(len(self.canvas.positions)):
                self.canvas.positions[i][2] += 1
            self.canvas.shader.set_buffer("position", self.canvas.positions)
        b_up.set_callback(cb_up)
        
        b_down = Button(tools, "down")
        def cb_down():
            for i in range(len(self.canvas.positions)):
                self.canvas.positions[i][2] -= 1
            self.canvas.shader.set_buffer("position", self.canvas.positions)
        b_down.set_callback(cb_down)

        self.perform_layout()

    def keyboard_event(self, key, scancode, action, modifiers):
        if super(TestApp, self).keyboard_event(key, scancode,
                                              action, modifiers):
            return True
        if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
            self.set_visible(False)
            return True
        return False

if __name__ == "__main__":
    nanogui.init()
    test = TestApp()
    test.draw_all()
    test.set_visible(True)
    nanogui.mainloop(refresh=1 / 60.0 * 1000)
    del test
    gc.collect()
    nanogui.shutdown()
