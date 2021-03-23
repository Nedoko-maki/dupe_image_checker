# dupe_image_checker
Imports: PIL, os

Python code for an optimised version of a duplicate image checker I found online on Google. Previous version did some processing that could just be listed and referenced later, so implementation and optimisation took not too long. 

The limitations of this program is that it can only detect exact duplicates.

If an image is identical, but slightly edited or something, it will not detect the duplicate.
GIFs and MP4s do not work.

Additionally, the images should be in folders in the same directory as this .py file. (PIL should be installed too)
You can select the folder that the images are in. 
