import numpy as np
from scipy.stats import chisquare

def standard_deviation_ratio(scores, groups):
    std_dev_group_A = np.std(scores[groups[0]])
    std_dev_group_B = np.std(scores[groups[1]])
    return std_dev_group_A / std_dev_group_B

def standard_deviation_disparity(scores, groups):
    std_dev_group_A = np.std(scores[groups[0]])
    std_dev_group_B = np.std(scores[groups[1]])
    std_dev_overall = np.std(scores)
    return (std_dev_group_A - std_dev_group_B) / std_dev_overall


def equal_opportunity(true_positives, total_positives):
    return true_positives / total_positives


def chi2_test(observed, alpha=0.05):
    expected = [sum(observed) / len(observed)] * 6
    chi2, p = chisquare(observed, f_exp=expected)
    return p < alpha

