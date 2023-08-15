#include <iostream>
#include <vector>
#include <iomanip>
#include <algorithm>
#include <numbers>
#include <tuple>
#include <cstdlib>

using Row = std::vector<int>;
using Matrix = std::vector<Row>;
using Plan = std::vector<std::tuple<int, int>>;
using Size = std::tuple<int, int>;
using Offset = std::tuple<int, int>;

auto printRow(const Row &row) -> void {
  for (const auto &col : row) {
    std::cout << std::setw(2) << col << " ";
  }
  std::cout << std::endl;
}

auto printMat(const Matrix &mat) -> void {
  for (const auto &row : mat) {
    printRow(row);
  }
  std::cout << std::endl;
}

auto initMat(Matrix &mat, int rows, int cols) -> void {
  int i = 0;
  mat.resize(rows);
  for (auto &row : mat) {
    row.resize(cols);
    for (auto &col : row) {
      col = i++;
    }
  }
}

auto getSize(const Matrix &mat) -> std::pair<int, int> {
  return {mat.size(), mat[0].size()};
}

auto getRowMajorAccessor(const Matrix &mat) {
  auto size = getSize(mat);
  int rows = std::get<0>(size);
  int cols = std::get<1>(size);
  return [rows, cols](int idx) -> std::pair<int, int> {
    return {idx / cols, idx % cols};
  };
}

auto createShuffleMajorPlan(Plan &plan, const Size &bases, const Size size, const Offset offset) -> void {
  Size newSize = {
    std::max(std::get<0>(size) / std::get<0>(bases), 1),
    std::max(std::get<1>(size) / std::get<1>(bases), 1)
  };
  if (std::get<0>(newSize) == 1 &&
      std::get<1>(newSize) == 1) {
    for (int i = 0; i < std::get<0>(bases); i++) {
      for (int j = 0; j < std::get<1>(bases); j++) {
        plan.push_back({std::get<0>(offset) + i, std::get<1>(offset) + j});
      }
    }
  } else {
    for (int i = 0; i < std::get<0>(bases); i++) {
      for (int j = 0; j < std::get<1>(bases); j++) {
        Offset newOffset = {
          std::get<0>(offset) + i * std::get<0>(newSize),
          std::get<1>(offset) + j * std::get<1>(newSize)
        };
        createShuffleMajorPlan(plan, bases, newSize, newOffset);
      }
    }
  }
}

auto createShuffleMajorPlan(Size size, Size bases) -> const Plan {
  Plan plan;
  Offset offset = {0, 0};
  createShuffleMajorPlan(plan, bases, size, offset);
  return plan;
}

auto getShuffleMajorAccessor(const Matrix &mat, Size bases) {
  const auto plan = createShuffleMajorPlan(getSize(mat), bases);
  return [=](int idx) { return plan[idx]; };
}

template<typename Accessor>
auto flatten(const Matrix &mat, const Accessor &accessor) -> Row {
  Row flat;
  const auto &[rows, cols] = getSize(mat);
  flat.resize(rows * cols);
  for (int k = 0; k < flat.size(); k++) {
    const auto access = accessor(k);
    flat[k] = mat[std::get<0>(access)][std::get<1>(access)];
  }
  return flat;
}

auto flatten(const Matrix &mat) -> Row {
  return flatten(mat, getRowMajorAccessor(mat));
}

int main(int argc, char *argv[]) {
  if (argc < 3) {
    return 1;
  }
  
  Matrix mat;
  int rows = atoi(argv[1]);
  int cols = atoi(argv[2]);
  initMat(mat, rows, cols);
  //printMat(mat);

  //std::cout << "Row Major:" << std::endl;
  //printRow(flatten(mat, getRowMajorAccessor(mat)));

  //std::cout << "Shuffle Major:" << std::endl;
  //printRow(flatten(mat, getShuffleMajorAccessor(mat, {2, 2})));

  createShuffleMajorPlan({rows, cols}, {4, 4});
  return 0;
}