import math

class NormalDistribution():
    def __init__(self, mean, std):
        self.mean = float(mean)
        self.std = float(std)
        self.var = float(std) ** 2

    def cdf(self, x):
        return 0.5 * (1 + math.erf((x - self.mean) / math.sqrt(2 * self.std ** 2)))

    def pmf(self, x):
        #return self.cdf(x + 1) - self.cdf(x)
        a = math.exp(-1 * ((x - self.mean) ** 2) / (2 * self.var))
        return (1 / math.sqrt(2 * math.pi * self.var)) * a 

    def log_pmf(self, x):
        #return math.log(self.pmf(x))
        return - ((0.5 * (math.log(2) + math.log(math.pi) + math.log(self.var))) + (((x - self.mean) ** 2) / (2 * self.var)))

class ErrorDistribution():
    def __init__(self, p):
        self.p = p
        self.mean = 0

    def pmf(self, x):
        return self.p ** x

    def log_pmf(self, x):
        return x * math.log(self.p)

def variance(data):
    m = sum(data) / len(data)
    variance = sum((x - m) ** 2 for x in data) / len(data)
    return variance

def std(data):
    return math.sqrt(variance(data))

def mean(data):
    m = sum(data) / len(data)
    return m

def median(data):
    n = len(data)
    return data[n / 2]