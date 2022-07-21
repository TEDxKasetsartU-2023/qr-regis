# custom config file format
# | IMPORT SECTION
import os

# | CLASS SECTION
from typing import Dict


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

    def pop_section(self, section_name: str) -> Dict[str, str]:
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
                    file.write(f"{k}: {v}\n")
                file.write("\n")

    def fromFile(self, file_name: str):
        with open(file_name, "rt", encoding="utf-8") as file:
            data = file.readlines()

        section_tmp = []
        data_tmp = {}

        in_section = False
        section_dummy = ""
        for line in data:
            print(repr(line))
            if (
                line != "\n"
                and line.strip()[0] == "["
                and line.strip()[-1] == "]"
                and not in_section
            ):
                in_section = True
                section_dummy = line.strip()[1:-1]
                section_tmp.append(section_dummy)
                data_tmp[section_dummy] = {}
            else:
                if line == "\n":
                    in_section = False
                    continue
                else:
                    data_tmp[section_dummy][line.strip().split(":")[0].strip()] = (
                        line.strip().split(":")[1].strip()
                    )

        self.__data = data_tmp
        self.__section = sorted(section_tmp)

    class SectionNameExist(Exception):
        pass

    class SectionNameNotFound(Exception):
        pass
