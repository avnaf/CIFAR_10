# ============================================================================================================================================= #
#Imports
import cv2
import numpy as np
# ============================================================================================================================================= #



# ============================================================================================================================================= #
#Globals:
file = # add file path
# ============================================================================================================================================= #



# ============================================================================================================================================= #
# dict = {data : lables}
# data = 10000*3072 numpy array of uint8
# 	Each row of the array stores a 32x32 colour image
#	The first 1024 entries contain the red channel values, the next 1024 the green, and the final 1024 the blue
# 	The image is stored in row-major order, so that the first 32 entries of the array are the red channel values of the first row of the image
# lables =  list of 10000 numbers in the range 0-9
#	The number at index i indicates the label of the ith image in the array data
# ============================================================================================================================================= #
# The dataset contains another file, called batches.meta. It too contains a Python dictionary object. It has the following entries:
#	label_names = 10-element list which gives meaningful names to the numeric labels in the labels array described above.
#	For example, label_names[0] == "airplane", label_names[1] == "automobile", etc.
# ============================================================================================================================================= #
def unpickle(file):
    import cPickle
    with open(file, 'rb') as fo:
        dict = cPickle.load(fo)
    return dict






# ============================================================================================================================================= #
if __name__ == '__main__':

	print '='*100
	print 'loading images from file into dict'
	dict = unpickle(file)

	categories = # get label_names from data-set
	print 'these are the classifier categories: ', categories

	print 'extracting SIFT key-points'
	sift = cv2.SIFT()

	# do this for every image?
	kp = sift.detect(img,None) # None means no mask on the img -> detect over the whole image

	#2nd option (returns key-points and descriptors):  [https://docs.opencv.org/3.0-beta/doc/py_tutorials/py_feature2d/py_matcher/py_matcher.html]
	kp1, des1 = sift.detectAndCompute(img1,None)
	kp2, des2 = sift.detectAndCompute(img2,None)


