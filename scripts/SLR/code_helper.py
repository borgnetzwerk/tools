import time


# helpful functions
def index_all(input_list, item):
    return [i for i, x in enumerate(input_list) if x == item]


def split_string(input_string, delimiters=[" ", "-", "_"]):
    for delimiter in delimiters:
        input_string = " ".join(input_string.split(delimiter))
    return input_string.split()


def path_cleaning(text):
    mapping = {
        "\\": "/",
    }
    for key, value in mapping.items():
        text = text.replace(key, value)
    return text


def time_function(func):
    def wrapper(*args, **kwargs):
        appendix = ""
        # if instances in args:
        if "instances" in kwargs:
            # append len of instances
            appendix = f"({len(kwargs['instances'])} instances"
        if "papers" in kwargs:
            if appendix:
                appendix += ", "
            appendix += f"{len(kwargs['papers'])} papers"
        if appendix:
            appendix += ")"
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} executed in {end_time - start_time} seconds" + appendix)
        return result

    return wrapper


## Obsidian


def fill_digits(var_s, cap=2):
    """Add digits until cap is reached"""
    var_s = str(var_s)
    while len(var_s) < cap:
        var_s = "0" + var_s
    return var_s


def get_clean_title(title, eID=None, obsidian=False):
    """
    Cleans a given title to make it suitable for filenames.

    Parameters:
    title (string): The title. "episode1"
    eID (int): The position of that episode in the playlist.

    Returns:
    string: cleaned title for use as filename
    """
    noFileChars = r'":\<>*?/'

    replace_dict = {
        "–": "-",
        "’": "´",
        " ": " ",
    }
    clean_title = title
    for each in noFileChars:
        clean_title = clean_title.replace(each, "")
    for key, value in replace_dict.items():
        clean_title = clean_title.replace(key, value)
    if obsidian:
        clean_title = clean_title.replace("#", "")
    if eID:
        clean_title = fill_digits(eID, 3) + "_" + clean_title
    return clean_title.strip()


def clear_name(name, can_be_folder=True):
    if can_be_folder:
        clean_title = name.replace("/", "[SLASH]")
    else:
        clean_title = name.replace("/", " or ")
    clean_title = get_clean_title(clean_title, obsidian=True)
    if can_be_folder:
        clean_title = clean_title.replace("[SLASH]", "/")
    if clean_title.startswith("https"):
        clean_title = clean_title[5:]
    while clean_title.startswith("/"):
        clean_title = clean_title[1:]
    if clean_title.startswith("www."):
        clean_title = clean_title[4:]
    while clean_title.endswith("/"):
        clean_title = clean_title[:-1]
    return clean_title


def parse_link(text):
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1]
    if text.startswith("[[") and text.endswith("]]"):
        text = text[2:-2]
    return text


def json_proof(data):
    """Converts a dictionary to a JSON-proof string"""
    res = data
    if isinstance(data, dict):
        res = {}
        for key, value in data.items():
            if isinstance(value, dict):
                res[key] = json_proof(value)
            # if isinstance(value, list):
            #     data[key] = [json_proof(each) for each in value]
            # if isinstance(value, str):
            #     data[key] = value.replace('"', "'")
            elif hasattr(value, "__dict__"):
                res[key] = json_proof(value.__dict__)
            else:
                res[key] = value
    return res
