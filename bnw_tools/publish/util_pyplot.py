import matplotlib.pyplot as plt
import numpy as np
import os


def dict_to_barchart(data: dict[str:float], path = None, show = False, force = False, sort = False, prune = False):
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
            print(f"File already exists: {path}")
            return
    
    if sort:
        data = dict(sorted(data.items(), key=lambda item: item[1], reverse=True))
    

    if prune:
        # we can delete every entry after the first with 0 was found
        if sort:
            position = 0
            for key, value in data.items():
                if value == 0:
                    break
                else:
                    position += 1
            data = {k: v for k, v in list(data.items())[:position]}
        else:
            data = {k: v for k, v in data.items() if v > 0}

    # values = np.random.uniform(0, 1, (len(data), ))
    values = list(data.values())
    labels = list(data.keys())
    # values.reverse()
    # labels.reverse()

    positions = np.arange(len(values)) * 2 + 0.5
    


    height = len(max(data.keys(), key=len))
    height = height / 10 + 2 # account for labels + bars
    width = len(data) / 2 # + 2
    fig, ax = plt.subplots(figsize=(width, height))
    fig.subplots_adjust(bottom=.6)
    plt.margins(x=0, tight=True)

    plt.bar(positions, values, align='center')
    plt.xticks(positions, labels, rotation=45, ha='right')

    plt.tick_params(axis='x', labelsize=20)
    plt.ylabel('% of max')
    plt.title('Relevant Keywords frequency present in this document, compared to the maximum found in any document.')
    plt.grid(True, axis= 'y')

    if path:
        plt.savefig(path, bbox_inches='tight')
    if show:
        plt.show()
    plt.close()