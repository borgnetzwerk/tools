import os
import subprocess

def generate_dot_file(episodes, filename, path, image_format = "png"):
    # Create a list of nodes, where each node represents an episode
    
    nodes = []
    for episode_id, ep in episodes.items():
        node_id = f"episode_{episode_id}"
        title = ep['title'].replace('"', "'")
        nodes.append(f"{node_id} [label=\"{title}\"]")

    # Create a list of edges, where each edge represents a common word between two episodes
    edges = []
    for episode_id_1, ep_1 in episodes.items():
        for episode_id_2, ep_2 in episodes.items():
            if episode_id_1 >= episode_id_2:
                continue

            common_words = set(ep_1['words']) & set(ep_2['words'])
            if common_words:
                node_id_1 = f"episode_{episode_id_1}"
                node_id_2 = f"episode_{episode_id_2}"
                edges.append(f"{node_id_1} -> {node_id_2} [label=\"{', '.join(common_words)}\"]")

    # Assemble the Graphviz DOT file
    dot_file = "digraph {\n"
    dot_file += "node [shape=ellipse, style=filled, color=lightblue, fontcolor=black, fontsize=12]\n"
    dot_file += "\n".join(nodes)
    dot_file += "\n"
    dot_file += "edge [dir=none, color=gray, fontcolor=black, fontsize=10]\n"
    dot_file += "\n".join(edges)
    dot_file += "\n}"

    filepath = os.path.join(path.replace("\\edited", "\\graph"), filename)
    dot_filename = filepath + ".dot"
    with open(dot_filename, "w", encoding="utf8") as f:
        f.write(dot_file)

    image_filename = filepath + "." + image_format
    # subprocess.run(["dot", "-Kneato", "-v",  "-T" + image_format, "-Gsize=100,100", "-Gdpi=300",  dot_filename, "-o", image_filename.replace("."+image_format, "_neato2."+image_format)])
    # subprocess.run(["dot", "-Kneato", "-v",  "-T" + image_format, dot_filename, "-o", image_filename.replace("."+image_format, "_neato."+image_format)])
    subprocess.run(["dot", "-v",  "-Tsvg", dot_filename, "-o", image_filename.replace("."+image_format, ".svg")])
    subprocess.run(["dot", "-v",  "-T" + image_format, dot_filename, "-o", image_filename])
    # subprocess.run(["dot", "-v",  "-T" + image_format, "-Gsize=50,50", "-Gdpi=300", dot_filename, "-o", image_filename.replace("."+image_format, "2."+image_format)])
    # subprocess.run(["dot", "-Kfdp", "-v",  "-T" + image_format, "-Gsize=50,50", "-Gdpi=300", dot_filename, "-o", image_filename.replace("."+image_format, "_fpd2."+image_format)])
    subprocess.run(["dot", "-Kfdp", "-v",  "-Tsvg", dot_filename, "-o", image_filename.replace("."+image_format, "_fpd.svg")])
    subprocess.run(["dot", "-Kfdp", "-v",  "-T" + image_format, dot_filename, "-o", image_filename.replace("."+image_format, "_fpd."+image_format)])
    return dot_file
