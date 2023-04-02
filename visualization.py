import numpy as np
from stl import mesh  # pip install numpy-stl
import plotly.graph_objs as go
from plotly.offline import plot


def stl2mesh3d(stl_mesh):
    # stl_mesh is read by nympy-stl from a stl file; it is  an array of faces/triangles (i.e. three 3d points)
    # this function extracts the unique vertices and the lists I, J, K to define a Plotly mesh3d
    p, q, r = stl_mesh.vectors.shape #(p, 3, 3)
    # the array stl_mesh.vectors.reshape(p*q, r) can contain multiple copies of the same vertex;
    # extract unique vertices from all mesh triangles
    vertices, ixr = np.unique(stl_mesh.vectors.reshape(p*q, r), return_inverse=True, axis=0)
    I = np.take(ixr, [3*k for k in range(p)])
    J = np.take(ixr, [3*k+1 for k in range(p)])
    K = np.take(ixr, [3*k+2 for k in range(p)])
    return vertices, I, J, K


def visualize_model(model_url):

    my_mesh = mesh.Mesh.from_file('./models/' + model_url)

    volume, cog, inertia = my_mesh.get_mass_properties()

    volume /= 1000

    vertices, I, J, K = stl2mesh3d(my_mesh)
    x, y, z = vertices.T

    colorscale = [[0, '#e5dee5'], [1, '#e5dee5']]

    mesh3D = go.Mesh3d(x=x,
                       y=y,
                       z=z,
                       i=I,
                       j=J,
                       k=K,
                       flatshading=True,
                       colorscale=colorscale,
                       intensity=z,
                       showscale=False)

    layout = go.Layout(paper_bgcolor='rgba(0,0,0,0)',
                       plot_bgcolor='rgba(0,0,0,0)',
                       autosize=True,
                       scene_xaxis_visible=False,
                       scene_yaxis_visible=False,
                       scene_zaxis_visible=False)

    fig = go.Figure(data=[mesh3D], layout=layout)

    fig.data[0].update(lighting=dict(ambient=0.18,
                                     diffuse=1,
                                     fresnel=.1,
                                     specular=1,
                                     roughness=.1,
                                     facenormalsepsilon=0))
    fig.data[0].update(lightposition=dict(x=3000,
                                          y=3000,
                                          z=10000))

    img_location = f'./images/{"".join(model_url.split(".")[:-1])}.png'
    fig.write_image(img_location)

    # Show the plot to the screen
    return img_location, volume
