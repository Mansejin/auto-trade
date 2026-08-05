#include "bt/candle.hpp"
#include "bt/engine.hpp"
#include "bt/indicators.hpp"
#include <nlohmann/json.hpp>

#include <algorithm>
#include <chrono>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace fs = std::filesystem;
using json = nlohmann::json;
using namespace bt;

static int64_t parse_day_ms(const std::string& ymd) {
  // YYYY-MM-DD   UTC midnight ms
  int y = 0, m = 0, d = 0;
  if (std::sscanf(ymd.c_str(), "%d-%d-%d", &y, &m, &d) != 3) return 0;
  // Civil to days since 1970-01-01 (Howard Hinnant)
  y -= m <= 2;
  const int era = (y >= 0 ? y : y - 399) / 400;
  const unsigned yoe = static_cast<unsigned>(y - era * 400);
  const unsigned doy = (153 * (m + (m > 2 ? -3 : 9)) + 2) / 5 + d - 1;
  const unsigned doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
  const int64_t days = static_cast<int64_t>(era) * 146097 + static_cast<int64_t>(doe) - 719468;
  return days * 86400000LL;
}

static int find_ge(const std::vector<Candle>& c, int64_t ts) {
  int lo = 0, hi = (int)c.size();
  while (lo < hi) {
    int mid = (lo + hi) / 2;
    if (c[mid].ts_ms < ts) lo = mid + 1;
    else hi = mid;
  }
  return lo;
}

static StrategyCfg load_strategy(const json& j) {
  StrategyCfg cfg;
  cfg.name = j.value("name", "unnamed");
  cfg.side = (j.value("side", "short") == "long") ? Side::Long : Side::Short;
  cfg.fee = j.value("fee", 0.0006);
  cfg.startup = j.value("startup", 80);
  const auto& e = j.at("entry");
  cfg.mode = parse_mode(e.value("mode", "di_only"));
  cfg.rsi_period = e.value("rsi_period", 14);
  cfg.adx_period = e.value("adx_period", 14);
  cfg.adx_min = e.value("adx_min", 25.0);
  cfg.rsi_max = e.value("rsi_max", 55.0);
  const auto& x = j.at("exit");
  cfg.exit.stoploss = x.value("stoploss", -0.01);
  cfg.exit.take_profit = x.value("take_profit", 0.03);
  cfg.exit.trailing = x.value("trailing", false);
  cfg.exit.trail_pos = x.value("trail_pos", 0.0);
  cfg.exit.trail_offset = x.value("trail_offset", 0.0);
  return cfg;
}

static json read_json(const fs::path& p) {
  std::ifstream in(p);
  if (!in) throw std::runtime_error("cannot open " + p.string());
  json j;
  in >> j;
  return j;
}

static std::string tag_of(EntryMode mode, double adx, double rsi, const ExitCfg& x) {
  std::ostringstream os;
  os << mode_str(mode) << "_adx" << (int)adx << "_rsi" << (int)rsi << "_sl" << std::abs(x.stoploss)
     << "_tp" << x.take_profit;
  if (x.trailing) os << "_tr" << x.trail_pos << "_" << x.trail_offset;
  else os << "_notrail";
  std::string s = os.str();
  for (char& ch : s)
    if (ch == '.') ch = 'p';
  return s;
}

static int cmd_run(const fs::path& root, const fs::path& strat_path, const fs::path& data_dir,
                   const std::string& start, const std::string& end) {
  auto sj = read_json(strat_path);
  auto cfg = load_strategy(sj);
  auto symbols = sj.at("symbols").get<std::vector<std::string>>();
  auto tf = sj.value("timeframe", "5m");
  if (symbols.empty()) throw std::runtime_error("no symbols");

  auto series = load_ohlcv((data_dir / (symbols[0] + "-" + tf + ".ohlcv")).string());
  series.symbol = symbols[0];
  series.timeframe = tf;
  auto ind = compute_indicators(series.bars, cfg.rsi_period, cfg.adx_period);
  auto sig = entry_signals(series.bars, ind, cfg);
  int i0 = start.empty() ? 0 : find_ge(series.bars, parse_day_ms(start));
  int i1 = end.empty() ? (int)series.bars.size() : find_ge(series.bars, parse_day_ms(end));
  if (cfg.side != Side::Short) {
    std::cerr << "long not implemented yet\n";
    return 2;
  }
  auto r = simulate_short(series.bars, sig, cfg.exit, cfg.fee, i0, i1);
  std::printf("trades=%d pf=%.4f pnl_pct_sum=%.2f window=[%d,%d)\n", r.trades, r.profit_factor,
              r.sum_pnl_pct, i0, i1);
  return 0;
}

static int cmd_grid(const fs::path& root, const fs::path& grid_path, const fs::path& data_dir) {
  auto gj = read_json(grid_path);
  fs::path base_rel = gj.at("base_strategy").get<std::string>();
  fs::path base_path = grid_path.parent_path() / base_rel;
  if (!fs::exists(base_path)) base_path = root / base_rel;
  if (!fs::exists(base_path)) base_path = root / "cpp-bt" / base_rel;
  if (!fs::exists(base_path)) base_path = grid_path.parent_path().parent_path() / base_rel;
  auto sj = read_json(base_path);
  auto base = load_strategy(sj);
  auto symbols = sj.at("symbols").get<std::vector<std::string>>();
  auto tf = sj.value("timeframe", "5m");

  auto series = load_ohlcv((data_dir / (symbols[0] + "-" + tf + ".ohlcv")).string());
  auto ind = compute_indicators(series.bars, base.rsi_period, base.adx_period);

  struct Win {
    std::string name;
    int i0, i1;
  };
  std::vector<Win> wins;
  for (auto& w : gj.at("windows")) {
    Win ww;
    ww.name = w.at("name");
    ww.i0 = find_ge(series.bars, parse_day_ms(w.at("start")));
    ww.i1 = find_ge(series.bars, parse_day_ms(w.at("end")));
    wins.push_back(ww);
  }

  std::vector<EntryMode> modes;
  for (auto& m : gj.at("entry_modes")) modes.push_back(parse_mode(m.get<std::string>()));
  auto adxs = gj.at("adx_min").get<std::vector<double>>();
  auto rsis = gj.at("rsi_max").get<std::vector<double>>();

  struct ExitVar {
    ExitCfg cfg;
  };
  std::vector<ExitVar> exits;
  for (auto& e : gj.at("exits")) {
    for (auto& t : gj.at("trailing")) {
      ExitCfg x;
      x.stoploss = e.at("stoploss");
      x.take_profit = e.at("take_profit");
      x.trailing = t.value("enabled", false);
      x.trail_pos = t.value("trail_pos", 0.0);
      x.trail_offset = t.value("trail_offset", 0.0);
      exits.push_back({x});
    }
  }

  const double min_pf = gj.at("criteria").value("min_pf", 1.2);
  const int min_tr = gj.at("criteria").value("min_trades", 20);

  struct Row {
    std::string tag;
    double min_pf_obs = 0;
    json detail;
  };
  std::vector<Row> rows;
  int hits = 0;
  int combos = 0;

  auto t0 = std::chrono::steady_clock::now();

  for (auto mode : modes) {
    for (double adx : adxs) {
      if (mode == EntryMode::CloudBreak && adx != adxs[adxs.size() / 2]) continue;  // one adx
      const auto& rsi_list = (mode == EntryMode::DiOnly) ? rsis : std::vector<double>{55.0};
      for (double rsi : rsi_list) {
        StrategyCfg cfg = base;
        cfg.mode = mode;
        cfg.adx_min = adx;
        cfg.rsi_max = rsi;
        auto sig = entry_signals(series.bars, ind, cfg);
        for (auto& ev : exits) {
          ++combos;
          json wj = json::object();
          bool ok = true;
          double minpf = 1e9;
          for (auto& w : wins) {
            auto r = simulate_short(series.bars, sig, ev.cfg, cfg.fee, w.i0, w.i1);
            wj[w.name] = {{"trades", r.trades},
                          {"profit_factor", r.profit_factor},
                          {"profit_pct", r.sum_pnl_pct}};
            if (r.trades < min_tr || r.profit_factor < min_pf) ok = false;
            minpf = std::min(minpf, r.profit_factor);
          }
          auto tag = tag_of(mode, adx, rsi, ev.cfg);
          rows.push_back({tag, minpf, {{"tag", tag},
                                       {"mode", mode_str(mode)},
                                       {"adx_min", adx},
                                       {"rsi_max", rsi},
                                       {"exit",
                                        {{"stoploss", ev.cfg.stoploss},
                                         {"take_profit", ev.cfg.take_profit},
                                         {"trailing", ev.cfg.trailing},
                                         {"trail_pos", ev.cfg.trail_pos},
                                         {"trail_offset", ev.cfg.trail_offset}}},
                                       {"windows", wj},
                                       {"hit", ok}}});
          if (ok) {
            ++hits;
            std::printf("*** HIT %s\n", tag.c_str());
          }
        }
      }
    }
  }

  auto ms = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t0).count();
  std::sort(rows.begin(), rows.end(),
            [](const Row& a, const Row& b) { return a.min_pf_obs > b.min_pf_obs; });

  json summary;
  summary["criteria"] = gj.at("criteria");
  summary["combos"] = combos;
  summary["hits"] = json::array();
  summary["elapsed_ms"] = ms;
  summary["engine"] = "cpp-bt";
  for (auto& r : rows)
    if (r.detail["hit"] == true) summary["hits"].push_back(r.detail);
  summary["top20"] = json::array();
  for (int i = 0; i < (int)rows.size() && i < 20; ++i) summary["top20"].push_back(rows[i].detail);

  fs::path out_dir = root / "reports";
  fs::create_directories(out_dir);
  std::string out_name = "trend-short-grid-summary.json";
  if (grid_path.has_stem()) out_name = grid_path.stem().string() + "-summary.json";
  fs::path out = out_dir / out_name;
  std::ofstream(out) << summary.dump(2);
  std::printf("combos=%d hits=%d elapsed_ms=%.1f best=%s\n", combos, hits, ms,
              rows.empty() ? "-" : rows[0].tag.c_str());
  std::printf("wrote %s\n", out.string().c_str());
  return 0;
}

static void usage() {
  std::cerr << "cpp-bt run  --strategy FILE --data DIR [--start YYYY-MM-DD --end YYYY-MM-DD]\n"
            << "cpp-bt grid --grid FILE --data DIR\n";
}

int main(int argc, char** argv) {
  try {
    if (argc < 2) {
      usage();
      return 1;
    }
    std::string cmd = argv[1];
    fs::path strategy, grid, data = "data";
    std::string start, end;
    for (int i = 2; i < argc; ++i) {
      std::string a = argv[i];
      auto need = [&](const char* flag) -> std::string {
        if (a == flag) {
          if (i + 1 >= argc) throw std::runtime_error(std::string("missing value for ") + flag);
          return argv[++i];
        }
        return {};
      };
      if (auto v = need("--strategy"); !v.empty()) strategy = v;
      else if (auto v = need("--grid"); !v.empty()) grid = v;
      else if (auto v = need("--data"); !v.empty()) data = v;
      else if (auto v = need("--start"); !v.empty()) start = v;
      else if (auto v = need("--end"); !v.empty()) end = v;
      else throw std::runtime_error("unknown arg " + a);
    }
    fs::path root = fs::current_path();
    if (cmd == "run") return cmd_run(root, strategy, data, start, end);
    if (cmd == "grid") return cmd_grid(root, grid, data);
    usage();
    return 1;
  } catch (const std::exception& ex) {
    std::cerr << "error: " << ex.what() << "\n";
    return 1;
  }
}
