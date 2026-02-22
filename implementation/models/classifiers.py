from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC

def create_knn():
    """
    Modèle KNN
    """
    return KNeighborsClassifier(n_neighbors=3)

def create_svm():
    """
    Modèle SVM
    """
    return SVC(kernel='rbf', probability=True)
