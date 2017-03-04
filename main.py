import matplotlib.pyplot as plt
import numpy

from cross_entropy_classifier import CrossEntropyClassifier
from fisher_feature_extractor import FisherFeatureExtractor
from hog_feature_extractor import HOGFeatureExtractor
from kernel_pca import KernelPCA
from kernels import LinearKernel, GaussianKernel, HistogramIntersectionKernel, LaplacianRBFKernel, SublinearRBFKernel
from svm import KernelSVMOneVsOneClassifier, KernelSVMOneVsAllClassifier
from utils import load_data, plot_history, write_output, concat_bias

output_suffix = 'trial14'
feature_extractor = 'hog_fisher'
classifier = 'svm_ovo'
validation = 0.2

print("Loading data")
Xtrain, Ytrain, Xtest = load_data()

if feature_extractor == 'hog':
    hog = HOGFeatureExtractor()
    Xtrain = hog.predict(Xtrain)
    Xtest = hog.predict(Xtest)
elif feature_extractor == 'hog_fisher':
    fisher = FisherFeatureExtractor(nclasses=5)
    Xtrain = fisher.predict(Xtrain)
    Xtest = fisher.predict(Xtest)
elif feature_extractor == 'raw':
    pass
else:
    raise Exception("Unknown feature extractor")

Xtrain = numpy.reshape(Xtrain, (Xtrain.shape[0], -1))
Xtest = numpy.reshape(Xtest, (Xtest.shape[0], -1))

print(Xtrain.shape)
print(Xtest.shape)

kernel_pca = False

if kernel_pca:
    print("Kernel PCA")
    pca = KernelPCA(GaussianKernel(0.1))
    X = numpy.concatenate((Xtrain, Xtest), axis=0)
    pca.fit(X)

    components = min(1000, Xtrain.shape[1])
    X = pca.predict(components)
    ntrain = Xtrain.shape[0]
    Xtrain = X[:ntrain, :]
    Xtest = X[ntrain:, :]

print("Fitting on training data")
nclasses = 10
if classifier == 'cross_entropy':
    Xtrain = concat_bias(Xtrain)
    Xtest = concat_bias(Xtest)

    model = CrossEntropyClassifier(nclasses)
    iterations = 500
    lr = 0.01
    history = model.fit(Xtrain, Ytrain, iterations, lr, validation, 10)

    best = numpy.argmax(history['val_accuracy'])
    print("Best accuracy is %.3f at iteration %d" % (history['val_accuracy'][best], best))

    f = plot_history(history)
    f.savefig('plots/' + output_suffix + '.png')

    model = CrossEntropyClassifier(nclasses)
    history = model.fit(Xtrain, Ytrain, best, lr)
elif classifier == 'svm_ovo':
    model = KernelSVMOneVsOneClassifier(nclasses)
    #kernel = GaussianKernel(0.6)
    #kernel = HistogramIntersectionKernel(0.25)
    kernel = LaplacianRBFKernel(1)
    #kernel = SublinearRBFKernel(4)
    #kernel = LinearKernel()
    reg_lambda = 0.5
    model.fit(Xtrain, Ytrain, kernel, reg_lambda, validation)

    model = KernelSVMOneVsOneClassifier(nclasses)
    model.fit(Xtrain, Ytrain, kernel, reg_lambda)
elif classifier == 'svm_ova':
    model = KernelSVMOneVsAllClassifier(nclasses)
    kernel = GaussianKernel(1.5)
    reg_lambda = 0.5
    model.fit(Xtrain, Ytrain, kernel, reg_lambda, validation)

    model = KernelSVMOneVsAllClassifier(nclasses)
    model.fit(Xtrain, Ytrain, kernel, reg_lambda)
else:
    raise Exception("Unknown classifier")

print("Predicting on test data")
Ytest = model.predict(Xtest)
write_output(Ytest, 'results/Yte_' + output_suffix + '.csv')
