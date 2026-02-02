#include <algorithm>
#include <cmath>
#include <ctime>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <omp.h>
#include <sstream>
#include <string>
#include <vector>

// --- Data Structures ---

struct Tick {
  std::time_t time;
  double price;
};

struct DailyBar {
  std::time_t date; // Midnight timestamp
  double open;
  double close;
};

struct CycleMetrics {
  std::vector<double> gains;
  // Hold times etc can be added if needed
};

struct SimulationResult {
  int fast_window;
  int slow_window;
  double cagr;
  int numOrders;
  CycleMetrics metrics;
};

// --- Helpers ---

std::time_t parseDate(const std::string &dateStr, const std::string &timeStr) {
  std::tm tm = {};
  std::stringstream ss(dateStr + " " + timeStr);
  char delimiter;
  int month, day, year, hour, minute;
  ss >> month >> delimiter >> day >> delimiter >> year >> hour >> delimiter >>
      minute;

  tm.tm_year = year - 1900;
  tm.tm_mon = month - 1;
  tm.tm_mday = day;
  tm.tm_hour = hour;
  tm.tm_min = minute;
  tm.tm_sec = 0;
  tm.tm_isdst = -1;

  return std::mktime(&tm);
}

std::time_t getMidnight(std::time_t t) {
  std::tm *tm = std::localtime(&t);
  tm->tm_hour = 0;
  tm->tm_min = 0;
  tm->tm_sec = 0;
  return std::mktime(tm);
}

double getDaysDiff(std::time_t t1, std::time_t t2) {
  return std::difftime(t2, t1) / (60.0 * 60.0 * 24.0);
}

// --- CSV Processing ---

class CSVReader {
public:
  static std::vector<Tick> readCSV(const std::string &filename) {
    std::vector<Tick> data;
    std::ifstream file(filename);
    std::string line;

    if (!file.is_open()) {
      std::cerr << "Error: Could not open file " << filename << std::endl;
      return data;
    }

    size_t discardedCount = 0;
    while (std::getline(file, line)) {
      std::stringstream ss(line);
      std::string dateStr, timeStr, priceStr;

      if (!std::getline(ss, dateStr, ','))
        continue;
      if (!std::getline(ss, timeStr, ','))
        continue;
      if (!std::getline(ss, priceStr, ','))
        continue;

      // Filter Market Hours (09:30 - 16:00)
      try {
        int hour = 0;
        int minute = 0;
        size_t colonPos = timeStr.find(':');
        if (colonPos != std::string::npos) {
          hour = std::stoi(timeStr.substr(0, colonPos));
          minute = std::stoi(timeStr.substr(colonPos + 1));
        }

        int totalMinutes = hour * 60 + minute;
        if (totalMinutes < 570 || totalMinutes > 960) {
          discardedCount++;
          continue;
        }
      } catch (...) {
        continue;
      }

      try {
        double price = std::stod(priceStr);
        std::time_t time = parseDate(dateStr, timeStr);
        if (time != -1) {
          data.push_back({time, price});
        }
      } catch (...) {
        continue;
      }
    }

    if (discardedCount > 0) {
      std::cout << "Discarded " << discardedCount
                << " rows outside market hours." << std::endl;
    }

    return data;
  }
};

// --- Daily Aggregation ---

std::vector<DailyBar> aggregateToDaily(const std::vector<Tick> &ticks) {
  std::map<std::time_t, std::vector<double>> dayPrices;
  std::vector<DailyBar> dailyBars;

  if (ticks.empty())
    return dailyBars;

  // Group by day
  for (const auto &tick : ticks) {
    std::time_t day = getMidnight(tick.time);
    dayPrices[day].push_back(tick.price);
  } // Since ticks are chronological, this is efficient map insertion order

  for (const auto &[date, prices] : dayPrices) {
    if (!prices.empty()) {
      dailyBars.push_back({date, prices.front(), prices.back()});
    }
  }

  return dailyBars; // Already sorted by map key
}

// --- Indicators ---

// Returns SMA vector aligned with input prices. First (period-1) elements
// remain 0.0 or NaN representation.
std::vector<double> calculateSMA(const std::vector<DailyBar> &bars,
                                 int period) {
  std::vector<double> smas(bars.size(), 0.0);
  if (bars.size() < period)
    return smas;

  double sum = 0.0;
  // Initial sum
  for (int i = 0; i < period; ++i) {
    sum += bars[i].close;
  }
  smas[period - 1] = sum / period;

  // Rolling window
  for (size_t i = period; i < bars.size(); ++i) {
    sum += bars[i].close;
    sum -= bars[i - period].close;
    smas[i] = sum / period;
  }
  return smas;
}

// --- Simulation Logic ---

SimulationResult simulate(const std::vector<DailyBar> &bars,
                          const std::vector<double> &fastSMA,
                          const std::vector<double> &slowSMA,
                          double InitialCapital, int fastPeriod, int slowPeriod,
                          double WindowDurationDays) {
  SimulationResult res;
  res.fast_window = fastPeriod;
  res.slow_window = slowPeriod;
  res.cagr = 0.0;
  res.numOrders = 0;

  if (bars.empty())
    return res;

  double cash = InitialCapital;
  double shares = 0.0;
  bool invested = false;

  // Start simulation after the slow period allows for valid data
  // We make decisions at the *start* of Day i based on Day i-1 data.
  // So we can trade on Day 'slowPeriod' (index) based on SMAs at
  // 'slowPeriod-1'.

  int startIdx = slowPeriod;
  if (startIdx >= bars.size())
    return res;

  for (size_t i = startIdx; i < bars.size(); ++i) {
    // Look at previous day's signals
    double prevFast = fastSMA[i - 1];
    double prevSlow = slowSMA[i - 1];

    // Ensure valid SMA
    if (prevFast == 0.0 || prevSlow == 0.0)
      continue;

    // Current execution price (Open of today)
    double currentPrice = bars[i].open;

    if (!invested) {
      // Check for Golden Cross
      if (prevFast > prevSlow) {
        // Buy
        shares = cash / currentPrice;
        cash = 0.0;
        invested = true;
        res.numOrders++;
      }
    } else {
      // Check for Death Cross
      if (prevFast < prevSlow) {
        // Sell
        double proceeds = shares * currentPrice;
        double gain =
            proceeds - (shares * bars[i].open); // Approximate gain metric
        cash = proceeds;
        shares = 0.0;
        invested = false;
        res.numOrders++;
        res.metrics.gains.push_back(gain); // Tracking realized PnL
      }
    }
  }

  // Final Equity
  double finalEquity = cash;
  if (invested) {
    finalEquity += shares * bars.back().close;
    res.numOrders++; // Liquidate
  }

  // CAGR
  if (InitialCapital != 0 && WindowDurationDays > 0) {
    double years = WindowDurationDays / 365.25;
    if (years > 0) {
      res.cagr = std::pow(finalEquity / InitialCapital, 1.0 / years) - 1.0;
    }
  }

  return res;
}

// --- Output ---

void printJSON(std::ostream &out,
               const std::vector<SimulationResult> &results) {
  out << "[\n";
  for (size_t i = 0; i < results.size(); ++i) {
    const auto &res = results[i];
    out << "  {\n";
    out << "    \"parameters\": {\n";
    out << "      \"fast\": " << res.fast_window << ",\n";
    out << "      \"slow\": " << res.slow_window << ",\n";
    out << "      \"cagr\": " << res.cagr << ",\n";
    out << "      \"numOrders\": " << res.numOrders << "\n";
    out << "    }\n"; // Simplified, no cycle metrics array for now to save
                      // space
    out << "  }" << (i < results.size() - 1 ? "," : "") << "\n";
  }
  out << "]\n";
}

// --- Main ---

int main(int argc, char *argv[]) {
  if (argc < 9) {
    std::cerr << "Usage: " << argv[0]
              << " <CSV_File> <Initial_Capital> <StartDate> <EndDate> "
                 "<MinFast> <MaxFast> <MinSlow> <MaxSlow> <Step>"
              << std::endl;
    return 1;
  }

  std::string filename = argv[1];
  double InitialCapital = std::stod(argv[2]);
  std::string startDateStr = argv[3];
  std::string endDateStr = argv[4];
  int minFast = std::stoi(argv[5]);
  int maxFast = std::stoi(argv[6]);
  int minSlow = std::stoi(argv[7]);
  int maxSlow = std::stoi(argv[8]);
  int step = std::stoi(argv[9]);

  std::time_t startTime = parseDate(startDateStr, "00:00");
  std::time_t endTime = parseDate(endDateStr, "23:59");

  // Load Data
  std::cout << "Loading " << filename << "..." << std::endl;
  std::vector<Tick> allData = CSVReader::readCSV(filename);

  // Filter Time Window
  std::vector<Tick> data;
  for (const auto &tick : allData) {
    if (tick.time >= startTime && tick.time <= endTime) {
      data.push_back(tick);
    }
  }

  if (data.empty()) {
    std::cerr << "No data in time window." << std::endl;
    return 1;
  }

  double WindowDuration = getDaysDiff(startTime, endTime);

  // Aggregate Daily
  std::vector<DailyBar> dailyBars = aggregateToDaily(data);
  std::cout << "Aggregated " << dailyBars.size() << " daily bars." << std::endl;

  if (dailyBars.empty())
    return 1;

  // Parameter Sweep
  // We need to sweep fast and slow.
  // Slow must be > Fast.
  // To avoid re-calculating SMAs constantly, we can pre-calculate all possible
  // SMAs needed? Or just calculate on the fly per thread? Calculating SMA is
  // O(N). Simulation is O(N). Total complexity O(K * N) where K is number of
  // param sets. Pre-calc is better if we reuse. But simple sweep is fine for
  // reasonable N.

  int numSteps = std::stoi(argv[9]);

  // Calculate increment based on Number of Steps
  // If numSteps is 10, we want 10 points in the range.
  // Stride = (Max - Min) / numSteps. Avoid 0 stride.

  int fastRange = maxFast - minFast;
  int slowRange = maxSlow - minSlow;

  int fastStride =
      (numSteps > 0 && fastRange > 0) ? std::max(1, fastRange / numSteps) : 1;
  int slowStride =
      (numSteps > 0 && slowRange > 0) ? std::max(1, slowRange / numSteps) : 1;

  std::vector<std::pair<int, int>> params;
  for (int f = minFast; f <= maxFast; f += fastStride) {
    for (int s = minSlow; s <= maxSlow; s += slowStride) {
      if (s > f) {
        params.push_back({f, s});
      }
    }
  }

  std::vector<SimulationResult> results(params.size());
  std::cout << "Running " << params.size() << " simulations..." << std::endl;

#pragma omp parallel for
  for (size_t i = 0; i < params.size(); ++i) {
    int f = params[i].first;
    int s = params[i].second;

    // Calculate SMAs locally (or shared cache if optim needed)
    std::vector<double> fastSMA = calculateSMA(dailyBars, f);
    std::vector<double> slowSMA = calculateSMA(dailyBars, s);

    results[i] = simulate(dailyBars, fastSMA, slowSMA, InitialCapital, f, s,
                          WindowDuration);
  }

  // Output
  // Simple basename extraction
  size_t lastSlash = filename.find_last_of("/\\");
  std::string basename = (lastSlash == std::string::npos)
                             ? filename
                             : filename.substr(lastSlash + 1);
  size_t lastDot = basename.find_last_of(".");
  if (lastDot != std::string::npos) {
    basename = basename.substr(0, lastDot);
  }
  std::string outputFilename = "mac_" + basename + ".json";

  std::ofstream outFile(outputFilename);
  printJSON(outFile, results);
  std::cout << "Results written to " << outputFilename << std::endl;

  return 0;
}
