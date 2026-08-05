#include "bt/candle.hpp"
#include <cmath>
#include <cstring>
#include <fstream>
#include <limits>
#include <stdexcept>

namespace bt {

static void fill_cloud_extremes(Indicators& ind) {
  const size_t n = ind.cloud1.size();
  ind.cloud_top.resize(n);
  ind.cloud_bot.resize(n);
  for (size_t i = 0; i < n; ++i) {
    if (std::isnan(ind.cloud1[i]) || std::isnan(ind.cloud2[i])) {
      ind.cloud_top[i] = ind.cloud_bot[i] = std::numeric_limits<double>::quiet_NaN();
    } else {
      ind.cloud_top[i] = std::max(ind.cloud1[i], ind.cloud2[i]);
      ind.cloud_bot[i] = std::min(ind.cloud1[i], ind.cloud2[i]);
    }
  }
}

Series load_ohlcv(const std::string& path) {
  std::ifstream in(path, std::ios::binary);
  if (!in) throw std::runtime_error("cannot open " + path);
  char magic[8];
  in.read(magic, 8);
  if (std::memcmp(magic, "OHLCV001", 8) != 0) throw std::runtime_error("bad magic: " + path);
  uint64_t n = 0;
  in.read(reinterpret_cast<char*>(&n), sizeof(n));
  Series s;
  s.bars.resize(static_cast<size_t>(n));
  for (uint64_t i = 0; i < n; ++i) {
    Candle& c = s.bars[static_cast<size_t>(i)];
    in.read(reinterpret_cast<char*>(&c.ts_ms), sizeof(c.ts_ms));
    in.read(reinterpret_cast<char*>(&c.open), sizeof(double));
    in.read(reinterpret_cast<char*>(&c.high), sizeof(double));
    in.read(reinterpret_cast<char*>(&c.low), sizeof(double));
    in.read(reinterpret_cast<char*>(&c.close), sizeof(double));
    in.read(reinterpret_cast<char*>(&c.volume), sizeof(double));
  }
  if (!in) throw std::runtime_error("truncated read: " + path);
  s.has_ind = false;
  return s;
}

Series load_ftind(const std::string& path) {
  std::ifstream in(path, std::ios::binary);
  if (!in) throw std::runtime_error("cannot open " + path);
  char magic[8];
  in.read(magic, 8);
  if (std::memcmp(magic, "FTIND001", 8) != 0) throw std::runtime_error("bad magic: " + path);
  uint64_t n = 0;
  in.read(reinterpret_cast<char*>(&n), sizeof(n));
  Series s;
  s.bars.resize(static_cast<size_t>(n));
  s.ind.rsi.resize(static_cast<size_t>(n));
  s.ind.adx.resize(static_cast<size_t>(n));
  s.ind.plus_di.resize(static_cast<size_t>(n));
  s.ind.minus_di.resize(static_cast<size_t>(n));
  s.ind.cloud1.resize(static_cast<size_t>(n));
  s.ind.cloud2.resize(static_cast<size_t>(n));
  for (uint64_t i = 0; i < n; ++i) {
    const size_t k = static_cast<size_t>(i);
    Candle& c = s.bars[k];
    in.read(reinterpret_cast<char*>(&c.ts_ms), sizeof(c.ts_ms));
    in.read(reinterpret_cast<char*>(&c.open), sizeof(double));
    in.read(reinterpret_cast<char*>(&c.high), sizeof(double));
    in.read(reinterpret_cast<char*>(&c.low), sizeof(double));
    in.read(reinterpret_cast<char*>(&c.close), sizeof(double));
    in.read(reinterpret_cast<char*>(&c.volume), sizeof(double));
    in.read(reinterpret_cast<char*>(&s.ind.rsi[k]), sizeof(double));
    in.read(reinterpret_cast<char*>(&s.ind.adx[k]), sizeof(double));
    in.read(reinterpret_cast<char*>(&s.ind.plus_di[k]), sizeof(double));
    in.read(reinterpret_cast<char*>(&s.ind.minus_di[k]), sizeof(double));
    in.read(reinterpret_cast<char*>(&s.ind.cloud1[k]), sizeof(double));
    in.read(reinterpret_cast<char*>(&s.ind.cloud2[k]), sizeof(double));
  }
  if (!in) throw std::runtime_error("truncated read: " + path);
  fill_cloud_extremes(s.ind);
  s.has_ind = true;
  return s;
}

}  // namespace bt
