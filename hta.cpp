#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstring>
#include <ctime>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <omp.h>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>

struct DataPoint {
  std::string date;
  std::string time;
  double price;
  std::chrono::system_clock::time_point datetime;
};

// Parse date string "MM/DD/YYYY" to time_t
// Used for command-line date range arguments
// Returns time_t for the given date
// Example: "01/15/2024" -> time_t

time_t parseDate(const std::string &dateStr) {
  struct tm tm = {};
  int month, day, year;
  sscanf(dateStr.c_str(), "%d/%d/%d", &month, &day, &year);

  tm.tm_mday = day;
  tm.tm_mon = month - 1;    // months are 0-11
  tm.tm_year = year - 1900; // years since 1900
  tm.tm_hour = 0;
  tm.tm_min = 0;
  tm.tm_sec = 0;
  tm.tm_isdst = -1; // auto-detect DST

  return mktime(&tm);
}

// Parse time string "HH:MM:SS" and combine with date to create datetime
// Used for parsing each row in the CSV file
// Returns std::chrono::system_clock::time_point
// Example: "01/15/2024", "09:30:00" -> time_point
std::chrono::system_clock::time_point
parseDateTime(const std::string &dateStr, const std::string &timeStr) {
  struct tm tm = {};
  int month, day, year;
  sscanf(dateStr.c_str(), "%d/%d/%d", &month, &day, &year);
  sscanf(timeStr.c_str(), "%d:%d:%d", &tm.tm_hour, &tm.tm_min, &tm.tm_sec);

  tm.tm_mon = month - 1; // months are 0-11
  tm.tm_mday = day;
  tm.tm_year = year - 1900; // years since 1900
  tm.tm_isdst = -1;         // auto-detect DST

  time_t t = mktime(&tm);
  return std::chrono::system_clock::from_time_t(t);
}

// Filter data by date range (inclusive)
std::vector<DataPoint> filterDataByDateRange(const std::vector<DataPoint> &data,
                                             time_t startDate, time_t endDate) {
  std::vector<DataPoint> filtered;

  for (const auto &point : data) {
    time_t pointTime = std::chrono::system_clock::to_time_t(point.datetime);
    if (pointTime >= startDate && pointTime <= endDate) {
      filtered.push_back(point);
    }
  }

  return filtered;
}

// Load CSV data from file
// Expects columns: Date,Time,Price (header is skipped)
std::vector<DataPoint> loadData(const std::string &filename) {
  std::vector<DataPoint> data;
  std::ifstream file(filename);
  if (!file.is_open()) {
    throw std::runtime_error("Error: Could not open file '" + filename + "'.");
  }
  std::string line;

  // Skip header
  std::getline(file, line);

  while (std::getline(file, line)) {
    std::stringstream ss(line);
    std::string date, time, priceStr;

    if (std::getline(ss, date, ',') && std::getline(ss, time, ',') &&
        std::getline(ss, priceStr, ',')) {

      DataPoint point;
      point.date = date;
      point.time = time;
      point.price = std::stod(priceStr);
      point.datetime = parseDateTime(date, time);

      data.push_back(point);
    }
  }

  file.close();
  return data;
}

// Compute hitting times for a specific target percentage
// entryPoints: sampled entry points (random instants)
// fullData: entire dataset
// targetPercentage: e.g., 1.10 means 10% increase over entry price
// Returns: vector of hitting times in minutes
std::vector<double>
computeHittingTimes(const std::vector<DataPoint> &entryPoints,
                    const std::vector<DataPoint> &fullData,
                    double targetPercentage) {
  std::vector<double> hittingTimes(entryPoints.size());

#pragma omp parallel for schedule(dynamic, 64)
  for (size_t i = 0; i < entryPoints.size(); i++) {
    double targetPrice = entryPoints[i].price * targetPercentage;
    auto startTime = entryPoints[i].datetime;

    // Find the index of this entry in fullData (match by datetime and price)
    size_t entryIdx = 0;
    for (; entryIdx < fullData.size(); entryIdx++) {
      if (fullData[entryIdx].datetime == entryPoints[i].datetime &&
          fullData[entryIdx].price == entryPoints[i].price) {
        break;
      }
    }

    // Search for first price >= targetPrice after entryIdx
    size_t firstIndex = entryIdx + 1;
    for (; firstIndex < fullData.size(); firstIndex++) {
      if (fullData[firstIndex].price >= targetPrice) {
        break;
      }
    }

    // Always expect to find a hit; compute duration
    auto endTime = fullData[firstIndex].datetime;
    auto duration =
        std::chrono::duration_cast<std::chrono::minutes>(endTime - startTime);
    hittingTimes[i] = static_cast<double>(duration.count());
  }

  return hittingTimes;
}

// Calculate average of a vector, ignoring -1.0 values
double calculateAverage(std::vector<double> values) {
  // Filter out -1 values (not found)
  std::vector<double> filtered;
  for (double v : values) {
    if (v >= 0.0)
      filtered.push_back(v);
  }
  if (filtered.empty())
    return -1.0;

  double sum = 0.0;
  for (double v : filtered) {
    sum += v;
  }
  return sum / filtered.size();
}

int main(int argc, char *argv[]) {
  if (argc == 1) {
    std::cerr << "Usage: " << argv[0]
              << " <csv_file> [start_date] [end_date] [N] [min_target] "
                 "[max_target] [num_steps]\n"
              << "\n"
              << "Arguments:\n"
              << "  <csv_file>         CSV file with columns Date,Time,Price "
                 "(default: IVE.csv)\n"
              << "  [start_date]       Optional start date (MM/DD/YYYY)\n"
              << "  [end_date]         Optional end date (MM/DD/YYYY)\n"
              << "  [N]                Number of random entry points to sample "
                 "(default: 1000)\n"
              << "  [min_target]       Minimum target percentage (e.g., 1.01 "
                 "for 1% gain, default: 1.001)\n"
              << "  [max_target]       Maximum target percentage (e.g., 1.05 "
                 "for 5% gain, default: max feasible)\n"
              << "  [num_steps]        Number of target steps (default: 10)\n"
              << "\n"
              << "Examples:\n"
              << "  " << argv[0] << " IBM.csv\n"
              << "  " << argv[0]
              << " IBM.csv 01/01/2025 01/01/2026 500 1.01 1.05 20\n";
    return 1;
  }

  std::string csv_file = argv[1];
  std::cout << "Loading " << csv_file << "..." << std::endl;
  std::vector<DataPoint> data;
  try {
    data = loadData(csv_file);
  } catch (const std::exception &e) {
    std::cerr << e.what() << std::endl;
    return 1;
  }
  std::cout << "Loaded " << data.size() << " data points." << std::endl;

  // Determine date range for entry window
  time_t startDate, endDate;

  if (argc >= 4) {
    // Parse command-line arguments for start and end dates
    try {
      startDate = parseDate(argv[2]);
      endDate = parseDate(argv[3]);
      std::cout << "Using user-specified date range: " << argv[2] << " to "
                << argv[3] << std::endl;
    } catch (...) {
      std::cerr << "Error parsing dates. Usage: " << argv[0]
                << " <csv_file> [start_date] [end_date]" << std::endl;
      std::cerr << "Date format: MM/DD/YYYY (e.g., 01/15/2024)" << std::endl;
      return 1;
    }
  } else {
    // Default: last year from max date in data
    if (data.empty()) {
      std::cerr << "No data loaded." << std::endl;
      return 1;
    }
    time_t maxDate = std::chrono::system_clock::to_time_t(data.back().datetime);
    endDate = maxDate;
    // Calculate one year before max date
    struct tm *tm_info = localtime(&maxDate);
    tm_info->tm_year -= 1;
    startDate = mktime(tm_info);
    // Print the default range
    char dateStr[20];
    strftime(dateStr, sizeof(dateStr), "%m/%d/%Y", localtime(&startDate));
    std::cout << "Using default date range (last year): " << dateStr << " to ";
    strftime(dateStr, sizeof(dateStr), "%m/%d/%Y", localtime(&endDate));
    std::cout << dateStr << std::endl;
  }

  // Filter data by date range for entry window (used for sampling entry points)
  std::vector<DataPoint> filteredData =
      filterDataByDateRange(data, startDate, endDate);
  std::cout << "Filtered to " << filteredData.size() << " data points."
            << std::endl;

  if (filteredData.empty()) {
    std::cerr << "No data in the specified date range." << std::endl;
    return 1;
  }

  // Find index in full dataset where entry window starts
  size_t entryWindowStartIdx = 0;
  for (size_t i = 0; i < data.size(); i++) {
    if (data[i].datetime >= filteredData[0].datetime) {
      entryWindowStartIdx = i;
      break;
    }
  }

  // Use entire filtered window as entry candidates for sampling
  std::vector<DataPoint> entryWindow = filteredData;

  // Parse N (number of random entry points to sample)
  int N = 1000;
  if (argc >= 5) {
    N = std::stoi(argv[4]);
    if (N <= 0) {
      std::cerr << "Error: N must be positive." << std::endl;
      return 1;
    }
  }

  // Sample N unique random indices from entryWindow
  std::vector<DataPoint> sampledEntries;
  if ((size_t)N >= entryWindow.size()) {
    sampledEntries = entryWindow;
    N = entryWindow.size();
  } else {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, entryWindow.size() - 1);
    std::unordered_set<size_t> chosen;
    while (chosen.size() < (size_t)N) {
      size_t idx = dis(gen);
      chosen.insert(idx);
    }
    for (size_t idx : chosen) {
      sampledEntries.push_back(entryWindow[idx]);
    }
  }

  // Find min and max prices in sampled entries to set target range
  double minPrice = sampledEntries[0].price;
  double maxPrice = sampledEntries[0].price;
  for (const auto &point : sampledEntries) {
    if (point.price < minPrice)
      minPrice = point.price;
    if (point.price > maxPrice)
      maxPrice = point.price;
  }

  // Find max price in data after entry window (to determine feasible targets)
  double maxFuturePrice = 0.0;
  for (size_t i = entryWindowStartIdx + entryWindow.size(); i < data.size();
       i++) {
    if (data[i].price > maxFuturePrice) {
      maxFuturePrice = data[i].price;
    }
  }

  // Set target range: from min_target to max_target (clamped to feasible)
  double rightLimit = maxFuturePrice / maxPrice;
  double leftLimit = 1.001;

  // Parse min_target, max_target, num_steps from command line if provided
  double min_target = leftLimit;
  double max_target = rightLimit;
  int numSteps = 10;
  if (argc >= 6) {
    min_target = std::stod(argv[5]);
  }
  if (argc >= 7) {
    max_target = std::stod(argv[6]);
  }
  if (argc >= 8) {
    numSteps = std::stoi(argv[7]);
    if (numSteps < 2)
      numSteps = 2;
  }

  // Clamp max_target to rightLimit if needed
  if (max_target > rightLimit) {
    std::cout << "Warning: max_target (" << max_target
              << ") is above feasible limit (" << rightLimit
              << "). Clamping to " << rightLimit << "." << std::endl;
    max_target = rightLimit;
  }
  if (min_target < leftLimit) {
    std::cout << "Warning: min_target (" << min_target
              << ") is below minimum allowed (" << leftLimit
              << "). Clamping to " << leftLimit << "." << std::endl;
    min_target = leftLimit;
  }
  if (rightLimit <= leftLimit) {
    std::cerr << "Error: No feasible target range. Max future price ("
              << maxFuturePrice << ") is not higher than entry window max ("
              << maxPrice << ")." << std::endl;
    return 1;
  }

  std::cout << "Sampled entry points: " << N << std::endl;
  std::cout << "Sampled price range: " << minPrice << " - " << maxPrice
            << std::endl;
  std::cout << "Max future price (after window): " << maxFuturePrice
            << std::endl;
  std::cout << "Target range: " << min_target << " ("
            << (min_target - 1.0) * 100 << "%) to " << max_target << " ("
            << (max_target - 1.0) * 100 << "%)" << std::endl;

  // Compute average hitting times for each target in the range
  std::vector<double> targets(numSteps);
  std::vector<double> averages(numSteps);
  std::vector<int> counts(numSteps);
  std::string errorMsg;
  bool hasError = false;

  std::cout << "Computing hitting times for " << numSteps << " target levels..."
            << std::endl;

  // Loop over target percentages (outer loop sequential, inner loop
  // parallelized)
  for (int step = 0; step < numSteps && !hasError; step++) {
    double target =
        min_target + (step / (numSteps - 1.0)) * (max_target - min_target);
    targets[step] = target;

    try {
      std::vector<double> hittingTimes =
          computeHittingTimes(sampledEntries, data, target);
      averages[step] = calculateAverage(hittingTimes);
      counts[step] = hittingTimes.size();
    } catch (const std::runtime_error &e) {
      errorMsg = e.what();
      hasError = true;
    }

    std::cout << "Progress: " << (step + 1) << "/" << numSteps
              << " (target=" << target << ", " << (target - 1.0) * 100 << "%)"
              << std::endl;
  }

  if (hasError) {
    std::cerr << errorMsg << std::endl;
    return 1;
  }

  // Write results to CSV (long format: Target,HittingTime)
  // Each row: target percentage, hitting time in minutes
  // Generate output filename: "hta_" + input filename (without path)
  std::string baseName = csv_file.substr(csv_file.find_last_of("/\\") + 1);
  std::string outFileName = "hta_" + baseName;
  std::ofstream outFile(outFileName);
  outFile << "Target,HittingTime\n";
  int validCount = 0;
  for (int step = 0; step < numSteps; step++) {
    std::vector<double> hittingTimes =
        computeHittingTimes(sampledEntries, data, targets[step]);
    for (size_t i = 0; i < hittingTimes.size(); i++) {
      outFile << std::fixed << std::setprecision(4) << targets[step] << ","
              << std::fixed << std::setprecision(2) << hittingTimes[i] << "\n";
    }
    validCount++;
  }
  outFile.close();
  std::cout << "Results written to hitting_time_results.csv" << std::endl;
  std::cout << "Computed " << validCount << " target points." << std::endl;
  return 0;
}
