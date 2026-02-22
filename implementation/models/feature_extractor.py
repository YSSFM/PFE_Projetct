import tensorflow as tf
from keras.applications import MobileNetV2
from keras.models import Model
from keras.layers import GlobalAveragePooling2D

def load_feature_extractor():
    """
    Charge MobileNetV2 comme extracteur de features
    """

    base_model = MobileNetV2(
        weights="imagenet",      # Poids pré-entraînés
        include_top=False,       # Supprimer classification finale
        input_shape=(224, 224, 3)
    )

    # Ajouter couche pooling globale
    x = base_model.output
    x = GlobalAveragePooling2D()(x)

    model = Model(inputs=base_model.input, outputs=x)

    return model
