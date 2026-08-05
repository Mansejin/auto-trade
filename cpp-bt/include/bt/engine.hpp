#pragma once
#include "bt/candle.hpp"
#include "bt/indicators.hpp"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <string>
#include <vector>

namespace bt {

enum class Side { Long, Short };
enum class EntryMode { CloudBreak, DiCloud, DiOnly };

struct ExitCfg {
  double stoploss = -0.01;     // negative fraction, e.g. -0.02
  double take_profit = 0.03;   // positive fraction
  bool trailing = false;
  double trail_pos = 0.0;
  double trail_offset = 0.0;
};

struct StrategyCfg {
  std::string name;
  Side side = Side::Short;
  double fee = 0.0006;
  int startup = 80;
  EntryMode mode = EntryMode::DiOnly;
  int rsi_period = 14;
  int adx_period = 14;
  double adx_min = 25;
  double rsi_max = 55;
  ExitCfg exit;
};

struct SimResult {
  int trades = 0;
  double profit_factor = 0;  // 0 if no losses
  double sum_pnl_pct = 0;   // sum of per-trade net ratios * 100
  double win_abs = 0;
  double loss_abs = 0;
};

inline EntryMode parse_mode(const std::string& s) {
  if (s == "cloud_break") return EntryMode::CloudBreak;
  if (s == "di_cloud") return EntryMode::DiCloud;
  return EntryMode::DiOnly;
}

inline const char* mode_str(EntryMode m) {
  switch (m) {
    case EntryMode::CloudBreak: return "cloud_break";
    case EntryMode::DiCloud: return "di_cloud";
    default: return "di_only";
  }
}

inline std::vector<uint8_t> entry_signals(const std::vector<Candle>& c, const Indicators& ind,
                                          const StrategyCfg& cfg) {
  const int n = (int)c.size();
  std::vector<uint8_t> sig(n, 0);
  for (int i = 1; i < n; ++i) {
    if (i < cfg.startup) continue;
    if (is_nan(ind.cloud1[i]) || c[i].volume <= 0) continue;
    bool ok = false;
    switch (cfg.mode) {
      case EntryMode::CloudBreak:
        ok = !is_nan(ind.cloud_top[i - 1]) && !is_nan(ind.cloud_bot[i]) &&
             c[i - 1].close >= ind.cloud_top[i - 1] && c[i].close < ind.cloud_bot[i];
        break;
      case EntryMode::DiCloud:
        ok = !is_nan(ind.minus_di[i]) && !is_nan(ind.plus_di[i]) && !is_nan(ind.adx[i]) &&
             ind.minus_di[i] > ind.plus_di[i] && ind.adx[i] >= cfg.adx_min &&
             c[i].close < ind.cloud1[i] && c[i].close < ind.cloud2[i];
        break;
      case EntryMode::DiOnly:
        ok = !is_nan(ind.minus_di[i]) && !is_nan(ind.rsi[i]) && !is_nan(ind.adx[i]) &&
             ind.minus_di[i] > ind.plus_di[i] && ind.adx[i] >= cfg.adx_min &&
             ind.rsi[i] < cfg.rsi_max;
        break;
    }
    sig[i] = ok ? 1 : 0;
  }
  return sig;
}

// True short simulation. Signal on bar i (closed)   enter at open[i+1].
// Fee charged both sides. Pessimistic if SL and TP both hit same bar: SL first.
inline SimResult simulate_short(const std::vector<Candle>& c, const std::vector<uint8_t>& sig,
                                const ExitCfg& ex, double fee, int i0, int i1) {
  SimResult r;
  const int n = (int)c.size();
  i0 = std::max(0, i0);
  i1 = std::min(n, i1);
  int i = i0;
  while (i + 1 < i1) {
    if (!sig[i]) {
      ++i;
      continue;
    }
    const int entry_i = i + 1;
    if (entry_i >= i1) break;
    const double entry = c[entry_i].open;
    const double sl_px = entry * (1.0 + std::abs(ex.stoploss));
    const double tp_px = entry * (1.0 - ex.take_profit);
    double trail_stop = sl_px;
    bool armed = false;
    int j = entry_i;
    double exit_px = c[i1 - 1].close;
    bool closed = false;
    for (; j < i1; ++j) {
      const auto& b = c[j];
      if (ex.trailing) {
        const double fav = (entry - b.low) / entry;
        if (!armed && fav >= ex.trail_offset) armed = true;
        if (armed) {
          const double candidate = b.low * (1.0 + ex.trail_pos);
          if (candidate < trail_stop) trail_stop = candidate;
        }
      }
      const double stop = (ex.trailing && armed) ? trail_stop : sl_px;
      const bool hit_sl = b.high >= stop;
      const bool hit_tp = !ex.trailing && b.low <= tp_px;
      if (hit_sl && hit_tp) {
        exit_px = stop;  // pessimistic
        closed = true;
        break;
      }
      if (hit_sl) {
        exit_px = stop;
        closed = true;
        break;
      }
      if (hit_tp) {
        exit_px = tp_px;
        closed = true;
        break;
      }
    }
    if (!closed) {
      // force flat at window end
      exit_px = c[i1 - 1].close;
      j = i1 - 1;
    }
    // short pnl ratio before fee
    double gross = (entry - exit_px) / entry;
    double net = gross - 2.0 * fee;
    r.trades++;
    r.sum_pnl_pct += net * 100.0;
    if (net >= 0) r.win_abs += net;
    else r.loss_abs += -net;
    i = j + 1;  // next search starts after exit bar (matches skip_exit_bar reference)
  }
  if (r.loss_abs > 0) r.profit_factor = r.win_abs / r.loss_abs;
  else r.profit_factor = r.trades > 0 ? 99.0 : 0.0;
  return r;
}

}  // namespace bt
