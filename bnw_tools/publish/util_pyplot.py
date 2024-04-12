import matplotlib.pyplot as plt
import numpy as np
import os

MAX_PARITIONS = 4


def dict_to_barchart(
    data: dict[str:float],
    path=None,
    title=None,
    ylabel=None,
    xlabel=None,
    show=False,
    force=False,
    sort=False,
    prune=False,
    limit=50,
):
    """
    Create a bar chart from a dictionary.

    Args:
        dict (dict[str:float]): A dictionary where the keys are the labels and the values are the heights.
        path (str): The path to save the plot.
        show (bool): Show the graph or not. False by default.
    """
    # check if file exists:
    if path and not force:
        if os.path.exists(path):
            # print(f"File already exists: {path}")
            return

    if sort:
        data = dict(sorted(data.items(), key=lambda item: item[1], reverse=True))

    if prune:
        # we can delete every entry after the first with 0 was found
        if sort:
            position = 0
            for value in data.values():
                if value == 0:
                    break
                else:
                    position += 1
            data = {k: v for k, v in list(data.items())[:position]}
        else:
            data = {k: v for k, v in data.items() if v > 0}

    if limit and len(data) > limit:
        for i in range(MAX_PARITIONS):
            floor = i * limit
            ceiling = (i + 1) * limit
            if ceiling > len(data):
                ceiling = len(data)
            rest = dict(list(data.items())[floor:ceiling])
            part_path = path
            if i:
                part_path = path.replace(".png", f"_r{i}.png")
            if title:
                part_title = title + f" (rank {floor} to {ceiling})"
            else:
                part_title = None
            part_ylabel = ylabel
            part_xlabel = xlabel
            dict_to_barchart(
                rest,
                path=part_path,
                show=show,
                force=force,
                sort=sort,
                prune=prune,
                limit=limit,
                title=part_title,
                ylabel=part_ylabel,
                xlabel=part_xlabel,
            )
            if ceiling == len(data):
                break
        return

    # values = np.random.uniform(0, 1, (len(data), ))
    values = list(data.values())
    labels = list(data.keys())
    # values.reverse()
    # labels.reverse()

    positions = np.arange(len(values)) * 2 + 0.5

    fontdict = {"fontsize": 20}

    height = len(max(data.keys(), key=len))
    height = height / 10 + 2  # account for labels + bars
    width = len(data) / 2  # + 2
    width = width if width > 5 else 5
    fig, ax = plt.subplots(figsize=(width, height))
    fig.subplots_adjust(bottom=0.6)
    plt.margins(x=0, tight=True)

    plt.bar(positions, values, align="center")
    plt.xticks(positions, labels, rotation=45, ha="right")

    plt.tick_params(axis="x", labelsize=20)
    if ylabel:
        plt.ylabel(ylabel, fontdict=fontdict)
    if xlabel:
        plt.xlabel(xlabel, fontdict=fontdict)
    if title:
        plt.title(title, fontdict=fontdict)
    plt.grid(True, axis="y")

    if path:
        plt.savefig(path, bbox_inches="tight")
    if show:
        plt.show()
    plt.close()
