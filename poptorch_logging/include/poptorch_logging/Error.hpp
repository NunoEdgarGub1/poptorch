// Copyright (c) 2020 Graphcore Ltd. All rights reserved.
#ifndef INCLUDE_POPTORCH_LOGGING_ERROR_HPP
#define INCLUDE_POPTORCH_LOGGING_ERROR_HPP

#include <sstream>
#include <stdexcept>

namespace logging {

#define UNUSED(var) (void)(var)

#define ERROR(msg)                                                             \
  do {                                                                         \
    std::stringstream __error_msg;                                             \
    __error_msg << "ERROR in " << __FILE__ << ":" << __LINE__ << ": " << msg;  \
    throw logging::internal_error(__error_msg.str().c_str());                  \
  } while (0)

#define ERROR_ON_MSG(condition, msg)                                           \
  do {                                                                         \
    if (condition) {                                                           \
      ERROR(msg);                                                              \
    }                                                                          \
  } while (0)

#define ERROR_ON(condition) ERROR_ON_MSG(condition, #condition)

/**
 * Exception class for poptorch
 */
class error : public std::runtime_error {
public:
  explicit error(const char *s);
};

/**
 * Exception class specific to internal errors
 * This should be used as an assert; for states where the user should not have
 * been able to create.
 */
class internal_error : public error {
public:
  using error::error;
};
} // namespace logging

#endif // INCLUDE_POPTORCH_LOGGING_ERROR_HPP