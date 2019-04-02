from os import path

import matplotlib.pyplot as plt
from matplotlib import colors
import numpy as np

from cityseer.metrics import networks, layers
from cityseer.util import mock, graphs, plot

plt.style.use('./matplotlibrc')

base_path = path.dirname(__file__)

#
#
# INTRO PLOT
G = mock.mock_graph()
plot.plot_nX(G, path='graph.png', labels=True, dpi=150)

# INTRO EXAMPLE PLOTS
G = graphs.nX_simple_geoms(G)
G = graphs.nX_decompose(G, 20)

N = networks.Network_Layer_From_nX(G, distances=[400])
N.gravity()

data_dict = mock.mock_data_dict(G, random_seed=25)
D = layers.Data_Layer_From_Dict(data_dict)
D.assign_to_network(N, max_dist=400)
landuse_labels = mock.mock_categorical_data(len(data_dict), random_seed=25)
D.hill_branch_wt_diversity(landuse_labels, qs=[0])
G_metrics = N.to_networkX()

gravity_vals = []
mixed_uses_vals = []
for node, data in G_metrics.nodes(data=True):
    gravity_vals.append(data['metrics']['centrality']['gravity'][400])
    mixed_uses_vals.append(data['metrics']['mixed_uses']['hill_branch_wt'][0][400])

# custom colourmap
cmap = colors.LinearSegmentedColormap.from_list('cityseer', ['#64c1ff', '#d32f2f'])
gravity_vals = colors.Normalize()(gravity_vals)
gravity_cols = cmap(gravity_vals)
plt.cla()
plt.clf()
plot.plot_nX(G_metrics, path='intro_gravity.png', labels=False, colour=gravity_cols, dpi=150)

# plot hill mixed uses
mixed_uses_vals = colors.Normalize()(mixed_uses_vals)
mixed_uses_cols = cmap(mixed_uses_vals)
plt.cla()
plt.clf()
plot.plot_assignment(N, D, path='intro_mixed_uses.png', node_colour=mixed_uses_cols, data_labels=landuse_labels)

#
#
# MOCK MODULE
plt.cla()
plt.clf()
G = mock.mock_graph()
G = graphs.nX_simple_geoms(G)
plot.plot_nX(G, path='graph_example.png', labels=True, dpi=150)  # WITH LABELS

#
#
# GRAPH MODULE
plt.cla()
plt.clf()
plot.plot_nX(G, path='graph_simple.png', labels=False, dpi=150)  # NO LABELS

G_simple = graphs.nX_simple_geoms(G)
G_decomposed = graphs.nX_decompose(G_simple, 100)

plt.cla()
plt.clf()
plot.plot_nX(G_decomposed, path='graph_decomposed.png', labels=False, dpi=150)

plt.cla()
plt.clf()
G_dual = graphs.nX_to_dual(G_simple)
plot.plot_nX_primal_or_dual(G_simple, G_dual, 'graph_dual.png', labels=False, dpi=150)

#
#
# NETWORKS MODULE
# before and after plots
# prepare a mock graph
G = mock.mock_graph()
G = graphs.nX_simple_geoms(G)
G = graphs.nX_auto_edge_params(G)

plt.cla()
plt.clf()
plot.plot_nX(G, path='graph_before.png', labels=True, dpi=150)

# generate the network layer and compute some metrics
N = networks.Network_Layer_From_nX(G, distances=[200, 400, 800, 1600])
# compute some-or-other metrics
N.harmonic_closeness()
# convert back to networkX
G_post = N.to_networkX()

plt.cla()
plt.clf()
plot.plot_nX(G_post, path='graph_after.png', labels=True, dpi=150)

#
#
# LAYERS MODULE
# show assignment to network
# random seed 25
G = mock.mock_graph()
G = graphs.nX_simple_geoms(G)
G = graphs.nX_auto_edge_params(G)
N = networks.Network_Layer_From_nX(G, distances=[200, 400, 800, 1600])

data_dict = mock.mock_data_dict(G, random_seed=25)
L = layers.Data_Layer_From_Dict(data_dict)
L.assign_to_network(N, max_dist=500)

plt.cla()
plt.clf()
plot.plot_assignment(N, L, path='assignment.png')

G_decomposed = graphs.nX_decompose(G, 50)
N_decomposed = networks.Network_Layer_From_nX(G_decomposed, distances=[200, 400, 800, 1600])

L = layers.Data_Layer_From_Dict(data_dict)
L.assign_to_network(N_decomposed, max_dist=500)

plt.cla()
plt.clf()
plot.plot_assignment(N_decomposed, L, path='assignment_decomposed.png')

#
#
# PLOT MODULE
# generate a graph and compute gravity
G = mock.mock_graph()
G = graphs.nX_simple_geoms(G)
G = graphs.nX_decompose(G, 50)
N = networks.Network_Layer_From_nX(G, distances=[800])
N.gravity()
G_after = N.to_networkX()

# let's extract and normalise the values
vals = []
for node, data in G_after.nodes(data=True):
    vals.append(data['metrics']['centrality']['gravity'][800])

cmap = colors.LinearSegmentedColormap.from_list('cityseer', ['#64c1ff', '#d32f2f'])
vals = colors.Normalize()(vals)
cols = cmap(vals)

# plot
plt.cla()
plt.clf()
plot.plot_nX(G_after, path='graph_colour.png', labels=False, colour=cols, dpi=150)

# assignment plot
data_dict = mock.mock_data_dict(G, random_seed=25)
D = layers.Data_Layer_From_Dict(data_dict)
D.assign_to_network(N, max_dist=400)
landuse_labels = mock.mock_categorical_data(len(data_dict), random_seed=25)

plt.cla()
plt.clf()
plot.plot_assignment(N, D, path='assignment_plot.png', data_labels=landuse_labels)

#
#
# BETA DECAYS
plt.cla()
plt.clf()
fig, ax = plt.subplots(1, 1, figsize=(5, 2.5))

w_min = 0.01831563888873418
# set the betas
betas = []
for d_max in [200, 400, 800, 1600]:
    beta = np.log(w_min) / d_max
    distances_arr = []
    for d in range(0, d_max + 1):
        distances_arr.append(d)
    distances_arr = np.array(distances_arr)
    y_falloff = np.exp(beta * distances_arr)
    ax.plot(distances_arr, y_falloff, label=f'$-\\beta={round(beta, 4)}$')

# add w_min
plt.axhline(y=w_min, color='#eeeeee', ls='--', lw=0.5)
ax.text(10, 0.035, '$w_{min}$', color='#eeeeee')

ax.set_xticks([200, 400, 800, 1600])
ax.set_xticklabels(['$d_{max}=200$', '$d_{max}=400$', '$d_{max}=800$', '$d_{max}=1600$'])
ax.set_xlim([0, 1600])
ax.set_xlabel('Distance in Metres')
ax.set_ylim([0, 1.0])
ax.set_ylabel('Weighting')
ax.legend(loc='upper right', title='$exp(-\\beta \\cdot d[i,j])$')
plt.savefig('betas.png', dpi=150)
