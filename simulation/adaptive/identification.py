"""Offline lecture ARX(2,2) and RLS reference. No plant communications."""
from dataclasses import dataclass, field
import numpy as np

@dataclass
class ARX22:
    y1: float = 0.0
    y2: float = 0.0

    def step(self, u1: float, u2: float, b1: float = 0.1) -> float:
        y = 1.2*self.y1 - 0.36*self.y2 + b1*u1 + 0.06*u2
        self.y2, self.y1 = self.y1, y
        return y

@dataclass
class RLS4:
    forgetting: float = 1.0
    initial_information_inverse: float = 10000.0
    theta: np.ndarray = field(init=False)
    P: np.ndarray = field(init=False)

    def __post_init__(self):
        if not np.isfinite(self.forgetting) or not 0 < self.forgetting <= 1:
            raise ValueError('Forgetting factor must be finite and in (0, 1].')
        if not np.isfinite(self.initial_information_inverse) or self.initial_information_inverse <= 0:
            raise ValueError('Initial diagonal must be finite and positive.')
        self.theta = np.zeros(4)
        self.P = self.initial_information_inverse * np.eye(4)

    def step(self, phi, y):
        phi = np.asarray(phi, dtype=float)
        if phi.shape != (4,) or not np.isfinite(phi).all() or not np.isfinite(y):
            raise ValueError('Expected four finite regressors and a finite output.')
        prediction = float(phi @ self.theta)
        error = float(y-prediction)
        gain = self.P @ phi / (self.forgetting + phi @ self.P @ phi)
        candidate_theta = self.theta + gain*error
        candidate_P = (self.P-np.outer(gain, phi @ self.P))/self.forgetting
        candidate_P = (candidate_P+candidate_P.T)/2
        if not np.isfinite(candidate_theta).all() or not np.isfinite(candidate_P).all():
            raise ArithmeticError('Non-finite estimate; state not updated.')
        self.theta, self.P = candidate_theta, candidate_P
        return prediction, error


def run_experiment(inputs, forgetting=1.0, change=False):
    """inputs[0]=u(0)=0; each row k uses only u(k-1),u(k-2)."""
    plant, estimator = ARX22(), RLS4(forgetting)
    rows = []
    for k in range(1, len(inputs)):
        u1, u2 = inputs[k-1], inputs[k-2] if k >= 2 else 0.0
        phi = np.array([plant.y1, plant.y2, u1, u2])
        b1 = .4 if change and k >= 51 else .1
        y = plant.step(u1, u2, b1)
        prediction,error = estimator.step(phi,y)
        rows.append([k,inputs[k],u1,u2,y,prediction,error,*estimator.theta,b1])
    return np.array(rows),estimator
