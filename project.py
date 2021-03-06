# ============================================================================================================================================= #
#Imports
import cv2
import numpy as np
import time
import cPickle
from sklearn.svm import SVC 
from sklearn.externals import joblib
from sklearn.metrics import confusion_matrix
# ============================================================================================================================================= #
N = 10000
# ============================================================================================================================================= #
# dict = {data : lables}
# data = 10000*3072 numpy array of uint8
#   Each row of the array stores a 32x32 colour image
#   The first 1024 entries contain the red channel values, the next 1024 the green, and the final 1024 the blue
#   The image is stored in row-major order, so that the first 32 entries of the array are the red channel values of the first row of the image
# lables =  list of 10000 numbers in the range 0-9
#   The number at index i indicates the label of the ith image in the array data
# ============================================================================================================================================= #
# The dataset contains another file, called batches.meta. It too contains a Python dictionary object. It has the following entries:
#   label_names = 10-element list which gives meaningful names to the numeric labels in the labels array described above.
#   For example, label_names[0] == "airplane", label_names[1] == "automobile", etc.
# ============================================================================================================================================= #
def unpickle(file, print_msg = False):
    if print_msg:
        print 'starting unpickling {}...'.format(file[file.rfind('\\')+1:])
        
    with open(file, 'rb') as fo:
        dict = cPickle.load(fo)
        
    if print_msg:
        print 'finished unpickling {}...'.format(file[file.rfind('\\')+1:])
        print '#'*50 
    return dict

# ============================================================================================================================================= #
# input: array of 3072 elements
# ============================================================================================================================================= #
def img_2_RGB(im, print_msg = False):
    if print_msg:
        print 'reshaping image to RGB format (32*32*3)'
        
    mat = np.zeros((32,32,3), np.uint8)
    for i in range(32*32*3):
        mat[(i % (32*32)) // 32][i % 32][i // (32*32)] = im[i]
    return mat

# ============================================================================================================================================= #
# input: image list, heading (optional), delay [mili-seconds] (optional)
# for testing. Not used
# ============================================================================================================================================= #
def show_img(i, heading = '', delay = 1000):
    cv2.imshow(heading, i) 
    cv2.waitKey(delay)
    cv2.destroyAllWindows()

# ============================================================================================================================================= #
# finds good key-points for the classifier using one of many hueristics
# ============================================================================================================================================= #
def find_good_kp(test_imgs_path, hueristic = 'richest images from problematic classes 4 & 6 + richest'):
    #print num_of_test_images
    d = unpickle(test_imgs_path)    
    images = d.values()[0]
    labels = d.values()[1]
    sift = cv2.xfeatures2d.SIFT_create()
    
    good_kp = []
    
    # find best image (with most KP), and use it
    if hueristic == 'richest image':
        max_kp = 0
        for im in enumerate(images):
            img = img_2_RGB(im[1])
            kp = sift.detect(img, None)
            if len(kp) > max_kp:
                max_kp = len(kp)
                good_kp = kp
              
    # use predetermined locations and size for KP (trying to catch good KP in the image)                
    elif hueristic == 'dense':
        W,H = 32,32
        margin = 1
        step = 5
        size = 4
        good_kp = [cv2.KeyPoint(w,h,size) for w in range(margin, W - margin, step) for h in range(margin, H - margin, step)]
     
    # find best image (with most KP), and use it
    if hueristic == 'richest images from problematic classes 4 & 6':
        good_kp = []
        max_kp_num = [0 for i in range(10)]
        tmp_kp = [[] for i in range(10)]
              
        for enum_pair in enumerate(zip(images,labels)):
            img = img_2_RGB(enum_pair[1][0])
            lbl = enum_pair[1][1]
            if lbl not in (3,5): # problematic classes as discovered by my last runs
                continue
            kp = sift.detect(img, None)
            if len(kp) > max_kp_num[lbl]:
                max_kp_num[lbl] = len(kp)
                tmp_kp[lbl] = kp

        good_kp = tmp_kp[3] + tmp_kp[5]
        
    # find best image (with most KP), and use it
    if hueristic == 'richest images from problematic classes 4 & 6 + richest':
        good_kp = []
        max_kp_num = [0 for i in range(10)]
        tmp_kp = [[] for i in range(10)]
              
        for enum_pair in enumerate(zip(images,labels)):
            img = img_2_RGB(enum_pair[1][0])
            lbl = enum_pair[1][1]
            if lbl not in (3,5): # problematic classes as discovered by my last runs
                continue
            kp = sift.detect(img, None)
            if len(kp) > max_kp_num[lbl]:
                max_kp_num[lbl] = len(kp)
                tmp_kp[lbl] = kp

        good_kp = tmp_kp[3] + tmp_kp[5]
        
        used_code_pls_replace_max_kp = []
        max_kp = 0
        for im in enumerate(images):
            img = img_2_RGB(im[1])
            kp = sift.detect(img, None)
            if len(kp) > max_kp:
                max_kp = len(kp)
                used_code_pls_replace_max_kp = kp
        good_kp = used_code_pls_replace_max_kp + tmp_kp[3] + tmp_kp[5]
        
    # takes much longer time with no significant improvement. Not used            
#    elif hueristic == 'several good images':  
#        count = 0
#        for im in enumerate(tst_images):
#            img = img_2_RGB(im[1])
#            kp = sift.detect(img, None)
#            if len(kp) >= 25:
#                good_kp += kp
#                count += 1
#            if count == num_of_images_to_sum:
#                break
            
    del d   
    del images
    del sift
    print '# of descriptors {}'.format(len(good_kp))
    return good_kp

# ============================================================================================================================================= #      
# input: sift, images path (can be list of paths), key-points to be used by sift, num_of_image_sets
# unpickles each data set
# uses sift to extract descriptors and appends into list
# appends labels into 2nd list
# return descriptors as np.array, labels list, time
# ============================================================================================================================================= #
def img_2_descriptors(sift, kp, imgs_path):
    global N #for debug. should be 10000 for normal runs
    start_time = time.time()
    descriptors_ls = []
    labels_ls = [] 

    if type(imgs_path) == list:
        for img_path in imgs_path:
            d = unpickle(img_path)    
            images = d.values()[0][:N]
            labels = d.values()[1][:N]  

            for im,lb in zip(images, labels):
                im = img_2_RGB(im)
                kp,ds = sift.compute(im, kp)
                
                descriptors_ls.append(ds.flatten())
                labels_ls.append(lb)
    else:
        d = unpickle(imgs_path)    
        images = d.values()[0][:N]
        labels = d.values()[1][:N] 
        

        for im,lb in zip(images, labels):
            img = img_2_RGB(im)
            kp,ds = sift.compute(img, kp)
            
            descriptors_ls.append(ds.flatten())
            labels_ls.append(lb)
            
    return np.array(descriptors_ls), labels_ls, time.time() - start_time

# ============================================================================================================================================= #      
# input: X (training data), y (training labels), clf_name (path to where clf should be saved)
# creates SVM
# fits the data
# pickles
# ============================================================================================================================================= #
def train_clf(X,y,clf_name):
    start_time = time.time()
    # after many tests, this was found to be best classifier
    clf = SVC(C = 0.01, kernel='poly')
    clf.fit(X,y)
    print 'fit done... {} seconds'.format(time.time() - start_time)
    with open(clf_name, "wb") as fo:
        joblib.dump(clf, fo, compress = 0) 
#        cPickle.dump(clf, fo,  protocol = cPickle.HIGHEST_PROTOCOL) 
    return time.time() - start_time

# ============================================================================================================================================= #      
# input: data_batch (file paths for data images), clf_name (path to save the classifier into), test (test images path)
# creates sift
# gets key-points
# calls img_2_descriptors & train_clf
# prints timings
# ============================================================================================================================================= #
def train_and_save(data_batch, clf_name, test):
    start_time = time.time()
    sift, sift_time = cv2.xfeatures2d.SIFT_create(), time.time()
    print 'sift created... {} seconds'.format(sift_time - start_time)
    kp, kp_time = find_good_kp(test_imgs_path = test), time.time()
    print 'key-points generated... {} seconds'.format(kp_time - sift_time)
    X,y,descriptors_time = img_2_descriptors(sift, kp, data_batch)
    print 'descriptors generated... {} seconds'.format(descriptors_time)
    training_time = train_clf(X,y,clf_name)
    print 'clf trained and pickled... {} seconds'.format(training_time)

# ============================================================================================================================================= #
# input: test (image file to test), clf_name (classifier to load and predict with), use_score [optional]
# creates sift
# gets key-points
# unpickles the classifier
# uses score(), predict(), confusion_matrix()
# prints timings
# ============================================================================================================================================= #
def load_and_predict(test, clf_name, use_score = False, use_predict = False):
    start_time = time.time()
    sift, sift_time = cv2.xfeatures2d.SIFT_create(), time.time()
    print 'sift created... {} seconds'.format(sift_time - start_time)
    kp, kp_time = find_good_kp(test_imgs_path = test), time.time()
    with open(clf_name, 'rb') as fo:
         clf, load_time = joblib.load(fo) , time.time()
         print 'classifier loaded... {} seconds'.format(load_time - kp_time)
         X,y,descriptors_time = img_2_descriptors(sift, kp, test)
         print 'descriptors generated... {} seconds'.format(descriptors_time)
         if use_score:
            print '#'*50, '\nRate = {}%'.format(100*clf.score(X,y))
         if use_predict:
            print '#'*50, '\nconfusion matrix:\n{}\n'.format(confusion_matrix(y, clf.predict(X)))

# ============================================================================================================================================= #      
# Allows user to train & save a classifier OR to load and predict
# ============================================================================================================================================= #
def main():

    project_dir = r'C:\Users\avi_na\project_CIFAR_10'
    batch_dir = project_dir+ r'\cifar-10-batches-py'
    data_1 = batch_dir + r'\data_batch_1'
    data_2 = batch_dir + r'\data_batch_2'
    data_3 = batch_dir + r'\data_batch_3'
    data_4 = batch_dir + r'\data_batch_4'
    data_5 = batch_dir + r'\data_batch_5'
    data_batch = [data_1, data_2, data_3, data_4, data_5]
    test = batch_dir + r'\test_batch'
    clf_name = project_dir + r'\clf_classes_4_6_joblib_and_richest'

    inp = input('What would you like to do?\n1 --------- train classifier and save it\n2 --------- load classifier and predict test images\n3 --------- exit\n')
    
    if inp == 1:
        print 'Make sure the paths for the data batches and the classifier are correct. If not, quit now, change the and re-launch\n'
        print 'These are the current data paths:\n'
        for data in data_batch:
            print '{}\n'.format(data)
        print 'This is the current test path:\n\t"{}"'.format(test)
        print 'This is the current path for a classifier to be saved. Make sure it does not overwrite an existing one:\n\t"{}"'.format(clf_name)

        while True:
            inp = raw_input('Continue?\t[y/n]\t')
            if inp =='n' or inp =='N':
                return
            elif inp == 'y' or inp == 'Y':
                print '\n'
                train_and_save(data_batch, clf_name, test)
                break

    elif inp == 2:
        print '\nMake sure the paths for the test batch and the classifier are correct. If not, quit now, change the and re-launch\n'
        print 'This is the current test path:\n\t"{}"'.format(test)
        print 'This is the current path for a classifier to be loaded:\n\t"{}"'.format(clf_name)
        
        while True:
            inp = raw_input('Continue?\t[y/n]\t')
            if inp =='n' or inp =='N':
                return
            elif inp == 'y'or inp == 'Y':
                use_score = False
                use_predict = False
                while True:
                    inp = raw_input('use predict (comes with confusion matrix)?\t[y/n]\t')
                    if inp == 'y' or inp == 'Y':
                        use_predict = True
                        break
                    if inp == 'n' or inp =='N':
                        break
                while True:
                    inp = raw_input('use score (accuracy rate in percents)?\t[y/n]\t')
                    if inp == 'y' or inp == 'Y':
                        use_score = True
                        break
                    if inp == 'n' or inp =='N':
                        break   
                if not use_predict and not use_score:
                    use_score = True
                print '\n'
                # the function has both score & predict functions. Each takes ~1800 seconds. predict is relevant for 
                # confusion matrix. score is relevant for accuracy percentage. At least one should be True
                load_and_predict(test, clf_name, use_score, use_predict)
                break

    elif inp == 3:
        print 'Bye Bye!\n'
        return

if __name__ == '__main__':
    main()
