import numpy as np
from scipy.stats import multivariate_normal


class GradientAccent(object):
    def __init__(self, oracle, lr=0.1):
        """
        :param oracle: Oracle function that compute log(value) and a gradient(log(value)) in a given point
        """
        self.oracle = oracle
        self.number_of_steps = 0
        self.lr = lr

    def initialize(self, intialization):
        self.current = intialization

    def update(self):
        value, grad = self.oracle(self.current)
        self.current += self.lr * grad
        self.number_of_steps += 1
        return value


class MetropolisHastingsMCMC(object):
    def __init__(self, oracle, lr=0.1, lr_decay=1):
        self.oracle = oracle
        self.lr = lr
        self.lr_decay = lr_decay
        self.number_of_steps = 0

    def initialize(self, initialization):
        self.current = initialization
        self.current_value = self.oracle(self.current)

    def transition(self):
        return multivariate_normal(mean=self.current, cov=self.lr).rvs(size=(1, ))

    def compute_alpha(self, new, new_value):
        symmetric_part = np.exp(new_value[0] - self.current_value[0])
        return min(1, symmetric_part)

    def update(self):
        accepted = False
#        print self.current_value[1]
        old_lr = self.lr
        while not accepted:
            new = self.transition()
            new_value = self.oracle(new)
            alpha = self.compute_alpha(new, new_value)
            th = np.random.uniform(0, 1)
            self.lr *= self.lr_decay
            if alpha > th:
                accepted = True
                self.current = new
                self.current_value = new_value
            self.number_of_steps += 1
        self.lr = old_lr
        return self.current_value[0]


class LangevinMCMC(MetropolisHastingsMCMC):
    def __init__(self, oracle, lr=0.1, lr_decay=1):
        super(LangevinMCMC, self).__init__(oracle, lr, lr_decay)

    def transition(self):
        noise = multivariate_normal(mean=np.zeros_like(self.current), cov=1).rvs(size=(1, ))
        return self.current + self.lr * self.current_value[1] + np.sqrt(2 * self.lr) * noise

    def proposal_a_given_b(self, a, b, a_value, b_value):
        val = a - b - self.lr * b_value[1]
        return -np.sum(val ** 2)/(4 * self.lr)

    def compute_alpha(self, new, new_value):
        symmetric_part = np.exp(new_value[0] - self.current_value[0])
        assymetric_part = np.exp(self.proposal_a_given_b(self.current, new, self.current_value, new_value) -
                                 self.proposal_a_given_b(new, self.current, new_value, self.current_value))
        return min(1, symmetric_part * assymetric_part)


class HamiltonyanMCMC(MetropolisHastingsMCMC):
    def __init__(self, oracle, lr=0.1, lr_decay=1, L=10):
        super(HamiltonyanMCMC, self).__init__(oracle, lr, lr_decay)
        self.L = L

    def transition(self):
        q = self.current.copy()
        p = np.random.normal(size=self.current.shape)
        current_p = p.copy()
        p += self.lr * self.current_value[1] / 2
        for i in range(self.L):
            q += self.lr * p
            if i != self.L - 1:
                p += self.lr * self.oracle(q)[1]

        new_value = self.oracle(q)
        p += self.lr * new_value[1] / 2

        proposed_u = -new_value[0]
        current_u = -self.current_value[0]
        current_k = np.sum(current_p ** 2) / 2
        proposed_k = np.sum(p ** 2) / 2

        alpha = np.exp(current_u - proposed_u + current_k - proposed_k)

        return q, new_value, alpha

    def update(self):
        accepted = False
        
        old_lr = self.lr
        while not accepted:
            new, new_value,  alpha = self.transition()
            th = np.random.uniform(0, 1)
            self.lr *= self.lr_decay
            if alpha > th:
                accepted = True
                self.current = new
                self.current_value = new_value
            self.number_of_steps += 1
        self.lr = old_lr

        return self.current_value[0]


if __name__ == "__main__":
    from tqdm import tqdm
    oracle = lambda x: (np.log(multivariate_normal(mean=[5, 5], cov=[[1, 0], [0, 1]]).pdf(x)), -(x - 5))
    #log_grad_density = lambda x:
    mcmc = HamiltonyanMCMC(oracle, 0.1, 0.9)

    mcmc.initialize(np.array([50.0, 50.0]))
    values = []

    for i in tqdm(range(1000)):
        mcmc.update()
        next = mcmc.current
        if i > 100:
            values.append(next)

    print (mcmc.number_of_steps)
    import pylab as plt
    plt.subplot(1, 2, 1)
    values = np.array(values)
    print (values.mean(axis=0), values.var(axis=0))
    plt.scatter(values[:, 0], values[:, 1])

    plt.subplot(1, 2, 2)
    vals = multivariate_normal(mean=[5, 5], cov=[[5, 0], [0, 5]]).rvs(size=900)
    print (vals.shape)
    plt.scatter(vals[:, 0], vals[:, 1], color='red')
    plt.show()





