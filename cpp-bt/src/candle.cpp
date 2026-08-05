#include "bt/candle.hpp"
#include <cstdio>
#include <cstring>
#include <fstream>
#include <stdexcept>

namespace bt {

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
  return s;
}

}  // namespace bt
