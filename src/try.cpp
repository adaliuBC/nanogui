/*
    src/example4.cpp -- C++ version of an example application that shows
    how to use the OpenGL widget. For a Python implementation, see
    '../python/example4.py'.

    NanoGUI was developed by Wenzel Jakob <wenzel.jakob@epfl.ch>.
    The widget drawing code is based on the NanoVG demo application
    by Mikko Mononen.

    All rights reserved. Use of this source code is governed by a
    BSD-style license that can be found in the LICENSE.txt file.
*/

#include <nanogui/screen.h>
#include <nanogui/layout.h>
#include <nanogui/window.h>
#include <nanogui/button.h>
#include <nanogui/canvas.h>
#include <nanogui/shader.h>
#include <nanogui/renderpass.h>
#include <GLFW/glfw3.h>
#include <iostream>

#if defined(_WIN32)
#  if defined(APIENTRY)
#    undef APIENTRY
#  endif
#  include <windows.h>
#endif

using nanogui::Vector3f;
using nanogui::Vector2i;
using nanogui::Shader;
using nanogui::Canvas;
using nanogui::ref;

constexpr float Pi = 3.14159f;

class MyCanvas : public Canvas {
public:
    MyCanvas(Widget* parent) : Canvas(parent, 1), m_rotation(0.f) {
        using namespace nanogui;

        model_shader = new Shader(
            render_pass(),

            // An identifying name
            "model_shader",

            // Vertex shader
            R"(
            #version 330
            uniform mat4 mvp;
            in vec3 position;
            in vec3 color;

            out vec4 frag_color;
            void main() {
                frag_color = vec4(color, 1.0);
                gl_Position = mvp * vec4(position, 1.0);
            }
            )",

            // Fragment shader
            R"(
            #version 330
            out vec4 model_color;
            in vec4 frag_color;
            uniform vec4 light_color;

            void main() {
                // ambient
                float ambient_light = 0.1;
                vec4 ambient = ambient_light * light_color;

                model_color = (ambient) * frag_color;
            }
            )"
        );

        light_shader = new Shader(
            render_pass(),
            // name
            "light_shader",

            // Vertex shader
            R"(
            #version 330
            uniform mat4 mvp;
            in vec3 position;
            void main() {
                gl_Position = mvp * vec4(position, 1.0);
            }
            )",

            // Fragment shader
            R"(
            #version 330
            out vec4 light_cube_color;
            void main() {
                light_cube_color = vec4(1.0);
            }
            )"
        );


        uint32_t indices[3 * 12] = {
            3, 2, 6, 6, 7, 3,
            4, 5, 1, 1, 0, 4,
            4, 0, 3, 3, 7, 4,
            1, 5, 6, 6, 2, 1,
            0, 1, 2, 2, 3, 0,
            7, 6, 5, 5, 4, 7
        };  // 6个面，每个面由两个三角形组成，共12个三角形。
        // 每三个连续值定义一个三角形。

        float positions[3 * 8] = {
            -1.f, 1.f, 1.f,
            -1.f, -1.f, 1.f,
            1.f, -1.f, 1.f,
            1.f, 1.f, 1.f,
            -1.f, 1.f, -1.f,
            -1.f, -1.f, -1.f,
            1.f, -1.f, -1.f,
            1.f, 1.f, -1.f
        };
        // 每三个连续值定义一个顶点的(x, y, z)，立方体一共八个点

        float colors[3 * 8] = {
            0, 1, 1, 0, 0, 1,
            1, 0, 1, 1, 1, 1,
            0, 1, 0, 0, 0, 0,
            1, 0, 0, 1, 1, 0
        };   // 每三个连续值定义一个顶点的 color (r, g, b)，立方体一共八个点
        
        // color of light : all white now
        Vector4f light_color = { 1.f, 1.f, 1.f, 1.f };

        // normal
        /*float normal[3 * 6] = {
            1.f,  0.f,  0.f,
            -1.f, 0.f,  0.f,
            0.f,  1.f,  0.f,
            0.f,  -1.f, 0.f,
            0.f,  0.f,  1.f,
            0.f,  0.f,  -1.f
        };*/

        model_shader->set_buffer("indices", VariableType::UInt32, { 3 * 12 }, indices);
        model_shader->set_buffer("position", VariableType::Float32, { 8, 3 }, positions);
        model_shader->set_buffer("color", VariableType::Float32, { 8, 3 }, colors);
        model_shader->set_uniform("light_color", light_color);
        //model_shader->set_buffer("normal", VariableType::Float32, { 6, 3 }, normal);
        
        float positions_light[3 * 8] = {
            1.5f, 2.f,  2.f, 
            1.5f, 1.5f, 2.f,
            2.f,  1.5f, 2.f, 
            2.f,  2.f,  2.f,
            1.5f, 2.f,  1.5f, 
            1.5f, 1.5f, 1.5f,
            2.f,  1.5f, 1.5f, 
            2.f,  2.f,  1.5f
        };

        light_shader->set_buffer("indices", VariableType::UInt32, { 3 * 12 }, indices);
        light_shader->set_buffer("position", VariableType::Float32, { 8, 3 }, positions_light);
    }

    void set_rotation(float rotation) {
        m_rotation = rotation;
    }

    virtual void draw_contents() override {
        using namespace nanogui;

        Matrix4f view = Matrix4f::look_at(
            Vector3f(0, -2, -10),  // origin
            Vector3f(0, 0, 0),     // target
            Vector3f(0, 1, 0)      // up dir
        );

        Matrix4f model = Matrix4f::rotate(
            Vector3f(0, 1, 0),    // axis
            20.0f //(float)glfwGetTime()  // angle
        );

        Matrix4f model2 = Matrix4f::rotate(
            Vector3f(1, 0, 0),
            m_rotation
        );

        Matrix4f proj = Matrix4f::perspective(
            float(25 * Pi / 180),     // fov
            0.1f,                     // near
            20.f,                     // far
            m_size.x() / (float)m_size.y()  // aspect
        );

        Matrix4f mvp = proj * view * model * model2;

        model_shader->set_uniform("mvp", mvp);

        light_shader->set_uniform("mvp", mvp);

        // Draw 12 triangles starting at index 0
        model_shader->begin();
        model_shader->draw_array(Shader::PrimitiveType::Triangle, 0, 12 * 3, true);
        // type, offset, count, render index geometry?
        model_shader->end();

        light_shader->begin();
        light_shader->draw_array(Shader::PrimitiveType::Triangle, 0, 12 * 3, true);
        // type, offset, count, render index geometry?
        light_shader->end();
    }

private:
    ref<Shader> model_shader;
    ref<Shader> light_shader;
    float m_rotation;
};

class ExampleApplication : public nanogui::Screen {
public:
    ExampleApplication() : nanogui::Screen(Vector2i(800, 600), "NanoGUI Test", false) {
        using namespace nanogui;

        Window* window = new Window(this, "Canvas widget demo");
        window->set_position(Vector2i(15, 15));
        window->set_layout(new GroupLayout());

        m_canvas = new MyCanvas(window);
        m_canvas->set_background_color({ 100, 100, 100, 255 });
        m_canvas->set_fixed_size({ 400, 400 });

        Widget* tools = new Widget(window);
        tools->set_layout(new BoxLayout(Orientation::Horizontal,
            Alignment::Middle, 0, 5));

        Button* b0 = new Button(tools, "Random Background");
        b0->set_callback([this]() {
            m_canvas->set_background_color(
                Vector4i(rand() % 256, rand() % 256, rand() % 256, 255));
            });

        Button* b1 = new Button(tools, "Random Rotation");
        b1->set_callback([this]() {
            m_canvas->set_rotation((float)Pi * rand() / (float)RAND_MAX);
            });

        perform_layout();
    }

    virtual bool keyboard_event(int key, int scancode, int action, int modifiers) {
        if (Screen::keyboard_event(key, scancode, action, modifiers))
            return true;
        if (key == GLFW_KEY_ESCAPE && action == GLFW_PRESS) {
            set_visible(false);
            return true;
        }
        return false;
    }

    virtual void draw(NVGcontext* ctx) {
        // Draw the user interface
        Screen::draw(ctx);
    }
private:
    MyCanvas* m_canvas;
};

int main(int /* argc */, char** /* argv */) {
    try {
        nanogui::init();

        /* scoped variables */ {
            nanogui::ref<ExampleApplication> app = new ExampleApplication();
            app->draw_all();
            app->set_visible(true);
            nanogui::mainloop(1 / 60.f * 1000);
        }

        nanogui::shutdown();
    }
    catch (const std::runtime_error& e) {
        std::string error_msg = std::string("Caught a fatal error: ") + std::string(e.what());
#if defined(_WIN32)
        MessageBoxA(nullptr, error_msg.c_str(), NULL, MB_ICONERROR | MB_OK);
#else
        std::cerr << error_msg << std::endl;
#endif
        return -1;
    }

    return 0;
}
