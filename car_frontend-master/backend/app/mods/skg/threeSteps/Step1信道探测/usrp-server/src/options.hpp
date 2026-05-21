#ifndef _OPTIONS_HPP_
#define _OPTIONS_HPP_

#include <boost/program_options.hpp>

#include <string>

namespace po = boost::program_options;

class options {
private:
  po::options_description desc;
  po::variables_map vm;

public:
  // ZeroMQ server bind address. --bind
  std::string zmq_bind;
  // Device arguments. --device-args
  std::string device_args;

  options();
  void parse_options(int argc, char **argv);
  int count(const char *) const;
  bool check_options() const;
};

#endif
