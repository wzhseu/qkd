cmake_minimum_required(VERSION 3.5.1)
project(usrp-server CXX)

## Configure Compiler.
set(CMAKE_CXX_STANDARD 11)

## Set up build environment.
## Choose a static or shared-library build (shared is default, and static will
## probably need some special care!)
## Set this to ON in order to link a static build of UHD:
option(UHD_USE_STATIC_LIBS OFF)

## Disable developer warnings.
if(NOT DEFINED CMAKE_SUPPRESS_DEVELOPER_WARNINGS)
  set(CMAKE_SUPPRESS_DEVELOPER_WARNINGS 1 CACHE INTERNAL "No dev warnings")
endif()

find_package(UHD "3.15.0")
find_package(RapidJSON)
find_package(PkgConfig)
pkg_check_modules(PC_ZeroMQ QUIET zmq)
pkg_check_modules(PC_FFTW3 QUIET fftw3)

find_path(ZEROMQ_INCLUDE_DIR
  NAMES zmq.hpp
  PATHS ${PC_ZeroMQ_INCLUDE_DIRS}
)

find_path(FFTW3_INCLUDE_DIR
  NAMES fftw3.h
  PATHS ${PC_FFTW3_INCLUDE_DIRS}
)

find_library(ZEROMQ_LIBRARY
  NAMES zmq
  PATHS ${PC_ZeroMQ_LIBRARY_DIRS}
)

find_library(FFTW3_LIBRARY
  NAMES fftw3
  PATHS ${PC_FFTW3_LIBRARY_DIRS}
)

# This example also requires Boost.
# Set components here, then include UHDBoost to do the actual finding
set(UHD_BOOST_REQUIRED_COMPONENTS
  program_options
  system
  thread
)
set(BOOST_MIN_VERSION 1.58)
include(UHDBoost)

## need these include and link directories for the build
include_directories(
  ${Boost_INCLUDE_DIRS}
  ${UHD_INCLUDE_DIRS}
  ${ZEROMQ_INCLUDE_DIR}
  ${FFTW3_INCLUDE_DIR}
)
link_directories(${Boost_LIBRARY_DIRS} ${ZEROMQ_LIBRARY_DIR} ${FFTW3_LIBRARY_DIR})

## Make the executable
add_executable(usrp_server src/main.cc src/options.cc src/usrp.cc src/message.cc src/wave_table.cc)

set(CMAKE_BUILD_TYPE "Release")

## Shared library case: All we need to do is link against the library, and
## anything else we need (in this case, some Boost libraries):
if(NOT UHD_USE_STATIC_LIBS)
  message(STATUS "Linking against shared UHD library.")
  target_link_libraries(usrp_server ${UHD_LIBRARIES}
                                    ${Boost_LIBRARIES}
                                    ${ZEROMQ_LIBRARY}
                                    fftw3 fftw3f)
else(NOT UHD_USE_STATIC_LIBS)
  message(STATUS "Linking against static UHD library.")
  target_link_libraries(usrp_server
  ## We could use ${UHD_LIBRARIES}, but linking requires some extra flags,
  ## so we use this convenience variable provided to us
  ${UHD_STATIC_LIB_LINK_FLAG}
  ## Also, when linking statically, we need to pull in all the deps for
  ## UHD as well, because the dependencies don't get resolved automatically
  ${UHD_STATIC_LIB_DEPS}
  ${ZEROMQ_LIBRARY}
  fftw3 fftw3f
)
endif(NOT UHD_USE_STATIC_LIBS)
