/* ============================================================================

   Copyright (C) 2000, 2003, 2008, 2009, 2010, 2011, 2014  Konrad Bernloehr

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

/** @file io_hess.h 
 *  @short Definition and structures for H.E.S.S./CTA data in eventio format.
 *
 *  This file contains definitions and data structures used
 *  for writing and reading HESS data (both Monte Carlo and
 *  real data) in the eventio format. It was then extended to
 *  include potential additional CTA data.
 *
 *  @author  Konrad Bernl&ouml;hr 
 *  @date initial version: July 2000
 *
 *  @date    @verbatim CVS $Date: 2018/09/11 13:20:49 $ @endverbatim
 *  @version @verbatim CVS $Revision: 1.105 $ @endverbatim
 */

/* ================================================================ */

#ifndef IO_HESS_HEADER
#define IO_HESS_HEADER 1

#define IO_HESS_VERSION 2

#include "mc_tel.h"

#ifdef __cplusplus
extern "C" {
#endif

/** Which index refers to which type of channel: */

#define HI_GAIN          0     /**< Index to high-gain channels in adc_sum, adc_sample, pedestal, ... */
#define LO_GAIN          1     /**< Index to low-gain channels in adc_sum, adc_sample, pedestal, ... */

/** Maximum sizes for various arrays: */

/* If it is not HESS phase 1 we are more genereous with memory consumption */

#ifndef HESS_PHASE_1
# ifndef NO_LARGE_TELESCOPE
#  define LARGE_TELESCOPE 1
# endif
# ifndef NO_SMARTPIXEL
#  define SMARTPIXEL 1
# endif
#ifndef H_MAX_TEL
# define H_MAX_TEL       16    /**< Maximum number of telescopes handled */
#endif
#endif

#ifdef CTA_MINI2
# define CTA_PROD2 2
# define CTA_MINI 2
#endif
#ifdef CTA_MINI3
# define CTA_PROD3 2
# define CTA_MINI 3
#endif
#ifdef CTA_MINI4
# define CTA_PROD4 2
# define CTA_MINI 4
#endif
#ifdef CTA_PROD3_DEMO
# define CTA_PROD3_SC 1
#endif
#ifdef CTA_ULTRA3
# define CTA_ULTRA 3
#endif
#ifdef CTA_ULTRA5
# define CTA_ULTRA 5
#endif
#ifdef CTA_PROD3_MERGE
# define CTA_MAX 1
#endif

/* You should, apart from an optional CTA definition, not have defined more than one of the following: */
#if defined(CTA) || \
    defined(HESS_PHASE_3) || \
    defined(CTA_ULTRA) || \
    defined(CTA_MAX) || \
    defined(CTA_SC) || \
    defined(CTA_PROD1) || \
    defined(CTA_PROD2) || \
    defined(CTA_PROD2_SC) || \
    defined(CTA_PROD3) || \
    defined(CTA_PROD3_SC) || \
    defined(CTA_PROD3_DEMO) || \
    defined(CTA_PROD4) || \
    defined(CTA_PROD4_SC) || \
    defined(CTA_PROD4_DEMO) || \
    defined(CTA_MAX_SC)
/* Checking more systematically now */
# ifdef CTA_ULTRA
#  if (CTA_ULTRA -0 == 3) || (CTA_ULTRA -0 == 2) || (CTA_ULTRA -0 == 1) || (CTA_ULTRA -0 == 0)
#   define CTA_PROD1 1
#  elif CTA_ULTRA -0 == 5
#   define CTA_PROD2 1
#  endif
#  undef CTA_ULTRA
#  if defined(CTA_PROD1)
#   define CTA_ULTRA 3
#  elif defined(CTA_PROD2)
#   define CTA_ULTRA 5
#  endif
# endif
# ifdef CTA_KIND
#  undef CTA_KIND
# endif
# ifdef CTA_MAX_SC
#  define CTA_KIND 7
/* #  undef CTA_MAX_SC */
# endif
# ifdef CTA_PROD4
#  ifdef CTA_KIND
#   error "Configuration conflict - use only one of them"
#  endif
#  define CTA_KIND 10
# endif
# if defined(CTA_PROD4_SC) || defined(CTA_PROD4_DEMO)
#  ifdef CTA_KIND
#   error "Configuration conflict - use only one of them"
#  endif
#  define CTA_KIND 11
# endif
# ifdef CTA_PROD3_SC
#  ifdef CTA_KIND
#   error "Configuration conflict - use only one of them"
#  endif
#  define CTA_KIND 9
# endif
# ifdef CTA_PROD3
#  ifdef CTA_KIND
#   error "Configuration conflict - use only one of them"
#  endif
#  define CTA_KIND 8
# endif
# ifdef CTA_PROD2_SC
#  ifdef CTA_KIND
#   error "Configuration conflict - use only one of them"
#  endif
#  define CTA_KIND 6
# endif
# ifdef CTA_PROD2
#  ifdef CTA_KIND
#   error "Configuration conflict - use only one of them"
#  endif
#  define CTA_KIND 5
# endif
# ifdef CTA_SC
#  ifdef CTA_KIND
#   error "Configuration conflict - use only one of them"
#  endif
#  define CTA_KIND 4
# endif
# ifdef CTA_MAX
#  ifdef CTA_KIND
#   error "Configuration conflict - use only one of them"
#  endif
#  define CTA_KIND 3
# endif
# if defined(CTA_PROD1)
#  ifdef CTA_KIND
#   error "Configuration conflict - use only one of them"
#  endif
#  define CTA_KIND 2
# endif
# ifdef HESS_PHASE_3
#  ifdef CTA_KIND
#   error "Configuration conflict - use only one of them"
#  endif
#  define CTA_KIND 1
# endif
# ifndef CTA_KIND
#  define CTA_KIND 0
# endif
# ifdef CTA
#  undef CTA
/* #  define CTA CTA_KIND */
# endif
# define CTA CTA_KIND

# ifdef H_MAX_TEL
#  undef H_MAX_TEL
# endif
# ifdef H_MAX_PIX
#  undef H_MAX_PIX
# endif

# if CTA_KIND == 0       /* CTA and nothing else: benchmark array */
#  define H_MAX_TEL 101
# elif CTA_KIND == 1     /* HESS_PHASE_3: 41 and 97 telescope configurations */
#  define H_MAX_TEL 102
# elif CTA_KIND == 2     /* CTA_PROD1 and CTA_ULTRA = 1 to 4: Prod-1 and similar */
#  define H_MAX_TEL 275
#  define H_MAX_PIX 2841
#  define H_SAVE_MEMORY 1
# elif CTA_KIND == 3     /* CTA_MAX: more telescopes */
#  define H_MAX_TEL 568
#  ifdef CTA_PROD3_MERGE
#   define H_MAX_PIX 2368
#  endif
#  define H_MAX_SECTORS 23310 /* Needed for ASTRI with 5NN (7770 with 4NN) */
# elif CTA_KIND == 4     /* CTA_SC: fewer telescopes but more pixels */
#  define H_MAX_TEL 61
#  if defined(CTA_SC)
#   if (CTA_SC == 3)
#    undef H_MAX_TEL
#    define H_MAX_TEL 111
#    define H_MAX_PIX 11328
#    define NO_LOW_GAIN
#   elif (CTA_SC == 2)
#    define H_MAX_PIX 11328
#    define NO_LOW_GAIN
#   elif (CTA_SC == 4 )
#    define H_MAX_PIX 11328
#   else
#    define H_MAX_PIX 14336
#   endif
#  endif
# elif CTA_KIND == 5     /* CTA_PROD2: prod-2 (without SCTs) */
#  define H_MAX_TEL 200
#  define H_MAX_PIX 2368
#  define NO_LOW_GAIN
#  ifndef H_MAX_TRG_PER_SECTOR
#   define H_MAX_TRG_PER_SECTOR 3
#  endif
#  if ( H_MAX_PIX*H_MAX_TRG_PER_SECTOR < 10138 )
#   define H_MAX_SECTORS 10138
#  else
#   define H_MAX_SECTORS (H_MAX_PIX*H_MAX_TRG_PER_SECTOR)
#  endif
# elif CTA_KIND == 6     /* CTA_PROD2_SC: prod-2 with SCTs */
#  define H_MAX_TEL 229
#  define H_MAX_PIX 11328
#  define NO_LOW_GAIN
#  ifndef H_MAX_TRG_PER_SECTOR
#   define H_MAX_TRG_PER_SECTOR 3
#  endif
#  define H_MAX_SECTORS (2*H_MAX_PIX) /* actually 16292 for SCTs, fewer for others */
# elif CTA_KIND == 7    /* CTA_MAX_SC: more telescopes and pixels */
#  define H_MAX_TEL 624 /* prod2: 197 + 111 + 102, so we can merge data from three simulations */
#  define H_MAX_PIX 11328
#  ifndef H_MAX_TRG_PER_SECTOR
#   define H_MAX_TRG_PER_SECTOR 3
#  endif
#  define H_MAX_SECTORS 53508 /* Biggest number needed so far */
# elif CTA_KIND == 8 /* CTA_PROD3 preliminary */
#  define H_MAX_TEL 200
#  define H_MAX_PIX 2368
#  ifndef H_MAX_TRG_PER_SECTOR
#   define H_MAX_TRG_PER_SECTOR 4
#  endif
#  if ( H_MAX_PIX*H_MAX_TRG_PER_SECTOR < 23310 )
#   define H_MAX_SECTORS 23310 /* Needed for ASTRI with 5NN */
#  else
#   define H_MAX_SECTORS (H_MAX_PIX*H_MAX_TRG_PER_SECTOR)
#  endif
# elif CTA_KIND == 9 /* CTA_PROD3_SC preliminary */
#  ifdef CTA_PROD3_DEMO
#   define H_MAX_TEL 126
#  else
#   define H_MAX_TEL 70
#  endif
#  define H_MAX_PIX 11328
#  ifndef H_MAX_TRG_PER_SECTOR
#   define H_MAX_TRG_PER_SECTOR 4
#  endif
#  define H_MAX_SECTORS 53508 /* Needed for latest SCT configuration */
# elif CTA_KIND == 10 /* CTA_PROD4 preliminary */
#  define H_MAX_TEL 99
#  define H_MAX_PIX 2368
#  ifndef H_MAX_TRG_PER_SECTOR
#   define H_MAX_TRG_PER_SECTOR 4
#  endif
#  if ( H_MAX_PIX*H_MAX_TRG_PER_SECTOR < 23310 )
#   define H_MAX_SECTORS 23310 /* Needed for ASTRI with 5NN */
#  else
#   define H_MAX_SECTORS (H_MAX_PIX*H_MAX_TRG_PER_SECTOR)
#  endif
#  ifndef MAXIMUM_SLICES
#   define MAXIMUM_SLICES 160
#  endif
# elif CTA_KIND == 11 /* CTA_PROD4_SC or CTA_PROD4_DEMO preliminary */
#  define H_MAX_TEL 126
#  define H_MAX_PIX 11328
#  ifndef H_MAX_TRG_PER_SECTOR
#   define H_MAX_TRG_PER_SECTOR 4
#  endif
#  define H_MAX_SECTORS 53508 /* Needed for latest SCT configuration */
#  ifndef MAXIMUM_SLICES
#   define MAXIMUM_SLICES 160
#  endif
# endif

#ifndef H_MAX_TRG_PER_SECTOR
# define H_MAX_TRG_PER_SECTOR 1
#endif
#ifndef H_MAX_SECTORS
# define H_MAX_SECTORS (H_MAX_PIX*H_MAX_TRG_PER_SECTOR)
#endif

#ifdef CTA_MINI
# undef H_MAX_TEL
# define H_MAX_TEL 25
#endif

# ifndef LARGE_TELESCOPE
#  define LARGE_TELESCOPE 1
# endif
# ifndef H_MAX_TEL
#  define H_MAX_TEL 103
# endif
# ifndef H_MAX_PIX
#  define H_MAX_PIX 4095
# endif

#endif

#ifndef H_MAX_TRG_PER_SECTOR
# define H_MAX_TRG_PER_SECTOR 1
#endif

/* Enlarged limits for a super-HESS/CTA telescope type etc... */

#ifdef ULTRA_FINE_PIXELS
# ifdef H_MAX_PIX
#  undef H_MAX_PIX
# endif
# ifndef H_MAX_PIX
#  define H_MAX_PIX 40000       /**< This may need huge amounts of memory. */
# endif
#endif

#ifdef LARGE_TELESCOPE
# ifndef H_MAX_PIX
#  define H_MAX_PIX 4095
# endif
# ifdef SMARTPIXEL
#  ifndef H_MAX_SECTORS 
#   ifdef CTA_SC
#    define H_MAX_SECTORS (2*H_MAX_PIX*H_MAX_TRG_PER_SECTOR)
#   else
#    define H_MAX_SECTORS (H_MAX_PIX*H_MAX_TRG_PER_SECTOR)
#   endif
#  endif
#  ifndef H_MAX_DRAWERS 
#   define H_MAX_DRAWERS H_MAX_PIX
#  endif
# endif
# ifndef H_MAX_DRAWERS
#  define H_MAX_DRAWERS 256
# endif
# ifndef H_MAX_SECTORS 
#  define H_MAX_SECTORS 200
# endif
#endif

/* Version for visualization of shower images with extreme resolution */

#ifdef MEGAPIX
# undef H_MAX_TEL
# define H_MAX_TEL 5
# undef H_MAX_PIX
# define H_MAX_PIX 230000
# undef H_MAX_SECTORS
# define H_MAX_SECTORS 230000
# undef H_MAX_DRAWERS
# define H_MAX_DRAWERS 230000
#endif

/* Otherwise limits correspond to HESS phase 1 telescopes. */

#ifndef H_MAX_TEL
# define H_MAX_TEL         4    /**< Maximum number of telescopes handled */
#endif
#ifndef H_MAX_PIX
# define H_MAX_PIX        960  /**< Maximum number of pixels handled */
#endif
# ifdef NO_LOW_GAIN
#  define H_MAX_GAINS      1    /**< Maximum number of different gains per PM */
# else
#  define H_MAX_GAINS      2    /**< Maximum number of different gains per PM */
# endif
#ifndef H_MAX_SECTORS
# define H_MAX_SECTORS    38   /**< Max. no. of `sectors' (trigger groups) */
#endif
#ifdef CTA
# define H_MAX_PIXSECTORS 19   /**< 7*majo + 6*asum  + 6*dsum */
#else
# define H_MAX_PIXSECTORS 4
#endif
#ifndef H_MAX_DRAWERS
# define H_MAX_DRAWERS    60   /**< Maximum number of drawers. */
#endif
#if defined(CTA_PROD1) || defined(SAVE_MEMORY)
# ifndef H_SAVE_MEMORY
#  define H_SAVE_MEMORY 1
# endif
#endif
#ifdef H_SAVE_MEMORY
# if defined(CTA_PROD2) || defined(CTA_SC) || defined(CTA_PROD2_SC) || \
   defined(CTA_PROD3) || defined(CTA_PROD3_SC) || defined(CTA_MAX_SC) || defined(CTA_MAX)
#  define H_MAX_SLICES     96   /**< Maximum number of time slices handled. */
# else
#  define H_MAX_SLICES     40   /**< Maximum number of time slices handled. */
# endif
#else
# ifndef H_MAX_SLICES
#  define H_MAX_SLICES     128  /**< Maximum number of time slices handled. */
# endif
#endif
#define H_MAX_HOTPIX     5     /**< The max. size of the list of hottest pix. */
#define H_MAX_PROFILE    10    /**< The max. number of MC shower profiles. */
#define H_MAX_D_TEMP     8
#define H_MAX_C_TEMP     10
#define H_MAX_FSHAPE     1000  /**< Max. number of (sub-) samples of reference pulse shapes. */
#define H_MAX_TRG_TYPES  4

/** Compile-time override of the most relevant limits: */
#ifdef MAXIMUM_TELESCOPES
# undef H_MAX_TEL
# define H_MAX_TEL MAXIMUM_TELESCOPES
#endif
#ifdef MAXIMUM_PIXELS
# undef H_MAX_PIX
# define H_MAX_PIX MAXIMUM_PIXELS
#endif
#ifdef MAXIMUM_SECTORS
# undef H_MAX_SECTORS
# define H_MAX_SECTORS MAXIMUM_SECTORS
#endif
#ifdef MAXIMUM_DRAWERS
# undef H_MAX_DRAWERS
# define H_MAX_DRAWERS MAXIMUM_DRAWERS
#endif
#ifdef MAXIMUM_SLICES
# undef H_MAX_SLICES
# define H_MAX_SLICES MAXIMUM_SLICES
#endif

/** Macro expanding into a function call checking if user function */
/** is taking the same maximum array sizes as the library. */

#define H_CHECK_MAX() check_hessio_max(11,H_MAX_TEL,H_MAX_PIX,H_MAX_SECTORS,\
   H_MAX_DRAWERS,H_MAX_PIXSECTORS,H_MAX_SLICES,H_MAX_HOTPIX,H_MAX_PROFILE,\
   H_MAX_D_TEMP,H_MAX_C_TEMP,H_MAX_GAINS);

void check_hessio_max (int ncheck, int max_tel, int max_pix, int max_sectors,
  int max_drawers, int max_pixsectors, int max_slices, int max_hotpix, 
  int max_profile, int max_d_temp, int max_c_temp, int max_gains);
void show_hessio_max (void);

/** Flags used for saving and restoring event data: */

#define RAWDATA_FLAG   0x01
#define RAWSUM_FLAG    0x02
#define TRACKRAW_FLAG  0x04
#define TRACKCOR_FLAG  0x08
#define TRACKDATA_FLAG (TRACKRAW_FLAG|TRACKCOR_FLAG)
#define IMG_BASE_FLAG  0x10
#define IMG_ERR_FLAG   0x20
#define IMG_34M_FLAG   0x40
#define IMG_HOT_FLAG   0x80
#define IMG_PIXTM_FLAG 0x100
#define IMAGE_FLAG (IMG_BASE_FLAG|IMG_ERR_FLAG|IMG_34M_FLAG|IMG_HOT_FLAG|IMG_PIXTM_FLAG)
#define TIME_FLAG      0x200
#define SHOWER_FLAG    0x400
#define CALSUM_FLAG    0x800

/* I/O item types: */

/** Never change the following numbers after MC data is created: */
#define IO_TYPE_HESS_BASE         2000
#define IO_TYPE_HESS_RUNHEADER    (IO_TYPE_HESS_BASE+0)
#define IO_TYPE_HESS_MCRUNHEADER  (IO_TYPE_HESS_BASE+1)
#define IO_TYPE_HESS_CAMSETTINGS  (IO_TYPE_HESS_BASE+2)
#define IO_TYPE_HESS_CAMORGAN     (IO_TYPE_HESS_BASE+3)
#define IO_TYPE_HESS_PIXELSET     (IO_TYPE_HESS_BASE+4)
#define IO_TYPE_HESS_PIXELDISABLE (IO_TYPE_HESS_BASE+5)
#define IO_TYPE_HESS_CAMSOFTSET   (IO_TYPE_HESS_BASE+6)
#define IO_TYPE_HESS_POINTINGCOR  (IO_TYPE_HESS_BASE+7)
#define IO_TYPE_HESS_TRACKSET     (IO_TYPE_HESS_BASE+8)
#define IO_TYPE_HESS_CENTEVENT    (IO_TYPE_HESS_BASE+9)
#define IO_TYPE_HESS_TRACKEVENT   (IO_TYPE_HESS_BASE+100)
#define IO_TYPE_HESS_TELEVENT     (IO_TYPE_HESS_BASE+200)
#define IO_TYPE_HESS_EVENT        (IO_TYPE_HESS_BASE+10)
#define IO_TYPE_HESS_TELEVTHEAD   (IO_TYPE_HESS_BASE+11)
#define IO_TYPE_HESS_TELADCSUM    (IO_TYPE_HESS_BASE+12)
#define IO_TYPE_HESS_TELADCSAMP   (IO_TYPE_HESS_BASE+13)
#define IO_TYPE_HESS_TELIMAGE     (IO_TYPE_HESS_BASE+14)
#define IO_TYPE_HESS_SHOWER       (IO_TYPE_HESS_BASE+15)
#define IO_TYPE_HESS_PIXELTIMING  (IO_TYPE_HESS_BASE+16)
#define IO_TYPE_HESS_PIXELCALIB   (IO_TYPE_HESS_BASE+17)
#define IO_TYPE_HESS_MC_SHOWER    (IO_TYPE_HESS_BASE+20)
#define IO_TYPE_HESS_MC_EVENT     (IO_TYPE_HESS_BASE+21)
#define IO_TYPE_HESS_TEL_MONI     (IO_TYPE_HESS_BASE+22)
#define IO_TYPE_HESS_LASCAL       (IO_TYPE_HESS_BASE+23)
#define IO_TYPE_HESS_RUNSTAT      (IO_TYPE_HESS_BASE+24)
#define IO_TYPE_HESS_MC_RUNSTAT   (IO_TYPE_HESS_BASE+25)
#define IO_TYPE_HESS_MC_PE_SUM    (IO_TYPE_HESS_BASE+26)
#define IO_TYPE_HESS_PIXELLIST    (IO_TYPE_HESS_BASE+27)
#define IO_TYPE_HESS_CALIBEVENT   (IO_TYPE_HESS_BASE+28)
#define IO_TYPE_HESS_AUX_DIGITAL_TRACE (IO_TYPE_HESS_BASE+29)
#define IO_TYPE_HESS_AUX_ANALOG_TRACE  (IO_TYPE_HESS_BASE+30)
#define IO_TYPE_HESS_FS_PHOT      (IO_TYPE_HESS_BASE+31)
#define IO_TYPE_HESS_PIXELTRG_TM  (IO_TYPE_HESS_BASE+32)

/** Run header common to measured and simulated data. */

struct hess_run_header_struct
{
   /** Recorded data: */
   int run;                  ///< Run number.
   time_t time;              ///< Time of run start [UTC sec since 1970.0].
   int run_type;             ///< Data/pedestal/laser/muon run or MC run:
                             ///<   MC run: -1,
                             ///<   Data run: 1,
                             ///<   Pedestal run: 2,
                             ///<   Laser run: 3,
                             ///<   Muon run: 4.
   int tracking_mode;        ///< Tracking/pointing mode:
                             ///<   0: Az/Alt, 1: R.A./Dec. 2000
   int reverse_flag;         ///< Normal or reverse tracking:
                             ///<   0: Normal, 1: reverse.
   double direction[2];      ///< Tracking/pointing direction in [radians]:
                             ///<   [0]=Azimuth, [1]=Altitude in mode 0,
                             ///<   [0]=R.A., [1]=Declination in mode 1.
   double offset_fov[2];     ///< Offset of pointing dir. in camera f.o.v.
                             ///<   divided by focal length, 
                             ///<   i.e. converted to [radians]:
                             ///<   [0]=Camera x (downwards in normal pointing,
                             ///<   i.e. increasing Alt, [1]=Camera y -> Az).
   double conv_depth;        ///< Atmospheric depth of convergence point.
                             ///<   In [g/cm^2] from the top of the atmosphere
                             ///<   along the system viewing direction.
                             ///<   Typically 0 for parallel viewing or
                             ///<   about Xmax(0.x TeV) for convergent viewing.
   double conv_ref_pos[2];   ///< Reference position for convergent pointing.
                             ///<   X,y in [m] at the telescope reference height.
   int ntel;                 ///< Number of telescopes involved.
   int tel_id[H_MAX_TEL];    ///< ID numbers of telescopes used in this run.
   double tel_pos[H_MAX_TEL][3];  ///< x,y,z positions of the telescopes [m].
                             ///<   x is counted from array reference position
                             ///<   towards North, y towards West, z upwards.
   int min_tel_trig;         ///< Minimum number of tel. in system trigger.
   int duration;             ///< Nominal duration of run [s].
   char *target;             ///< Primary target object name.
   char *observer;           ///< Observer(s) starting or supervising run.
   /** For internal data handling only: */
   int max_len_target;
   int max_len_observer;
};
typedef struct hess_run_header_struct RunHeader;

/** MC run header */

struct hess_mc_run_header_struct
{
   /** Recorded data: */
   int shower_prog_id;      ///< CORSIKA=1, ALTAI=2, KASCADE=3, MOCCA=4.
   int shower_prog_vers;    ///< version * 1000
   time_t shower_prog_start; ///< Time when shower simulation of run started (CORSIKA: only date)
   int detector_prog_id;    ///< sim_telarray=1, ...
   int detector_prog_vers;  ///< version * 1000
   time_t detector_prog_start; ///< Time when detector simulation of run started   
   double obsheight;        ///< Height of simulated observation level.
   int num_showers;         ///< Number of showers (intended to be) simulated.
   int num_use;             ///< Number of uses of each shower.
   int core_pos_mode;       ///< Core position fixed/circular/rectangular/...
   double core_range[2];    ///< rmin+rmax or dx+dy [m].
   double az_range[2];      ///< Range of shower azimuth [rad, N->E].
   double alt_range[2];     ///< Range of shower altitude [rad].
   int diffuse;             ///< Diffuse mode off/on
   double viewcone[2];      ///< Min.+max. opening angle for diffuse mode [degrees] (was always in degrees despite earlier '[rad]' comment).
   double E_range[2];       ///< Energy range [TeV] of simulated showers.
   double spectral_index;   ///< Power-law spectral index of spectrum (<0).
   double B_total;          ///< Total geomagnetic field assumed [microT].
   double B_inclination;    ///< Inclination of geomagnetic field [rad].
   double B_declination;    ///< Declination of geomagnetic field [rad].
   double injection_height; ///< Height of particle injection [m].
   double fixed_int_depth;  ///< Fixed depth of first interaction or 0 [g/cm^2].
   int atmosphere;          ///< Atmospheric model number.
   /* ... + shower MC specific ... */
   int corsika_iact_options;
   int corsika_low_E_model;
   int corsika_high_E_model;
   double corsika_bunchsize;
   double corsika_wlen_min;
   double corsika_wlen_max;
   int corsika_low_E_detail;
   int corsika_high_E_detail;
   /* ... + detector MC specific ... */
};
typedef struct hess_mc_run_header_struct MCRunHeader;

#define HAS_CORSIKA_INTERACTION_DETAIL 1

/** Definition of camera optics settings. */

struct hess_camera_settings_struct
{
   int tel_id;              ///< Telescope ID.
   int num_pixels;          ///< Number of pixels in camera.
   double xpix[H_MAX_PIX];  ///< Pixel x position in camera [m].
   double ypix[H_MAX_PIX];  ///< Pixel y position in camera [m].
   double zpix[H_MAX_PIX];  ///< Pixel z position w.r.t. focal plane in camera center [m].  {new}
   double nxpix[H_MAX_PIX]; ///< Pixel pointing direction (nx,ny,1) x component. {new}
   double nypix[H_MAX_PIX]; ///< Pixel pointing direction (nx,ny,1) y component. {new}
   double area[H_MAX_PIX];  ///< Pixel active area ([m^2]).
   double size[H_MAX_PIX];  ///< Pixel diameter (flat-to-flat, [m]).
   int pixel_shape[H_MAX_PIX]; ///< Pixel shape type (0: circ., 1,3: hex, 2: square, -1: unknown). {new}
   double cam_rot;          ///< Rotation angle of camera (counter-clock-wise from back side for prime focus camera).
   // Main telescope optics parameters included here:
   double flen;             ///< Focal length of optics (geometric or nominal) [m].
   double eff_flen;         ///< Suggested effective focal length for image scale (can be zero). [m]
   int num_mirrors;         ///< Number of mirror tiles.
   double mirror_area;      ///< Total area of individual mirrors corrected
                            ///< for inclination [m^2].
   int curved_surface;      ///< 0 for flat surface, 1 for curved surface. {new}
   int pixels_parallel;     ///< 0 if (some) pixels are inclined, 1 if all pixels are parallel {new}
   int common_pixel_shape;  ///< instead of individual pixel shape if al pixels are the same. {new}
};
typedef struct hess_camera_settings_struct CameraSettings;

/** Logical organisation of camera electronics channels. */

struct hess_camera_organisation_struct
{
   int tel_id;              ///< Telescope ID.
   int num_pixels;          ///< Number of pixels in camera.
   int num_drawers;         ///< Number of drawers (mechanical units) in camera.
   int num_gains;           ///< Number of gains per PM.
   int num_sectors;         ///< Number of sectors (trigger groups).
   int drawer[H_MAX_PIX];   ///< Drawer assignment for each pixel.
   int card[H_MAX_PIX][H_MAX_GAINS];
   int chip[H_MAX_PIX][H_MAX_GAINS];
   int channel[H_MAX_PIX][H_MAX_GAINS];
   int nsect[H_MAX_PIX];    ///< Number of sectors (trigger groups) for trigger(s).
   int sectors[H_MAX_PIX][H_MAX_PIXSECTORS]; ///< Pixels in sectors (trigger groups).
   int sector_type[H_MAX_SECTORS]; ///< 0: majority, 1: analog sum, 2: digital sum
   /* We could think of different settings for same type of trigger, e.g. one
      with a small number of pixels above a high threshold and one with many 
      pixels above a low threshold. */
   double sector_threshold[H_MAX_SECTORS]; ///< Multiplicity or sum threshold applied to sector. [mV ?]
   double sector_pixthresh[H_MAX_SECTORS]; ///< Pixel threshold for majority or clipping limit for sum triggers. [mV ?]
};
typedef struct hess_camera_organisation_struct CameraOrganisation;

/** Settings of pixel HV and thresholds. */

struct hess_pixel_setting_struct
{
   int tel_id;                   ///< The telescope ID number (1 ... n)
   int setup_id;
   int trigger_mode;
   int min_pixel_mult;           ///< The minimum number of pixels in a camera.
   int num_pixels;               ///< Local copy of the number of pixels.
   int pixel_HV_DAC[H_MAX_PIX];  ///< High voltage DAC values set.
   int num_drawers;              ///< Local copy of the number of drawers in the camera
   int threshold_DAC[H_MAX_DRAWERS];  ///< Threshold DAC values set.
   int ADC_start[H_MAX_DRAWERS];      
   int ADC_count[H_MAX_DRAWERS];
   double time_slice;            ///< Width of readout time slice (i.e. one sample) [ns].
   int sum_bins;                 ///< Standard integration over so many time slices.
   int nrefshape;                ///< Number of following reference pulse shapes (num_gains or 0)
   int lrefshape;                ///< Length of following reference pulse shape(s).
   double refshape[H_MAX_GAINS][H_MAX_FSHAPE];///< Reference pulse shape(s).
   double ref_step;              ///< Time step between refshape entries [ns].
};
typedef struct hess_pixel_setting_struct PixelSetting;

/** Pixels disabled in HV and/or trigger. */

struct hess_pixel_disabled_struct
{
   int tel_id;             ///< The telescope ID number (1 ... n)
   int num_trig_disabled;
   int trigger_disabled[H_MAX_PIX];
   int num_HV_disabled;
   int HV_disabled[H_MAX_PIX];
};
typedef struct hess_pixel_disabled_struct PixelDisabled;

/** Software settings used in camera process. */

struct hess_camera_software_setting_struct
{
   int tel_id;             ///< The telescope ID number (1 ... n)
   int dyn_trig_mode;
   int dyn_trig_threshold;
   int dyn_HV_mode;
   int dyn_HV_threshold;
   int data_red_mode;      ///< The desired data reduction mode.
   int zero_sup_mode;      ///< The desired zero suppression mode.
                           ///< The mode actually used may depend on the data.
   int zero_sup_num_thr;   ///< The number of thresholds to be used by z.s.
   int zero_sup_thresholds[10]; ///< Threshold values to be used by z.s.
   int unbiased_scale;
   int dyn_ped_mode;
   int dyn_ped_events;
   int dyn_ped_period;     ///< [ms]
   int monitor_cur_period; ///< [ms]
   int report_cur_period;  ///< [ms]
   int monitor_HV_period;  ///< [ms]
   int report_HV_period;   ///< [ms]
};
typedef struct hess_camera_software_setting_struct CameraSoftSet;

/**
 *  @short Definition of tracking parameters.
 *  This is a copy of the configuration given to the tracking computers.
 *  Note: all angles are in radians.
 *  This block should not be needed for event analysis.
*/

struct hess_tracking_setup_struct
{
   int tel_id;               ///< Telescope ID.
   int known;
   int drive_type_az;        ///< 0 for now.
   int drive_type_alt;       ///< 0 for now.
   double zeropoint_az;      ///< Offsets subtracted from the values reported
   double zeropoint_alt;     ///< by hardware before calculating 'raw' angles [rad].
   double sign_az;           ///< This is -1 if hardware counts the other way than
   double sign_alt;          ///< we do, and +1 otherwise.
   double resolution_az;     ///< Typical resolution expected [rad].
   double resolution_alt;    ///< Typical resolution expected [rad].
   /** Note: The values may be outside the [0...2*pi[ range. */
   double range_low_az;
   double range_low_alt;
   double range_high_az;
   double range_high_alt;
   double park_pos_az;
   double park_pos_alt;
};
typedef struct hess_tracking_setup_struct TrackingSetup;

/** Pointing correction parameters. */

struct hess_pointing_correction_struct
{
   int tel_id;             ///< The telescope ID number (1 ... n)
   int function_type;
   int num_param;
   double pointing_param[20];
};
typedef struct hess_pointing_correction_struct PointingCorrection;

/** Breakdown of time into seconds since 1970.0 and nanoseconds. */

struct hess_time_struct
{
   long seconds;
   long nanoseconds;
};
typedef struct hess_time_struct HTime;

/** ADC data (either sampled or sum mode) */

struct hess_tel_event_adc_struct
{
   int known;          ///< Must be set to 1 if and only if raw data is available.
   int tel_id;         ///< Must match the expected telescope ID when reading.
   int num_pixels;     ///< The number of pixels in the camera (as in configuration)
   int num_gains;      ///< The number of different gains per pixel (2 for HESS).
   int num_samples;    ///< The number of samples (time slices) recorded.
   int zero_sup_mode;  ///< The desired or used zero suppression mode.
   int data_red_mode;  ///< The desired or used data reduction mode.
   int offset_hg8;     ///< The offset to be used in shrinking high-gain data.
   int scale_hg8;      ///< The scale factor (denominator) in shrinking h-g data.
   int threshold;      ///< Threshold (in high gain) for recording low-gain data.
   int list_known;     ///< Was list of significant pixels filled in?
   int list_size;      ///< Size of the list of available pixels (with list mode).
   int adc_list[H_MAX_PIX];  ///< List of available pixels (with list mode).
   uint8_t significant[H_MAX_PIX];  ///< Was amplitude large enough to record it? Bit 0: sum, 1: samples.
   uint8_t adc_known[H_MAX_GAINS][H_MAX_PIX]; ///< Was individual channel recorded? Bit 0: sum, 1: samples, 2: ADC was in saturation.
   uint32_t adc_sum[H_MAX_GAINS][H_MAX_PIX];  ///< Sum of ADC values.
   uint16_t adc_sample[H_MAX_GAINS][H_MAX_PIX][H_MAX_SLICES]; ///< Pulses sampled.
};
typedef struct hess_tel_event_adc_struct AdcData;

/* Auxilliary digital trace (derived from FADC samples) */

struct hess_aux_digital_trace
{
   int known;              ///< Must be set to 1 if and only if corresponding data is available.
   int tel_id;             ///< Must match the expected telescope ID when reading.
   int trace_type;         ///< Indicate what type of trace we have (1: DigitalSum trigger trace)
   float time_scale;       ///< Time per auxilliary sample over time per normal FADC sample (typ.: 1.0)
   size_t num_traces;      ///< The number of traces coming from the camera.
   size_t len_traces;      ///< The length of each trace in FADC samples.
   uint16_t *trace_data;   ///< Allocated on first use with num_traces*len_traces elements.
};
typedef struct hess_aux_digital_trace AuxTraceD;

/* Auxilliary analog trace (part of analog majority or sum trigger processing) */

struct hess_aux_analog_trace
{
   int known;              ///< Must be set to 1 if and only if corresponding data is available.
   int tel_id;             ///< Must match the expected telescope ID when reading.
   int trace_type;         ///< Indicate what type of trace we have (1: pixel input, 2: analog sum, 3: disc/comp. output, 4: majority input)
   float time_scale;       ///< Time per auxilliary sample over time per normal FADC sample (typ.: 0.25)
   size_t num_traces;      ///< The number of traces coming from the camera.
   size_t len_traces;      ///< The length of each trace in FADC samples.
   float *trace_data;      ///< Allocated on first use with num_traces*len_traces elements.
};
typedef struct hess_aux_analog_trace AuxTraceA;

#define MAX_AUX_TRACE_D 1   /**< Only one auxilliary digital trace */
#define MAX_AUX_TRACE_A 4   /**< Up to four auxilliary analog traces */
 
/** In addition to ADC we may (optionally) also have timing data. */

#define H_MAX_PIX_TIMES 7

#define PIX_TIME_PEAKPOS_TYPE 1       /**< Position of peak in time (slices since readout). */
#define PIX_TIME_STARTPOS_REL_TYPE 2  /**< Position of first rise above fraction of peak ampl. */
#define PIX_TIME_STARTPOS_ABS_TYPE 3  /**< Position of first rise above absolute threshold. */
#define PIX_TIME_WIDTH_REL_TYPE 4     /**< Width of pulse over fraction of peak ampl. */
#define PIX_TIME_WIDTH_ABS_TYPE 5     /**< Width of pulse over absolute threshold (time over threshold). */

struct hess_pixel_timing_struct
{
   int known;                 ///< is pixel timing data known?
   int tel_id;                ///< Telescope ID
   int num_pixels;            ///< Pixels in camera: list should be in this range.
   int num_gains;             ///< Number of different gains per pixel.
   int list_type;             ///< 0: not set; 1: individual pixels; 2: pixel ranges.
   int list_size;             ///< The size of the pixels in this list.
   int pixel_list[2*H_MAX_PIX]; ///< The actual list of pixel numbers.
   int threshold;             ///< Minimum base-to-peak raw amplitude
                              ///< difference applied in pixel selection.
   int before_peak;           ///< Number of bins before peak being summed up.
   int after_peak;            ///< Number of bins after peak being summed up.
   int num_types;             ///< How many different types of times can we store?
   int time_type[H_MAX_PIX_TIMES]; ///< Which types come in which order.
   float time_level[H_MAX_PIX_TIMES]; ///< The width and startpos types apply
                              ///< above some fraction from base to peak.
   float granularity;         ///< Actually stored are the following timvals
                              ///< divided by granularity, as 16-bit integers.
                              ///< Set this to e.g. 0.25 for a 0.25 time slice
                              ///< stepping.
   float peak_global;         ///< Camera-wide (mean) peak position [time slices].
   float timval[H_MAX_PIX][H_MAX_PIX_TIMES]; ///< Only the first 'pixels'
                              ///< elements are actually filled and stored.
                              ///< Others are undefined.
   int pulse_sum_loc[H_MAX_GAINS][H_MAX_PIX]; ///< Amplitude sum around
                              ///< local peak, for pixels in list. Ped. subtr.
                              ///< Only present if before&after_peak>=0.
   int pulse_sum_glob[H_MAX_GAINS][H_MAX_PIX]; ///< Amplitude sum around
                              ///< global peak; for all pixels. Ped. subtracted.
                              ///< Only present if before&after_peak>=0 and
                              ///< if list is of size>0 (otherwise no peak).
};
typedef struct hess_pixel_timing_struct PixelTiming;

struct hess_pixeltrg_time_struct
{
   int known;                 ///< is pixel timing data known?
   int tel_id;                ///< Telescope ID
   double time_step;          ///< Time interval [ns] after telescope trigger in which times are reported.
   int num_times;             ///< Number of fired discriminators for which time gets reported.
   int pixel_list[H_MAX_PIX]; ///< List of pixels IDs for which times get reported.
   int pixel_time[H_MAX_PIX]; ///< Time when pixel disciminator/comparator fired, in units of given time intercal since telescope trigger.
};
typedef struct hess_pixeltrg_time_struct PixelTrgTime;

struct hess_pixel_calibrated_struct
{
   int known;                 ///< is calibrated pixel data known?
   int tel_id;                ///< Telescope ID
   int num_pixels;            ///< Pixels in camera: list should be in this range.
   int int_method;            ///< -2 (timing local peak), -1 (timing global peak), >=0 (integration scheme, if known)
   int list_known;            ///< Was list of significant pixels filled in? 1: use list, 2: all pixels significant
   int list_size;             ///< Size of the list of available pixels (with list mode). 
   int pixel_list[H_MAX_PIX];   ///< List of available pixels (with list mode).
   uint8_t significant[H_MAX_PIX];  ///< Was amplitude large enough to record it?
   float pixel_pe[H_MAX_PIX]; ///< Calibrated & flat-fielded pixel intensity [p.e.]
};
typedef struct hess_pixel_calibrated_struct PixelCalibrated;

/** Lists of pixels (triggered, selected, etc.) */

struct hess_pixel_list
{
   int code;               ///< Indicates what sort of list this is:
                           ///< 0 (triggered pixel), 1 (selected pixel), ...
   int pixels;             ///< The size of the pixels in this list.
   int pixel_list[H_MAX_PIX]; ///< The actual list of pixel numbers.
};
typedef struct hess_pixel_list PixelList;

/** Image parameters */

struct hess_tel_image_struct
{
   int known;        ///< is image data known?
   int tel_id;       ///< Telescope ID
   int pixels;       ///< number of pixels used for image

   int cut_id;       ///< For which set of tail-cuts was used.
   double amplitude; ///< Image amplitude (="SIZE") [mean p.e.]
   double clip_amp;  ///< Pixel amplitude clipping level [mean p.e.] or zero for no clipping.
   int num_sat;      ///< Number of pixels in saturation (ADC saturation or dedicated clipping).
   /** Position */
   double x;         ///< X position (c.o.g.) [rad], corrected for any camera rotation.
   double x_err;     ///< Error on x (0: error not known, <0: x not known) [rad]
   double y;         ///< Y position (c.o.g.) [rad], corrected for any camera rotation.
   double y_err;     ///< Error on y (0: error not known, <0: y not known) [rad]
   /** Orientation */
   double phi;       ///< Angle of major axis w.r.t. x axis [rad], corrected for any camera rotation.
   double phi_err;   ///< Error on phi (0: error not known, <0: phi not known) [rad]
   /** Shape */
   double l;         ///< Length (major axis) [rad]
   double l_err;     ///< Error on length (0: error not known, <0: l not known) [rad]
   double w;         ///< Width (minor axis) [rad]
   double w_err;     ///< Error on width (0: error not known, <0: w not known) [rad]
   double skewness;      ///< Skewness, indicating asymmetry of image
   double skewness_err;  ///< Error (0: error not known, <0: skewness not known)
   double kurtosis;      ///< Kurtosis, indicating sharpness of peak of image
   double kurtosis_err;  ///< Error (0: error not known, <0: kurtosis not known)
   int num_conc;         ///< Number of hottest pixels used for concentration
   double concentration; ///< Fraction of total amplitude in num_conc hottest pixels
   /** Timing */
   double tm_slope;      ///< Slope in peak times along major axis as given by phi. [ns/rad]
   double tm_residual;   ///< R.m.s. average residual time after slope correction. [ns]
   double tm_width1;     ///< Average pulse width (50% of peak or time over threshold) [ns]
   double tm_width2;     ///< Average pulse width (20% of peak or 0) [ns]
   double tm_rise;       ///< Average pixel rise time (or 0) [ns]

   /** Individual pixels */
   int num_hot;          ///< Number of hottest pixels individually saved
   int hot_pixel[H_MAX_HOTPIX];  ///< Pixel IDs of hotest pixels
   double hot_amp[H_MAX_HOTPIX]; ///< Amplitudes of hotest pixels [mean p.e.]
};
typedef struct hess_tel_image_struct ImgData;

/** Event raw and image data from one telescope. */

struct hess_tel_event_data_struct
{
   int known;
   int tel_id;             ///< The telescope ID number (1 ... n)
   int loc_count;          ///< The counter for local triggers.
   int glob_count;         ///< The counter for system triggers.
   HTime cpu_time;         ///< Camera CPU system time of event.
   HTime gps_time;         ///< GPS time of event, if any.
   int trg_source;         ///< 1=internal (event data) or 2=external (calib data).
   int num_list_trgsect;   ///< Number of trigger groups (sectors) listed.
   int list_trgsect[H_MAX_SECTORS]; ///< List of triggered groups (sectors).
   int known_time_trgsect; ///< Are the trigger times known? (0/1)
   double time_trgsect[H_MAX_SECTORS]; ///< Times when trigger groups (as in list) fired.
//   char type_trgsect[H_MAX_SECTORS]; ///< 0: majority, 1: analog sum, 2: digital sum.
   int readout_mode;       ///< Sum mode (0) or sample mode only (1) or both (>=2)
   int num_image_sets;     ///< how many 'img' sets are available.
   int max_image_sets;     ///< how many 'img' sets were allocated.
   AdcData *raw;           ///< Pointer to raw data, if any.
   PixelTiming *pixtm;     ///< Optional pixel (pulse shape) timing. 
   ImgData *img;           ///< Pointer to second moments, if any.
   PixelCalibrated *pixcal;///< Pointer to calibrated pixel intensities, if available.
   int num_phys_addr;      ///< (not used)
   int phys_addr[4*H_MAX_DRAWERS];///< (not used)
   PixelList trigger_pixels; ///< List of triggered pixels.
   PixelList image_pixels;   ///< Pixels included in (first) image.
   PixelTrgTime pixeltrg_time; ///< Times when individual pixels fired.
   AuxTraceD aux_trace_d[MAX_AUX_TRACE_D]; ///< Optional auxilliary digital traces.
   AuxTraceA aux_trace_a[MAX_AUX_TRACE_A]; ///< Optional auxilliary analog traces.
};
typedef struct hess_tel_event_data_struct TelEvent;

/** Central trigger event data */

struct hess_central_event_data_struct
{
   int glob_count;      ///< Global event count.
   HTime cpu_time;      ///< CPU time at central trigger station.
   HTime gps_time;      ///< GPS time at central trigger station.
   int teltrg_pattern;  ///< Bit pattern of telescopes having sent 
                        ///< a trigger signal to the central station.
                        ///< (Historical; only useful for small no. of telescopes.)
   int teldata_pattern; ///< Bit pattern of telescopes having sent
                        ///< event data that could be merged.
                        ///< (Historical; only useful for small no. of telescopes.)
   int num_teltrg;      ///< How many telescopes triggered.
   int teltrg_list[H_MAX_TEL];  ///< List of IDs of triggered telescopes.
   float teltrg_time[H_MAX_TEL];///< Relative time of trigger signal
                        ///< after correction for nominal delay [ns].
   int teltrg_type_mask[H_MAX_TEL]; ///< Bit mask which type of trigger fired.
   float teltrg_time_by_type[H_MAX_TEL][H_MAX_TRG_TYPES]; ///< Time of trigger separate for each type.
   int num_teldata;     ///< Number of telescopes expected to have data.
   int teldata_list[H_MAX_TEL]; ///< List of IDs of telescopes with data.
};
typedef struct hess_central_event_data_struct CentralEvent;

/** Tracking data interpolated for one event and one telescope */

struct hess_tracking_event_data_struct
{
   int tel_id;            ///< The telescope ID number (1 ... n)
   double azimuth_raw;    ///< Raw azimuth angle [radians from N->E].
   double altitude_raw;   ///< Raw altitude angle [radians].
   double azimuth_cor;    ///< Azimuth corrected for pointing errors.
   double altitude_cor;   ///< Azimuth corrected for pointing errors.
   int raw_known;         ///< Set if raw angles are known.
   int cor_known;         ///< Set if corrected angles are known.
};
typedef struct hess_tracking_event_data_struct TrackEvent;

/** Reconstructed shower parameters */

struct hess_shower_parameter
{
   int known;
   int num_trg;      ///< Number of telescopes contributing to central trigger.
   int num_read;     ///< Number of telescopes read out.
   int num_img;      ///< Number of images used for shower parameters.
   int img_pattern;  ///< Bit pattern of which telescopes were used (for small no. of telescopes only).
   int img_list[H_MAX_TEL]; ///< With more than 16 or 32 telescopes, we can only use the list.
   int result_bits;  /**< Bit pattern of what results are available:
                            Bits 0 + 1: direction + errors
		            Bits 2 + 3: core position + errors
		            Bits 4 + 5: mean scaled image shape + errors
		            Bits 6 + 7: energy + error
		            Bits 8 + 9: shower maximum + error	       */
   double Az;        ///< Azimuth angle [radians from N->E]
   double Alt;       ///< Altitude [radians]
   double err_dir1;  ///< Error estimate in nominal plane X direction (|| Alt) [rad]
   double err_dir2;  ///< Error estimate in nominal plane Y direction (|| Az) [rad]
   double err_dir3;  ///< ?
   double xc;        ///< X core position [m]
   double yc;        ///< Y core position [m]
   double err_core1; ///< Error estimate in X coordinate [m]
   double err_core2; ///< Error estimate in Y coordinate [m]
   double err_core3; ///< ?
   double mscl;      ///< Mean scaled image length [gammas ~1 (HEGRA-style) or ~0 (HESS-style)].
   double err_mscl;
   double mscw;      ///< Mean scaled image width [gammas ~1 (HEGRA-style) or ~0 (HESS-style)].
   double err_mscw;
   double energy;    ///< Primary energy [TeV], assuming a gamma.
   double err_energy;
   double xmax;      ///< Atmospheric depth of shower maximum [g/cm^2].
   double err_xmax;
};
typedef struct hess_shower_parameter ShowerParameters;

/** All data for one event */

struct hess_event_data_struct
{
   int num_tel;                     ///< Number of telescopes in run.
   CentralEvent central;            ///< Central trigger data and data pattern.
   TelEvent teldata[H_MAX_TEL];     ///< Raw and/or image data.
   TrackEvent trackdata[H_MAX_TEL]; ///< Interpolated tracking data.
   ShowerParameters shower;         ///< Reconstructed shower parameters.
   int num_teldata;     ///< Number of telescopes for which we actually have data.
   int teldata_list[H_MAX_TEL]; ///< List of IDs of telescopes with data.
};
typedef struct hess_event_data_struct FullEvent;

/** Monte Carlo shower profile (sort of histogram). */

struct hess_mc_shower_profile_struct
{
   /** @short    Type of profile (also determines units below).
    *
    *            Temptative definitions:
    *            @li 1000*k + 1:  Profile of all charged particles.
    *            @li 1000*k + 2:  Profile of electrons+positrons.
    *            @li 1000*k + 3:  Profile of muons.
    *            @li 1000*k + 4:  Profile of hadrons.
    *            @li 1000*k + 10: Profile of Cherenkov photon emission [1/m].
    *
    *            The value of k specifies the binning:
    *            @li k = 0: The profile is in terms of atmospheric depth
    *                along the shower axis.
    *            @li k = 1: in terms of vertical atmospheric depth.
    *            @li k = 2: in terms of altitude [m] above sea level.
    */
   int id;
   int num_steps;       ///< Number of histogram steps
   int max_steps;       ///< Number of allowed steps as allocated for content
   double start;        ///< Start of ordinate ([m] or [g/cm^2])
   double end;          ///< End of it.
   double binsize;      ///< (End-Start)/num_steps; not saved
   double *content;     ///< Histogram contents (allocated on demand).
};
typedef struct hess_mc_shower_profile_struct ShowerProfile;

/** Shower specific data. */

struct hess_mc_shower_struct
{
   int shower_num;
   int primary_id;      ///< Particle ID of primary. Was in CORSIKA convention
                        ///< where detector_prog_vers in MC run header was 0,
                        ///< and is now 0 (gamma), 1(e-), 2(mu-), 100*A+Z
                        ///< for nucleons and nuclei, negative for antimatter.
   double energy;       ///< primary energy [TeV]
   double azimuth;      ///< Azimuth (N->E) [rad]
   double altitude;     ///< Altitude [rad]
   double depth_start;  ///< Atmospheric depth where particle started [g/cm^2].
   double h_first_int;  ///< height of first interaction a.s.l. [m]
   double xmax;         ///< Atmospheric depth of shower maximum [g/cm^2],
                        ///< derived from all charged particles.
   double hmax;         ///< Height of shower maximum [m] in xmax.
   double emax;         ///< Atm. depth of maximum in electron number.
   double cmax;         ///< Atm. depth of max. in Cherenkov photon emission.
   int num_profiles;    ///< Number of profiles filled.
   ShowerProfile profile[H_MAX_PROFILE];
   struct shower_extra_parameters extra_parameters;
};
typedef struct hess_mc_shower_struct MCShower;

/** Sums of photo-electrons in MC (total and per pixel). */

struct hess_mc_pe_sum_struct
{
   int event;              ///< Event number -> global counter.
   int shower_num;         ///< Shower number as in shower structure.
   int num_tel;            ///< Number of telescopes simulated.
   int num_pe[H_MAX_TEL];  ///< Number of photo-electrons per telescope
   int num_pixels[H_MAX_TEL]; ///< Pixels per telescope or 0.
   int pix_pe[H_MAX_TEL][H_MAX_PIX]; ///< Photo-electrons per pixel (without NSB).
   double photons[H_MAX_TEL];        ///< The sum of the photon content of all bunches.
   double photons_atm[H_MAX_TEL];    ///< Photons surviving atmospheric transmission.
   double photons_atm_3_6[H_MAX_TEL];///< Photons surv. atm. tr. in the 300 to 600 nm range.
   double photons_atm_400[H_MAX_TEL];///< Photons surv. atm. tr. in the 350 to 450 nm range.
   double photons_atm_qe[H_MAX_TEL]; ///< Photons surviving atmospheric transmission,
                                     ///< mirror reflectivity (except funnel), and Q.E. 
};
typedef struct hess_mc_pe_sum_struct MCpeSum;

/** Photons from Monte Carlo. */

struct hess_mc_photons
{
   struct bunch *bunches;  ///< Bunches of photons.
   int nbunches;           ///< How many photon bunches we have at this telescope.
   int max_bunches;        ///< How many we can store in 'bunches' vector above.
   double photons;         ///< The sum of the photon content of all bunches.
};

/** Photons incident on focal surface */

struct fs_photon
{
   float x, y;             ///< Impact position, projected [cm]
   float cx, cy;           ///< Direction cosines w.r.t. focal surface normal.
   float prob;             ///< Probability not accounted for yet.
   uint16_t wavelength;    ///< Wavelength [nm]
   uint16_t flags;         ///< ?
};

/** List of photons incident on focal surface */

struct hess_mc_fs_phot
{
   int nphot;              ///< Number of photons to record.
   struct fs_photon *phot; ///< Only allocated on demand; not needed for normal simulations.
   int max_phot;           ///< How many we can store in 'phot' above, without re-allocating.
};

/** Photo-electrons from Monte Carlo individually */

struct hess_mc_pe_list
{
   int npe;                ///< The number of all photo-electrons in the telescope.
   int pixels;             ///< The number of pixels in the camera.
   int flags;              ///< Bit 0: with amplitudes, bit 1: includes NSB.
#ifdef STORE_PIX_PHOTONS
   int photon_count[H_MAX_PIX]; ///< The numbers of photons arriving at each pixel.
                                ///< For efficiency reasons not filled in normal simulations.
#endif
   int pe_count[H_MAX_PIX];///< The numbers of p.e. at each pixel.
   int itstart[H_MAX_PIX]; ///< The start index for each pixel in the sequential atimes vector.
   double *atimes;         ///< The list of start times of all photo-eletrons.
   double *amplitudes;     ///< Optional list of matching amplitudes [mean p.e.].
   int max_npe;            ///< How many p.e. we can store in the atimes (+amplitudes) vector(s).
};

/** Monte Carlo event-specific data. */

struct hess_mc_event_struct
{
   int event;              ///< Event number -> global counter.
   int shower_num;         ///< Shower number as in shower structure.
   double xcore;           ///< Core position w.r.t. array reference point [m],
   double ycore;           ///<   x -> N, y -> W.
   double aweight;         ///< Area weight (units: [m**2]) in case of non-uniform
                           ///< sampling, normallly counted in the shower plane and
                           ///< normalized such that the sum over all events for a shower
                           ///< should, on average, be the area over which core offsets
                           ///< are thrown (see also num_use and core_range in 
                           ///< @ref MCRunHeader ).
                           ///< It may be zero for uniform sampling.
   double photons[H_MAX_TEL]; ///< The CORSIKA photon sum into fiducial volume.
   struct hess_mc_pe_sum_struct mc_pesum;  ///< Numbers of / sums of photo-electrons.
   struct hess_mc_photons mc_photons[H_MAX_TEL];  ///< Raw simulated photons (fiducial sphere).
   struct hess_mc_pe_list mc_pe_list[H_MAX_TEL];  ///< List of detected photo-electrons.
   struct hess_mc_fs_phot mc_phot_list[H_MAX_TEL];///< List of photons imaged onto focal surface.
};
typedef struct hess_mc_event_struct MCEvent;

/** Monitoring data. */

struct hess_tel_monitor_struct
{
   int known;              ///< Status etc., pedestals, DC, HV.
   int new_parts;          ///< What of that is new.

   int tel_id;             ///< Telescope ID number.
   int num_sectors;        ///< Number of sector available for trigger (default trigger).
   int num_pixels;         ///< Number of pixels in camera.
   int num_drawers;        ///< Number of drawers in camera.
   int num_gains;
   int num_ped_slices;     ///< How many slices have been added for pedestal.
   int num_drawer_temp;    ///< Number of temperatures per drawer.
   int num_camera_temp;    ///< Number of other temperatures monitored.
   
   int monitor_id;         ///< Incremented with each update.
   HTime moni_time;        ///< Time when last monitoring data was sent.
   HTime status_time;
   HTime trig_time;        ///< Time when last trigger monitor data was read.
   HTime ped_noise_time;   ///< Time when pedestals + noise were determined.
   HTime hv_temp_time;     ///< Time when hv+currents+temp. were all read out.
   HTime dc_rate_time;     ///< Time when DC current + pixels scalers were read.  
   HTime set_hv_thr_time;  ///< Time when HV + thresholds where set.
   HTime set_daq_time;     ///< Time when DAQ parameters where set.

   int status_bits;        ///< Lid, HV, trigger, readout, drawers, fans.

   /** These have to be obtained from the camera trigger electronics (first trigger type only)*/
   long coinc_count;       ///< Count of pixel coincidences (local triggers).
   long event_count;       ///< Count of events read out.
   double event_rate;      ///< Average event rate [Hz].
   double data_rate;       ///< Average rate of packed data [MB/s].
   double trigger_rate;    ///< Camera average local trigger rate [Hz].
   double sector_rate[H_MAX_SECTORS];  ///< Sector trigger rate [Hz].

   /** These are computed by the readout software: */
   double mean_significant;    // Average number of pixels taken as significant.
   double pedestal[H_MAX_GAINS][H_MAX_PIX];  ///< Average pedestal on ADC sums.
   double noise[H_MAX_GAINS][H_MAX_PIX];     ///< Average noise on ADC sums.

   /** These numbers need mapping from drawers+channel to pixel id: */
   uint16_t current[H_MAX_PIX];   ///< ADC values of DC current.
   uint16_t scaler[H_MAX_PIX];    ///< ADC values of pixel trigger rate.
   uint16_t hv_v_mon[H_MAX_PIX];  ///< ADC values of HV voltage monitor.
   uint16_t hv_i_mon[H_MAX_PIX];  ///< ADC values of HV current monitor.
   uint16_t hv_dac[H_MAX_PIX];    ///< DAC values of HV settings.
   uint16_t thresh_dac[H_MAX_DRAWERS]; ///< Thresholds set in each drawer.
   uint8_t trig_set[H_MAX_PIX];   ///< Set if pixel excluded from trigger.
   uint8_t hv_set[H_MAX_PIX];     ///< Set if HV switched off for pixel.
   uint8_t hv_stat[H_MAX_PIX];    ///< Set if HV switched off for pixel.

   /** That is left in its raw order: */
   short drawer_temp[H_MAX_DRAWERS][H_MAX_D_TEMP]; ///< ADC values.
   short camera_temp[H_MAX_C_TEMP]; ///< ADC values.
   /* ... + various voltages and currents to be defined ... */ 
   
   /** As set by CNTRLDaq message */
   uint16_t daq_conf;
   uint16_t daq_scaler_win;
   uint16_t daq_nd;
   uint16_t daq_acc;
   uint16_t daq_nl;
};
typedef struct hess_tel_monitor_struct TelMoniData;

/** Laser calibration data. */

struct hess_laser_calib_data_struct
{
   int known;        ///< Are the calibration values known?
   int tel_id;       ///< Telescope ID.
   int num_pixels;   ///< Number of pixels.
   int num_gains;    ///< Number of gains.
   int lascal_id;    ///< Laser calibration ID.
   double calib[H_MAX_GAINS][H_MAX_PIX]; /**< ADC to laser/LED p.e. conversion,
                   in [mean p.e.], details depending on calibration procedure. */
   double max_int_frac[H_MAX_GAINS]; ///< Maximum fraction of the signal which
                                     ///< can be in the fixed integration window.
   double max_pixtm_frac[H_MAX_GAINS]; ///< Maximum fraction of the signal which
                                       ///< can be in the pixel timing integration.
   double tm_calib[H_MAX_GAINS][H_MAX_PIX]; /** Transit time calibration [ns] */
};
typedef struct hess_laser_calib_data_struct LasCalData;

/** End-of-run statistics */

struct hess_run_end_statistics_struct
{
   int run_num;                    ///< Run number.
   int num_tel;                    ///< Number of telescopes used.
   int tel_ids[H_MAX_TEL];         ///< IDs of all telescopes.
   int num_central_trig;           ///< Number of system triggers.
   int num_local_trig[H_MAX_TEL];  ///< Number of local telescope triggers.
   int num_local_sys_trig[H_MAX_TEL]; ///< Number of valid telescope triggers.
   int num_events[H_MAX_TEL];      ///< Number of events read out.
};
typedef struct hess_run_end_statistics_struct RunStat;

/** MC end-of-run statistics */

struct hess_run_end_mc_statistics_struct
{
   int run_num;                    ///< Run number.
   int num_showers;                ///< Number of simulated showers found.
   int num_events;                 ///< Number of MC events found.
};
typedef struct hess_run_end_mc_statistics_struct MCRunStat;

/** Container for all H.E.S.S. data */

struct hess_all_data_struct
{
   RunHeader run_header;
   MCRunHeader mc_run_header;
   CameraSettings camera_set[H_MAX_TEL];
   CameraOrganisation camera_org[H_MAX_TEL];
   PixelSetting pixel_set[H_MAX_TEL];
   PixelDisabled pixel_disabled[H_MAX_TEL];
   CameraSoftSet cam_soft_set[H_MAX_TEL];
   TrackingSetup tracking_set[H_MAX_TEL];
   PointingCorrection point_cor[H_MAX_TEL];
   FullEvent event;
   MCShower mc_shower;
   MCEvent mc_event;
   // MCpeSum mc_pesum;
   TelMoniData tel_moni[H_MAX_TEL];
   LasCalData tel_lascal[H_MAX_TEL];
   RunStat run_stat;
   MCRunStat mc_run_stat;
};
typedef struct hess_all_data_struct AllHessData;

/* ====================== Function prototypes ======================== */

/* io_hess.c */
#ifdef MAX_IO_ITEM_LEVEL
/* Prototypes are only used if eventio headers were included before. */

void hs_reset_env(void);

void set_tel_idx_ref (int iref);
void set_tel_idx (int ntel, int *idx);
int find_tel_idx (int tel_id);

int write_hess_runheader(IO_BUFFER *iobuf, RunHeader *rh);
int read_hess_runheader(IO_BUFFER *iobuf, RunHeader *rh);
int print_hess_runheader(IO_BUFFER *iobuf);

int write_hess_mcrunheader(IO_BUFFER *iobuf, MCRunHeader *mcrh);
int read_hess_mcrunheader(IO_BUFFER *iobuf, MCRunHeader *mcrh);
int print_hess_mcrunheader(IO_BUFFER *iobuf);

int write_hess_camsettings(IO_BUFFER *iobuf, CameraSettings *cs);
int read_hess_camsettings(IO_BUFFER *iobuf, CameraSettings *cs);
int print_hess_camsettings(IO_BUFFER *iobuf);

int write_hess_camorgan(IO_BUFFER *iobuf, CameraOrganisation *co);
int read_hess_camorgan(IO_BUFFER *iobuf, CameraOrganisation *co);
int print_hess_camorgan(IO_BUFFER *iobuf);

int write_hess_pixelset(IO_BUFFER *iobuf, PixelSetting *ps);
int read_hess_pixelset(IO_BUFFER *iobuf, PixelSetting *ps);
int print_hess_pixelset(IO_BUFFER *iobuf);

int write_hess_pixeldis(IO_BUFFER *iobuf, PixelDisabled *pd);
int read_hess_pixeldis(IO_BUFFER *iobuf, PixelDisabled *pd);
int print_hess_pixeldis(IO_BUFFER *iobuf);

int write_hess_camsoftset(IO_BUFFER *iobuf, CameraSoftSet *cs);
int read_hess_camsoftset(IO_BUFFER *iobuf, CameraSoftSet *cs);
int print_hess_camsoftset(IO_BUFFER *iobuf);

int write_hess_trackset(IO_BUFFER *iobuf, TrackingSetup *ts);
int read_hess_trackset(IO_BUFFER *iobuf, TrackingSetup *ts);
int print_hess_trackset(IO_BUFFER *iobuf);

int write_hess_pointingcor(IO_BUFFER *iobuf, PointingCorrection *pc);
int read_hess_pointingcor(IO_BUFFER *iobuf, PointingCorrection *pc);
int print_hess_pointingcor(IO_BUFFER *iobuf);

int write_hess_centralevent(IO_BUFFER *iobuf, CentralEvent *ce);
int read_hess_centralevent(IO_BUFFER *iobuf, CentralEvent *ce);
int print_hess_centralevent(IO_BUFFER *iobuf);

int write_hess_trackevent(IO_BUFFER *iobuf, TrackEvent *tke);
int read_hess_trackevent(IO_BUFFER *iobuf, TrackEvent *tke);
int print_hess_trackevent(IO_BUFFER *iobuf);

int write_hess_televt_head(IO_BUFFER *iobuf, TelEvent *te);
int read_hess_televt_head(IO_BUFFER *iobuf, TelEvent *te);
int print_hess_televt_head(IO_BUFFER *iobuf);

int write_hess_teladc_sums(IO_BUFFER *iobuf, AdcData *raw);
int read_hess_teladc_sums(IO_BUFFER *iobuf, AdcData *raw);
int print_hess_teladc_sums(IO_BUFFER *iobuf);

int write_hess_teladc_samples(IO_BUFFER *iobuf, AdcData *raw);
int read_hess_teladc_samples(IO_BUFFER *iobuf, AdcData *raw, int what);
int print_hess_teladc_samples(IO_BUFFER *iobuf);

int write_hess_aux_trace_digital(IO_BUFFER *iobuf, AuxTraceD *auxd);
int read_hess_aux_trace_digital(IO_BUFFER *iobuf, AuxTraceD *auxd);
int print_hess_aux_trace_digital(IO_BUFFER *iobuf);

int write_hess_aux_trace_analog(IO_BUFFER *iobuf, AuxTraceA *auxd);
int read_hess_aux_trace_analog(IO_BUFFER *iobuf, AuxTraceA *auxa);
int print_hess_aux_trace_analog(IO_BUFFER *iobuf);

int write_hess_pixeltrg_time (IO_BUFFER *iobuf, PixelTrgTime *dt);
int read_hess_pixeltrg_time (IO_BUFFER *iobuf, PixelTrgTime *dt);
int print_hess_pixeltrg_time (IO_BUFFER *iobuf);

int write_hess_pixtime (IO_BUFFER *iobuf, PixelTiming *pixtm);
int read_hess_pixtime (IO_BUFFER *iobuf, PixelTiming *pixtm);
int print_hess_pixtime (IO_BUFFER *iobuf);

int write_hess_pixcalib (IO_BUFFER *iobuf, PixelCalibrated *pixcal);
int read_hess_pixcalib (IO_BUFFER *iobuf, PixelCalibrated *pixcal);
int print_hess_pixcalib (IO_BUFFER *iobuf);

int write_hess_telimage(IO_BUFFER *iobuf, ImgData *img, int what);
int read_hess_telimage(IO_BUFFER *iobuf, ImgData *img);
int print_hess_telimage(IO_BUFFER *iobuf);

int write_hess_televent(IO_BUFFER *iobuf, TelEvent *te, int what);
int read_hess_televent(IO_BUFFER *iobuf, TelEvent *te, int what);
int print_hess_televent(IO_BUFFER *iobuf);

int write_hess_shower(IO_BUFFER *iobuf, ShowerParameters *sp);
int read_hess_shower(IO_BUFFER *iobuf, ShowerParameters *sp);
int print_hess_shower(IO_BUFFER *iobuf);

int write_hess_event(IO_BUFFER *iobuf, FullEvent *ev, int what);
int read_hess_event(IO_BUFFER *iobuf, FullEvent *ev, int what);
int print_hess_event(IO_BUFFER *iobuf);

int write_hess_calib_event (IO_BUFFER *iobuf, FullEvent *ev, int what, int type);
int read_hess_calib_event (IO_BUFFER *iobuf, FullEvent *ev, int what, int *ptype);
int print_hess_calib_event (IO_BUFFER *iobuf);

int write_hess_mc_shower(IO_BUFFER *iobuf, MCShower *mcs);
int read_hess_mc_shower(IO_BUFFER *iobuf, MCShower *mcs);
int print_hess_mc_shower(IO_BUFFER *iobuf);

int write_hess_mc_event(IO_BUFFER *iobuf, MCEvent *mce);
int read_hess_mc_event(IO_BUFFER *iobuf, MCEvent *mce);
int print_hess_mc_event(IO_BUFFER *iobuf);

int write_hess_mc_pe_sum(IO_BUFFER *iobuf, MCpeSum *mcpes);
int read_hess_mc_pe_sum(IO_BUFFER *iobuf, MCpeSum *mcpes);
int print_hess_mc_pe_sum(IO_BUFFER *iobuf);

void reset_htime (HTime *t);
void fill_htime_now(HTime *now);
void copy_htime(HTime *t2, HTime *t1);

int write_hess_tel_monitor(IO_BUFFER *iobuf, TelMoniData *mon, int what);
int read_hess_tel_monitor(IO_BUFFER *iobuf, TelMoniData *mon);
int print_hess_tel_monitor(IO_BUFFER *iobuf);

int write_hess_laser_calib(IO_BUFFER *iobuf, LasCalData *lcd);
int read_hess_laser_calib(IO_BUFFER *iobuf, LasCalData *lcd);
int print_hess_laser_calib(IO_BUFFER *iobuf);

int write_hess_run_stat(IO_BUFFER *iobuf, RunStat *rs);
int read_hess_run_stat(IO_BUFFER *iobuf, RunStat *rs);
int print_hess_run_stat(IO_BUFFER *iobuf);

int write_hess_mc_run_stat(IO_BUFFER *iobuf, MCRunStat *mcrs);
int read_hess_mc_run_stat(IO_BUFFER *iobuf, MCRunStat *mcrs);
int print_hess_mc_run_stat(IO_BUFFER *iobuf);

int read_hess_mc_phot (IO_BUFFER *iobuf, MCEvent *mce);
int print_hess_mc_phot (IO_BUFFER *iobuf);

int write_hess_pixel_list(IO_BUFFER *iobuf, PixelList *pl, int telescope);
int read_hess_pixel_list(IO_BUFFER *iobuf, PixelList *pl, int *telescope);
int print_hess_pixel_list(IO_BUFFER *iobuf);
#endif

#ifdef __cplusplus
}
#endif

#endif
