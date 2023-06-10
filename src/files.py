# files.py

import os, shutil

class File:
    def __init__(self, path: str) -> None:
        '''Init file object with path'''
        self.path = path

    def exists(self):
        '''Checks if the file exists'''
        return os.path.isfile(self.path)

    def check_type(self, extension: str):
        '''Checks if the file is of a certain type'''
        if(self.exists()):
            return self.path.endswith(extension)

        return False
    
    def get_type(self):
        '''Returns the file type'''
        return self.path.split(".")[-1]

    def create(self):
        '''Creates the file'''
        with open(self.path, 'a+'):
            pass

        return self.exists()

    def delete(self):
        '''Deletes the file'''
        if(self.exists()):
            os.remove(self.path)

        return not self.exists()

class Directory:
    def __init__(self, path: str) -> None:
        '''Init directory object with path'''
        self.path = path

    def exists(self):
        '''Checks if the directory exists'''
        return os.path.isdir(self.path)

    def create(self):
        '''Creates the directory'''
        try:
            os.mkdir(self.path)
        except FileExistsError:
            pass
        
        return self.exists()

    def delete(self):
        if(self.exists()):
            shutil.rmtree(self.path)

        return not self.exists()
    
    def contents(self):
        if self.exists():
            return os.listdir(self.path)
        
    def contents_long(self):
        if self.exists():
            return [self.path + ('/' if not self.path.endswith('/') else '') + file for file in self.contents()]

if __name__ == "__main__":
    directory = Directory("./testdir/")
    file = File("./testdir/testfile.txt")

    print(f"Directory exists: {directory.exists()}")
    print(f"Directory created: {directory.create()}")
    print(f"Directory exists: {directory.exists()}\n")

    print(f"File exists: {file.exists()}")
    print(f"File created: {file.create()}")
    print(f"File exists: {file.exists()}\n")

    print(f"File is .txt: {file.check_type('.txt')}")
    print(f"File is .json: {file.check_type('.json')}")
    print(f"File is of type: {file.get_type()}\n")

    print(f"File is deleted: {file.delete()}")
    print(f"File exists: {file.exists()}\n")

    print(f"Directory is deleted: {directory.delete()}")
    print(f"Directory exists: {directory.exists()}")