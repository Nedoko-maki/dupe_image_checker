import copy
import datetime
import imagehash
import json
import traceback
from pathlib import Path
from PIL import Image


class ImageStruct:
    def __init__(self, directory: Path, emitters: dict):

        """
        An ImageStruct object, manages all image data and metadata.

        :param directory: pathlib Path object.
        :param emitters: Dictionary that contains PyQt pyqtSignal signallers.
        """

        self.directory = directory
        self.metadata = None
        self.image_data = None
        self.emitters = emitters

    def load_data(self):
        """
        Loads a json file from disk and stores the data in a ImageStruct object.

        :return: No return value
        """

        if Path(self.directory, "hash_data").is_dir() and \
                Path(self.directory, "hash_data", "fp_hash_data.json").is_file():

            try:
                with open(Path(self.directory, "hash_data", "fp_hash_data.json"), "r") as json_file:
                    json_data = json.load(json_file)
                    json_file.close()

                for image_data_dict in json_data["image_data"]:
                    json_data["image_data"][image_data_dict]["hash_list"] = \
                        list(map(lambda x: imagehash.hex_to_hash(x),
                                 json_data["image_data"][image_data_dict]["hash_list"]))
                    # using imagehash.hex_to_hash to reverse the encoding.

                self.metadata = json_data["metadata"]
                self.image_data = copy.deepcopy(json_data["image_data"])

                if Path(self.metadata["directory"]) != self.directory:
                    self.emitters["text_log"].emit("Warning: the given directory and the loaded directory are not the same!")

            except WindowsError as e:
                print(f"Error loading hashes: {e}")
                traceback.print_exc()

    def generate_data(self, file_list: list, grid_density=10):

        """
        Generates a dict that contains a list of hashes, and creates new metadata in the ImageStruct object.

        :param file_list: takes a list of files.
        :param grid_density: takes an integer value as the density of grid squares of hashes generated.
        :return: No return value
        """

        output_hashes = dict()
        for num, image in enumerate(file_list, start=1):
            _ = Image.open(Path(self.directory, image))
            x, y = _.size
            hash_list = list()
            for x_grid in range(grid_density):  # -1 since we're going by intersections of the grid, not the grid itself
                for y_grid in range(grid_density):
                    hash_list.append(imagehash.average_hash(_.crop(
                        ((x_grid * (x / grid_density)), (y_grid * (y / grid_density)),
                         ((x_grid + 1) * (x / grid_density)), ((y_grid + 1) * (y / grid_density)))
                    )))

            # [left, upper, right, lower] for the PIL Image.crop() method. OLD
            # Now it generates a grid, where each part of the grid is averaged. NEW
            # looking at small sections of the image vs. the whole image
            # since the bg shouldn't change that much

            output_hashes[image] = {"size": _.size, "average_hash": str(imagehash.average_hash(_)),
                                    "hash_list": hash_list}
            _.close()
            self.emitters["progress_bar"].emit(round(100*num/len(file_list)))

        self.image_data = output_hashes
        self.metadata = {"directory": str(self.directory),
                         "time_of_creation": f"{datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
                         # dd/mm/yyyy hh:mm:ss
                         "last_time_modified": f"{datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
                         "grid_density": grid_density}

    def save_data(self):

        """
        Saves the ImageStruct's member data into a json file, and saves it onto disk.

        :return: No return value
        """

        self.metadata["last_time_modified"] = f"{datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        output_dict = {"metadata": self.metadata,
                       "image_data": self.image_data}

        temp_dict = copy.deepcopy(self.image_data)

        for image_data_dict in self.image_data:
            temp_dict[image_data_dict]["hash_list"] = list(map(lambda x: str(x),
                                                               self.image_data[image_data_dict]["hash_list"]))
            # converting binary arrays to hex for better readability in .json (with str())

        output_dict["image_data"] = copy.deepcopy(temp_dict)

        if not Path(self.directory, "hash_data").is_dir():
            try:
                Path(self.directory, "hash_data").mkdir(exist_ok=True)
            except OSError:
                print(f"Creation of the directory 'hash_data' failed.")
        try:
            self.emitters["text_log"].emit("Saving json file...")
            with open(Path(self.directory, "hash_data", "fp_hash_data.json"), "w") as json_file:
                json.dump(output_dict, json_file, indent=4)
                json_file.close()
            self.emitters["text_log"].emit("Saved!")
        except:
            self.emitters["text_log"].emit("Could not save json file.")
            traceback.print_exc()


def f_num0(value: int,
           n: int):  # formats the int value to have n zeros before it. (method name = fNum zero, but integer)
    try:
        return str(int(n - len(str(value))) * str(0) + str(value))
    except TypeError as e:
        print(f"Error in f_num0: {e}")


def display_folders():

    """
    **Depreciated. PyQt5 allows the ability to use QComboBoxes which replace the functionality of this method.**

    Prints all the folders in the current working directory and the number of files in each folder.
    Returns a list of all the folders.

    :return: List of folders in the current working directory.
    """
    folders = [x.name for x in Path.cwd().glob("*") if x.is_dir()]
    try:
        for num, folder in enumerate(folders):
            if Path(Path.cwd(), folder).is_dir():
                file_num = len([_ for _ in Path(Path.cwd(), folder).glob("*") if _.is_file()])
                num_formatted = f_num0(num, 3)
                folder_formatted = folder + " " * (30 - len(str(folder)))
                print(f"{num_formatted} | {folder_formatted} | Number of files: {file_num}")
    except:
        traceback.print_exc()
    print("")
    return folders


def choose_int(text: str, **kwargs):
    max_value = None
    input_list = None
    if "max_value" in kwargs:
        max_value = kwargs["max_value"]
    if "input_list" in kwargs:
        input_list = kwargs["input_list"]

    while True:
        try:
            user_input = int(input(f"\n{text}"))
            if user_input < 0:  # if not negative, pass.
                print("Invalid input (value is less than 0!)")
            else:
                if "max_value" not in kwargs:  # if no limit to value
                    if "input_list" not in kwargs:  # if no input_list, any positive int value.
                        output_choice = user_input
                        print("> " + str(output_choice))
                        return output_choice
                    else:
                        output_choice = input_list[user_input]
                        print("> " + str(output_choice))
                        return output_choice
                elif user_input >= max_value:
                    print("Invalid input (value exceeds the max value)!")
                else:
                    if "input_list" not in kwargs:
                        output_choice = user_input
                        print("> " + str(output_choice))
                        return output_choice
                    else:
                        output_choice = input_list[user_input]
                        print("> " + str(output_choice))
                        return output_choice
        except Exception as e:
            print(f"Invalid input (error encountered)! \nError: {e}")


def confirm_choice(text: str):
    while True:
        try:
            _ = input(text + " (Y/N)?:").lower()
            if _ in ["y", "ye", "yes"]:
                return True
            elif _ in ["n", "no"]:
                return False
            else:
                print("Invalid input!")
        except Exception as e:
            print(e)


def f_type_return(file, file_type_list: list):  # takes string and file type list as input.
    for f_type in file_type_list:
        if str(file).endswith(f_type):
            return str(f_type)


def rename_to_num(directory: Path, file_list: list, format_string: str, file_type_list: list):
    for num, file in enumerate(file_list):
        try:
            Path(directory, file).rename(Path(directory, format_string+str(num)+f_type_return(file, file_type_list)))
        except WindowsError:
            try:
                Path(directory, file).rename(Path(directory, "_temp_"+str(num)+f_type_return(file, file_type_list)))
            except Exception as e:
                print(f"An exception has occured on iteration {num}: {e}")
        except Exception as e:
            print(f"An exception has occured on iteration {num}: {e}")


def strfex(expression: str, **kwargs) -> str:  # string format expression
    # using % as a special character marker,
    # %grp% marks the group series
    # %grp_num% marks the iteration of a group series
    # %num% marks the iteration of all the images. (not implemented yet, looking into making a metadata dict for this)

    # only limit with this system is that it doesn't account for open-ended tags (invalid),
    # or %tag%text_that_is_a_tag%tag%

    """
    **A string formatting function that can take a user input expression and format an input string.**

    %grp% - marks the group series

    %grp_num% - marks the iteration of a group series

    %num% - marks the iteration out of all the images

    :param expression: A strfex expression.
    :param kwargs: The data to be formatted into a string.
    :return: The formatted string
    """

    valid_kwargs = ["grp", "grp_num", "num"]
    output_str = str()

    expression_list = expression.split("%")
    for str_chunk in expression_list:
        if str_chunk in valid_kwargs:
            if str_chunk in ["grp", "grp_num", "num"]:  # this is to format special data, other tags like date
                # wouldn't need to be formatted like this. (else)
                output_str += f_num0(kwargs[str_chunk], 3)
            else:
                output_str += kwargs[str_chunk]
        else:
            output_str += str_chunk
    return output_str


def check_json_exists(directory: Path):
    if Path(directory, "hash_data").is_dir() and Path(directory, "hash_data", "fp_hash_data.json").is_file():
        return True
    else:
        return False


def compare_hashes(hash_input_1: dict, hash_input_2: dict, kwargs):

    """
    Compares two dicts of hashes, and returns a true value if the number of successful matches exceed the success ratio.

    The threshold for matching depends on the cutoff.
    There is two modes: similar and identical.

    :param hash_input_1: Hash dict 1
    :param hash_input_2: Hash dict 2
    :param kwargs: success ratio, cutoff, mode
    :return: True or False
    """
    score = 0

    if "success_ratio" in kwargs:
        success_ratio = kwargs["success_ratio"]
    else:
        success_ratio = 0.3
    if "cutoff" in kwargs:
        cutoff = kwargs["cutoff"]
    else:
        cutoff = 0
    if "mode" in kwargs:
        mode = kwargs["mode"]
    else:
        mode = "similar"

    if mode == "identical":
        if hash_input_1["hash_list"] == hash_input_2["hash_list"]:
            return True
        else:
            return False
    elif mode == "similar":
        for index in range(len(hash_input_1["hash_list"])):
            if abs(hash_input_1["hash_list"][index] - hash_input_2["hash_list"][index]) < cutoff:
                score += 1

        if score >= round(len(hash_input_1["hash_list"]) * success_ratio):
            return True
        else:
            return False


def cross_compare_list(image_struct: ImageStruct, comparison_function, **kwargs) -> list:
    # cutoff 0, a 12 to 10 density is ideal, crosschecking a nested list of hashes.
    # Potential improvements could be to rework this so it can take a function as the comparing function so it can
    # compare with different data sets. Input the file list.

    """

    Compares two lists for matches using a comparison function.

    :param image_struct: Takes an ImageStruct object in
    :param comparison_function: Takes a comparison function that compares the inputs
    :param kwargs: Arguments that pass off into the comparison function.
    :return: Returns a 2 element list of [duplicate items, grouped duplicate items]
    """

    text = {"identical": "perfect", "similar": "similar"}

    dupe_items = []
    g_dupe_items = []
    item_list = image_struct.image_data
    image_struct.emitters["text_log"].emit(f"Cross checking for {text[kwargs['mode']]} duplicates...")
    for num, item_1 in enumerate(item_list, start=1):
        group = []
        if item_1 not in dupe_items:
            for item_2 in item_list:
                if item_1 != item_2 and item_2 not in dupe_items:

                    if (comparison_function(item_list[item_1],
                                            item_list[item_2], kwargs)):
                        if item_1 not in dupe_items:
                            dupe_items.append(item_1)
                            group.append(item_1)
                        dupe_items.append(item_2)
                        group.append(item_2)

            if len(group) != 0:
                g_dupe_items.append(group)
        image_struct.emitters["progress_bar"].emit(round(100 * num / len(item_list)))
    image_struct.emitters["text_log"].emit("Done!")
    return [dupe_items, g_dupe_items]


def regroup_files(file_list: list, image_struct: ImageStruct,
                  type_list: list, expression="%grp%-%grp_num%"):

    """

    :param file_list: Takes a list of files.
    :param image_struct: Takes an ImageStruct object.
    :param type_list: Takes a list of file types.
    :param expression: A string formatted expression, or strfex. Check the strfex function for more info.
    :return: No return value
    """

    for i, file_list_2 in enumerate(file_list):
        for i2, filename in enumerate(file_list_2):
            try:
                if f_type_return(filename, type_list) in type_list:
                    Path(image_struct.directory, filename).rename(Path(image_struct.directory,
                                                                       strfex(expression, grp=i,
                                                                           grp_num=i2) + f_type_return(filename,
                                                                                                       type_list)))
                    image_struct.image_data[
                        strfex(expression, grp=i, grp_num=i2) + f_type_return(filename, type_list)] = \
                        image_struct.image_data[filename]  # renaming the key associated with the filename.
                    del image_struct.image_data[filename]  # deleting old reference
            except Exception as e:
                image_struct.emitters["text_log"].emit("regroup_files error: " + str(e))
        image_struct.emitters["progress_bar"].emit(round(100 * (i + 1) / len(file_list)))
    image_struct.save_data()


def product(x): return x[0] * x[1]  # can be tuple/list


def move_files(new_folder: str, file_list: list, image_struct: ImageStruct):

    """

    Moves a list of files to a subdirectory in the current working directory, then returns the altered ImageStruct
    object, without the moved files in the concerned image_data dict.

    :param new_folder: Name of the to-be-created subdirectory in the current working directory.
    :param file_list: Takes a list of files to be moved.
    :param image_struct: An ImageStruct object.
    :return: Returns an ImageStruct object.
    """

    try:
        Path(image_struct.directory, new_folder).mkdir(exist_ok=True)
    except OSError:
        image_struct.emitters["text_log"].emit(f"Creation of the directory '{new_folder}' failed.")
    else:
        image_struct.emitters["text_log"].emit("Successfully created the directory.")

    image_struct.emitters["text_log"].emit("Moving duplicates...")

    try:
        if Path(image_struct.directory, new_folder).is_dir():
            for num, grouped_files in enumerate(file_list, start=1):
                HQ_image = grouped_files[0]  # setting HQ image as first
                for file in grouped_files:
                    if product(image_struct.image_data[file]["size"]) > product(
                            image_struct.image_data[HQ_image]["size"]):
                        HQ_image = file  # higher quality, set new HQ file

                for file in grouped_files:
                    if file != HQ_image:  # If the file isn't the HQ one, it moves all exact dupes to another folder.
                        Path(image_struct.directory, file).rename(Path(image_struct.directory, new_folder, file))
                        for filename in image_struct.image_data:  # deleting moved files' hashes
                            if filename == file:
                                del image_struct.image_data[filename]
                                break

                image_struct.emitters["progress_bar"].emit(round(100 * num / len(file_list)))
            image_struct.emitters["text_log"].emit("Done!")
    except Exception as e:
        print(e)

    return image_struct


if __name__ == "__main__":
    print("""dil: This is a module, made to be used to check for duplicate images, and identify and package images.
""")

    _ = input()
