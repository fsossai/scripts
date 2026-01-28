#include <algorithm>
#include <cmath>
#include <ctime>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <omp.h>
#include <sstream>
#include <string>
#include <vector>

struct CycleMetrics {
  std::vector<double> gains;
  std::vector<double> wait_times;
  std::vector<double> hold_times;
};

struct SimulationResult {
  double to;
  double tc;
  double timeLimitHold;
  double timeLimitWait;
  double cagr;
  int numOrders;
  CycleMetrics metrics;
};

struct Tick {
  std::time_t time;
  double price;
};

// Helper to convert date string to time_t (midnight)
std::time_t parseDate(const std::string &dateStr, const std::string &timeStr) {
  std::tm tm = {};
  std::stringstream ss(dateStr + " " + timeStr);
  // Format: MM/DD/YYYY HH:MM
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
  tm.tm_isdst = -1; // Let system determine DST

  return std::mktime(&tm);
}

// Helper to get calendar difference in days
double getDaysDiff(std::time_t t1, std::time_t t2) {
  return std::difftime(t2, t1) / (60.0 * 60.0 * 24.0);
}

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

    while (std::getline(file, line)) {
      std::stringstream ss(line);
      std::string dateStr, timeStr, priceStr;

      // MM/DD/YYYY,HH:MM,Price,...
      if (!std::getline(ss, dateStr, ','))
        continue;
      if (!std::getline(ss, timeStr, ','))
        continue;
      if (!std::getline(ss, priceStr, ','))
        continue;

      try {
        double price = std::stod(priceStr);
        std::time_t time = parseDate(dateStr, timeStr);
        if (time != -1) {
          data.push_back({time, price});
        }
      } catch (...) {
        continue; // Skip malformed lines
      }
    }
    return data;
  }
};

enum State {
  HOLDING, // Owning the stock, waiting to sell
  WAITING  // Sold/Not owning, waiting to buy
};

SimulationResult simulate(const std::vector<Tick> &data, double InitialCapital,
                          double TargetOpenPct, double TargetClosePct, double E,
                          double WindowDuration) {
  SimulationResult res;
  res.to = TargetOpenPct;
  res.tc = TargetClosePct;
  res.cagr = 0.0;
  res.numOrders = 0;

  // Limits in days
  res.timeLimitHold = (TargetClosePct / E) * WindowDuration;
  res.timeLimitWait = (std::abs(TargetOpenPct) / E) * WindowDuration;

  if (data.empty())
    return res;

  State state = HOLDING;

  // Capital Tracking
  double cash = 0.0;
  double shares = 0.0;
  int orders = 0;

  // Step 1: Buy at current price P (first tick)
  // We assume we start with InitialCapital in cash, and immediately buy.
  double entryPrice = data[0].price;
  if (entryPrice > 0) {
    shares = InitialCapital / entryPrice;
    cash = 0.0;
    orders++;
  }

  double exitPrice = 0.0;
  std::time_t lastEventTime = data[0].time;

  for (size_t i = 1; i < data.size(); ++i) {
    double currentPrice = data[i].price;
    std::time_t currentTime = data[i].time;
    double daysSinceEvent = getDaysDiff(lastEventTime, currentTime);

    if (state == HOLDING) {
      double targetPrice = entryPrice * (1.0 + TargetClosePct / 100.0);

      bool timeLimitReached = daysSinceEvent >= res.timeLimitHold;
      bool priceTargetReached = currentPrice >= targetPrice;

      if (priceTargetReached || timeLimitReached) {
        // Sell all shares
        double saleValue = shares * currentPrice;
        double tradeGain =
            saleValue -
            (shares * entryPrice); // Gain for metrics (absolute profit)

        cash = saleValue;
        shares = 0.0;
        orders++;

        // Metrics
        res.metrics.gains.push_back(tradeGain);
        res.metrics.hold_times.push_back(daysSinceEvent);

        exitPrice = currentPrice;
        lastEventTime = currentTime;
        state = WAITING;
      }
    } else if (state == WAITING) {
      // TargetOpenPct is for buying dip (given as negative)
      // Condition 1: Price drops to S * (1 + TargetOpen/100)
      double targetPrice = exitPrice * (1.0 + TargetOpenPct / 100.0);

      bool timeLimitReached = daysSinceEvent >= res.timeLimitWait;
      bool priceTargetReached = currentPrice <= targetPrice;

      if (priceTargetReached || timeLimitReached) {
        // Buy as many shares as possible
        if (currentPrice > 0) {
          shares = cash / currentPrice;
          cash = 0.0;
          orders++;
        }
        entryPrice = currentPrice;

        // Metrics
        res.metrics.wait_times.push_back(daysSinceEvent);

        lastEventTime = currentTime;
        state = HOLDING;
      }
    }
  }

  // Last day logic
  double finalEquity = cash;
  if (state == HOLDING) {
    double currentPrice = data.back().price;
    double positionValue = shares * currentPrice;
    double tradeGain = positionValue - (shares * entryPrice);

    finalEquity += positionValue;
    // We do NOT increment orders here unless we actually sell.
    // The previous logic just calculated paper value.
    // If we consider "End of Simulation" as a forced liquidation, we should
    // increment. However, existing code didn't change state. Let's assume paper
    // valuation. But wait, if we are liquidating to calculate final equity, in
    // a way it is an exit. The requirement says "each buy and sell count as
    // one". I will count it as a sell for consistency if we liquidate.
    // Actually, to get Realized PnL we liquidate.
    // Let's increment orders if we held shares.
    if (shares > 0)
      orders++; // Liquidate

    res.metrics.gains.push_back(tradeGain);
    double daysSinceEvent = getDaysDiff(lastEventTime, data.back().time);
    res.metrics.hold_times.push_back(daysSinceEvent);
  }

  // Return CAGR
  res.numOrders = orders;
  if (InitialCapital != 0 && WindowDuration > 0) {
    double years = WindowDuration / 365.25;
    if (years > 0) {
      res.cagr = std::pow(finalEquity / InitialCapital, 1.0 / years) - 1.0;
    } else {
      res.cagr = 0.0;
    }
  } else {
    res.cagr = 0.0;
  }
  return res;
}

void printJSON(std::ostream &out,
               const std::vector<SimulationResult> &results) {
  out << "[\n";
  for (size_t i = 0; i < results.size(); ++i) {
    const auto &res = results[i];
    out << "  {\n";
    out << "    \"parameters\": {\n";
    out << "      \"to\": " << res.to << ",\n";
    out << "      \"tc\": " << res.tc << ",\n";
    out << "      \"timeLimitHold\": " << res.timeLimitHold << ",\n";
    out << "      \"timeLimitWait\": " << res.timeLimitWait << ",\n";
    out << "      \"cagr\": " << res.cagr << ",\n";
    out << "      \"numOrders\": " << res.numOrders << "\n";
    out << "    },\n";
    out << "    \"result\": {\n";

    // Gains
    out << "      \"cycle_gains\": [";
    for (size_t k = 0; k < res.metrics.gains.size(); ++k) {
      out << res.metrics.gains[k]
          << (k < res.metrics.gains.size() - 1 ? "," : "");
    }
    out << "],\n";

    // Wait Times
    out << "      \"cycle_wait_times\": [";
    for (size_t k = 0; k < res.metrics.wait_times.size(); ++k) {
      out << res.metrics.wait_times[k]
          << (k < res.metrics.wait_times.size() - 1 ? "," : "");
    }
    out << "],\n";

    // Hold Times
    out << "      \"cycle_hold_times\": [";
    for (size_t k = 0; k < res.metrics.hold_times.size(); ++k) {
      out << res.metrics.hold_times[k]
          << (k < res.metrics.hold_times.size() - 1 ? "," : "");
    }
    out << "]\n";

    out << "    }\n";
    out << "  }" << (i < results.size() - 1 ? "," : "") << "\n";
  }
  out << "]\n";
}

int main(int argc, char *argv[]) {
  if (argc < 9) {
    std::cerr << "Usage: " << argv[0]
              << " <CSV_File> <Initial_Capital> <Expected_Gain_Percent_E> "
                 "<StartDate_MM/DD/YYYY> <EndDate_MM/DD/YYYY> <Min_Target_Pct> "
                 "<Max_Target_Pct> <Num_Steps>"
              << std::endl;
    std::cerr << "Example: " << argv[0]
              << " IBM.csv 10000 10 01/01/2000 01/01/2001 0.5 5.0 10"
              << std::endl;
    return 1;
  }

  std::string filename = argv[1];
  double InitialCapital = std::stod(argv[2]);
  double E = std::stod(argv[3]);
  std::string startDateStr = argv[4];
  std::string endDateStr = argv[5];
  double minTarget = std::stod(argv[6]);
  double maxTarget = std::stod(argv[7]);
  int numSteps = std::stoi(argv[8]);

  std::time_t startTime = parseDate(startDateStr, "00:00");
  std::time_t endTime = parseDate(endDateStr, "23:59"); // End of day

  if (startTime == -1 || endTime == -1) {
    std::cerr << "Error parsing dates. Please use MM/DD/YYYY format."
              << std::endl;
    return 1;
  }

  double WindowDuration = getDaysDiff(startTime, endTime);
  if (WindowDuration <= 0) {
    std::cerr << "Error: Start date must be before end date." << std::endl;
    return 1;
  }

  std::cout << "Parsing file " << filename << "..." << std::endl;
  auto parseStart = std::chrono::high_resolution_clock::now();

  std::vector<Tick> allData = CSVReader::readCSV(filename);

  auto parseEnd = std::chrono::high_resolution_clock::now();
  std::chrono::duration<double> parseElapsed = parseEnd - parseStart;
  std::cout << "Parsing completed in " << parseElapsed.count() << " seconds."
            << std::endl;

  if (allData.empty()) {
    std::cerr << "No data loaded." << std::endl;
    return 1;
  }

  // Filter data based on window
  std::vector<Tick> data;
  for (const auto &tick : allData) {
    if (tick.time >= startTime && tick.time <= endTime) {
      data.push_back(tick);
    }
  }

  if (data.empty()) {
    std::cerr << "No data found within the specified time window." << std::endl;
    return 1;
  }

  std::cout << "Simulating on " << data.size() << " ticks from " << startDateStr
            << " to " << endDateStr << " (" << WindowDuration << " days)."
            << std::endl;

  // Parameter Sweep
  double step = (numSteps > 0) ? (maxTarget - minTarget) / numSteps : 0;
  if (step <= 0 && numSteps > 0)
    step = 0.5;

  int totalSteps = numSteps + 1;
  int totalSimulations = totalSteps * totalSteps;
  std::vector<SimulationResult> results(totalSimulations);

  std::cout << "Running " << totalSimulations << " simulations..." << std::endl;
  auto simStart = std::chrono::high_resolution_clock::now();

#pragma omp parallel for collapse(2)
  for (int i = 0; i <= numSteps; ++i) {
    for (int j = 0; j <= numSteps; ++j) {
      double to = -(minTarget + i * step);
      double tc = minTarget + j * step;

      // Thread-safe write by index
      int idx = i * totalSteps + j;
      results[idx] = simulate(data, InitialCapital, to, tc, E, WindowDuration);
    }
  }

  auto simEnd = std::chrono::high_resolution_clock::now();
  std::chrono::duration<double> simElapsed = simEnd - simStart;
  std::cout << "Simulation completed in " << simElapsed.count() << " seconds."
            << std::endl;

  std::cout << "Writing results to output.json..." << std::endl;
  std::ofstream outFile("output.json");
  printJSON(outFile, results);

  std::cout << "Results written to output.json" << std::endl;

  return 0;
}
