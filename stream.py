# Convolution
import numpy as np
import matplotlib.pyplot as plt


def plot_fx(fx):
    t = np.linspace(-10, 10, num=1000)

    plt.figure()
    plt.scatter(x, fx(x))
    plt.show()


def softmax(x):
    numer = np.exp(x)
    denom = np.sum(np.exp(x))

    return numer / denom


def sigmoid(x):
    return 1./(1 + np.exp(-x))


def tanh(x):
    numer = np.exp(2 * x) - 1
    denon = np.exp(2 * x) * 1

    return numer / denon


x = np.array([
    [0., 0.],
    [0., 1],
    [1., 0],
    [1., 1]
])

y = np.array([
    [0.],
    [1.],
    [1.],
    [0.]
])


neurons = 4
input_dim = x.shape
output_dim = y.shape


hidden_weights = np.random.uniform(size=(neurons, input_dim[1]))
output_weights = np.random.uniform(size=(output_dim[1], neurons))


# print(hidden_weights)
# print(output_weights)

hidden_bias = np.zeros(shape=(neurons, 1))
output_bias = np.zeros(shape=(output_dim[0], 1))

# print(tanh(np.dot(hidden_weights, x.T) + hidden_bias))
# plot_fx(tanh)
# plot_fx(sigmoid)

# * Forward pass
hidden_results = tanh(np.dot(hidden_weights, x.T) + hidden_bias)
prediction = sigmoid(np.dot(output_weights, hidden_results) + output_bias)
print(prediction)
print(softmax(prediction))
