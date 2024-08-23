# represent a dict
import csv
import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx

from .config import Config


def prep_dict(input_dict):
    changes_needed = {}
    # get ONLY THE FIRST key and value
    key, value = next(iter(input_dict.items()))
    key_change = ""
    value_change = ""
    if isinstance(key, frozenset):
        key_change = "str"
    if isinstance(value, set):
        value_change = "list"
    if isinstance(value, dict):
        value_change = prep_dict(value)
    changes_needed[key_change] = value_change
    return changes_needed


def change_dict(input_dict, changes_needed):
    for key, value in changes_needed.items():
        if key == "str" and value == "list":
            input_dict = {str(key): list(value) for key, value in input_dict.items()}
        elif key == "str":
            input_dict = {str(key): value for key, value in input_dict.items()}
        elif value == "list":
            input_dict = {key: list(value) for key, value in input_dict.items()}
        elif key == "str" and value == "dict":
            input_dict = {
                str(key): change_dict(value, changes_needed["str"])
                for key, value in input_dict.items()
            }
        elif value == "dict":
            input_dict = {
                key: change_dict(value, changes_needed[""])
                for key, value in input_dict.items()
            }
    return input_dict


def process_list(config: Config, input_list: list, filename="some_list", path=None):
    if path is None:
        path = config.get_output_path()
    filepath = os.path.join(path, filename)
    with open(filepath + ".txt", "w", encoding="utf-8") as f:
        for item in input_list:
            f.write(f"{item}\n")


def process_dict(config: Config, input_dict: dict, filename="some_dict", path=None):
    # convert all sets to lists
    changes_needed = prep_dict(input_dict)
    processed_dict = change_dict(input_dict, changes_needed)

    if path is None:
        path = config.get_output_path()
    filepath = os.path.join(path, filename)
    with open(filepath + ".json", "w", encoding="utf-8") as f:
        json.dump(processed_dict, f, ensure_ascii=False, indent=4)

    # TODO: Only do this for dicts that need statistical analysis
    requires_analysis = False
    value = list(processed_dict.values())[
        0
    ]  # Convert dict_values to list to make it subscriptable
    if isinstance(value, dict):
        value = list(value.values())[
            0
        ]  # Convert dict_values to list to make it subscriptable
        if isinstance(value, int) or isinstance(value, float):
            requires_analysis = True
    if not requires_analysis:
        return

    container = [["Instance", "Min", "Max", "Mean", "Median", "Std"]]

    for instance, papers in input_dict.items():

        # print(f"Instance: {instance}")
        gaps = papers.values()
        # generate all kinds of statistical values
        min_gap = min(gaps)
        max_gap = max(gaps)
        mean_gap = sum(gaps) / len(gaps)
        median_gap = np.median(list(gaps))
        std_gap = np.std(list(gaps))
        container.append([instance, min_gap, max_gap, mean_gap, median_gap, std_gap])

    filepath = os.path.join(path, filename)

    # TODO: Handle CSV separator
    # if not for_git:
    # Function to convert a single value
    # def convert_decimal_delimiter(value, decimal=CSV_DECIMAL):
    #     if isinstance(value, float):
    #         return f"{value}".replace('.', decimal)
    #     return value

    # # Convert all floats in your container to strings with the desired decimal delimiter
    # container = [[convert_decimal_delimiter(value) for value in row] for row in container]

    # write to csv
    with open(filepath + ".csv", "w", newline="") as file:
        writer = csv.writer(file, delimiter=config.csv_separator)
        writer.writerows(container)


def process_dataframe(config: Config, input_df, name="some_df", path=None):
    if path is None:
        path = config.get_output_path()
    filepath = os.path.join(path, name)

    # convert all froensets to strings
    for col in input_df.columns:
        # input_df[col] = input_df[col].apply(lambda x: "_".join(x))
        first_element_type = input_df[col].apply(type).iloc[0]
        if first_element_type == frozenset:
            input_df[col] = input_df[col].apply(lambda x: " ".join(x))

    input_df.to_csv(
        filepath + ".csv", sep=config.csv_separator, decimal=config.csv_decimal
    )
    try:
        show(input_df)
    except:
        return input_df


def matrix_to_csv(
    config: Config, matrix: pd.DataFrame, name: str = "some_matrix", path=None
) -> None:
    if path is None:
        path = config.get_output_path()
    filepath = os.path.join(path, name)
    matrix.to_csv(
        filepath + ".csv",
        sep=config.csv_separator,
        decimal=config.csv_decimal,
    )


def get_figsize(
    config: Config,
    sizex: float = None,
    sizey: float = None,
    columns: int = None,
    rows: int = None,
) -> tuple[float, float]:
    if size_x and size_y:
        return size_x, size_y
    ## Calculate the maximum size of the plot
    dpi = 300
    max_dpi = 600
    if config.for_git:
        dpi = 96
        max_dpi = 200
    max_pixel = 2**16  # Maximum size in any direction
    max_size = max_pixel / dpi  # Maximum size in any direction
    max_size_total = max_size * max_size  # Maximum size in total
    max_size_total *= 0.05  # produce smaller files

    # Experience value of space required per cell
    factor = 0.18
    size_x: float = 2 + len(columns) * factor
    size_y: float = 3 + len(rows) * 0.8 * factor

    while size_x * size_y < max_size_total and dpi < max_dpi:
        dpi /= 0.95
        max_size_total *= 0.95

    if dpi > max_dpi:
        dpi = max_dpi

    while size_x * size_y > max_size_total:
        dpi *= 0.95
        max_size_total /= 0.95

    size_x = size_x
    size_y = size_y
    dpi = dpi

    return size_x, size_y


def visualize_matrix(
    config: Config,
    matrix: pd.DataFrame,
    name: str = "some_matrix",
    format=".png",
    path=None,
) -> None:
    rows = matrix.index
    columns = matrix.columns
    fig, ax = plt.subplots(figsize=get_figsize(config), dpi=dpi)

    cax = ax.matshow(matrix, cmap="viridis")

    # use labels from instance_occurrences
    ax.set_xticks(range(len(columns)))
    ax.set_xticklabels(list(columns), fontsize=10, rotation=90)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(list(rows), fontsize=10)

    # # adjust the spacing between the labels
    # plt.gca().tick_params(axis='x', which='major', pad=15)
    # plt.gca().tick_params(axis='y', which='major', pad=15)

    # show the number of co-occurrences in each cell, if greater than 0
    for i in range(len(matrix)):
        for j in range(len(matrix[i])):
            if matrix[i, j] == 0:
                continue
            # if co_occurrences[i, j] > 100:
            #     continue

            # make sure the text is at most 3 digits and a dot
            decimals = 2
            if matrix[i, j] > 99:
                decimals = 0
            elif matrix[i, j] > 9:
                decimals = 1
            cell_text = round(matrix[i, j], decimals)
            if decimals == 0:
                cell_text = int(cell_text)
            plt.text(
                j, i, cell_text, ha="center", va="center", color="white", fontsize=4
            )

    # plt.show()
    fig.tight_layout()

    # title
    plt.title(name)

    if isinstance(format, list):
        for f in format:
            if f[0] != ".":
                f = "." + f
            filepath = os.path.join(path, name + f)
            fig.savefig(filepath)
    else:
        if format[0] != ".":
            format = "." + format
        filepath = os.path.join(config.visualization_path, name + format)
        fig.savefig(filepath)


def visualize_matrix_graph(
    config: Config,
    matrix,
    instances,
    # instance_types_dicts,
    name="some_matrix_graph",
    path=None,
    node_size_mode="sqrt",
    raise_mode="prune",
):
    if not instances:
        return

    SEED = config.proximity_seed or 17
    K_SPRRING = config.proximity_k_spring or 18
    MIN_VALUE = config.proximity_min_value or 0.01

    scale = len(instances) * 0.12
    # Create a new figure
    x = scale / 10 * 16
    y = scale / 10 * 9
    fig = plt.figure(figsize=(x, y))

    # normalize the proximity matrix
    matrix = matrix / matrix.max()

    # Make sure the matrix is not completely stretched out
    if matrix.min() < MIN_VALUE:
        if raise_mode == "prune":
            # remove every value that is below MIN_VALUE
            # matrix = np.where(matrix < MIN_VALUE, 0, matrix)
            matrix = matrix.applymap(lambda x: 0 if x < MIN_VALUE else x)

        elif raise_mode == "sqrt":
            while matrix[matrix > 0].min().min() < MIN_VALUE:
            # while np.min(matrix[np.nonzero(matrix)]) < MIN_VALUE:
                matrix = np.sqrt(matrix)
                matrix = matrix.applymap(np.sqrt)

        else:
            raise ValueError("Unknown raise mode")

    # alternatives are:
    # "linear" - take proximity as is
    # "sqrt" - sqrt(proximity)
    # "log" - log(proximity)
    if node_size_mode == "log":
        # TODO: see how this works with log(1)
        nodesize_map = [np.log(matrix[:, i].sum() + 1) for i in range(len(instances))]
    elif node_size_mode == "sqrt":
        nodesize_map = [np.sqrt(matrix[:, i].sum()) for i in range(len(instances))]
    elif node_size_mode == "linear":
        nodesize_map = [matrix[:, i].sum() for i in range(len(instances))]
    else:
        nodesize_map = [matrix[:, i].sum() for i in range(len(instances))]

    # print(max(nodesize_map))
    # print(min(nodesize_map))

    nodesize_map = np.array(nodesize_map) / max(nodesize_map) * 1000

    # print(max(nodesize_map))
    # print(min(nodesize_map))

    # Create a graph from the proximity matrix
    G = nx.from_numpy_array(matrix)

    # Specify the layout
    pos = nx.spring_layout(
        G, seed=SEED, k=K_SPRRING / math.sqrt(G.order())
    )  # Seed for reproducibility

    color_map = []

    color = {
        "process": "#1f77b4",  # muted blue
        "software": "#ff7f0e",  # safety orange
        "data item": "#2ca02c",  # cooked asparagus green
        "data model": "#d62728",  # brick red
        "data format specification": "#9467bd",  # muted purple
        # "interchange format": "#8c564b",  # chestnut brown
        # "source": "#e377c2",  # raspberry yogurt pink
    }

    for instance in instances:
        added = False
        for instance_type in instance_types_dicts:
            if instance in instance_types_dicts[instance_type]:
                color_map.append(color[instance_type])
                added = True
                break
        if not added:
            color_map.append("grey")

    # Draw the graph
    options = {
        "edge_color": "grey",
        "linewidths": 0.5,
        "width": 0.5,
        "with_labels": True,  # This will add labels to the nodes
        "labels": {i: label for i, label in enumerate(instances)},
        "node_color": color_map,
        "node_size": nodesize_map,
        # "edge_color": "white",
        # "alpha": 0.9,
    }

    # print(nx.is_weighted(G))

    # nx.set_edge_attributes(G, values = 1, name = 'weight')

    nx.draw(G, pos, **options, ax=fig.add_subplot(111))

    # Make the graph more spacious
    fig.subplots_adjust(bottom=0.1, top=0.9, left=0.1, right=0.9)

    # Create a patch for each color
    patches = [mpatches.Patch(color=color[key], label=key) for key in color]

    # Add the legend to the graph
    plt.legend(handles=patches, loc="upper right", fontsize="x-large")

    plt.show()

    # save plot to file
    filepath = os.path.join(path, name)
    fig.savefig(filepath + ".png")
    fig.savefig(filepath + ".svg")

    # nx.get_edge_attributes(G, 'weight')


def matrix_to_sankey(
    config: Config,
    matrix,
    instances,
    instance_types_dicts,
    name="some_sankey",
    path=None,
):
    # TODO: Implement a method to create one graph per Process
    # if path is None:
    #     path = config.get_output_path(path, visualization=True)
    # Convert the proximity matrix into a list of source nodes, target nodes, and values
    sources = []
    targets = []
    values = []

    x_pos = [0] * len(instances)
    y_pos = [0] * len(instances)
    color_map = [0] * len(instances)

    max_types = len(instance_types_dicts)
    type_positions = [0.1 + (i / max_types) * 0.8 for i in range(max_types)]

    color = {
        "process": "#1f77b4",  # muted blue
        "software": "#ff7f0e",  # safety orange
        "data item": "#2ca02c",  # cooked asparagus green
        "data model": "#d62728",  # brick red
        "data format specification": "#9467bd",  # muted purple
        "interchange format": "#8c564b",  # chestnut brown
        # "source": "#e377c2",  # raspberry yogurt pink
    }
    color = list(color.values())

    space = {}

    for i in range(matrix.shape[0]):
        source_type = None

        for j in range(matrix.shape[1]):
            target_type = None

            for type_depth, type in enumerate(instance_types_dicts):
                if instances[i] in instance_types_dicts[type]:
                    source_type = type_depth
                if instances[j] in instance_types_dicts[type]:
                    target_type = type_depth

            # only keep directly forward moving connections
            if target_type - source_type != 1:
                continue

            # only keep forward moving connections
            if target_type - source_type <= 0:
                continue

            if source_type not in space:
                space[source_type] = {}
            if i not in space[source_type]:
                space[source_type][i] = 0
            space[source_type][i] += matrix[i][j]

            if target_type not in space:
                space[target_type] = {}
            if j not in space[target_type]:
                space[target_type][j] = 0
            space[target_type][j] += matrix[i][j]

            x_pos[i] = type_positions[source_type]
            x_pos[j] = type_positions[target_type]
            color_map[i] = color[source_type]
            color_map[j] = color[target_type]
            if matrix[i][j] > 0.0:  # Ignore zero values
                sources.append(i)
                targets.append(j)
                values.append(matrix[i][j])

    for type in space:
        sum_values = sum(space[type].values())
        space[type] = {
            k: v / sum_values
            for k, v in sorted(
                space[type].items(), key=lambda item: item[1], reverse=True
            )
        }

    # assign each instance a proper y position
    for type in space:
        bottom = 0.1
        for i, instance in enumerate(space[type]):
            y_pos[instance] = bottom
            bottom += space[type][instance] * 0.8

    nodes = dict(
        # pad=15,
        thickness=20,
        line=dict(color="black", width=0.5),
        label=instances,
        color=color_map,
        x=x_pos,
        y=y_pos,
        align="right",
    )

    # Create a Sankey diagram
    fig = go.Figure(
        data=[
            go.Sankey(
                node=nodes, link=dict(source=sources, target=targets, value=values)
            )
        ]
    )

    fig.update_layout(width=1920, height=1080)

    fig.update_layout(title_text="Sankey Diagram", font_size=10)
    # fig.show()

    filepath = os.path.join(path, name)
    fig.write_image(filepath + ".png")
    fig.write_image(filepath + ".svg")
    fig.write_html(filepath + ".html")


def process_matrix(
    config: Config, matrix: pd.DataFrame, name="some_matrix", path=None, instances=None, mode=None
):
    matrix_to_csv(config, matrix, name, path)

    if config.visualize:
        visualize_matrix(
            config,
            matrix,
            name,
            path=config.visualization_path,
        )

        if instances:
            matrix_to_sankey(
                config,
                matrix,
                name + "_sankey",
                path=config.visualization_path,
            )
            if mode:
                visualize_matrix_graph(
                    config,
                    matrix,
                    name + "_graph",
                    path=config.visualization_path,
                    node_size_mode=config.proximity_mode,
                )
            else:
                visualize_matrix_graph(
                    config,
                    matrix,
                    name + "_graph",
                    path=config.visualization_path,
                )
