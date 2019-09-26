import matplotlib.pyplot as plt
import torch
import torchvision
from torchvision import transforms, datasets


train = datasets.MNIST('', train=True, download=True,
                       transform=transforms.Compose([transforms.ToTensor()]))

test = datasets.MNIST('', test=False, download=True,
                      transform=transforms.Compose([transforms.ToTensor()]))


trainset = torch.utils.DataLoader(train, batch_size=10, shuffle=True)

testset = torch.utils.DataLoader(test, batch_size=10, shuffle=True)


for data in trainset:
    print(data)
    break


plt.imshow(data[0][0].view(28, 28))
plt.show()
