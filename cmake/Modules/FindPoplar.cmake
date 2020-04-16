set(WhatToDoString "Set POPLAR_INSTALL_DIR, \
something like -DPOPLAR_INSTALL_DIR=/path/to/build/install/")
FIND_PATH(POPLAR_INCLUDE_DIR 
  NAMES poplar/Engine.hpp
  HINTS ${POPLAR_INSTALL_DIR} ${POPLAR_INSTALL_DIR}/poplar/include ${POPLAR_INSTALL_DIR}/include 
  PATH_SUFFIXES poplar poplar/include
  DOC "directory with poplar include files (poplar/Engine.hpp etc.)")
IF(NOT POPLAR_INCLUDE_DIR)
  MESSAGE(FATAL_ERROR "Could not set POPLAR_INCLUDE_DIR. ${WhatToDoString}")
ENDIF()
MESSAGE(STATUS "Found POPLAR_INCLUDE_DIR ${POPLAR_INCLUDE_DIR}")
MARK_AS_ADVANCED(POPLAR_INCLUDE_DIR)

FIND_PATH(POPLIBS_INCLUDE_DIR
  NAMES poplin/MatMul.hpp 
  HINTS ${POPLAR_INSTALL_DIR}/poplibs/include ${POPLAR_INSTALL_DIR}/include ${POPLAR_INSTALL_DIR}
  PATH_SUFFIXES poplibs poplibs/include
  DOC "directory with poplibs include files (poplin/MatMult.hpp etc.)")
IF(NOT POPLIBS_INCLUDE_DIR)
  MESSAGE(FATAL_ERROR "Could not set POPLIBS_INCLUDE_DIR. ${WhatToDoString}")
ENDIF()
MESSAGE(STATUS "Found POPLIBS_INCLUDE_DIR ${POPLIBS_INCLUDE_DIR}")
MARK_AS_ADVANCED(POPLIBS_INCLUDE_DIR)


FIND_LIBRARY(POPLAR_LIB
  NAMES poplar
  HINTS ${POPLAR_INSTALL_DIR}/poplar/lib ${POPLAR_INSTALL_DIR}/lib
  PATH_SUFFIXES poplar poplar/lib
  DOC "poplar library to link to")
IF(NOT POPLAR_LIB)
  MESSAGE(FATAL_ERROR "Could not set POPLAR_LIB. ${WhatToDoString}")
ENDIF()
MESSAGE(STATUS "Found POPLAR_LIB ${POPLAR_LIB}")
MARK_AS_ADVANCED(POPLAR_LIB)

FIND_LIBRARY(POPLIN_LIB
  NAMES poplin
  HINTS ${POPLAR_INSTALL_DIR}/poplibs/lib ${POPLAR_INSTALL_DIR}/lib
  PATH_SUFFIXES poplibs poplibs/lib
  DOC "poplin library to link to")
IF(NOT POPLIN_LIB)
  MESSAGE(FATAL_ERROR "Could not set POPLIN_LIB. ${WhatToDoString}")
ENDIF()
MESSAGE(STATUS "Found POPLIN_LIB ${POPLIN_LIB}")
MARK_AS_ADVANCED(POPLIN_LIB)

FIND_LIBRARY(POPNN_LIB
  NAMES popnn
  HINTS ${POPLAR_INSTALL_DIR}/poplibs/lib ${POPLAR_INSTALL_DIR}/lib
  PATH_SUFFIXES poplibs poplibs/lib
  DOC "popnn library to link to")
IF(NOT POPNN_LIB)
  MESSAGE(FATAL_ERROR "Could not set POPNN_LIB. ${WhatToDoString}")
ENDIF()
MESSAGE(STATUS "Found POPNN_LIB ${POPNN_LIB}")
MARK_AS_ADVANCED(POPNN_LIB)

FIND_LIBRARY(POPOPS_LIB
  NAMES popops
  HINTS ${POPLAR_INSTALL_DIR}/poplibs/lib ${POPLAR_INSTALL_DIR}/lib
  PATH_SUFFIXES poplibs poplibs/lib
  DOC "popops library to link to")
IF(NOT POPOPS_LIB)
  MESSAGE(FATAL_ERROR "Could not set POPOPS_LIB. ${WhatToDoString}")
ENDIF()
MESSAGE(STATUS "Found POPOPS_LIB ${POPOPS_LIB}")
MARK_AS_ADVANCED(POPOPS_LIB)

FIND_LIBRARY(POPUTIL_LIB
  NAMES poputil
  HINTS ${POPLAR_INSTALL_DIR}/poplibs/lib ${POPLAR_INSTALL_DIR}/lib
  PATH_SUFFIXES poplibs poplibs/lib
  DOC "poputil library to link to")
IF(NOT POPUTIL_LIB)
  MESSAGE(FATAL_ERROR "Could not set POPUTIL_LIB. ${WhatToDoString}")
ENDIF()
MESSAGE(STATUS "Found POPUTIL_LIB ${POPUTIL_LIB}")
MARK_AS_ADVANCED(POPUTIL_LIB)

FIND_LIBRARY(POPRAND_LIB
  NAMES poprand
  HINTS ${POPLAR_INSTALL_DIR}/poplibs/lib ${POPLAR_INSTALL_DIR}/lib
  PATH_SUFFIXES poplibs poplibs/lib
  DOC "poprand library to link to")
IF(NOT POPRAND_LIB)
  MESSAGE(FATAL_ERROR "Could not set POPRAND_LIB. ${WhatToDoString}")
ENDIF()
MESSAGE(STATUS "Found POPRAND_LIB ${POPRAND_LIB}")
MARK_AS_ADVANCED(POPRAND_LIB)

SET(POPLAR_FIND_QUIETLY OFF)
IF (NOT POPLIBS_FIND_QUIETLY)
    MESSAGE(STATUS "Found all poplar and poplibs libs and headers!")
ENDIF (NOT POPLIBS_FIND_QUIETLY)