# custom config file format
# | IMPORT SECTION
import os

from typing import Dict, List, Tuple, Union

# | CLASS SECTION


class Config:
    def __init__(self) -> None:
        self.__data = {}
        self.__section = []

    def __getitem__(self, section_name: str) -> Dict[str, str]:
        if type(section_name) != str:
            raise TypeError(f"section_name must be string, got: {type(section_name)}")

        if section_name in self.__section:
            return self.__data[section_name]
        else:
            raise Config.SectionNameNotFound(f"'{section_name}' is not a section name.")

    def __setitem__(self, section_name: str, value: Dict[str, str]) -> None:
        if type(section_name) != str:
            raise TypeError(f"section_name must be string, got: {type(section_name)}")

        if type(value) != dict:
            raise TypeError(f"value must be dictionary, got: {type(value)}")

        if section_name in self.__section:
            self.__data[section_name] = value
        else:
            raise Config.SectionNameNotFound(f"'{section_name}' is not a section name.")

    def __str__(self):
        res = ""

        for section in self.__section:
            res += f"[{section}]\n"
            for k, v in self.__data[section].items():
                res += f"\t{k}:\t{v}\n"
            res += "\n"

        return res.strip()

    def add_section(self, section_name: str) -> None:
        if type(section_name) != str:
            raise TypeError(f"section_name must be string, got: {type(section_name)}")

        if section_name not in self.__section:
            self.__data[section_name] = {}
            self.__section.append(section_name)
            self.__section.sort()
        else:
            raise Config.SectionNameExist(f"'{section_name}' already a section name.")

    def remove_section(self, section_name: str) -> None:
        if type(section_name) != str:
            raise TypeError(f"section_name must be string, got: {type(section_name)}")

        if section_name in self.__section:
            self.__section.remove(section_name)
            self.__data.pop(section_name)
        else:
            raise Config.SectionNameNotFound(f"'{section_name}' is not a section name.")

    def pop_section(
        self, section_name: str
    ) -> Dict[str, Union[str, List[str], Dict[str, str]]]:
        if type(section_name) != str:
            raise TypeError(f"section_name must be string, got: {type(section_name)}")

        if section_name in self.__section:
            self.__section.remove(section_name)
            return self.__data.pop(section_name)
        else:
            raise Config.SectionNameNotFound(f"'{section_name}' is not a section name.")

    def toFile(self, file_name: str):
        if os.path.isfile(file_name):
            with open(file_name, "wt", encoding="utf-8") as file:
                file.write("")

        with open(file_name, "at", encoding="utf-8") as file:
            for section in self.__section:
                file.write(f"[{section}]\n")
                for k, v in self.__data[section].items():
                    if type(v) is str:
                        file.write(f"{k}:\t{v}\n")
                    elif type(v) is list:
                        new_v = "\n".join([f"\t- {string}" + string for string in v])
                        file.write(f"{k}:{new_v}\n")
                    elif type(v) is dict:
                        new_v = "\n".join([f"\t# {key}:\t{item}" for key, item in v.items()])
                        file.write(f"{k}:{new_v}\n")
                    else:
                        raise TypeError(f"can't parse to file, supported data type: str, list and dict, got: {type(v)}")
                file.write("\n")

    def fromFile(self, file_name: str):
        with open(file_name, "rt", encoding="utf-8") as file:
            data = file.readlines()

        section_tmp = []
        data_tmp = {}

        cur_section = ""
        in_list = False
        in_dict = False
        for line in data:
            if line == "\n":
                continue

            if in_list:
                if not line.strip().startswith("- "):
                    in_list = False
                else:
                    data_tmp[cur_section][key].append(line.strip()[2:])
                    continue
            elif in_dict:
                if not line.strip().startswith("# "):
                    in_dict = False
                else:
                    k_val = line.strip()[2:].split(":")[0].strip()
                    v_val = line.strip()[2:].split(":")[1].strip()
                    data_tmp[cur_section][key][k_val] = v_val
                    continue

            if line.strip().startswith("[") and line.strip().endswith("]"):
                cur_section = line.strip()[1:-1]
                section_tmp.append(cur_section)
                section_tmp.sort()
                data_tmp[cur_section] = {}
            else:
                if ":" in line.strip():
                    key, val = tuple(i.strip() for i in line.strip().split(":", maxsplit=1))
                    if val.startswith("- "):
                        data_tmp[cur_section][key] = [val[2:]]
                        in_list = True
                    elif val.startswith("# "):
                        k_val = val[2:].split(":")[0].strip()
                        v_val = val[2:].split(":")[1].strip()
                        data_tmp[cur_section][key] = {k_val: v_val}
                        in_dict = True
                    else:
                        data_tmp[cur_section][key] = val

        self.__data = data_tmp
        self.__section = sorted(section_tmp)

    class SectionNameExist(Exception):
        pass

    class SectionNameNotFound(Exception):
        pass
