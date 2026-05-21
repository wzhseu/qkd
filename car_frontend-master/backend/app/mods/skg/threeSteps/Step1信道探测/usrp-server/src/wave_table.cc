#include <complex>
#include "wave_table.hpp"

constexpr double PI = 3.1415926535897;

namespace {
template <typename sample_type>
static void gen_sine_wave(const sample_type ampl, size_t len,
			  std::vector<std::complex<sample_type>> &buffer) {
  static sample_type tau = 2 * PI;
  static const std::complex<sample_type> J(0, 1);

  for (size_t I = 0; I < len; ++I) {
    std::complex<sample_type> p =
      ampl * std::exp(J * static_cast<sample_type>(tau * I / len));
    buffer[I] = std::real(p);
  }
}

template <typename sample_type>
static void gen_m_seq_wave(const sample_type ampl, size_t len,
			   std::vector<std::complex<sample_type>> &buffer) {

}
} // end anonymous namespace.

template <typename sample_type>
wave_table<sample_type>::wave_table(wave_type wt, size_t len,
				    const sample_type ampl)
  : buffer(len, {0.0, 0.0}) {
  switch (wt) {
  case wave_type::WT_SINE:
    gen_sine_wave<sample_type>(ampl, len, buffer);
    power_dbfs = static_cast<double>(20 * std::log10(ampl));
    break;
  case wave_type::WT_MSEQ:
    gen_m_seq_wave<sample_type>(ampl, len, buffer);
    break;
  }
}

template <typename sample_type>
size_t wave_table<sample_type>::size() const {
  return buffer.size();
}

template <typename sample_type>
size_t wave_table<sample_type>::bytes() const {
  return buffer.size() * sizeof(std::complex<sample_type>);
}

template <typename sample_type>
const std::complex<sample_type>&
wave_table<sample_type>::operator[](size_t index) const {
  return buffer[index];
}

template <typename sample_type>
std::complex<sample_type>& wave_table<sample_type>::operator[](size_t index) {
  return buffer[index];
}

template <typename sample_type>
std::vector<std::complex<sample_type>>& wave_table<sample_type>::get_buffer() {
  return buffer;
}

// The explicit class instantiation should be put in the end of the .cc file.
template class wave_table<float>;
template class wave_table<double>;
