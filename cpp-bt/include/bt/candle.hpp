#pragma once
#include <cstdint>
#include <string>
#include <vector>

namespace bt {

struct Candle {
  int64_t ts_ms = 0;
  double open = 0, high = 0, low = 0, close = 0, volume = 0;
};

struct Series {
  std::string symbol;
  std::string timeframe;
  std::vector<Candle> bars;
};

// Load .ohlcv packed binary written by tools/export_ohlcv.py
Series load_ohlcv(const std::string& path);

}  // namespace bt
