import os
from PIL import Image, ImageStat

Image.MAX_IMAGE_PIXELS = None # Disabling max img size, for unexpectedly big images. Do delete if you don't fully trust all your images.  

print("""
The limitations of this program is that it can only detect exact duplicates.
If an image is identical, but slightly edited or something, it will not detect the duplicate.

GIFs and MP4s do not work.

Additionally, the images should be in folders in the same directory as this .py file. (PIL should be installed too)
""")

folders = os.listdir(os.getcwd())

for num, folder in enumerate(folders):
    if os.path.isdir(os.path.join(os.getcwd(), folder)):
        img_num = len(os.listdir(os.path.join(os.getcwd(), folder)))
        num_formatted = "0"*(3 - len(str(num))) + str(num) 
        folder_formatted = folder + " "*(30 - len(folder))
        print(f"{num_formatted} | {folder_formatted} | Number of imgs: {img_num}")


valid_input = False

while not valid_input:
    try: 
        chosen_folder = int(input("\nChoose a folder: "))
    except Exception:
        print("Invalid input!")

    if chosen_folder >= len(folders):
        print("Invalid input!")
    else:
        folder_name = folders[chosen_folder]
        print("\n> "+folder_name+"\n")
        valid_input = True
        break

image_folder = os.path.join(os.getcwd(), folder_name)
image_files = [_ for _ in os.listdir(image_folder) if _.endswith('jpg') or _.endswith('jpeg') or _.endswith('png')]
image_mean_list = []
printed = []

for num, image in enumerate(image_files):
    _ = Image.open(os.path.join(image_folder, image))
    image_mean_list.append([image, ImageStat.Stat(_).mean])
    if (round((100*num)/len(image_files))/10).is_integer() and round((100*num)/len(image_files)) not in printed: # Probably a bad way of doing % bar, but it works, without performance loss.
        print(f"Percent done processing: {round((100*num)/len(image_files))}%")
        printed.append(round((100*num)/len(image_files)))

duplicate_images = []
grouped_duplicate_images = []

for img1 in image_mean_list:
    if img1[0] not in duplicate_images:
        group = []
        for img2 in image_mean_list:
            if img1[0] != img2[0]:
                if img1[1] == img2[1]:
                    if img1[0] not in duplicate_images:
                        duplicate_images.append(img1[0])
                        group.append(img1[0])
                    duplicate_images.append(img2[0])
                    group.append(img2[0])
        if len(group) != 0:
            grouped_duplicate_images.append(group)

if len(grouped_duplicate_images) != 0:
    for _ in grouped_duplicate_images:
        print(_)
else:
    print("No duplicates!")
    
print("\nDone!")
_ = input()

                
        
        
    




        
                
            
        


