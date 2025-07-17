#include <omp.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
  long pages = sysconf(_SC_PHYS_PAGES);
  long page_size = sysconf(_SC_PAGE_SIZE);
  size_t total_bytes = (size_t)pages * page_size;
  size_t flush_bytes = total_bytes * 9 / 10;

  if (argc >= 2) {
    double gb = atof(argv[1]);
    flush_bytes = (size_t)(gb * 1024 * 1024 * 1024);
  }

  double flush_gb = flush_bytes / (1024.0 * 1024 * 1024);
  printf("About to allocate and flush ~%.2f GB of memory.\n", flush_gb);
  printf("Press 'y' to proceed: ");
  int c = getchar();
  if (c != 'y' && c != 'Y') {
    printf("Aborted.\n");
    return 0;
  }

  char *buffer = malloc(flush_bytes);
  if (!buffer) {
    perror("malloc");
    return 1;
  }

// Dirty memory in parallel (write every byte)
#pragma omp parallel for schedule(static)
  for (size_t i = 0; i < flush_bytes; i++) {
    buffer[i] = (char)(i % 256);
  }

  // Touch one byte per page during summation
  long long sum = 0;
  size_t page_count = flush_bytes / page_size;
#pragma omp parallel for reduction(+ : sum) schedule(static)
  for (size_t i = 0; i < page_count; i++) {
    sum += buffer[i * page_size];
  }

  printf("Touched %.2f GB (1 byte per page), checksum: %lld\n", flush_gb, sum);
  getchar();

  free(buffer);
  return 0;
}

