#pragma once
#include <cstdint>
#include <string>
#include <vector>

namespace bt {

struct Candle {
  int64_t ts_ms = 0;
  double open = 0, high = 0, low = 0, close = 0, volume = 0;
};

struct Indicators {
  std::vector<double> rsi;
  std::vector<double> adx;
  std::vector<double> plus_di;
  std::vector<double> minus_di;
  std::vector<double> cloud1;
  std::vector<double> cloud2;
  std::vector<double> cloud_top;
  std::vector<double> cloud_bot;
  std::vector<double> bb_mid;
  std::vector<double> bb_upper;
  std::vector<double> bb_lower;
};

struct Series {
  std::string symbol;
  std::string timeframe;
  std::vector<Candle> bars;
  Indicators ind;   // filled when loaded from .ftind
  bool has_ind = false;
};

// Load .ohlcv packed binary written by tools/export_ohlcv.py
Series load_ohlcv(const std::string& path);

// Load TA-Lib-aligned bundle (.ftind) from tools/export_ftind.py
Series load_ftind(const std::string& path);

}  // namespace bt
