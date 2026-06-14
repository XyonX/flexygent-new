from abc import ABC,abstractmethod


class UserIO(ABC):


    # get message from input could be input() in cli or other fucntion in api or other methon
    @abstractmethod
    def get_input(self,prompt:str=""):
        ...

    # show the output to the user could print() in cli
    @abstractmethod
    def show_output(self,message:str):
        ...



