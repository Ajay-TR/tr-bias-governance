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

def anova_bias(col1, col2):
    res = f_oneway(col1.tolist(),col2.tolist())
    print("H0 Accepted") if res.pvalue > 0.05 else print("H0 Rejected")
    
def demographic_parity(col1, col2,threshold):
    ratio1 = sum(col1) / len(col1)
    ratio2 = sum(col2) / len(col2)
    print("Bias exists") if(abs(ratio1-ratio2) > threshold) else print("No bias")


