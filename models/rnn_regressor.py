import random
import neptune
import numpy as np
import tensorflow as tf
import neptune_tensorboard as neptune_tb

from absl import flags
from absl import app
from data_processor import read_data
from tensorflow.keras import callbacks, Sequential
from tensorflow.keras.layers import SimpleRNN, Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam

flags.DEFINE_string('mode', 'train', 'In which mode should the program be run train/eval')
flags.DEFINE_float('dropout', 0.2, 'Set dropout')
flags.DEFINE_float('learning_rate', 0.0001, 'Set learning rate')
flags.DEFINE_string('activation', 'relu', 'Set activation method')
flags.DEFINE_string('data_dir', '../data/uniform_200k/', 'Relative path to the data folder')
flags.DEFINE_integer('epochs', 1, 'Number of epochs')
flags.DEFINE_integer('rnn_filter', 128, 'Number of units in RNN')

FLAGS = flags.FLAGS

RUN_NAME = 'run_{}'.format(random.getrandbits(64))
EXPERIMENT_LOG_DIR = 'logs/{}'.format(RUN_NAME)

def input_fn(trainingset_path):
    x_train, y_train = read_data(trainingset_path, 'train')
    x_eval, y_eval = read_data(trainingset_path, 'eval')
    x_train = np.reshape(x_train.values, (-1, x_train.shape[1], 1))
    y_train = np.reshape(y_train.values, (-1, 1))
    x_eval = np.reshape(x_eval.values, (-1, x_eval.shape[1], 1))
    y_eval = np.reshape(y_eval.values, (-1, 1))
    return x_train, y_train, x_eval, y_eval


def create_rnn(input_shape, hparams):
    model = Sequential()

    for _ in range(1):
        model.add(SimpleRNN(units=hparams['rnn_filter'], return_sequences=True))
    model.add(SimpleRNN(units=hparams['rnn_filter']))

    for _ in range(2):
        model.add(Dense(128, activation='relu'))
        model.add(Dropout(hparams['dropout']))
        model.add(BatchNormalization())

    return model


def train(hparams, dataset_path):
    neptune.init(project_qualified_name='kowson/OLN')
    with neptune.create_experiment(name="Recurrent neural network",
                                   params=hparams,
                                   tags=["RNN", "grid", "10k_uniform", "testing", "data_v2", "mse"]):
        x_train, y_train, x_eval, y_eval = input_fn(dataset_path)

        model = create_rnn(hparams)
        opt = Adam(lr=hparams["learning_rate"],
                   decay=1e-3 / 200)
        model.compile(loss=tf.keras.losses.MeanSquaredError(), optimizer=opt)

        tbCallBack = callbacks.TensorBoard(log_dir=EXPERIMENT_LOG_DIR)

        history_callback = model.fit(
            x_train,
            y_train,
            validation_data=(x_eval, y_eval),
            epochs=hparams["num_epochs"],
            batch_size=hparams["batch_size"],
            callbacks=[tbCallBack]
        )


def create_experiment():
    neptune_tb.integrate_with_tensorflow()
    hyper_params = {
            "shuffle": False,
            "num_threads": 1,
            "batch_size": 16384,
            "initializer": "uniform_unit_scaling",
            "rnn_filter": FLAGS.rnn_filter,
            "dropout": FLAGS.dropout,
            "learning_rate": FLAGS.learning_rate,
            "activation": 'relu',
            'num_epochs': FLAGS.epochs,
    }

    data_dir = FLAGS.data_dir

    print('--- Starting trial ---')
    train(hyper_params, data_dir)

def main(argv):
    if FLAGS.mode == 'train':
        create_experiment()
    elif FLAGS.mode == 'eval':
        pass


if __name__ == '__main__':
    app.run(main)
