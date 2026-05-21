#ifndef _WAVE_TABLE_HPP_
#define _WAVE_TABLE_HPP_

#include <complex>
#include <vector>

typedef enum {
  WT_SINE,
  WT_MSEQ,
} wave_type;

template <typename sample_type>
class wave_table {
private:
  double power_dbfs;
  std::vector<std::complex<sample_type>> buffer;
public:
  wave_table(wave_type wt, size_t len, const sample_type ampl);
  size_t size() const;
  size_t bytes() const;
  const std::complex<sample_type>& operator[](size_t index) const;
  std::complex<sample_type>& operator[](size_t index);
  std::vector<std::complex<sample_type>> &get_buffer();
};

#endif
