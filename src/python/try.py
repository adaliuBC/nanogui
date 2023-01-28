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
                    frag_color = vec4(color, 1.0);
                    mat4 mvp = projection_mat * view_mat * model_mat; 
                    gl_Position = mvp * vec4(position, 1.0);
                    frag_position = position;
                    frag_normal = normal;
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
                    float ambient = 0.3;
                    
                    // diffuse
                    float kd = 5.0;
                    float distance = length(light_position - frag_position);
                    vec3 light_dir = normalize(light_position - frag_position);
                    vec3 norm = normalize(frag_normal);
                    float energy_diffuse = max(dot(norm, light_dir), 0.0);
                    float diffuse = kd * light_intensity / (distance * distance) * energy_diffuse;

                    //specular
                    float ks = 3.0;
                    vec3 view_dir = normalize(view_position - frag_position);
                    vec3 h = (view_dir + light_dir) / length(view_dir + light_dir);
                    float p = 32;
                    float energy_specular = pow( max(dot(norm, h), 0.0), p);
                    float specular = ks * energy_specular;

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


            # Draw a cube
            indices = np.array(
                [3, 2, 6, 6, 7, 3,
                 4, 5, 1, 1, 0, 4,
                 4, 0, 3, 3, 7, 4,
                 1, 5, 6, 6, 2, 1,
                 0, 1, 2, 2, 3, 0,
                 7, 6, 5, 5, 4, 7],
                dtype=np.uint32)

            positions = np.array(
                [[-1, 1, 1], [-1, -1, 1],
                 [1, -1, 1], [1, 1, 1],
                 [-1, 1, -1], [-1, -1, -1],
                 [1, -1, -1], [1, 1, -1]],
                dtype=np.float32)

            normals = np.array(
                [[-1, 1, 1], [-1, -1, 1],
                 [1, -1, 1], [1, 1, 1],
                 [-1, 1, -1], [-1, -1, -1],
                 [1, -1, -1], [1, 1, -1]],
                dtype=np.float32)

            colors = np.array(
                [[0, 1, 1], [0, 0, 1],
                 [1, 0, 1], [1, 1, 1],
                 [0, 1, 0], [0, 0, 0],
                 [1, 0, 0], [1, 1, 0]],
                dtype=np.float32)
                
            light_color = np.array([1, 1, 1, 1], dtype=np.float32)
            
            light_position = np.array([0, 0., 5], dtype = np.float32)
            light_intensity = np.array(1, dtype = np.float32)
            view_position = np.array([0, 0, 3], dtype = np.float32)
            self.shader.set_buffer("indices", indices)
            self.shader.set_buffer("position", positions)
            self.shader.set_buffer("color", colors)
            self.shader.set_buffer("light_color", light_color)
            self.shader.set_buffer("light_position", light_position)
            self.shader.set_buffer("light_intensity", light_intensity)
            self.shader.set_buffer("normal", normals)
            self.shader.set_buffer("view_position", view_position)
            
            self.rotation = 0
        except ImportError:
            self.shader = None
            pass

    def draw_contents(self):
        if self.shader is None:
            return
        import numpy as np

        view = Matrix4f.look_at(
            origin=[0, -2, -10],
            target=[0, 0, 0],
            up=[0, 1, 0]
        )

        model = Matrix4f.rotate(
            [0, 1, 0],
            glfw.getTime()
        )

        model2 = Matrix4f.rotate(
            [1, 0, 0],
            self.rotation
        )

        size = self.size()
        proj = Matrix4f.perspective(
            fov=25 * np.pi / 180,
            near=0.1,
            far=20,
            aspect=size[0] / float(size[1])
        )

        mvp = proj @ view @ model @ model2

        self.shader.set_buffer("model_mat", (model @ model2).T)
        self.shader.set_buffer("view_mat", view.T)
        self.shader.set_buffer("projection_mat", proj.T)
        with self.shader:
            self.shader.draw_array(Shader.PrimitiveType.Triangle,
                                   0, 36, indexed=True)


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

        b1 = Button(tools, "Random Rotation")
        def cb1():
            self.canvas.rotation = random.random() * math.pi
        b1.set_callback(cb1)

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
