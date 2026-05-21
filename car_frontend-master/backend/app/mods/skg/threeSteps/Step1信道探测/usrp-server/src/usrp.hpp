#ifndef _USRP_HPP_
#define _USRP_HPP_

#include <vector>
#include <functional>
#include <boost/thread.hpp>
#include <uhd/usrp/multi_usrp.hpp>
#include <zmq.hpp>
#include "message.hpp"
#include "wave_table.hpp"

class usrp {
private:
  // ZeroMQ server listen address.
  std::string zmq_bind;
  // USRP device arguments.
  std::string device_args;

  // USRP device should be exclusively accessed.
  mutable boost::mutex device_lock;
  uhd::usrp::multi_usrp::sptr device;

  size_t rx_sample_per_buffer;
  size_t tx_sample_per_buffer;

  // The CPU format is a string that describes the format of host memory.
  // Conversions for the following CPU formats have been implemented:
  // fc64 - complex<double>
  // fc32 - complex<float>
  // sc16 - complex<int>
  // sc8  - complex<int8_t>
  std::string rx_cpu_format = "fc32";
  std::string tx_cpu_format = "fc32";
  // The OTW format is a string that describes the format over-the-wire. The
  // following over-the-wire formats have been implemented:
  // sc16 - Q16  I16
  // sc8  - Q8_1 I8_1 Q8_0 I8_0
  std::string rx_otw_format = "sc16";
  std::string tx_otw_format = "sc16";

  // Settling time before receiving/transmitting signals.
  double rx_settling_time = 0.0;
  double tx_settling_time = 0.0;

  // Add prefix waveform to TX signals.
  // These default values have been tested.
  bool tx_prefix_wave_enable = false;
  size_t tx_prefix_wave_len = 64;
  wave_type tx_prefix_wave_type = wave_type::WT_SINE;
  size_t tx_prefix_wave_periods = 20;
  std::vector<uint8_t> tx_prefix_wave_buffer;

  // Dump the samples guarded by prefix waves.
  bool rx_guarded_wave_dump = true;
  size_t rx_maximum_samples = 0;
  size_t rx_guarded_wave_fft_size = 1024;
  size_t rx_guarded_wave_fft_win_lo = 8;
  size_t rx_guarded_wave_fft_win_hi = 12;
  double rx_guarded_wave_fft_threshold = 0.5;

  // When rx_keep_sampling is false, the receiver will stop sampling to file.
  // rx_keep_sampling is protected by the sample_to_file_thread_lock.
  bool rx_keep_sampling = false;

  // Thread for sample_to_file.
  mutable boost::mutex sample_to_file_thread_lock;
  boost::thread *sample_to_file_thread = nullptr;

  // Thread for sample_from_file.
  mutable boost::mutex sample_from_file_thread_lock;
  boost::thread *sample_from_file_thread = nullptr;

  // Threads for running jobs.
  boost::thread_group threads;

  struct getter_setter_pair {
    std::function<std::string()> getter;
    std::function<void(std::string&)> setter;
  };
  std::unordered_map<std::string, getter_setter_pair> getter_setter_pairs;
  std::unordered_map<std::string,
		     std::function<message(const message &)>> task_map;
public:
  usrp(usrp &usrp) = delete;
  usrp(std::string device_args, std::string zmq_bind);
  uhd::usrp::multi_usrp::sptr get_device() { return device; }

  std::string get_pp_string() const;
  std::string get_rx_antenna() const;
  std::string get_rx_bandwidth() const;
  std::string get_rx_freq() const;
  std::string get_rx_gain() const;
  std::string get_rx_rate() const;
  std::string get_rx_sample_per_buffer() const;
  std::string get_rx_settling_time() const;
  std::string get_rx_cpu_format() const;
  std::string get_rx_otw_format() const;
  std::string get_rx_maximum_samples() const;
  std::string get_tx_antenna() const;
  std::string get_tx_bandwidth() const;
  std::string get_tx_freq() const;
  std::string get_tx_gain() const;
  std::string get_tx_rate() const;
  std::string get_tx_sample_per_buffer() const;
  std::string get_tx_settling_time() const;
  std::string get_tx_cpu_format() const;
  std::string get_tx_otw_format() const;
  std::string get_tx_prefix_wave() const;
  std::string get_clock_source() const;

  void set_pp_string(std::string &pp);
  void set_rx_antenna(std::string &ant);
  void set_rx_bandwidth(std::string &bw);
  void set_rx_freq(std::string &freq);
  void set_rx_gain(std::string &gain);
  void set_rx_rate(std::string &rate);
  void set_rx_sample_per_buffer(std::string &spb);
  void set_rx_settling_time(std::string &time);
  void set_rx_cpu_format(std::string &fmt);
  void set_rx_otw_format(std::string &fmt);
  void set_rx_maximum_samples(std::string &samples);
  void set_tx_antenna(std::string &ant);
  void set_tx_bandwidth(std::string &bw);
  void set_tx_freq(std::string &freq);
  void set_tx_gain(std::string &gain);
  void set_tx_rate(std::string &rate);
  void set_tx_sample_per_buffer(std::string &spb);
  void set_tx_settling_time(std::string &time);
  void set_tx_cpu_format(std::string &fmt);
  void set_tx_otw_format(std::string &fmt);
  void set_tx_prefix_wave(std::string &prefix);
  void set_clock_source(std::string &clock_source);

  std::string get_device_config(std::string &param) const;
  void set_device_config(std::string &param, std::string &val);
  message_payload get_or_set_device_configs(message_payload &&params);

  bool rx_is_sampling_to_file() const;

  template <typename sample_type>
  void sample_from_file_generic(const std::string &filename) const;
  void sample_from_file(const std::string &filename) const;
  message launch_sample_from_file(const message &msg);
  void shutdown_sample_from_file();

  template <typename sample_type>
  void sample_to_file_generic(const std::string &filename) const;
  void sample_to_file(const std::string &filename) const;
  message launch_sample_to_file(const message &msg);
  void shutdown_sample_to_file();
  message launch_shutdown_sample_to_file(const message &msg);

  void zmq_server_run();
  message handle_request(message &msg);
  message process_conf_req(message &msg);
  message process_work_req(message &msg);

  void force_shutdown_all_jobs();
  ~usrp();
};

#endif
