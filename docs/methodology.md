# Quantitative Methodology

## 1. Overview

This document describes the quantitative methods used by the Cross-Asset Market Risk Dashboard and MarketMate.

The application uses historical financial market data to calculate asset returns, volatility, drawdowns, correlations, and stress-regime statistics.

All numerical calculations are performed using Python and its data-analysis libraries. The LLM is used to interpret user requests and communicate analytical results; it is not responsible for independently calculating financial metrics.

## 2. Data Preparation

### 2.1 Historical Price Data

Historical daily prices are retrieved from the LSEG Data API using the instrument's Reuters Instrument Code (RIC).

For multi-asset analysis, the individual price series are combined into a single pandas DataFrame.

Let:

\[
P_{i,t}
\]

denote the observed price of instrument \(i\) at time \(t\).

The aligned price dataset contains observation dates as rows and financial instruments as columns.

### 2.2 Date Alignment and Missing Observations

Different instruments may have different trading calendars or missing observations.

The historical data preparation process aligns the individual price series by date. Missing observations are retained rather than automatically forward-filled.

This avoids introducing artificial price observations into the dataset.

Consequently, the number of available observations may differ across instruments and instrument pairs.

### 2.3 Differences in Missing-Price Treatment

Missing-price treatment differs between the dashboard and multi-asset historical analysis.

The dashboard's `calculate_metrics()` function removes missing price observations before calculating returns. Consequently, returns are calculated between consecutive valid price observations.

The multi-asset `calculate_daily_returns()` function retains missing observations and uses `pct_change(fill_method=None)`. A return is therefore unavailable when the current or immediately preceding aligned row contains a missing price.

This distinction is important when comparing results from the two analytical components, as their return series may differ when the underlying dataset contains missing observations.

## 3. Daily Returns

Daily percentage returns are calculated from consecutive available prices.

For instrument \(i\), the return at time \(t\) is:

\[
R_{i,t} = \frac{P_{i,t}}{P_{i,t-1}} - 1
\]

where:

- \(P_{i,t}\) is the current observed price.
- \(P_{i,t-1}\) is the previous available observed price.
- \(R_{i,t}\) is the resulting daily percentage return.

Returns are calculated using consecutive rows in the aligned price DataFrame. Missing prices are not automatically forward-filled (`fill_method=None`), so a return is not calculated when either the current or immediately preceding row contains a missing price for that instrument.

Infinite return values are subsequently replaced with missing values.

## 4. Volatility Analysis

### 4.1 Daily Volatility

Volatility measures the dispersion of returns around their mean.

For a sample of \(n\) daily returns, sample standard deviation is:

\[
\sigma_d =
\sqrt{
\frac{1}{n-1}
\sum_{t=1}^{n}(R_t-\bar R)^2
}
\]

where \(\bar R\) is the average daily return.

### 4.2 Annualized Volatility

Daily volatility is annualized using the conventional assumption of 252 trading days per year:

\[
\sigma_{\text{annual}} =
\sigma_d \sqrt{252}
\]

This allows volatility estimates to be expressed on a comparable annual basis.

The calculation assumes that daily returns are sufficiently well-behaved for the square-root-of-time scaling convention to be useful. It should not be interpreted as a guarantee that volatility remains constant throughout the year.

### 4.3 Rolling Volatility

The application implements rolling volatility in two contexts:

- **Dashboard:** Uses a rolling window of 20 daily return observations.
- **Historical cross-asset analysis:** Uses a configurable rolling window, with a default of 21 observations.

Both implementations calculate sample standard deviation and annualize it using the square root of 252 trading days.

A rolling volatility observation is produced only when the complete rolling window contains sufficient valid observations. In the historical analysis implementation, `min_periods` is explicitly set equal to the window length.

## 5. Drawdown Analysis

Drawdown measures the decline in an asset's cumulative value relative to its previous peak.

### 5.1 Wealth Index

Starting from an initial value of 1, the cumulative wealth index is:

\[
W_t = \prod_{j=1}^{t}(1+R_j)
\]

### 5.2 Running Peak

The running peak represents the highest cumulative value observed up to time \(t\):

\[
H_t = \max(1,W_1,\ldots,W_t)
\]

Including the initial value of 1 ensures that the running peak does not fall below the initial investment value.

### 5.3 Drawdown

Drawdown at time \(t\) is:

\[
D_t = \frac{W_t}{H_t}-1
\]

Drawdowns are non-positive under this convention.

### 5.4 Maximum Drawdown

Maximum drawdown is the most negative drawdown observed over the selected period:

\[
MDD = \min_t(D_t)
\]

It represents the largest peak-to-trough decline in cumulative value during the observation period.

Maximum drawdown is a historical measure and does not indicate the maximum loss that could occur in the future.

## 6. Correlation Analysis

### 6.1 Pearson Correlation

The application uses Pearson correlation to measure the linear relationship between pairs of asset returns.

For two return series \(X\) and \(Y\):

\[
\rho_{X,Y} =
\frac{\operatorname{Cov}(X,Y)}
{\sigma_X\sigma_Y}
\]

The correlation coefficient lies between -1 and +1.

| Correlation | Interpretation |
|---|---|
| +1 | Perfect positive linear relationship |
| 0 | No linear correlation |
| -1 | Perfect negative linear relationship |

A positive correlation indicates that the two return series tend to move in the same direction, while a negative correlation indicates that they tend to move in opposite directions.

Correlation does not establish causation and does not necessarily capture nonlinear relationships.

### 6.2 Pairwise Observations

Missing values are handled using available paired observations for each instrument pair.

A minimum-observation requirement is used to avoid calculating correlations from excessively small samples.

Because different pairs may have different sets of available observations, the resulting correlation matrix may not necessarily be positive semidefinite.

## 7. Stress-Regime Analysis

### 7.1 Identifying Stress Periods

The application identifies periods of elevated market volatility using a percentile threshold applied to rolling volatility.

Let \(\sigma_t\) denote the rolling volatility series.

For a selected percentile \(q\), the threshold is:

\[
T_q = Q_q(\sigma)
\]

where \(Q_q\) represents the corresponding sample quantile.

An observation is classified as a stress observation when:

\[
\sigma_t > T_q
\]

The stress threshold is calculated as the selected percentile of all valid observations in the supplied rolling-volatility series.

For the default percentile of 0.90, the threshold corresponds to the 90th percentile of the historical rolling-volatility distribution.

Observations strictly greater than this threshold are classified as stress observations. Observations equal to or below the threshold are classified as non-stress observations.

Because the threshold is estimated using the entire supplied sample, this approach is retrospective and may introduce look-ahead bias if used directly in a predictive backtesting strategy.

### 7.2 Regime Classification

Observations are divided into two groups:

- **Stress regime:** Observations for which rolling volatility exceeds the selected threshold.
- **Non-stress regime:** Remaining observations.

This classification allows the application to compare return behaviour under different historical volatility conditions.

### 7.3 Regime Statistics

The application calculates descriptive statistics separately for stress and non-stress observations.

These statistics can be used to examine differences in:

- Average returns.
- Return volatility.
- Number of observations.
- Other implemented regime-level measures.

The results help characterize how asset behaviour changes during periods of elevated market volatility.

## 8. Conditional Correlations

Conditional correlation analysis examines whether the relationship between two instruments changes across volatility regimes.

For instruments \(X\) and \(Y\), the application calculates:

\[
\rho_{\text{stress}} =
\operatorname{Corr}(X,Y \mid \text{Stress})
\]

and:

\[
\rho_{\text{non-stress}} =
\operatorname{Corr}(X,Y \mid \text{Non-stress})
\]

The difference between these estimates is:

\[
\Delta \rho =
\rho_{\text{stress}} -
\rho_{\text{non-stress}}
\]

A positive difference indicates a higher estimated correlation during stress observations, while a negative difference indicates a lower estimated correlation.

These estimates can provide insight into changing cross-asset relationships during volatile periods.

However, conditional correlations are sensitive to sample size. Stress observations may represent only a small fraction of the total dataset, resulting in less stable estimates.

A minimum-observation requirement is therefore applied before reporting conditional correlations.

The default minimum-observation requirement for conditional correlations is 30 paired observations per instrument pair and regime. Correlations are calculated independently for the stress and non-stress subsets.

The observation-count matrices are returned alongside the correlation matrices, allowing the reliability of individual pairwise estimates to be assessed in relation to their sample sizes.

## 9. Statistical Assumptions and Limitations

The quantitative methods used in this project have several important limitations.

### 9.1 Historical Dependence

The calculations are based on historical observations. Past return distributions, volatility levels, and correlations may not persist in the future.

### 9.2 Annualization Convention

Annualized volatility uses 252 trading days per year. This is a conventional approximation rather than an exact representation of every instrument's trading calendar.

### 9.3 Missing Data

Different instruments may have different observation calendars. Pairwise correlation calculations can therefore use different sample periods for different instrument pairs.

### 9.4 Correlation Limitations

Pearson correlation measures linear dependence and may fail to capture nonlinear or tail-dependent relationships.

### 9.5 Stress-Regime Sensitivity

Stress classification depends on the selected rolling window, percentile threshold, and historical sample.

Changing these parameters can materially alter which observations are classified as stress periods.

### 9.6 Retrospective Classification

The stress threshold is estimated from the selected historical volatility sample. Consequently, the classification is descriptive and retrospective rather than a real-time predictive signal.

For predictive backtesting, regime classification would need to avoid using information from future observations when estimating thresholds.

### 9.7 Sample Size

Conditional statistics calculated from small samples may be unstable. Results should therefore be interpreted alongside the number of observations used in each regime.

## 10. Interpretation

The dashboard and MarketMate provide complementary views of historical market risk.

The dashboard presents individual-instrument metrics, while MarketMate extends the analysis to multi-asset comparisons, correlations, and stress-regime behaviour.

Together, these capabilities provide a framework for exploring historical risk characteristics and cross-asset relationships.

The outputs are intended for educational and analytical purposes and should not be interpreted as investment advice or guaranteed predictions of future market behaviour.