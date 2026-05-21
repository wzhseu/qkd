#include <iostream>
#include <boost/format.hpp>
#include "options.hpp"

namespace po = boost::program_options;

options::options() : desc("Allowed options") {
  desc.add_options()
    ("help", "help message")
    ("bind", po::value<std::string>(&zmq_bind)->default_value("tcp://*:5555"),
             "ZeroMQ server listen address")
    ("device-args", po::value<std::string>(&device_args)->default_value(""),
                    "Device arguments");
}

void options::parse_options(int argc, char **argv) {
  po::store(po::parse_command_line(argc, argv, desc), vm);
  po::notify(vm);
}

int options::count(const char *key) const {
  return vm.count(key);
}

bool options::check_options() const {
  if (vm.count("help")) {
    std::cout << boost::format("%s") % desc << std::endl;
    return false;
  }

  return true;
}
