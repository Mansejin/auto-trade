#pragma once
#include "bt/indicators.hpp"
#include <cmath>
#include <limits>
#include <vector>

namespace bt {

inline constexpr double NaN = std::numeric_limits<double>::quiet_NaN();
inline bool is_nan(double x) { return std::isnan(x); }

// Wilder RSI (fallback when .ftind not used)
inline std::vector<double> rsi_wilder(const std::vector<Candle>& c, int period) {
  const int n = (int)c.size();
  std::vector<double> out(n, NaN);
  if (n <= period) return out;
  double gain = 0, loss = 0;
  for (int i = 1; i <= period; ++i) {
    double d = c[i].close - c[i - 1].close;
    if (d >= 0) gain += d;
    else loss -= d;
  }
  double ag = gain / period, al = loss / period;
  out[period] = al == 0 ? 100.0 : 100.0 - 100.0 / (1.0 + ag / al);
  for (int i = period + 1; i < n; ++i) {
    double d = c[i].close - c[i - 1].close;
    double g = d > 0 ? d : 0, l = d < 0 ? -d : 0;
    ag = (ag * (period - 1) + g) / period;
    al = (al * (period - 1) + l) / period;
    out[i] = al == 0 ? 100.0 : 100.0 - 100.0 / (1.0 + ag / al);
  }
  return out;
}

inline void dm_tr(const Candle& a, const Candle& b, double& plus_dm, double& minus_dm, double& tr) {
  double up = b.high - a.high;
  double down = a.low - b.low;
  plus_dm = (up > down && up > 0) ? up : 0;
  minus_dm = (down > up && down > 0) ? down : 0;
  tr = std::max(b.high - b.low, std::max(std::abs(b.high - a.close), std::abs(b.low - a.close)));
}

inline void adx_di(const std::vector<Candle>& c, int period,
                   std::vector<double>& adx, std::vector<double>& pdi, std::vector<double>& mdi) {
  const int n = (int)c.size();
  adx.assign(n, NaN);
  pdi.assign(n, NaN);
  mdi.assign(n, NaN);
  if (n <= period * 2) return;

  double atr = 0, p_dm = 0, m_dm = 0;
  for (int i = 1; i <= period; ++i) {
    double pd, md, tr;
    dm_tr(c[i - 1], c[i], pd, md, tr);
    atr += tr;
    p_dm += pd;
    m_dm += md;
  }
  double dx_sum = 0;
  for (int i = period; i < n; ++i) {
    if (i > period) {
      double pd, md, tr;
      dm_tr(c[i - 1], c[i], pd, md, tr);
      atr = atr - atr / period + tr;
      p_dm = p_dm - p_dm / period + pd;
      m_dm = m_dm - m_dm / period + md;
    }
    double plus = atr == 0 ? 0 : 100.0 * p_dm / atr;
    double minus = atr == 0 ? 0 : 100.0 * m_dm / atr;
    pdi[i] = plus;
    mdi[i] = minus;
    double den = plus + minus;
    double dx = den == 0 ? 0 : 100.0 * std::abs(plus - minus) / den;
    if (i < period * 2) {
      dx_sum += dx;
      if (i == period * 2 - 1) adx[i] = dx_sum / period;
    } else {
      adx[i] = (adx[i - 1] * (period - 1) + dx) / period;
    }
  }
}

inline double roll_hh(const std::vector<Candle>& c, int i, int len) {
  double v = c[i].high;
  for (int j = i - len + 1; j < i; ++j) v = std::max(v, c[j].high);
  return v;
}
inline double roll_ll(const std::vector<Candle>& c, int i, int len) {
  double v = c[i].low;
  for (int j = i - len + 1; j < i; ++j) v = std::min(v, c[j].low);
  return v;
}

inline void ichimoku(const std::vector<Candle>& c, Indicators& ind) {
  const int n = (int)c.size();
  ind.cloud1.assign(n, NaN);
  ind.cloud2.assign(n, NaN);
  ind.cloud_top.assign(n, NaN);
  ind.cloud_bot.assign(n, NaN);
  std::vector<double> span1(n, NaN), span2(n, NaN);
  for (int i = 0; i < n; ++i) {
    if (i >= 8) {
      double tenkan = 0.5 * (roll_hh(c, i, 9) + roll_ll(c, i, 9));
      if (i >= 25) {
        double kijun = 0.5 * (roll_hh(c, i, 26) + roll_ll(c, i, 26));
        span1[i] = 0.5 * (tenkan + kijun);
      }
    }
    if (i >= 51) span2[i] = 0.5 * (roll_hh(c, i, 52) + roll_ll(c, i, 52));
  }
  for (int i = 0; i < n; ++i) {
    if (i >= 26 && !is_nan(span1[i - 26])) ind.cloud1[i] = span1[i - 26];
    if (i >= 26 && !is_nan(span2[i - 26])) ind.cloud2[i] = span2[i - 26];
    if (!is_nan(ind.cloud1[i]) && !is_nan(ind.cloud2[i])) {
      ind.cloud_top[i] = std::max(ind.cloud1[i], ind.cloud2[i]);
      ind.cloud_bot[i] = std::min(ind.cloud1[i], ind.cloud2[i]);
    }
  }
}

inline void bollinger(const std::vector<Candle>& c, Indicators& ind, int period = 20, double mult = 2.0) {
  const int n = (int)c.size();
  ind.bb_mid.assign(n, NaN);
  ind.bb_upper.assign(n, NaN);
  ind.bb_lower.assign(n, NaN);
  for (int i = period - 1; i < n; ++i) {
    double sum = 0;
    for (int j = i - period + 1; j <= i; ++j) sum += c[j].close;
    double mid = sum / period;
    double var = 0;
    for (int j = i - period + 1; j <= i; ++j) {
      double d = c[j].close - mid;
      var += d * d;
    }
    double sd = std::sqrt(var / period);
    ind.bb_mid[i] = mid;
    ind.bb_upper[i] = mid + mult * sd;
    ind.bb_lower[i] = mid - mult * sd;
  }
}

inline Indicators compute_indicators(const std::vector<Candle>& c, int rsi_p, int adx_p) {
  Indicators ind;
  ind.rsi = rsi_wilder(c, rsi_p);
  adx_di(c, adx_p, ind.adx, ind.plus_di, ind.minus_di);
  ichimoku(c, ind);
  bollinger(c, ind);
  return ind;
}

// Fill BB on an existing indicator pack (e.g. after .ftind load).
inline void ensure_bb(const std::vector<Candle>& c, Indicators& ind) {
  if (ind.bb_mid.size() == c.size() && !ind.bb_mid.empty() && !is_nan(ind.bb_mid.back())) return;
  bollinger(c, ind);
}

}  // namespace bt
