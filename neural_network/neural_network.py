from keras.layers import Dense, Dropout
from keras.models import Sequential
import tensorflow as tf


class NeuralNetwork():
    model = None
    graph = tf.get_default_graph()

    @classmethod
    def initialize(cls):
        cls.model = Sequential()
        cls.model.add(Dense(15, input_dim=6, activation='relu'))    # input layer requires input_dim param
        cls.model.add(Dense(10, activation='relu'))
        cls.model.add(Dense(6, activation='relu'))
        cls.model.add(Dropout(.2))
        cls.model.add(Dense(1, activation='sigmoid'))   # sigmoid instead of relu for final probability between 0 and 1
        cls.model.load_weights('production.h5')

        cls.graph = tf.get_default_graph()