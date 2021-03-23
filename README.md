# dupe_image_checker

Python code for an optimised version of a duplicate image checker I found online on Google. Previous version did some processing that could just be listed and referenced later, so implementation and optimisation took not too long. 

The limitations of this program is that it can only detect exact duplicates. It will detect duplicates of different resolutions, given they are identical.

If an image is nearly identical, but slightly edited, it will not detect the duplicate.
GIFs and MP4s do not work in this program.

Additionally, the images should be in folders in the same directory as this .py file. (PIL should be installed via pip too)
You can select the folder that the images are in. 
