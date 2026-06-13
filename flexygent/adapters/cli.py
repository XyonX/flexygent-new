from flexygent.interfaces import UserIO



class CliUserIO(UserIO):
    def get_input(self,prompt:str):
        return input(prompt)
    def show_output(self,message:str):
        print(message)


