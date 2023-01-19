import os
import UnityPy
from PIL import Image

def unpack_all_assets(source_folder : str, destination_folder : str):
    # iterate over all files in source folder
    for root, dirs, files in os.walk(source_folder):
        for file_name in files:
            file_name = f'{root}/{file_name}'
            print(file_name)
            env = UnityPy.load(file_name)
            for obj in env.objects:
                if obj.type.name in ["Sprite"]:
                    # parse the object data
                    data = obj.read()
                    if '44' in data.name:
                        # create destination path
                        dest = f'{destination_folder}/{data.name}'
                        
                        # make sure that the extension is correct
                        # you probably only want to do so with images/textures
                        dest, ext = os.path.splitext(dest)
                        dest = dest + ".png"
                        i = 1
                        while os.path.exists(dest):
                            if i == 1:
                                dest = f"{dest[:-4]}_{i}.png"
                            else:
                                dest = f"{dest[:-5]}{i}.png"
                            i += 1

                        img = data.image
                        img.save(dest)
                    
if __name__ == "__main__":
    from UnityPy.helpers import TypeTreeHelper
    TypeTreeHelper.read_typetree_c = False
    asset1 = 'D:/MementoMori/MementoMori_Data/StreamingAssets/aa/StandaloneWindows64'
    asset2 = 'C:/Users/Scobra/AppData/LocalLow/BankOfInnovation/MementoMori/AssetBundle'
    unpack_all_assets(
        asset2,
        'D:/Datamining Stuff/Memento Mori/assetTest'
    )