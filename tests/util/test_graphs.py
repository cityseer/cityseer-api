import networkx as nx
import numpy as np
import pytest
from shapely import geometry

from cityseer.algos import checks
from cityseer.metrics import networks, layers
from cityseer.util import mock, graphs


def test_nX_simple_geoms():
    G = mock.mock_graph()
    G_geoms = graphs.nX_simple_geoms(G)

    for s, e in G.edges():
        line_geom = geometry.LineString([
            [G.nodes[s]['x'], G.nodes[s]['y']],
            [G.nodes[e]['x'], G.nodes[e]['y']]
        ])
        assert line_geom == G_geoms[s][e]['geom']

    # check that missing node attributes throw an error
    for attr in ['x', 'y']:
        G_wgs = mock.mock_graph(wgs84_coords=True)
        for n in G.nodes():
            # delete attribute from first node and break
            del G.nodes[n][attr]
            break
        # check that missing attribute throws an error
        with pytest.raises(AttributeError):
            graphs.nX_simple_geoms(G)


def test_nX_wgs_to_utm():
    # check that node coordinates are correctly converted
    G_utm = mock.mock_graph()
    G_wgs = mock.mock_graph(wgs84_coords=True)
    G_converted = graphs.nX_wgs_to_utm(G_wgs)
    for n, d in G_utm.nodes(data=True):
        # rounding can be tricky
        assert np.allclose(d['x'], G_converted.nodes[n]['x'])
        assert np.allclose(d['y'], G_converted.nodes[n]['y'])

    # check that edge coordinates are correctly converted
    G_utm = mock.mock_graph()
    G_utm = graphs.nX_simple_geoms(G_utm)

    G_wgs = mock.mock_graph(wgs84_coords=True)
    G_wgs = graphs.nX_simple_geoms(G_wgs)

    G_converted = graphs.nX_wgs_to_utm(G_wgs)
    for s, e, d in G_utm.edges(data=True):
        assert round(d['geom'].length, 1) == round(G_converted[s][e]['geom'].length, 1)

    # check that non-LineString geoms throw an error
    G_wgs = mock.mock_graph(wgs84_coords=True)
    for s, e in G_wgs.edges():
        G_wgs[s][e]['geom'] = geometry.Point([G_wgs.nodes[s]['x'], G_wgs.nodes[s]['y']])
    with pytest.raises(TypeError):
        graphs.nX_wgs_to_utm(G_wgs)

    # check that missing node attributes throw an error
    for attr in ['x', 'y']:
        G_wgs = mock.mock_graph(wgs84_coords=True)
        for n in G_wgs.nodes():
            # delete attribute from first node and break
            del G_wgs.nodes[n][attr]
            break
        # check that missing attribute throws an error
        with pytest.raises(AttributeError):
            graphs.nX_wgs_to_utm(G_wgs)

    # check that non WGS coordinates throw error
    G_utm = mock.mock_graph()
    with pytest.raises(AttributeError):
        graphs.nX_wgs_to_utm(G_utm)


def test_nX_remove_filler_nodes():
    # TODO: add test for self-loops

    # test that redundant (straight) intersections are removed
    G = mock.mock_graph()
    G = graphs.nX_simple_geoms(G)
    G_messy = G.copy()

    # complexify the graph - write changes to new graph to avoid in-place iteration errors
    for i, (s, e, d) in enumerate(G.edges(data=True)):
        # flip each third geom
        if i % 3 == 0:
            flipped_coords = np.fliplr(d['geom'].coords.xy)
            G_messy[s][e]['geom'] = geometry.LineString([[x, y] for x, y in zip(flipped_coords[0], flipped_coords[1])])
        # split each second geom
        if i % 2 == 0:
            line_geom = G[s][e]['geom']
            # check geom coordinates directionality - flip if facing backwards direction
            if not (G.nodes[s]['x'], G.nodes[s]['y']) == line_geom.coords[0][:2]:
                flipped_coords = np.fliplr(line_geom.coords.xy)
                line_geom = geometry.LineString([[x, y] for x, y in zip(flipped_coords[0], flipped_coords[1])])
            # remove old edge
            G_messy.remove_edge(s, e)
            # add new edges
            # TODO: change to ops.substring once shapely 1.7 released (bug fix)
            G_messy.add_edge(s, f'{s}-{e}', geom=graphs.substring(line_geom, 0, 0.5, normalized=True))
            G_messy.add_edge(e, f'{s}-{e}', geom=graphs.substring(line_geom, 0.5, 1, normalized=True))

    # simplify and test
    G_simplified = graphs.nX_remove_filler_nodes(G_messy)
    assert G_simplified.nodes == G.nodes
    assert G_simplified.edges == G.edges
    for s, e, d in G_simplified.edges(data=True):
        assert G_simplified[s][e]['geom'].length == G[s][e]['geom'].length

    # check that missing geoms throw an error
    G_attr = G_messy.copy()
    for i, (s, e) in enumerate(G_attr.edges()):
        if i % 2 == 0:
            del G_attr[s][e]['geom']
    with pytest.raises(AttributeError):
        graphs.nX_remove_filler_nodes(G_attr)

    # check that non-LineString geoms throw an error
    G_attr = G_messy.copy()
    for s, e in G_attr.edges():
        G_attr[s][e]['geom'] = geometry.Point([G_attr.nodes[s]['x'], G_attr.nodes[s]['y']])
    with pytest.raises(AttributeError):
        graphs.nX_remove_filler_nodes(G_attr)

    # catch non-touching Linestrings
    G_corr = G_messy.copy()
    for s, e in G_corr.edges():
        geom = G_corr[s][e]['geom']
        start = list(geom.coords[0])
        end = list(geom.coords[1])
        # corrupt a point
        start[0] = start[0] - 1
        G_corr[s][e]['geom'] = geometry.LineString([start, end])
    with pytest.raises(AttributeError):
        graphs.nX_remove_filler_nodes(G_corr)


def test_nX_decompose():
    # check that missing geoms throw an error
    G = mock.mock_graph()
    with pytest.raises(AttributeError):
        graphs.nX_decompose(G, 20)

    # check that non-LineString geoms throw an error
    G = mock.mock_graph()
    for s, e in G.edges():
        G[s][e]['geom'] = geometry.Point([G.nodes[s]['x'], G.nodes[s]['y']])
    with pytest.raises(TypeError):
        graphs.nX_decompose(G, 20)

    # test decomposition
    G = mock.mock_graph()
    G = graphs.nX_simple_geoms(G)

    G_decompose = graphs.nX_decompose(G, 20)
    assert nx.number_of_nodes(G_decompose) == 632
    assert nx.number_of_edges(G_decompose) == 653

    # check that total lengths and impedances are the same
    G_lens = 0
    G_imp = 0
    G_simple = graphs.nX_auto_edge_params(G)
    for s, e, e_data in G_simple.edges(data=True):
        G_lens += e_data['length']
        G_imp += e_data['impedance']
    G_d_lens = 0
    G_d_imp = 0
    for s, e, e_data in G_decompose.edges(data=True):
        G_d_lens += e_data['length']
        G_d_imp += e_data['impedance']
    assert np.allclose(G_lens, G_d_lens)
    assert np.allclose(G_imp, G_d_imp)

    # check that geoms are correctly flipped
    G_forward = mock.mock_graph()
    G_forward = graphs.nX_simple_geoms(G_forward)
    G_forward_decompose = graphs.nX_decompose(G_forward, 20)

    G_backward = mock.mock_graph()
    G_backward = graphs.nX_simple_geoms(G_backward)
    for i, (s, e, d) in enumerate(G_backward.edges(data=True)):
        # flip each third geom
        if i % 3 == 0:
            flipped_coords = np.fliplr(d['geom'].coords.xy)
            G[s][e]['geom'] = geometry.LineString([[x, y] for x, y in zip(flipped_coords[0], flipped_coords[1])])
    G_backward_decompose = graphs.nX_decompose(G_backward, 20)

    for n, d in G_forward_decompose.nodes(data=True):
        assert d['x'] == G_backward_decompose.nodes[n]['x']
        assert d['y'] == G_backward_decompose.nodes[n]['y']

    # test that geom coordinate mismatch throws an error
    G = mock.mock_graph()
    for attr in ['x', 'y']:
        for n in G.nodes():
            G.nodes[n][attr] = G.nodes[n][attr] + 1
            break
        with pytest.raises(AttributeError):
            graphs.nX_decompose(G, 20)


def test_nX_to_dual():
    # check that missing geoms throw an error
    G = mock.mock_graph()
    with pytest.raises(AttributeError):
        graphs.nX_to_dual(G)

    # check that non-LineString geoms throw an error
    G = mock.mock_graph()
    for s, e in G.edges():
        G[s][e]['geom'] = geometry.Point([G.nodes[s]['x'], G.nodes[s]['y']])
    with pytest.raises(TypeError):
        graphs.nX_to_dual(G)

    # check that missing node attributes throw an error
    for attr in ['x', 'y']:
        G = mock.mock_graph()
        for n in G.nodes():
            # delete attribute from first node and break
            del G.nodes[n][attr]
            break
        # check that missing attribute throws an error
        with pytest.raises(AttributeError):
            graphs.nX_to_dual(G)

    # test dual
    G = mock.mock_graph()
    G = graphs.nX_simple_geoms(G)

    # complexify the geoms to check with and without kinks, and in mixed forward and reverse directions
    for i, (s, e, d) in enumerate(G.edges(data=True)):
        # add a kink to each second geom
        if i % 2 == 0:
            geom = d['geom']
            start = geom.coords[0]
            end = geom.coords[-1]
            # bump the new midpoint coordinates
            mid = list(geom.centroid.coords[0])
            mid[0] += 10
            mid[1] -= 10
            # append 3d coord to check behaviour on 3d data
            for n in [start, mid, end]:
                n = list(n)
                n.append(10)
            G[s][e]['geom'] = geometry.LineString([start, mid, end])
        # flip each third geom
        if i % 3 == 0:
            flipped_coords = np.fliplr(d['geom'].coords.xy)
            G[s][e]['geom'] = geometry.LineString([[x, y] for x, y in zip(flipped_coords[0], flipped_coords[1])])
    G_dual = graphs.nX_to_dual(G)

    # from cityseer.util import plot
    # plot.plot_networkX_primal_or_dual(primal=G, dual=G_dual)

    # dual nodes should equal primal edges
    assert G_dual.number_of_nodes() == G.number_of_edges()
    # all new nodes should have in-out-degrees of 4
    for n in G_dual.nodes():
        if n in ['50_51']:
            assert nx.degree(G_dual, n) == 0
        elif n in ['46_47', '46_48']:
            assert nx.degree(G_dual, n) == 2
        elif n in ['19_22', '22_23', '22_27', '22_46']:
            assert nx.degree(G_dual, n) == 5
        else:
            assert nx.degree(G_dual, n) == 4

    # for debugging
    # plot.plot_networkX_graphs(primal=G, dual=G_dual)


def test_nX_auto_edge_params():
    # check that missing geoms throw an error
    G = mock.mock_graph()
    with pytest.raises(AttributeError):
        graphs.nX_auto_edge_params(G)

    # check that non-LineString geoms throw an error
    G = mock.mock_graph()
    for s, e in G.edges():
        G[s][e]['geom'] = geometry.Point([G.nodes[s]['x'], G.nodes[s]['y']])
    with pytest.raises(TypeError):
        graphs.nX_auto_edge_params(G)

    # test edge defaults
    G = mock.mock_graph()
    G = graphs.nX_simple_geoms(G)
    G_edge_defaults = graphs.nX_auto_edge_params(G)
    for s, e, d in G.edges(data=True):
        assert d['geom'].length == G_edge_defaults[s][e]['length']
        assert d['geom'].length == G_edge_defaults[s][e]['impedance']


def test_nX_m_weighted_nodes():
    # check that missing length attribute throws error
    G = mock.mock_graph()
    with pytest.raises(AttributeError):
        graphs.nX_m_weighted_nodes(G)

    # test length weighted nodes
    G = graphs.nX_simple_geoms(G)
    G = graphs.nX_auto_edge_params(G)
    G = graphs.nX_m_weighted_nodes(G)
    for n, d in G.nodes(data=True):
        agg_length = 0
        for nb in G.neighbors(n):
            agg_length += G[n][nb]['length'] / 2
        assert d['weight'] == agg_length


def test_graph_maps_from_nX():
    # TODO: add test for self-loops?

    # template graph
    G_template = mock.mock_graph()
    G_template = graphs.nX_simple_geoms(G_template)

    # test maps vs. networkX
    G_test = G_template.copy()
    G_test = graphs.nX_auto_edge_params(G_test)
    # set some random 'live' statuses
    for n in G_test.nodes():
        G_test.nodes[n]['live'] = bool(np.random.randint(0, 1))
    # randomise the impedances
    for s, e in G_test.edges():
        G_test[s][e]['impedance'] = G_test[s][e]['impedance'] * np.random.random() * 2000
    # generate length weighted nodes
    G_test = graphs.nX_m_weighted_nodes(G_test)
    # generate test maps
    node_uids, node_map, edge_map = graphs.graph_maps_from_nX(G_test)
    # debug plot
    # plot.plot_graphs(primal=G_test)
    # plot.plot_graph_maps(node_uids, node_map, edge_map)

    # run check
    checks.check_network_maps(node_map, edge_map)
    # check lengths
    assert len(node_uids) == len(node_map) == G_test.number_of_nodes()
    assert len(edge_map) == G_test.number_of_edges() * 2
    # check node maps (idx and label match in this case...)
    for n_label in node_uids:
        assert node_map[n_label][0] == G_test.nodes[n_label]['x']
        assert node_map[n_label][1] == G_test.nodes[n_label]['y']
        assert node_map[n_label][2] == G_test.nodes[n_label]['live']
        assert node_map[n_label][4] == G_test.nodes[n_label]['weight']
    # check edge maps (idx and label match in this case...)
    for start, end, length, impedance in edge_map:
        assert length == G_test[start][end]['length']
        assert impedance == G_test[start][end]['impedance']

    # check that missing node attributes throw an error
    G_test = G_template.copy()
    for attr in ['x', 'y']:
        G_test = graphs.nX_auto_edge_params(G_test)
        for n in G_test.nodes():
            # delete attribute from first node and break
            del G_test.nodes[n][attr]
            break
        with pytest.raises(AttributeError):
            graphs.graph_maps_from_nX(G_test)

    # check that missing edge attributes throw an error
    G_test = G_template.copy()
    for attr in ['length', 'impedance']:
        G_test = graphs.nX_auto_edge_params(G_test)
        for s, e in G_test.edges():
            # delete attribute from first edge and break
            del G_test[s][e][attr]
            break
        with pytest.raises(AttributeError):
            graphs.graph_maps_from_nX(G_test)

    # check that invalid lengths are caught
    G_test = G_template.copy()
    G_test = graphs.nX_auto_edge_params(G_test)
    # corrupt length attribute and break
    for corrupt_val in [0, -1, -np.inf, np.nan]:
        for s, e in G_test.edges():
            G_test[s][e]['length'] = corrupt_val
            break
        with pytest.raises(AttributeError):
            graphs.graph_maps_from_nX(G_test)

    # check that invalid impedances are caught
    G_test = G_template.copy()
    G_test = graphs.nX_auto_edge_params(G_test)
    # corrupt impedance attribute and break
    for corrupt_val in [-1, -np.inf, np.nan]:
        for s, e in G_test.edges():
            G_test[s][e]['length'] = corrupt_val
            break
        with pytest.raises(AttributeError):
            graphs.graph_maps_from_nX(G_test)


def test_nX_from_graph_maps():
    # also see test_networks.test_to_networkX for tests on implementation via Network layer

    # check round trip to and from graph maps results in same graph
    G = mock.mock_graph()
    G = graphs.nX_simple_geoms(G)
    G = graphs.nX_auto_edge_params(G)
    # explicitly set live and weight params for equality checks
    # graph_maps_from_networkX generates these implicitly if missing
    for n in G.nodes():
        G.nodes[n]['live'] = bool(np.random.randint(0, 1))
        G.nodes[n]['weight'] = np.random.random() * 2000

    # test directly from and to graph maps
    node_uids, node_map, edge_map = graphs.graph_maps_from_nX(G)
    G_round_trip = graphs.nX_from_graph_maps(node_uids, node_map, edge_map)
    assert G_round_trip.nodes == G.nodes
    assert G_round_trip.edges == G.edges

    # check with metrics dictionary
    N = networks.Network_Layer_From_nX(G, distances=[500, 1000])
    N.harmonic_closeness()
    data_dict = mock.mock_data_dict(G)
    landuse_labels = mock.mock_categorical_data(len(data_dict))
    D = layers.Data_Layer_From_Dict(data_dict)
    D.assign_to_network(N, max_dist=400)
    D.compute_aggregated(landuse_labels, mixed_use_keys=['hill', 'shannon'], accessibility_keys=['a', 'c'],
                         qs=[0, 1])
    metrics_dict = N.metrics_to_dict()
    # without backbone
    G_round_trip_data = graphs.nX_from_graph_maps(node_uids,
                                                  node_map,
                                                  edge_map,
                                                  metrics_dict=metrics_dict)
    for uid, metrics in metrics_dict.items():
        assert G_round_trip_data.nodes[uid]['metrics'] == metrics
    # with backbone
    G_round_trip_data = graphs.nX_from_graph_maps(node_uids,
                                                  node_map,
                                                  edge_map,
                                                  networkX_graph=G,
                                                  metrics_dict=metrics_dict)
    for uid, metrics in metrics_dict.items():
        assert G_round_trip_data.nodes[uid]['metrics'] == metrics

    # test with decomposed
    G_decomposed = graphs.nX_decompose(G, decompose_max=20)
    # NB -> set live and weight explicitly - otherwise generated implicitly e.g. weight=1
    # which means equality check won't work for nodes
    for n in G_decomposed.nodes():
        G_decomposed.nodes[n]['live'] = bool(np.random.randint(0, 1))
        G_decomposed.nodes[n]['weight'] = np.random.random() * 2000

    node_uids_d, node_map_d, edge_map_d = graphs.graph_maps_from_nX(G_decomposed)

    G_round_trip_d = graphs.nX_from_graph_maps(node_uids_d, node_map_d, edge_map_d)
    assert G_round_trip_d.nodes == G_decomposed.nodes
    assert G_round_trip_d.edges == G_decomposed.edges

    # error checks for when using backbone graph:
    # mismatching numbers of nodes
    corrupt_G = G.copy()
    corrupt_G.remove_node(0)
    with pytest.raises(ValueError):
        graphs.nX_from_graph_maps(node_uids, node_map, edge_map, networkX_graph=corrupt_G)
    # mismatching node uid
    with pytest.raises(AttributeError):
        corrupt_node_uids = list(node_uids)
        corrupt_node_uids[0] = 'boo'
        graphs.nX_from_graph_maps(corrupt_node_uids, node_map, edge_map, networkX_graph=G)
