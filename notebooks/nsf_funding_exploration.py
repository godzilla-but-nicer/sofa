#%%
from typing import Tuple
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import powerlaw
import statsmodels.api as sm
from scipy.stats import pearsonr

# load upthe nsf data
nsf = pd.read_csv("../data/nsf/nsf_awards.csv", index_col=0)
# filter grants only
nsf = nsf[nsf["award_type"] == "Grant"].reset_index()
print(nsf.info())

# %% [markdown]
# ## Distribution of monetary value of all NSF grants
# 
# Ultimately we want to look at the total amount of money awarded to
# individuals/states/institutions but first lets just get a sense of what kind
# of spread of award values we have.

#%%
nsf_vals = nsf["award_amount"].dropna().values

vals, counts = np.unique(nsf_vals, return_counts=True)
cdf = np.cumsum(counts) / np.sum(counts)


plt.plot(vals, 1 - cdf)
plt.xscale("log")
plt.yscale("log")
plt.xlabel("Size of Award (USD)")
plt.ylabel("CCDF")
plt.xlim((10**3, 10**10))
plt.show()
# %% [markdown]
# Looks like we have a power law in the tail. It might be informative to know
# what this award is about and to whom it was given.
#%%
nsf_max_idx = nsf.idxmax(numeric_only=True)
print(nsf_max_idx)
nsf_max = nsf.iloc[nsf_max_idx["award_amount"]]

print(f"The largest award between 1999 and 2019 was given to: {nsf_max['institution']}")
print(f"For project {nsf_max['title']}")
print(f"With a value of ${nsf_max['award_amount']}")
print(f"Beginning on {nsf_max['award_start']} and expiring {nsf_max['award_end']}")
# %% [markdown]
# Ok thats a weird one. a ~$140 million/year grant to raytheon?
#
# Let's table this for now and look at the total funds at different scales.
# We'll zoom in to state then institution then individual total funds.
#
# ## Total State Funding
#
# %%
nsf_states = nsf[["award_amount", "state"]]
state_funds = (nsf_states.groupby("state")
                         .sum()
                         .sort_values("award_amount", ascending=False))

plt.scatter(range(state_funds.shape[0]), state_funds, fc="none", ec="black")
plt.xlabel("State Funding Rank")
plt.ylabel("Total Funding (USD)")

# Let's label some of the top and bottom states
arrow_length = 5
vertical_length = 0.25e10
rank = 0
plt.arrow(rank + 6, 1.81e10, -arrow_length, 0, color="grey", length_includes_head=True)
plt.text(rank + 7, 1.81e10, f"{state_funds.index[rank]}", va="center", color="Grey")

rank = 1
plt.arrow(rank, 1.22e10, 0, -vertical_length, color="grey", length_includes_head=True)
plt.text(rank - 1, 1.25e10, f"{state_funds.index[rank]}", ha="left", color="Grey")

rank = 2
plt.arrow(rank + 6, 0.92e10, -arrow_length, 0, color="grey", length_includes_head=True)
plt.text(rank + 7, 0.92e10, f"{state_funds.index[rank]}", va="center", color="Grey")

plt.arrow(57, 0.3e10, 0, -vertical_length, color="grey", length_includes_head=True)
plt.text(58, 0.35e10, f"{state_funds.index[-1]}", ha="right", color="Grey")

plt.arrow(52, 0.20e10, 0, -0.5*vertical_length, color="grey", length_includes_head=True)
plt.text(53, 0.23e10, f"{state_funds.index[-6]}", ha="right", color="Grey")

rank = 22
plt.arrow(rank, 0.45e10, 0, -vertical_length, color="grey", length_includes_head=True)
plt.text(rank, 0.5e10, f"{state_funds.index[rank]}", ha="center", color="Grey")

plt.show()
# %% [markdown]
# Looks pretty imbalanced with the US territories occupying the bottom ranks.
# If we really want to draw conclusions here we probably need to normalize by
# population. California might just get the most money because its the largest
# by population.
#
# ## Funding to Institutions
#%%
nsf_inst = nsf[["institution", "award_amount"]]
inst_funds = (nsf_inst.groupby("institution")
                      .sum()
                      .sort_values("award_amount"))

inst_vals, inst_counts = np.unique(inst_funds["award_amount"], return_counts=True)
inst_cdf = np.cumsum(inst_counts) / np.sum(inst_counts)

logbins = np.logspace(-1, 9.1, 100)

inst_hist, bin_edges = np.histogram(inst_funds["award_amount"], bins=logbins)
bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2
inst_hist = inst_hist / np.sum(inst_hist)

plt.scatter(bin_centers, inst_hist)
plt.xscale("log")
plt.yscale("log")
plt.xlabel("Total Award Collected by Institution (USD)")
plt.ylabel("PDF")
plt.show()

# %% [markdown]
# Roughly lognormal or something? Whatever the distribution we see a wide range
# of total funds per institution but unlike in a power law we see an
# intermediate modal value somewhere between $100,000 and $1 million. Beyond
# this modal value we do have what looks like a power law tail.
# 
# Something else I want to look at at this scale is the autocorrelation 
# between years. I think we can do this with statsmodels time series
# functionality but I want to be sure I'm calculating the right thing so I'll
# do it by hand.
#
#%%
# we need to pull out the year
nsf["dt_award_start"] = pd.to_datetime(nsf["award_start"])
nsf["year"] = nsf["dt_award_start"].dt.year

# ok so we need to get essentially a long dataframe with cols relating one year
# to the following year. start by getting yearly sums for institutions
inst_yearly = nsf[["institution", "year", "award_amount"]]
inst_yearly_funds = (inst_yearly.groupby(["institution", "year"])
                                .sum()
                                .reset_index())

# convert this to wide with yearly sums as columns
inst_wide = pd.pivot(inst_yearly_funds, index="institution", 
                                        columns="year", 
                                        values="award_amount").reset_index()
inst_wide_pairs = inst_wide.copy()[["institution"]]

# now we can collect each year and the year that follows
for year in range(1999, 2020):
    inst_wide_pairs[f"this_year_{year}"] = inst_wide[year]
    inst_wide_pairs[f"next_year_{year}"] = inst_wide[year+1]

# convert to long
inst_pairs = pd.wide_to_long(inst_wide_pairs, stubnames=["this_year_", "next_year_"],
                                              i="institution",
                                              j="award_year")

# filter out missing or otherwise weird entries
inst_pairs = (inst_pairs[(inst_pairs["this_year_"] > 0) &
                         (inst_pairs["next_year_"] > 0)]
                        .dropna(how="any", subset=["this_year_", "next_year_"]))

# let's fit a regression line here as well
log_this_year = np.log(inst_pairs["this_year_"].values)
log_next_year = np.log(inst_pairs["next_year_"].values)

log_this_year = sm.add_constant(log_this_year)
ols_fit = sm.OLS(log_next_year, log_this_year).fit()

y_pred = ols_fit.predict(log_this_year)

# correlation instead. the thinking mans regression
sr = pearsonr(inst_pairs["this_year_"], inst_pairs["next_year_"])

fig, ax = plt.subplots()
ax.plot(np.exp([1, 20]), np.exp([1, 20]), c="C0", ls="--", label="1:1 line")
#ax.plot(np.exp(log_this_year[:, 1]), np.exp(y_pred), c="C1", label="OLS Fit")
ax.scatter(inst_pairs["this_year_"], inst_pairs["next_year_"], fc="none", 
                                                                ec="black",
                                                                s=10,
                                                                label="Institution")

ax.text(10**6, 5, fr"Pearson $\rho$: {sr.statistic:.3f}")
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel(r"Total NSF Awards in year $Y$ (USD)")
ax.set_ylabel(r"Total NSF Awards in year $Y+1$ (USD)")
ax.legend()
plt.show()

# %% [markdown]
# This was a pattern I had expected. The total funding recieved in a given year
# is correlated with the funding recieved in the following year. This means
# that well-funded institutions are likely to continue to be well funded and
# vice versa. It may be interesting to look at bigger lag times to see if the
# pattern holds. For now let's move on to the scale we're mostly concerned with
#
# ## Distribution of total individual funds
#
#%%
# we'll proably look at autocorrelation again
indiv = nsf[["first_name", "last_name", "award_amount"]]
indiv["name"] = (indiv["first_name"].str.cat(indiv["last_name"], sep=" ")
                                    .str.lower())
indiv = indiv[["name", "award_amount"]]

# for the last time we need to groupby and sum
indiv_totals = (indiv.groupby("name")
                     .sum()
                     .reset_index())
indiv_totals["award_plus_one"] = indiv_totals["award_amount"] + 1
logbins = np.logspace(np.log10(indiv_totals["award_amount"].min() + 1), 
                      np.log10(indiv_totals["award_amount"].max() + 1), 
                      60)
indiv_hist, indiv_bins = np.histogram(indiv_totals["award_amount"], bins=logbins)
bin_centers = indiv_bins[:-1] + np.diff(indiv_bins)

fig, ax = plt.subplots()
ax.scatter(bin_centers, indiv_hist)
ax.set_xscale("log")
#ax.set_yscale("log")
plt.show()
# %% [markdown]
# Definitely lognormal. I don't know what to make of that but there it is. We
# typically think of lognormal distributions as the result of multiplicative
# processes. That is, processes in which random variables are multiplied
# together. Here we are adding a random number of variables together. Is this
# multiplicative in a way I am not seeing?
#
# ## Autocorrelation for individual funding
#
# I want to look at this slightly differently. Grants usually last more than a
# single year. For institutions, in any given year many grants will be starting
# and ending. For individuals this is not the case. Most researchers are not
# getting new grants every year. As such we will first look at the
# autocorrelation at various time lags.
# %%
# we need to pull out the year
indiv = nsf[["first_name", "last_name", "year", "award_amount"]]
indiv["name"] = (indiv["first_name"].str.cat(indiv["last_name"], sep=" ")
                                    .str.lower())
indiv = indiv[["name", "year", "award_amount"]]

# same proceedure as with institutions to start
indiv_funds = (indiv.groupby(["name", "year"])
                    .sum()
                    .reset_index())

# convert this to wide with yearly sums as columns
indiv_wide = pd.pivot(indiv_funds, index="name", 
                                   columns="year", 
                                   values="award_amount").reset_index()

# I think a function would be helpful
def autocorrelation(wide_df: pd.DataFrame, lag: int) -> Tuple[float, float]:

    years = wide_df.columns.drop(["name", 1986, 1995, 1997, 1998])
    # lagged_years
    lagged = np.array([])
    current = np.array([])

    for year in range(1999 + lag, years.max() + 1):
        safe_wide = indiv_wide.dropna(how="any", subset=[year - lag, year])
        lagged = np.hstack((lagged, safe_wide[year - lag]))
        current = np.hstack((current, safe_wide[year]))

    res = pearsonr(lagged, current)
    return (res.statistic, res.pvalue)

auto_corrs = []
p_vals = []
total_years = 20
for time_lag in range(total_years):
    corr, pval = autocorrelation(indiv_wide, time_lag)
    auto_corrs.append(corr)
    p_vals.append(pval)

# bonnferroni correction
p_vals_corrected = np.array(p_vals) * (total_years - 1)
significant = p_vals_corrected < 0.05

# plot that shit
fig, ax = plt.subplots()
ax.plot(range(1, total_years), auto_corrs[1:] * significant[1:], marker="s", c="k")
ax.set_xticks(range(1, total_years))
ax.set_xlabel("Lag time (years)")
ax.set_ylabel(r"Pearson $\rho$")
plt.show()

#%% [markdown]
# All correlations are significant but the strongest appear at 6 years and 9
# years. I wonder if this can be explained by the duration of the grants. Let's
# look at the distribution of grant durations.
#%%
# extract the end years
nsf["dt_award_end"] = pd.to_datetime(nsf["award_end"])
nsf["end_year"] = nsf["dt_award_end"].dt.year

# count the frequency of each duration
nsf["duration"] = nsf["end_year"] - nsf["year"]
durations, counts = np.unique(nsf["duration"], return_counts=True)

# plot the distribution and the mean
fig, ax = plt.subplots()
ax.bar(durations, counts, alpha=0.6)
ax.axvline(np.mean(nsf["duration"]), c="k")
ax.text(np.mean(nsf["duration"]), 50000, 
                  f"Mean Duration {np.mean(nsf['duration']):.2} ",
                  ha="right")
ax.set_ylabel("Count")
ax.set_xlabel("Grant Duration")
plt.show()

# %% [markdown]
# This does not exactly explain it! The modal duration is 4 years, the mean is
# between 3 and 4. Perhaps NSF avoids giving overlapping grants by not giving
# them too frequently. This does not really explain why we see such strong
# correlation at a lag time of 6 and 9 years.
# %%
