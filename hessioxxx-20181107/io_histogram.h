/* ============================================================================

   Copyright (C) 1993, 1997, 2001, 2009, 2010, 2013  Konrad Bernloehr

   This file is part of the eventio/hessio library.

   The eventio/hessio library is free software; you can redistribute it and/or
   modify it under the terms of the GNU Lesser General Public
   License as published by the Free Software Foundation; either
   version 2.1 of the License, or (at your option) any later version.

   This library is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   Lesser General Public License for more details.

   You should have received a copy of the GNU Lesser General Public License
   along with this library. If not, see <http://www.gnu.org/licenses/>.

============================================================================ */

/** @file io_histogram.h
 *  @short Declarations for eventio I/O of histograms.
 *
 *  @author  Konrad Bernloehr 
 *  @date    @verbatim CVS $Date: 2013/10/21 12:53:31 $ @endverbatim
 *  @version @verbatim CVS $Revision: 1.11 $ @endverbatim
 */

#ifndef IO_HISTOGRAM_H__LOADED
#define IO_HISTOGRAM_H__LOADED 1

#ifndef HISTOGRAM_H__LOADED
#include "histogram.h"
#endif

#ifdef __cplusplus
extern "C" {
#endif

/* io_histogram.c */
int write_histograms (HISTOGRAM **phisto, int nhisto, IO_BUFFER *iobuf);
int read_histograms (HISTOGRAM **phisto, int nhisto, IO_BUFFER *iobuf);
int read_histograms_x (HISTOGRAM **phisto, int nhisto, const long *xcld_ids, int nxcld, IO_BUFFER *iobuf);
int print_histograms (IO_BUFFER *iobuf);
int write_all_histograms (const char *fname);
int read_histogram_file (const char *fname, int add_flag);
int read_histogram_file_x (const char *fname, int add_flag, const long *xcld_ids, int nxcld);

#ifdef __cplusplus
}
#endif

#endif
