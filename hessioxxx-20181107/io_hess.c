/* ============================================================================

   Copyright (C) 2000, 2003, 2008, 2009, 2010, 2011, 2013, 2014, 2017  Konrad Bernloehr

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

/** @file io_hess.c
 *  @short Writing and reading of H.E.S.S./CTA data (or other simulation data
 *     produced by sim_telarray/sim_hessarray) in eventio format.
 *
 *  This file provides functions for writing and reading of H.E.S.S./CTA
 *  related data blocks or similar data for other telescope arrays.
 *  This software will attempt to be backward-compatible, i.e. to
 *  be able to read older data in slightly different formats - 
 *  but we cannot guarantee that it really works. There is no
 *  attempt to write data in older formats.
 *  As always: use at your own risc.
 *
 *  @author  Konrad Bernl&ouml;hr
 *  @date July 2000 (initial version)
 *
 *  @date    @verbatim CVS $Date: 2018/08/22 15:12:48 $ @endverbatim
 *  @version @verbatim CVS $Revision: 1.104 $ @endverbatim
 */

/* ================================================================== */

#include "initial.h"      /* This file includes others as required. */
#include "io_basic.h"     /* This file includes others as required. */
#include "mc_tel.h"
#include "io_hess.h"
#include <assert.h>
#include <sys/time.h>

/** Support for checking if user functions are compiled with the same limits as the library. */

void check_hessio_max (int ncheck, int max_tel, int max_pix, int max_sectors, 
   int max_drawers, int max_pixsectors, int max_slices, int max_hotpix, 
   int max_profile, int max_d_temp, int max_c_temp, int max_gains)
{
   assert(ncheck==11);
   assert(max_tel==H_MAX_TEL);
   assert(max_pix==H_MAX_PIX);
   assert(max_sectors==H_MAX_SECTORS);
   assert(max_drawers==H_MAX_DRAWERS);
   assert(max_pixsectors==H_MAX_PIXSECTORS);
   assert(max_slices==H_MAX_SLICES);
   assert(max_hotpix==H_MAX_HOTPIX);
   assert(max_profile==H_MAX_PROFILE);
   assert(max_d_temp==H_MAX_D_TEMP);
   assert(max_c_temp==H_MAX_C_TEMP);
   assert(max_gains==H_MAX_GAINS);
}

void show_hessio_max()
{
   printf("\nThe hessio library was compiled with the following limits:\n");
   printf("   H_MAX_TEL: %d\n",H_MAX_TEL );
   printf("   H_MAX_PIX: %d\n", H_MAX_PIX);
   printf("   H_MAX_SECTORS: %d\n", H_MAX_SECTORS);
   printf("   H_MAX_DRAWERS: %d\n", H_MAX_DRAWERS);
   printf("   H_MAX_PIXSECTORS: %d\n", H_MAX_PIXSECTORS);
   printf("   H_MAX_SLICES: %d\n", H_MAX_SLICES);
   printf("   H_MAX_HOTPIX: %d\n", H_MAX_HOTPIX);
   printf("   H_MAX_PROFILE: %d\n", H_MAX_PROFILE);
   printf("   H_MAX_D_TEMP: %d\n", H_MAX_D_TEMP);
   printf("   H_MAX_C_TEMP: %d\n", H_MAX_C_TEMP);
   printf("   H_MAX_GAINS: %d\n\n", H_MAX_GAINS);
}

static int hs_verbose = -1; /**< Should hessio print_... functions be verbose? */
static int hs_maxprt = -1;  /**< What is the maximum number of per pixel outputs? */
static int hs_dynamic = -1; /**< Should be check environment variables each time? */

/** @short Allow user to override MAX_PRINT_ARRAY and PRINT_VERBOSE settings at a later time */

void hs_reset_env()
{
   hs_verbose = -1;
   hs_maxprt = -1;
   hs_dynamic = -1;
}

static void hs_check_env(void);

/** @short Get settings on how much information to print from environment */

static void hs_check_env()
{
   char *s;
   if ( hs_dynamic == 0 )
      return;

   hs_verbose = (getenv("PRINT_VERBOSE")!=NULL) ? 1 : 0;
   if ( (s = getenv("MAX_PRINT_ARRAY")) != NULL )
      hs_maxprt = atoi(s);
   else
      hs_maxprt = 20;
   hs_dynamic = (getenv("PRINT_DYNAMIC")!=NULL) ? 1 : 0;
}

static void put_time_blob (HTime *t, IO_BUFFER *iobuf);
static void get_time_blob (HTime *t, IO_BUFFER *iobuf);

static int g_tel_idx[3][H_MAX_TEL+1];
static int g_tel_idx_init[3];
static int g_tel_idx_ref;

/* ----------------- set_tel_idx_ref ---------------------- */
/** 
 *  Switch between multiple telescope lookup tables. 
 *
 *  Use this function when dealing simultaneously with multiple
 *  data streams for different array configurations.
 *  Both the set_tel_idx and the find_tel_idx will then work
 *  wit the selected choice of lookup table.
 *
 *  @param iref Which lookup table to use from now on (0<=iref<=2).
 *              Not switching lookup if iref is out of range.
 */
 

void set_tel_idx_ref (int iref)
{
   if ( iref >= 0 && iref<3 )
      g_tel_idx_ref = iref;
   else
   {
      fprintf(stderr,"Cannot switch to telescope index lookup table %d: out of range.\n", iref);
   }
}

/* -------------------- set_tel_idx -------------------- */
/** 
 *  Setup of telescope index lookup table. 
 *
 *  Must be filled before first use of find_tel_idx() - which
 *  is automatically done when reading a run header data block.
 *  When dealing with multiple lookups, use set_tel_idx_ref() first
 *  to select the one to fill.
 *
 *  @param ntel The number of telescope following.
 *  @param idx  The list of telescope IDs mapped to indices 0, 1, ...
 */

void set_tel_idx (int ntel, int *idx)
{
   int i;
   for (i=0; (size_t)i<sizeof(g_tel_idx[g_tel_idx_ref]) / sizeof(g_tel_idx[g_tel_idx_ref][0]); i++)
      g_tel_idx[g_tel_idx_ref][i] = -1;
   for (i=0; i<ntel; i++)
   {
      if ( idx[i] < 0 || (size_t) idx[i] >= 
            sizeof(g_tel_idx[g_tel_idx_ref]) / sizeof(g_tel_idx[g_tel_idx_ref][0]) )
      {
         fprintf(stderr,"Telescope ID %d is outside of valid range\n",idx[i]);
         exit(1);
      }
      if ( g_tel_idx[g_tel_idx_ref][idx[i]] != -1 )
      {
         fprintf(stderr,"Multiple telescope ID %d\n",idx[i]);
         fprintf(stderr,"Telescope ID %d is outside of valid range\n",idx[i]);
         exit(1);
      }
      g_tel_idx[g_tel_idx_ref][idx[i]] = i;
   }
   g_tel_idx_init[g_tel_idx_ref] = 1;
}

/* -------------------- find_tel_idx -------------------- */
/** 
 *  Lookup from telescope ID to offset number (index) in structures.
 *
 *  The lookup table must have been filled before with set_tel_idx().
 *  When dealing with multiple lookups, use set_tel_idx_ref() first
 *  to select the lookup table to be used.
 *
 *  @param tel_id A telescope ID for which we want the index count.
 *
 *  @return >= 0 (index in the original list passed to set_tel_idx), 
 *            -1 (not found in index,
 *            -2 (index not initialized).
 */

int find_tel_idx (int tel_id)
{
   if ( !g_tel_idx_init[g_tel_idx_ref] )
      return -2;
   if ( tel_id < 0 || (size_t)tel_id >= 
         sizeof(g_tel_idx[g_tel_idx_ref]) / sizeof(g_tel_idx[g_tel_idx_ref][0]) )
      return -1;
   return g_tel_idx[g_tel_idx_ref][tel_id];
}

/* -------------------- write_hess_runheader ---------------------- */
/**
 *  Write the run header in eventio format.
*/  

int write_hess_runheader (IO_BUFFER *iobuf, RunHeader *rh)
{
   IO_ITEM_HEADER item_header;
   
   if ( iobuf == (IO_BUFFER *) NULL || rh == NULL )
      return -1;
   
   item_header.type = IO_TYPE_HESS_RUNHEADER;  /* Data type */
   item_header.version = 2;                    /* Version 2 now */
   item_header.ident = rh->run;
   put_item_begin(iobuf,&item_header);

   put_int32(rh->run,iobuf);
   put_long(rh->time,iobuf);
   put_int32(rh->run_type,iobuf);
   put_int32(rh->tracking_mode,iobuf);
   put_int32(rh->reverse_flag,iobuf);           /* New in version 2! */
   put_vector_of_real(rh->direction,2,iobuf);
   put_vector_of_real(rh->offset_fov,2,iobuf);
   put_real(rh->conv_depth,iobuf);
   put_vector_of_real(rh->conv_ref_pos,2,iobuf); /* New in version 1! */
   put_int32(rh->ntel,iobuf);
   put_vector_of_int(rh->tel_id,rh->ntel,iobuf);
   
   set_tel_idx(rh->ntel,rh->tel_id);

   put_vector_of_real(&rh->tel_pos[0][0],3*rh->ntel,iobuf);
   put_int32(rh->min_tel_trig,iobuf);
   put_int32(rh->duration,iobuf);
   if ( rh->target != NULL )
      put_string(rh->target,iobuf);
   else
      put_string("",iobuf);
   if ( rh->observer != NULL )
      put_string(rh->observer,iobuf);
   else
      put_string("",iobuf);

   return put_item_end(iobuf,&item_header);
}

/* --------------------- read_hess_runheader ---------------------- */
/**
 *  Read the run header in eventio format.
*/  

int read_hess_runheader (IO_BUFFER *iobuf, RunHeader *rh)
{
   IO_ITEM_HEADER item_header;
   char line[1024];
   int rc;
   
   if ( iobuf == (IO_BUFFER *) NULL || rh == NULL )
      return -1;
   
   item_header.type = IO_TYPE_HESS_RUNHEADER;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 2 )
   {
      fprintf(stderr,"Unsupported run header version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   rh->run = get_int32(iobuf);
   rh->time = get_long(iobuf);
   rh->run_type = get_int32(iobuf);
   rh->tracking_mode = get_int32(iobuf);
   if ( item_header.version >= 2 )
      rh->reverse_flag = get_int32(iobuf);          /* New in version 2! */
   else
      rh->reverse_flag = 0;
   get_vector_of_real(rh->direction,2,iobuf);
   get_vector_of_real(rh->offset_fov,2,iobuf);
   rh->conv_depth = get_real(iobuf);
   if ( item_header.version >= 1 )
      get_vector_of_real(rh->conv_ref_pos,2,iobuf); /* New in version 1 */
   else
      rh->conv_ref_pos[0] = rh->conv_ref_pos[1] = 0.;
   rh->ntel = get_int32(iobuf);
   get_vector_of_int(rh->tel_id,rh->ntel,iobuf);
   
   set_tel_idx(rh->ntel,rh->tel_id);

   get_vector_of_real(&rh->tel_pos[0][0],3*rh->ntel,iobuf);
   rh->min_tel_trig = get_int32(iobuf);
   rh->duration = get_int32(iobuf);

   get_string(line,sizeof(line)-1,iobuf);
   if ( rh->target != NULL && rh->max_len_target > 0 )
      strncpy(rh->target,line,rh->max_len_target);
   else
   {
      int l = strlen(line);
      rh->max_len_target = 0;
      if ( rh->target != NULL )
      	 free(rh->target);
      if ( (rh->target = (char *) malloc(l+1)) != NULL )
      	 strcpy(rh->target,line);
   }

   get_string(line,sizeof(line)-1,iobuf);
   if ( rh->observer != NULL && rh->max_len_observer > 0 )
      strncpy(rh->observer,line,rh->max_len_observer);
   else
   {
      int l = strlen(line);
      rh->max_len_observer = 0;
      if ( rh->observer != NULL )
      	 free(rh->observer);
      if ( (rh->observer = (char *) malloc(l+1)) != NULL )
      	 strcpy(rh->observer,line);
   }

   return get_item_end(iobuf,&item_header);
}

/* --------------------- print_hess_runheader ---------------------- */
/**
 *  Read the run header in eventio format.
*/  

int print_hess_runheader (IO_BUFFER *iobuf)
{
   IO_ITEM_HEADER item_header;
   char line[1024];
   int rc;
   int i, j, ntel;
   
   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;
   
   item_header.type = IO_TYPE_HESS_RUNHEADER;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 2 )
   {
      fprintf(stderr,"Unsupported run header version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   printf("\nRun header for run %d:\n",get_int32(iobuf));
   printf("  Started at: ");
   {
      time_t t = get_long(iobuf);
      struct tm *tmvp = localtime(&t);
      printf(" %ld", t);
      if ( tmvp != NULL )
         printf(" (%d-%02d-%02d %02d:%02d:%02d %s)", 
         tmvp->tm_year+1900, tmvp->tm_mon+1, tmvp->tm_mday,
         tmvp->tm_hour, tmvp->tm_min, tmvp->tm_sec, 
         tzname[daylight?1:0]);
      printf("\n");
   }
   i = get_int32(iobuf);
   printf("  Run type: %d%s\n",i,(i==-1)?" (MC)":"");
   printf("  Tracking mode: %d\n",get_int32(iobuf));
   if ( item_header.version >= 2 )
      printf("  Reverse flag: %d\n", get_int32(iobuf)); /* New in version 2! */
   printf("  Azimuth centered at: %f deg\n", get_real(iobuf)*(180./M_PI));
   printf("  Altitude centered at: %f deg\n", get_real(iobuf)*(180./M_PI));
   printf("  Offset: %f,", get_real(iobuf)*(180./M_PI));
   printf(" %f deg\n", get_real(iobuf)*(180./M_PI));
   printf("  Convergence depth: %f g/cm^2\n", get_real(iobuf));
   if ( item_header.version >= 1 )
   {
      printf("  Convergence reference position x, y:");
      printf(" %f,", get_real(iobuf));
      printf(" %f m\n", get_real(iobuf));
   }
   ntel = get_int32(iobuf);
   printf("  With %d telescopes:",ntel);
   for (i=0;i<ntel;i++)
      printf(" CT%d", get_short(iobuf));
   printf("\n");
   printf("  Telescope positions:\n");
   for (i=0; i<ntel; i++)
   {
      for (j=0; j<3; j++)
         printf("\t%f",get_real(iobuf));
      printf("\n");
   }
   printf("  Trigger requires at least %d telescopes\n",get_int32(iobuf));
   printf("  Run duration: %d s\n",get_int32(iobuf));

   get_string(line,sizeof(line)-1,iobuf);
   printf("  Target: %s\n",line);

   get_string(line,sizeof(line)-1,iobuf);
   printf("  Observer: %s\n",line);

   return get_item_end(iobuf,&item_header);
}

/* -------------------- write_hess_mcrunheader ---------------------- */
/**
 *  Write the Monte Carlo run header in eventio format.
*/  

int write_hess_mcrunheader (IO_BUFFER *iobuf, MCRunHeader *mcrh)
{
   IO_ITEM_HEADER item_header;
   
   if ( iobuf == (IO_BUFFER *) NULL || mcrh == NULL )
      return -1;
   
   item_header.type = IO_TYPE_HESS_MCRUNHEADER;  /* Data type */
   item_header.version = 4;             /* Version */
   item_header.ident = -1;

   put_item_begin(iobuf,&item_header);

   put_int32(mcrh->shower_prog_id,iobuf);
   put_int32(mcrh->shower_prog_vers,iobuf);
   if ( item_header.version >= 4 )
      put_int32((int)mcrh->shower_prog_start,iobuf);
   put_int32(mcrh->detector_prog_id,iobuf);
   put_int32(mcrh->detector_prog_vers,iobuf);
   if ( item_header.version >= 4 )
      put_int32((int)mcrh->detector_prog_start,iobuf);
   put_real(mcrh->obsheight,iobuf);
   put_int32(mcrh->num_showers,iobuf);
   put_int32(mcrh->num_use,iobuf);
   put_int32(mcrh->core_pos_mode,iobuf);
   put_vector_of_real(mcrh->core_range,2,iobuf);
   put_vector_of_real(mcrh->alt_range,2,iobuf);
   put_vector_of_real(mcrh->az_range,2,iobuf);
   put_int32(mcrh->diffuse,iobuf);
   put_vector_of_real(mcrh->viewcone,2,iobuf);
   put_vector_of_real(mcrh->E_range,2,iobuf);
   put_real(mcrh->spectral_index,iobuf);
   put_real(mcrh->B_total,iobuf);
   put_real(mcrh->B_inclination,iobuf);
   put_real(mcrh->B_declination,iobuf);
   put_real(mcrh->injection_height,iobuf);
   put_int32(mcrh->atmosphere,iobuf);

   /* Shower MC specific data not yet covered here */
   /* New since version 2: */
   put_int32(mcrh->corsika_iact_options,iobuf);
   put_int32(mcrh->corsika_low_E_model,iobuf);
   put_int32(mcrh->corsika_high_E_model,iobuf);
   put_real(mcrh->corsika_bunchsize,iobuf);
   put_real(mcrh->corsika_wlen_min,iobuf);
   put_real(mcrh->corsika_wlen_max,iobuf);

   /* New since version 3: */
   if ( item_header.version >= 3 )
   {
      put_int32(mcrh->corsika_low_E_detail,iobuf);
      put_int32(mcrh->corsika_high_E_detail,iobuf);
   }

   /* Detector MC specific data not yet covered here */
  
   return put_item_end(iobuf,&item_header);
}

/* --------------------- read_hess_mcrunheader ---------------------- */
/**
 *  Read the Monte Carlo run header in eventio format.
*/  

int read_hess_mcrunheader (IO_BUFFER *iobuf, MCRunHeader *mcrh)
{
   IO_ITEM_HEADER item_header;
   int rc;
   
   if ( iobuf == (IO_BUFFER *) NULL || mcrh == NULL )
      return -1;
   
   item_header.type = IO_TYPE_HESS_MCRUNHEADER;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 4 )
   {
      fprintf(stderr,"Unsupported MC run header version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   mcrh->shower_prog_id = get_int32(iobuf);
   mcrh->shower_prog_vers = get_int32(iobuf);
   if ( item_header.version >= 4 )
      mcrh->shower_prog_start = get_int32(iobuf);
   else
      mcrh->shower_prog_start = 0;
   mcrh->detector_prog_id = get_int32(iobuf);
   mcrh->detector_prog_vers = get_int32(iobuf);
   if ( item_header.version >= 4 )
      mcrh->detector_prog_start = get_int32(iobuf);
   else
      mcrh->detector_prog_start = 0;
   mcrh->obsheight = get_real(iobuf);
   mcrh->num_showers = get_int32(iobuf);
   mcrh->num_use = get_int32(iobuf);
   mcrh->core_pos_mode = get_int32(iobuf);
   get_vector_of_real(mcrh->core_range,2,iobuf);
   get_vector_of_real(mcrh->alt_range,2,iobuf);
   get_vector_of_real(mcrh->az_range,2,iobuf);
   mcrh->diffuse = get_int32(iobuf);
   get_vector_of_real(mcrh->viewcone,2,iobuf);
   get_vector_of_real(mcrh->E_range,2,iobuf);
   mcrh->spectral_index = get_real(iobuf);
   mcrh->B_total = get_real(iobuf);
   mcrh->B_inclination = get_real(iobuf);
   mcrh->B_declination = get_real(iobuf);
   mcrh->injection_height = get_real(iobuf);
   mcrh->atmosphere = get_int32(iobuf); 

   if ( item_header.version >= 2 )
   {
      mcrh->corsika_iact_options = get_int32(iobuf);
      mcrh->corsika_low_E_model  = get_int32(iobuf);
      mcrh->corsika_high_E_model = get_int32(iobuf);
      mcrh->corsika_bunchsize    = get_real(iobuf);
      mcrh->corsika_wlen_min     = get_real(iobuf);
      mcrh->corsika_wlen_max     = get_real(iobuf);
   }
   else
   {
      mcrh->corsika_iact_options =
      mcrh->corsika_low_E_model  =
      mcrh->corsika_high_E_model = 0;
      mcrh->corsika_bunchsize    =
      mcrh->corsika_wlen_min     =
      mcrh->corsika_wlen_max     = 0.;
   }

   if ( item_header.version >= 3 )
   {
      mcrh->corsika_low_E_detail  = get_int32(iobuf);
      mcrh->corsika_high_E_detail = get_int32(iobuf);
   }
   else
   {
      mcrh->corsika_low_E_detail  = 0;
      mcrh->corsika_high_E_detail = 0;
   }

   return get_item_end(iobuf,&item_header);
}

/* --------------------- print_hess_mcrunheader ---------------------- */
/**
 *  Print the Monte Carlo run header data.
*/  

int print_hess_mcrunheader (IO_BUFFER *iobuf)
{
   IO_ITEM_HEADER item_header;
   int rc, i;
   int m_low_E = 0, m_high_E = 0;
   time_t start_s, start_d;

   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_MCRUNHEADER;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 4 )
   {
      fprintf(stderr,"Unsupported MC run header version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   /*
    * Attention: not more than one get_xxx(iobuf) per printf
    * since the calls are not done in the order as we read them!
    */

   printf("\nMC run header:\n");
   i = get_int32(iobuf);
   printf("  Shower program: %d",i);
   if ( i == 1 )
      printf(" (CORSIKA)");
   else if ( i == 2 )
      printf(" (ALTAI)");
   else if ( i == 3 )
      printf(" (KASCADE)");
   else if ( i == 4 )
      printf(" (MOCCA)");
   i = get_int32(iobuf);
   printf(" version %d\n",i);
   if ( item_header.version >= 4 )
      start_s = get_int32(iobuf);
   i = get_int32(iobuf);
   printf("  Detector program: %d",i);
   if ( i == 1 )
   {
      time_t t = get_int32(iobuf);
      struct tm *tmvp = localtime(&t);
      printf(" (sim_telarray)");
      if ( tmvp != NULL )
         printf(" version %d (%d-%02d-%02d %02d:%02d:%02d %s)\n", (int)t,
         tmvp->tm_year+1900, tmvp->tm_mon+1, tmvp->tm_mday,
         tmvp->tm_hour, tmvp->tm_min, tmvp->tm_sec, 
         tzname[daylight?1:0]);
      else
         printf(" version %d\n", (int)t);
   }
   else
      printf(" version %d\n",get_int32(iobuf));
   if ( item_header.version >= 4 )
   {
      char ss[32], sd[32];
      struct tm tms, tmd;
      start_d = get_int32(iobuf);
      (void) localtime_r(&start_s,&tms);
      (void) localtime_r(&start_d,&tmd);
      strftime(ss,sizeof(ss)-1,"%Y-%m-%d",&tms);
      strftime(sd,sizeof(sd)-1,"%Y-%m-%d",&tmd);
      printf("  Shower simulation started %s, detector simulation started %s\n",
         ss, sd);
   }
   printf("  Observation height: %f m\n",get_real(iobuf));
   printf("  Number of showers to be simulated: %d\n",get_int32(iobuf));
   printf("  Number of arrays per shower: %d\n",get_int32(iobuf));
   i = get_int32(iobuf);
   printf("  Core position mode: %d",i);
   if ( i == 0 )
      printf(" (fixed)\n");
   else if ( i == 1 )
      printf(" (circular)\n");
   else if ( i == 2 )
      printf(" (rectangular)\n");
   else
      printf("\n");
   printf("  Core range: %f,", get_real(iobuf)); 
   printf(" %f m\n", get_real(iobuf));
   printf("  Altitude range: %f", get_real(iobuf)*(180/M_PI));
   printf(" to %f deg\n", get_real(iobuf)*(180./M_PI));
   printf("  Azimuth range: %f", get_real(iobuf)*(180/M_PI));
   printf(" to %f deg\n", get_real(iobuf)*(180./M_PI));
   printf("  Diffuse mode: %d\n", get_int32(iobuf));
   {
      double vc1, vc2;
      vc1 = get_real(iobuf);
      vc2 = get_real(iobuf);
      if ( vc2*(180./M_PI) > 100. )
      {
         printf("  Checking units of viewcone parameters: in degrees!\n");
      }
      else if ( vc2 > 0. )
      {
         printf("  Checking units of viewcone parameters: degrees or radians?\n");
         if ( vc2*(180./M_PI) > 15. )
            printf("  Most likely in degrees.\n");
         else
            printf("  Could be radians but for historical reasons probably degrees.\n");
      }
      printf("  Viewcone: %f to %f deg\n", vc1, vc2);
   }
   printf("  Energy range: %g", get_real(iobuf));
   printf(" to %g TeV\n", get_real(iobuf));
   printf("  Spectral index: %f\n",get_real(iobuf));
   printf("  B field total: %f microT,", get_real(iobuf));
   printf(" incl.: %f deg,", get_real(iobuf)*(180/M_PI));
   printf(" decl.: %f deg\n",get_real(iobuf)*(180/M_PI));
   printf("  Injection height: %f km\n",get_real(iobuf)*0.001);
   printf("  Atmospheric density profile: %d\n",get_int32(iobuf)); 

   if ( item_header.version >= 2 )
   {
      printf("  IACT options: %d\n", get_int32(iobuf));
      m_low_E = get_int32(iobuf);
      printf("  Low energy model: %d (%s)\n", m_low_E,
         m_low_E==1 ? "GHEISHA" :  m_low_E==2 ? "URQMD" : m_low_E==3 ? "FLUKA" : "other");
      m_high_E = get_int32(iobuf);
      printf("  High energy model: %d (%s)\n", m_high_E,
         m_high_E==1 ? "VENUS" :  m_high_E==2 ? "Sibyll" : m_high_E==3 ? "QGSJET" :
         m_high_E==4 ? "DPMJET" : m_high_E==5 ? "NeXus" : m_high_E==6 ? "EPOS" : "other");
      printf("  Maximum bunchsize: %f\n", get_real(iobuf));
      printf("  Wavelength range: %f", get_real(iobuf));
      printf(" to %f nm\n", get_real(iobuf));
   }

   if ( item_header.version >= 3 )
   {
      int corsika_low_E_detail  = get_int32(iobuf);
      int corsika_high_E_detail = get_int32(iobuf);
      if ( corsika_low_E_detail > 0 )
         printf("  Details on low-E model: %d\n", corsika_low_E_detail);
      if ( corsika_high_E_detail > 0 )
      {
         printf("  Details on high-E model: version flag = %d, cross section flag = %d\n",
            corsika_high_E_detail%100, corsika_high_E_detail/100);
         if ( m_high_E == 3 )
         {
            if ( corsika_high_E_detail%100 == 2 )
               printf("  This is QGSJET01c.\n");
            else if ( corsika_high_E_detail%100 == 3 )
               printf("  This is QGSJET-II.\n");
            else if ( corsika_high_E_detail%100 == 1 )
               printf("  This is QGSJETOLD.\n");
            else
               printf("  This is an unknown QGSJET version.\n");
         }
         else if ( m_high_E == 2 )
         {
            if ( corsika_high_E_detail%100 == 2 )
               printf("  This is Sibyll 2.1.\n");
            else if ( corsika_high_E_detail%100 == 1 )
               printf("  This is Sibyll 1.6.\n");
         }
      }
   }

   return get_item_end(iobuf,&item_header);
}

/* -------------------- write_hess_camsettings -------------------- */
/**
 *  Write the camera definition (pixel positions) in eventio format.
*/  

int write_hess_camsettings (IO_BUFFER *iobuf, CameraSettings *cs)
{
   IO_ITEM_HEADER item_header;

   if ( iobuf == (IO_BUFFER *) NULL || cs == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_CAMSETTINGS;  /* Data type */
   // item_header.version = 2;             /* Version 2 */
   // if ( cs->cam_rot != 0. )
   //    item_header.version = 3;
   item_header.version = 4;  /* Need version 4 for pixel inclination */
   if ( cs->eff_flen != 0. )
      item_header.version = 5;
   item_header.ident = cs->tel_id;
   put_item_begin(iobuf,&item_header);

   put_int32(cs->num_pixels,iobuf);
   put_real(cs->flen,iobuf);
   if ( item_header.version > 4 )
      put_real(cs->eff_flen,iobuf);
   put_vector_of_real(cs->xpix,cs->num_pixels,iobuf);
   put_vector_of_real(cs->ypix,cs->num_pixels,iobuf);
   /* Data only written since version 4 or format changed with version 4: */
   if ( item_header.version >= 4 )
   {
      put_scount(cs->curved_surface,iobuf);
      put_scount(cs->pixels_parallel,iobuf);
      if ( cs->curved_surface )
      {
         put_vector_of_real(cs->zpix,cs->num_pixels,iobuf);
      }
      if ( ! cs->pixels_parallel )
      {
         put_vector_of_real(cs->nxpix,cs->num_pixels,iobuf);
         put_vector_of_real(cs->nypix,cs->num_pixels,iobuf);
      }
      put_scount(cs->common_pixel_shape,iobuf);
      if ( ! cs->common_pixel_shape )
      {
         put_vector_of_int_scount(cs->pixel_shape,cs->num_pixels,iobuf);
         put_vector_of_real(cs->area,cs->num_pixels,iobuf);
         put_vector_of_real(cs->size,cs->num_pixels,iobuf);
      }
      else /* Since all have the same shape and size, we write just one value each */
      {
         put_scount(cs->pixel_shape[0],iobuf);
         put_real(cs->area[0],iobuf);
         put_real(cs->size[0],iobuf);
      }
   }
   else
   {
      /* Used in version 1, 2, 3: */
      put_vector_of_real(cs->area,cs->num_pixels,iobuf); /* also in version 0 */
      put_vector_of_real(cs->size,cs->num_pixels,iobuf);
   }

   /* Data only written since version 2: */
   put_int32(cs->num_mirrors,iobuf);
   put_real(cs->mirror_area,iobuf);

   /* Data only written since version 3: */
   if ( item_header.version >= 3 )
   {
      put_real(cs->cam_rot,iobuf);
   }

   return put_item_end(iobuf,&item_header);
}

/* -------------------- read_hess_camsettings -------------------- */
/**
 *  Read the camera definition (pixel positions) in eventio format.
*/  

int read_hess_camsettings (IO_BUFFER *iobuf, CameraSettings *cs)
{
   IO_ITEM_HEADER item_header;
   int rc, i;

   if ( iobuf == (IO_BUFFER *) NULL || cs == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_CAMSETTINGS;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 5 )
   {
      fprintf(stderr,"Unsupported camera definition version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }
   if ( cs->tel_id >= 0 && item_header.ident != cs->tel_id )
   {
      Warning("Refusing to copy CameraSettings for wrong telescope");
      get_item_end(iobuf,&item_header);
      return -1;
   }

   cs->num_pixels = get_int32(iobuf);
   if ( cs->num_pixels < 1 || cs->num_pixels > H_MAX_PIX )
   {
      char text[200];
      sprintf(text,"Camera with %d pixels not supported."
         " Cannot read setting.",cs->num_pixels);
      Warning(text);
      cs->num_pixels = 0;
      get_item_end(iobuf,&item_header);
      return -1;
   }
   cs->flen = get_real(iobuf);
   cs->eff_flen = 0.;
   if ( item_header.version > 4 )
      cs->eff_flen = get_real(iobuf);
   get_vector_of_real(cs->xpix,cs->num_pixels,iobuf);
   get_vector_of_real(cs->ypix,cs->num_pixels,iobuf);
   if ( item_header.version >= 4 )
   {
      cs->curved_surface = get_scount(iobuf);
      cs->pixels_parallel = get_scount(iobuf);
      if ( cs->curved_surface )
      {
         get_vector_of_real(cs->zpix,cs->num_pixels,iobuf);
      }
      else
      {
         for ( i=0; i<cs->num_pixels; i++ )
         {
            cs->zpix[i] = 0.;  /* Assume a flat camera */
         }
      }
      if ( ! cs->pixels_parallel )
      {
         get_vector_of_real(cs->nxpix,cs->num_pixels,iobuf);
         get_vector_of_real(cs->nypix,cs->num_pixels,iobuf);
      }
      else
      {
         for ( i=0; i<cs->num_pixels; i++ )
         {
            cs->nxpix[i] = cs->nypix[i] = 0.;  /* Assume looking along optical axis */
         }
      }
      cs->common_pixel_shape = get_scount(iobuf);
      if ( ! cs->common_pixel_shape )
      {
         /* Pixel geometric properties reported individually */
         get_vector_of_int_scount(cs->pixel_shape,cs->num_pixels,iobuf);
         get_vector_of_real(cs->area,cs->num_pixels,iobuf);
         get_vector_of_real(cs->size,cs->num_pixels,iobuf);
      }
      else
      {
         /* All pixels of same shape and size */
         double area, size;
         int pixel_shape = get_scount(iobuf);
         area = get_real(iobuf);
         size = get_real(iobuf);
         for ( i=0; i<cs->num_pixels; i++ )
         {
            cs->pixel_shape[i] = pixel_shape;
            cs->area[i] = area;
            cs->size[i] = size;
         }
      }
   }
   else
   {
      cs->curved_surface = 0;
      cs->pixels_parallel = 1;
      cs->common_pixel_shape = 0;
      for ( i=0; i<cs->num_pixels; i++ )
      {
         cs->zpix[i] = 0.;  /* Assume a flat camera, */
         cs->nxpix[i] = cs->nypix[i] = 0.;  /* assume looking along optical axis, */
         cs->pixel_shape[i] = -1; /* unknown shape (can be derived from pixel positions) */
      }
      get_vector_of_real(cs->area,cs->num_pixels,iobuf);
      if ( item_header.version >= 1 )
         get_vector_of_real(cs->size,cs->num_pixels,iobuf);
      else
         for (i=0; i<cs->num_pixels; i++)
      	    cs->size[i] = 0.;
   }

   if ( item_header.version >= 2 )
   {
      cs->num_mirrors = get_int32(iobuf);
      cs->mirror_area = get_real(iobuf);
   }
   else
   {
      cs->num_mirrors = 0;
      cs->mirror_area = 0;
   }

   if ( item_header.version >= 3 )
   {
      cs->cam_rot = get_real(iobuf);
   }
   else
   {
      cs->cam_rot = 0.;
   }

   return get_item_end(iobuf,&item_header);
}

/* -------------------- print_hess_camsettings -------------------- */
/**
 *  Print the camera definition (pixel positions) in eventio format.
*/  

int print_hess_camsettings (IO_BUFFER *iobuf)
{
   IO_ITEM_HEADER item_header;
   int rc, i, num_pixels, pixel_shape;
   double flen, eff_flen, xpix, ypix, zpix, czpix, area, size;
   
   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;
   
   item_header.type = IO_TYPE_HESS_CAMSETTINGS;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 5 )
   {
      fprintf(stderr,"Unsupported camera definition version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }
   printf("\nCamera settings for telescope ID %ld\n", item_header.ident);

   num_pixels = get_int32(iobuf);
   printf("   num_pixels = %d\n", num_pixels);
   flen = get_real(iobuf);
   eff_flen = 0.;
   printf("   flen = %f m\n", flen);
   if ( item_header.version > 4 )
   {
      eff_flen = get_real(iobuf);
      printf("   eff_flen = %f m\n", eff_flen);
   }
   printf("   xpix = ");
   for ( i=0; i<num_pixels; i++ )
   {
      xpix = get_real(iobuf);
      if ( i<10 )
         printf(" %f,", xpix);
      else if ( i==10 )
         printf(" ...");
   }
   printf(" m\n");
   printf("   ypix = ");
   for ( i=0; i<num_pixels; i++ )
   {
      ypix = get_real(iobuf);
      if ( i<10 )
         printf(" %f,", ypix);
      else if ( i==10 )
         printf(" ...");
   }
   printf(" m\n");
   if ( item_header.version >= 4 )
   {
      int curved_surface, pixels_parallel, common_pixel_shape;
      curved_surface = get_scount(iobuf);
      pixels_parallel = get_scount(iobuf);
      if ( curved_surface )
      {
         printf("   Camera has a curved surface.\n");
         printf("   zpix = ");
         for ( i=0; i<num_pixels; i++ )
         {
            zpix = get_real(iobuf);
            if ( i<10 )
               printf(" %f,", zpix);
            else if ( i==10 )
               printf(" ...");
         }
         printf(" m\n");
      }
      else
      {
         printf("   Camera has a flat surface.\n");
      }
      if ( pixels_parallel )
      {
         printf("   Pixels are parallel to optical axis.\n");
      }
      else
      {
         printf("   Pixels are inclined w.r.t. optical axis.\n");
         printf("   nxpix = ");
         for ( i=0; i<num_pixels; i++ )
         {
            czpix = get_real(iobuf);
            if ( i<10 )
               printf(" %f,", czpix);
            else if ( i==10 )
               printf(" ...");
         }
         printf("\n");
         printf("   nypix = ");
         for ( i=0; i<num_pixels; i++ )
         {
            czpix = get_real(iobuf);
            if ( i<10 )
               printf(" %f,", czpix);
            else if ( i==10 )
               printf(" ...");
         }
         printf("\n");
      }
      common_pixel_shape = get_scount(iobuf);
      if ( ! common_pixel_shape )
      {
         printf("   Individual pixel shapes and/or sizes:\n");
         printf("   pixel_shape = ");
         for ( i=0; i<num_pixels; i++ )
         {
            pixel_shape = get_scount(iobuf);
            if ( i<10 )
               printf(" %d,", pixel_shape);
            else if ( i==10 )
               printf(" ...");
         }
         printf("\n");
         printf("   pixel area = ");
         for ( i=0; i<num_pixels; i++ )
         {
            area = get_real(iobuf);
            if ( i<10 )
               printf(" %f,", area);
            else if ( i==10 )
               printf(" ...");
         }
         printf(" m^2\n");
         printf("   pixel size = ");
         for ( i=0; i<num_pixels; i++ )
         {
            size = get_real(iobuf);
            if ( i<10 )
               printf(" %f,", size);
            else if ( i==10 )
               printf(" ...");
         }
         printf(" m\n");
      }
      else
      {
         printf("   Common pixel shapes and/or sizes:\n");
         pixel_shape = get_scount(iobuf);
         area = get_real(iobuf);
         size = get_real(iobuf);
         printf("   pixel_shape = %d\n", pixel_shape);
         printf("   pixel area = %f m^2\n", area);
         printf("   pixel size = %f m\n", size);
      }
   }
   else
   {
      printf("   Pixels assumed parallel to optical axis.\n");
      printf("   pixel area = ");
      for ( i=0; i<num_pixels; i++ )
      {
         area = get_real(iobuf);
         if ( i<10 )
            printf(" %f,", area);
         else if ( i==10 )
            printf(" ...");
      }
      printf(" m^2\n");
      if ( item_header.version >= 1 )
      {
         printf("   pixel size = ");
         for ( i=0; i<num_pixels; i++ )
         {
            size = get_real(iobuf);
            if ( i<10 )
               printf(" %f,", size);
            else if ( i==10 )
               printf(" ...");
         }
         printf(" m\n");
      }
   }

   if ( item_header.version >= 2 )
   {
      printf("   num_mirrors = %d\n", get_int32(iobuf));
      printf("   mirror_area = %f m^2\n", get_real(iobuf));
   }
   
   if ( item_header.version >= 3 )
   {
      printf("   camera rotation = %5.3f deg.\n", get_real(iobuf)*(180./M_PI));
   }

   return get_item_end(iobuf,&item_header);
}

/* -------------------- write_hess_camorgan -------------------- */
/**
 *  Write the logical organisation of camera electronics in eventio format.
*/  

int write_hess_camorgan (IO_BUFFER *iobuf, CameraOrganisation *co)
{
   IO_ITEM_HEADER item_header;
   int i, j, n;
   
   if ( iobuf == (IO_BUFFER *) NULL || co == NULL )
      return -1;
   
   item_header.type = IO_TYPE_HESS_CAMORGAN;  /* Data type */
   item_header.version = 1;             /* Version 1 (extended) */
   if ( co->num_pixels >= 32768 || co->num_sectors >= 32768 )
      item_header.version = 2;          /* allow for larger drawer ID numbers etc. */
   item_header.ident = co->tel_id;
   put_item_begin(iobuf,&item_header);

   put_int32(co->num_pixels,iobuf);
   put_int32(co->num_drawers,iobuf);
   put_int32(co->num_gains,iobuf);
   if ( item_header.version >= 1 )
      put_int32(co->num_sectors,iobuf);
   if ( item_header.version <= 1 )
   {
      put_vector_of_int(co->drawer,co->num_pixels,iobuf);
      put_vector_of_int(&co->card[0][0],co->num_pixels*co->num_gains,iobuf);
      put_vector_of_int(&co->chip[0][0],co->num_pixels*co->num_gains,iobuf);
      put_vector_of_int(&co->channel[0][0],co->num_pixels*co->num_gains,iobuf);
      for (i=0; i<co->num_pixels; i++)
      {
         n = co->nsect[i];
         if ( n > H_MAX_PIXSECTORS )
            n = H_MAX_PIXSECTORS;
         for (j=0; j<n; j++)
         {
      	    if ( co->sectors[i][j] < 0 )
	    {
	       n = j;
	       break;
	    }
         }
         put_short(n,iobuf);
         put_vector_of_int(co->sectors[i],n,iobuf);
      }
   }
   else
   {
      put_vector_of_int_scount(co->drawer,co->num_pixels,iobuf);
      put_vector_of_int_scount(&co->card[0][0],co->num_pixels*co->num_gains,iobuf);
      put_vector_of_int_scount(&co->chip[0][0],co->num_pixels*co->num_gains,iobuf);
      put_vector_of_int_scount(&co->channel[0][0],co->num_pixels*co->num_gains,iobuf);
      for (i=0; i<co->num_pixels; i++)
      {
         n = co->nsect[i];
         if ( n > H_MAX_PIXSECTORS )
            n = H_MAX_PIXSECTORS;
         for (j=0; j<n; j++)
         {
      	    if ( co->sectors[i][j] < 0 )
	    {
	       n = j;
	       break;
	    }
         }
         put_scount32(n,iobuf);
         put_vector_of_int_scount(co->sectors[i],n,iobuf);
      }
   }
   
   if ( item_header.version >= 1 )
   {
      for (i=0; i<co->num_sectors; i++)
      {
         put_byte(co->sector_type[i],iobuf);
         put_real(co->sector_threshold[i],iobuf);
         put_real(co->sector_pixthresh[i],iobuf);
      }
   }

   return put_item_end(iobuf,&item_header);
}


/* -------------------- read_hess_camorgan -------------------- */
/**
 *  Read the logical organisation of camera electronics in eventio format.
*/  

int read_hess_camorgan (IO_BUFFER *iobuf, CameraOrganisation *co)
{
   IO_ITEM_HEADER item_header;
   int i, j, n;
   int rc;
   int w_psmx = 0, ix;
   
   if ( iobuf == (IO_BUFFER *) NULL || co == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_CAMORGAN;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 2 )
   {
      fflush(stdout);
      fprintf(stderr,"Unsupported camera organisation version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }
   if ( co->tel_id >= 0 && item_header.ident != co->tel_id )
   {
      fflush(stdout);
      fprintf(stderr,"Expected CameraOrganisation for telescope ID = %d, got %ld\n",
         co->tel_id, item_header.ident);
      Warning("Refusing to copy CameraOrganisation for wrong telescope");
      get_item_end(iobuf,&item_header);
      return -1;
   }

   co->num_pixels = get_int32(iobuf);
   co->num_drawers = get_int32(iobuf);
   co->num_gains = get_int32(iobuf);
   if ( item_header.version >= 1 )
      co->num_sectors = get_int32(iobuf);
   if ( co->num_pixels < 0 || co->num_pixels > H_MAX_PIX ||
        co->num_gains < 0 || co->num_gains > H_MAX_GAINS )
   {
      fflush(stdout);
      Warning("Data size in CameraOrganisation is invalid.");
      fprintf(stderr,"  num_pixels = %d; allowed: %d\n", co->num_pixels, H_MAX_PIX);
      fprintf(stderr,"  num_gains  = %d; allowed: %d\n", co->num_gains, H_MAX_GAINS);
      co->num_pixels = co->num_drawers = co->num_gains = 0;
      get_item_end(iobuf,&item_header);
      return -1;
   }
   if ( item_header.version <= 1 )
   {
      get_vector_of_int(co->drawer,co->num_pixels,iobuf);
      get_vector_of_int(&co->card[0][0],co->num_pixels*co->num_gains,iobuf);
      get_vector_of_int(&co->chip[0][0],co->num_pixels*co->num_gains,iobuf);
      get_vector_of_int(&co->channel[0][0],co->num_pixels*co->num_gains,iobuf);
      for (i=0; i<co->num_pixels; i++)
      {
         n = get_short(iobuf);
         if ( n > H_MAX_PIXSECTORS )
         {
            if ( n > w_psmx )
            {
               fflush(stdout);
               fprintf(stderr,"There are up to %d trigger groups ('sectors') associated to pixels "
                  "but H_MAX_PIXSECTORS=%d. Extra sectors are ignored.\n", n, H_MAX_PIXSECTORS);
               w_psmx = n;
            }
            get_vector_of_int(co->sectors[i],H_MAX_PIXSECTORS,iobuf);
            for (ix=H_MAX_PIXSECTORS; ix<n; ix++)
               (void) get_short(iobuf);
            n = H_MAX_PIXSECTORS;
         }
         else
         {
            get_vector_of_int(co->sectors[i],n,iobuf);
         }
         /* Fix for old bug in write_hess_camorgan(): trailing '0' sectors. */
         /* Since the sector list is always ordered a sector number of 0 */
         /* after the first position indicates the end of the list. */
         for ( j=1; j<n; j++ )
            if ( co->sectors[i][j] == 0 )
            {
               n = j;
               break;
            }
         for ( j=n; j<H_MAX_PIXSECTORS; j++)
      	    co->sectors[i][j] = -1;
         co->nsect[i] = n;
      }
   }
   else
   {
      get_vector_of_int_scount(co->drawer,co->num_pixels,iobuf);
      get_vector_of_int_scount(&co->card[0][0],co->num_pixels*co->num_gains,iobuf);
      get_vector_of_int_scount(&co->chip[0][0],co->num_pixels*co->num_gains,iobuf);
      get_vector_of_int_scount(&co->channel[0][0],co->num_pixels*co->num_gains,iobuf);
      for (i=0; i<co->num_pixels; i++)
      {
         n = get_scount32(iobuf);
         if ( n > H_MAX_PIXSECTORS )
         {
            if ( n > w_psmx )
            {
               fflush(stdout);
               fprintf(stderr,"There are up to %d trigger groups ('sectors') associated to pixels "
                  "but H_MAX_PIXSECTORS=%d. Extra sectors are ignored.\n", n, H_MAX_PIXSECTORS);
               w_psmx = n;
            }
            get_vector_of_int_scount(co->sectors[i],H_MAX_PIXSECTORS,iobuf);
            for (ix=H_MAX_PIXSECTORS; ix<n; ix++)
               (void) get_scount(iobuf);
            n = H_MAX_PIXSECTORS;
         }
         else
         {
            get_vector_of_int_scount(co->sectors[i],n,iobuf);
         }
         /* Fix for old bug in write_hess_camorgan(): trailing '0' sectors. */
         /* Since the sector list is always ordered a sector number of 0 */
         /* after the first position indicates the end of the list. */
         for ( j=1; j<n; j++ )
            if ( co->sectors[i][j] == 0 )
            {
               n = j;
               break;
            }
         for ( j=n; j<H_MAX_PIXSECTORS; j++)
      	    co->sectors[i][j] = -1;
         co->nsect[i] = n;
      }
   }

   if ( item_header.version >= 1 )
   {
      for (i=0; i<co->num_sectors && i<H_MAX_SECTORS; i++)
      {
         co->sector_type[i] = get_byte(iobuf);
         co->sector_threshold[i] = get_real(iobuf);
         co->sector_pixthresh[i] = get_real(iobuf);
      }
      if ( co->num_sectors > H_MAX_SECTORS )
      {
         fflush(stdout);
         fprintf(stderr,
            "There are %d trigger groups ('sectors') in telescope ID %d but only %d are supported.\n",
            co->num_sectors, co->tel_id, H_MAX_SECTORS);
         for ( i=H_MAX_SECTORS; i<co->num_sectors; i++ )
         {
            (void) get_byte(iobuf);
            (void) get_real(iobuf);
            (void) get_real(iobuf);
         }
      }
   }
   else
   {
      for (i=0; i<co->num_sectors; i++)
      {
         co->sector_type[i] = 0;
         co->sector_threshold[i] = 0.;
         co->sector_pixthresh[i] = 0.;
      }
   }

   return get_item_end(iobuf,&item_header);
}

/* -------------------- print_hess_camorgan -------------------- */
/**
 *  Read the logical organisation of camera electronics in eventio format.
*/  

int print_hess_camorgan (IO_BUFFER *iobuf)
{
   IO_ITEM_HEADER item_header;
   int i, j, n;
   int rc;
   int npix=0, ndraw=0, ngain=0, nsect=0;
   int nmax = 20;
   int w_psmx = 0, ix;
   
   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;
      
   hs_check_env();

   item_header.type = IO_TYPE_HESS_CAMORGAN;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 2 )
   {
      fprintf(stderr,"Unsupported camera organisation version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }
   // Version no. may be 1 with less than 32k pixels; otherwise must be >= 2.
   printf("\nCamera organisation (version %d) for telescope id = %ld\n", 
      item_header.version, item_header.ident);
   printf("   num_pixels = %d\n", npix=get_int32(iobuf));
   printf("   num_drawers= %d\n", ndraw=get_int32(iobuf));
   printf("   num_gains  = %d\n", ngain=get_int32(iobuf));
   // Details of the sectors (trigger groups) are recorded only since version 1.
   if ( item_header.version >= 1 )
      printf("   num_sectors  = %d\n", nsect=get_int32(iobuf));

   // Each pixel can only be part of one drawer
   printf("   drawer = ");
   for ( i=0; i<npix; i++ )
   {
      int jd = (item_header.version<2 ? get_short(iobuf) : get_scount32(iobuf));
      if ( i < hs_maxprt )
         printf("%d, ", jd );
      else if ( i == nmax )
         printf("...");
   }
   printf("\n");

   // Each gain for each pixel goes to some electronics card
   printf("   card = ");
   for ( i=0; i<npix*ngain; i++ )
   {
      int jc = (item_header.version<2 ? get_short(iobuf) : get_scount32(iobuf));
      if ( i < hs_maxprt*ngain )
         printf("%d%c ", jc, ((i+1)%ngain)==0?';':',');
      else if ( i == hs_maxprt*ngain )
         printf("...");
   }
   printf("\n");

   // Each gain for each pixel goes to some chip number (on the electronics card)
   printf("   chip = ");
   for ( i=0; i<npix*ngain; i++ )
   {
      int jc = (item_header.version<2 ? get_short(iobuf) : get_scount32(iobuf));
      if ( i < hs_maxprt*ngain )
         printf("%d%c ", jc, ((i+1)%ngain)==0?';':',');
      else if ( i == hs_maxprt*ngain)
         printf("...");
   }
   printf("\n");
   
   // Each gain for each pixel goes to some channel (on the chip)
   printf("   channel = ");
   for ( i=0; i<npix*ngain; i++ )
   {
      int jc = (item_header.version<2 ? get_short(iobuf) : get_scount32(iobuf));
      if ( i < hs_maxprt*ngain )
         printf("%d%c ", jc, ((i+1)%ngain)==0?';':',');
      else if ( i == hs_maxprt*ngain)
         printf("...");
   }
   printf("\n");

   // This is not actually a list of all sectors but for each pixel 
   // a (partial) list of sectors (trigger groups) to which it contributes. 
   // The number of sectors for each pixel is not actually limited in
   // the simulation, but the current format of reporting it is more
   // restricted. Therefore, the reported list may be incomplete.
   printf("   in-sectors = ");
   for (i=0; i<npix; i++)
   {
      int sectors[H_MAX_PIXSECTORS+20];
      size_t nsx = sizeof(sectors)/sizeof(sectors[0]);
      n = (item_header.version<2 ? get_short(iobuf) : get_scount32(iobuf));
      if ( hs_verbose && i<hs_maxprt )
         printf("(px=%d: n=%d) ", i, n);
      if ( (size_t) n > nsx )
      { 
         if ( n > w_psmx )
         {
            printf(" Up to %d trigger groups ('sectors') associated to pixels "
               "but can show only up to %zu. Extra sectors are ignored. ", n, nsx);
            w_psmx = n;
         }
         if ( item_header.version < 2 )
            get_vector_of_int(sectors,H_MAX_PIXSECTORS,iobuf);
         else
            get_vector_of_int_scount(sectors,H_MAX_PIXSECTORS,iobuf);
         for (ix=H_MAX_PIXSECTORS; ix<n; ix++)
         {
            if ( item_header.version < 2 )
               (void) get_short(iobuf);
            else
               (void) get_scount(iobuf);
         }
         n = H_MAX_PIXSECTORS;
      }
      else
      {
         if ( item_header.version < 2 )
            get_vector_of_int(sectors,n,iobuf);
         else
            get_vector_of_int_scount(sectors,n,iobuf);
      }
      /* Fix for old bug in write_hess_camorgan(): trailing '0' sectors. */
      /* Since the sector list is always ordered a sector number of 0 */
      /* after the first position indicates the end of the list. */
      for ( j=1; j<n; j++ )
         if ( sectors[j] == 0 )
         {
            n = j;
            if ( hs_verbose )
               printf("[n=%d] ", n);
            break;
         }
      for ( j=n; j<H_MAX_PIXSECTORS; j++)
      	 sectors[j] = -1;
      if ( i < hs_maxprt )
      {
         for ( j=0; j<n; j++ )
            printf("%d%c",sectors[j],(j+1)==n?';':',');
         printf(" ");
      }
      else if ( i == hs_maxprt )
         printf("...");
   }
   printf("\n");

   if ( item_header.version >= 1 )
   {
      for (i=0; i<nsect; i++)
      {
         int sector_type = get_byte(iobuf);
         double sector_threshold = get_real(iobuf);
         double sector_pixthresh = get_real(iobuf);
         if ( i < hs_maxprt )
         {
            printf("   Sector %d is of type %d (%s)", i, sector_type,
              sector_type==0 ? "majority" : 
              sector_type==1 ? "analog sum" : 
              sector_type==2 ? "digital sum" : "unknown");
            if ( sector_type == 0 )
               printf(" with threshold %f p.e. at pixel level and %f pixels at sector level.\n",
                  sector_pixthresh, sector_threshold);
            else if ( sector_type == 1 || sector_type == 2 )
               printf(" with clipping at %f p.e. and threshold at %f p.e.\n",
                  sector_pixthresh, sector_threshold);
         }
         else if ( i == hs_maxprt )
            printf("   ...\n");
      }
   }

   return get_item_end(iobuf,&item_header);
}

/* -------------------- write_hess_pixelset ------------------- */
/**
 *  Write the settings of pixel parameters (HV, thresholds, ...) in eventio format.
*/  

int write_hess_pixelset (IO_BUFFER *iobuf, PixelSetting *ps)
{
   IO_ITEM_HEADER item_header;

   if ( iobuf == (IO_BUFFER *) NULL || ps == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_PIXELSET;  /* Data type */
   if ( ps->time_slice == 0. )
      item_header.version = 0;             /* We can use the older format */
   else
      item_header.version = 1;             /* Newer format required */
   if ( ps->nrefshape > 0 && ps->lrefshape > 0 )
      item_header.version = 2;             /* Even newer */
   item_header.ident = ps->tel_id;
   put_item_begin(iobuf,&item_header);

   put_int32(ps->setup_id,iobuf);
   put_int32(ps->trigger_mode,iobuf);
   put_int32(ps->min_pixel_mult,iobuf);

   /* One high voltage value for each pixel */
   put_int32(ps->num_pixels,iobuf);
   put_vector_of_int32(ps->pixel_HV_DAC,ps->num_pixels,iobuf);

   /* The same threshold for each pixel in a drawer */
   put_int32(ps->num_drawers,iobuf);
   put_vector_of_int32(ps->threshold_DAC,ps->num_drawers,iobuf);

   /* The same readout window for each pixel in a drawer */
   put_int32(ps->num_drawers,iobuf);
   put_vector_of_int(ps->ADC_start,ps->num_drawers,iobuf);
   put_vector_of_int(ps->ADC_count,ps->num_drawers,iobuf);
   
   /* The width of a readout sample in time may also be stored */
   if ( item_header.version >= 1 )
   {
      put_real(ps->time_slice,iobuf);
      put_int32(ps->sum_bins,iobuf);
   }

   /* We also have reference pulse shapes available. */
   /* These could be of potential use for later pulse shape analysis. */
   if ( item_header.version >= 2 )
   {
      int i, n;
      put_scount(ps->nrefshape,iobuf);
      put_scount(ps->lrefshape,iobuf);
      put_real(ps->ref_step,iobuf);
      for (n=0; n<ps->nrefshape; n++)
         for (i=0; i<ps->lrefshape; i++)
            put_sfloat(ps->refshape[n][i],iobuf);
   }  

   return put_item_end(iobuf,&item_header);
}

/* -------------------- read_hess_pixelset ------------------- */
/**
 *  Read the settings of pixel parameters (HV, thresholds, ...) in eventio format.
*/  

int read_hess_pixelset (IO_BUFFER *iobuf, PixelSetting *ps)
{
   IO_ITEM_HEADER item_header;
   int rc;
   
   if ( iobuf == (IO_BUFFER *) NULL || ps == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_PIXELSET;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 2 )
   {
      fprintf(stderr,"Unsupported pixel parameter version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }
   if ( ps->tel_id >= 0 && item_header.ident != ps->tel_id )
   {
      Warning("Refusing to copy PixelSetting for wrong telescope");
      get_item_end(iobuf,&item_header);
      return -1;
   }

   ps->setup_id = get_int32(iobuf);
   ps->trigger_mode = get_int32(iobuf);
   ps->min_pixel_mult = get_int32(iobuf);

   /* One high voltage value for each pixel */
   ps->num_pixels = get_int32(iobuf);
   if ( ps->num_pixels < 0 || ps->num_pixels > H_MAX_PIX )
   {
      char message[1024];
      snprintf(message,sizeof(message),
         "Data size in PixelSetting is invalid: You attempt to"
         " read settings for %d pixels but the library was compiled"
         " for a maximum of %d.", ps->num_pixels, H_MAX_PIX);
      Warning(message);
      ps->num_pixels = 0;
      get_item_end(iobuf,&item_header);
      return -1;
   }
   get_vector_of_int32(ps->pixel_HV_DAC,ps->num_pixels,iobuf);
   
   /* The same threshold for each pixel in a drawer */
   ps->num_drawers = get_int32(iobuf);
   if ( ps->num_drawers < 0 || ps->num_drawers > H_MAX_DRAWERS )
   {
      char message[1024];
      snprintf(message,sizeof(message),
         "Data size in PixelSetting is invalid: You attempt to"
         " read settings for %d drawers but the library was compiled"
         " for a maximum of %d.", ps->num_drawers, H_MAX_DRAWERS);
      Warning(message);
      ps->num_drawers = 0;
      get_item_end(iobuf,&item_header);
      return -1;
   }
   get_vector_of_int32(ps->threshold_DAC,ps->num_drawers,iobuf);

   /* The same readout window for each pixel in a drawer */
   if ( (rc=get_int32(iobuf)) != ps->num_drawers )
   {
      char message[1024];
      snprintf(message,sizeof(message),
         "Data size in PixelSetting is invalid: Expected data"
         " for %d drawers but got %d", ps->num_drawers, rc);
      Warning(message);
      ps->num_drawers = 0;
      get_item_end(iobuf,&item_header);
      return -1;
   }
   get_vector_of_int(ps->ADC_start,ps->num_drawers,iobuf);
   get_vector_of_int(ps->ADC_count,ps->num_drawers,iobuf);
   
   if ( item_header.version >= 1 )
   {
      ps->time_slice = get_real(iobuf);
      ps->sum_bins = get_int32(iobuf);
   }
   else
   {
      ps->time_slice = 0.;
      ps->sum_bins = 0;
   }

   /* We may also have reference pulse shapes available. */
   /* These could be of potential use for later pulse shape analysis. */
   if ( item_header.version >= 2 )
   {
      int i, n;
      ps->nrefshape = get_scount(iobuf);
      ps->lrefshape = get_scount(iobuf);
      if ( ps->nrefshape > H_MAX_GAINS || 
           ps->lrefshape > H_MAX_FSHAPE )
      {
         char message[1024];
         snprintf(message,sizeof(message),
            "Invalid reference pulse shape data in PixelSetting.\n");
         Warning(message);
         get_item_end(iobuf,&item_header);
         return -1;
      }
      ps->ref_step = get_real(iobuf);
      for (n=0; n<ps->nrefshape; n++)
      {
         for (i=0; i<ps->lrefshape; i++)
            ps->refshape[n][i] = get_sfloat(iobuf);
      }
   }
   else
   {
      ps->nrefshape = ps->lrefshape = 0;
      ps->ref_step = 0.;
   }

   return get_item_end(iobuf,&item_header);
}

/* -------------------- print_hess_pixelset ------------------- */
/**
 *  Show the settings of pixel parameters (HV, thresholds, ...) in eventio format.
*/  

int print_hess_pixelset (IO_BUFFER *iobuf)
{
   IO_ITEM_HEADER item_header;
   int i, rc;
   int tel_id, num_pixels, num_drawers;
   int hv_dac[H_MAX_PIX];
   int threshold_dac[H_MAX_DRAWERS];
   int adc_start[H_MAX_DRAWERS];
   int adc_count[H_MAX_DRAWERS];

   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;
      
   hs_check_env();

   item_header.type = IO_TYPE_HESS_PIXELSET;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 2 )
   {
      fprintf(stderr,"Unsupported pixel parameter version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }
   tel_id = item_header.ident;
   printf("\nPixel settings for telescope %d:\n", tel_id);
   printf("   Setup ID: %d\n", get_int32(iobuf));
   printf("   Trigger mode: %d\n", get_int32(iobuf));
   printf("   Minimum pixel multiplicity: %d\n", get_int32(iobuf));

   /* One high voltage value for each pixel */
   num_pixels = get_int32(iobuf);
   printf("   Number of pixels: %d\n", num_pixels);
   if ( num_pixels < 0 || num_pixels > H_MAX_PIX )
   {
      char message[1024];
      snprintf(message,sizeof(message),
         "Data size in PixelSetting is invalid: You attempt to"
         " read settings for %d pixels but the library was compiled"
         " for a maximum of %d.", num_pixels, H_MAX_PIX);
      Warning(message);
      get_item_end(iobuf,&item_header);
      return -1;
   }
   get_vector_of_int32(hv_dac,num_pixels,iobuf);
   
   /* The same threshold for each pixel in a drawer */
   num_drawers = get_int32(iobuf);
   printf("   Number of drawers: %d\n", num_drawers);
   if ( num_drawers < 0 || num_drawers > H_MAX_DRAWERS )
   {
      char message[1024];
      snprintf(message,sizeof(message),
         "Data size in PixelSetting is invalid: You attempt to"
         " read settings for %d drawers but the library was compiled"
         " for a maximum of %d.", num_drawers, H_MAX_DRAWERS);
      Warning(message);
      get_item_end(iobuf,&item_header);
      return -1;
   }
   get_vector_of_int32(threshold_dac,num_drawers,iobuf);

   /* The same readout window for each pixel in a drawer */
   if ( (rc=get_int32(iobuf)) != num_drawers )
   {
      char message[1024];
      snprintf(message,sizeof(message),
         "Data size in PixelSetting is invalid: Expected data"
         " for %d drawers but got %d", num_drawers, rc);
      Warning(message);
      get_item_end(iobuf,&item_header);
      return -1;
   }
   get_vector_of_int(adc_start,num_drawers,iobuf);
   get_vector_of_int(adc_count,num_drawers,iobuf);
   for ( i=0; i<5 && i<num_drawers; i++ )
   {
      if ( adc_count[i] > 0 )
         printf("   Drawer %d: start readout at offset %d for %d slices.\n",
            i, adc_start[i], adc_count[i]);
   }
   if ( num_drawers > 5 )
      printf("   ...\n");
   
   if ( item_header.version >= 1 )
   {
      printf("   A readout time slice is %4.2f ns long.\n", get_real(iobuf));
      printf("   Standard integration is over %d time slices.\n", get_int32(iobuf));
   }
   else
      printf("   Readout time slice length not known - most likely 1.0 ns.\n");

   if ( item_header.version >= 2 )
   {
      int l, n, nr, lr;
      double rs;
      nr = get_scount(iobuf);
      lr = get_scount(iobuf);
      rs = get_real(iobuf);
      printf("   Reference pulse shapes of %d (sub-) samples of %4.2f ns for %d gains.\n",
         lr, rs, nr);
      if ( hs_verbose )
      {
         for (n=0; n<nr; n++)
         {
            printf("   Shape %d:", n);
            for (l=0; l<lr; l++)
               printf(" %f", get_sfloat(iobuf));
            printf("\n");
         }
      }
      else
      {
         for (n=0; n<nr; n++)
            for (l=0; l<lr; l++)
               (void) get_sfloat(iobuf);
      }
   }
   return get_item_end(iobuf,&item_header);
}

/* -------------------- write_hess_pixeldis ------------------- */
/**
 *  Write which pixels are disabled in HV and/or trigger in eventio format.
*/  

int write_hess_pixeldis (IO_BUFFER *iobuf, PixelDisabled *pd)
{
   IO_ITEM_HEADER item_header;
   
   if ( iobuf == (IO_BUFFER *) NULL || pd == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_PIXELDISABLE;  /* Data type */
   item_header.version = 0;             /* Version 0 (test) */
   item_header.ident = pd->tel_id;
   put_item_begin(iobuf,&item_header);

   put_int32(pd->num_trig_disabled,iobuf);
   put_vector_of_int32(pd->trigger_disabled,pd->num_trig_disabled,iobuf);
   put_int32(pd->num_HV_disabled,iobuf);
   put_vector_of_int32(pd->HV_disabled,pd->num_HV_disabled,iobuf);

   return put_item_end(iobuf,&item_header);
}

/* -------------------- read_hess_pixeldis ------------------- */
/**
 *  Read which pixels are disabled in HV and/or trigger in eventio format.
*/  

int read_hess_pixeldis (IO_BUFFER *iobuf, PixelDisabled *pd)
{
   IO_ITEM_HEADER item_header;
   int rc;
   
   if ( iobuf == (IO_BUFFER *) NULL || pd == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_PIXELDISABLE;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version != 0 )
   {
      fprintf(stderr,"Unsupported disabled pixels version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }
   if ( pd->tel_id >= 0 && item_header.ident != pd->tel_id )
   {
      Warning("Refusing to copy PixelDisable for wrong telescope");
      get_item_end(iobuf,&item_header);
      return -1;
   }

   pd->num_trig_disabled = get_int32(iobuf);
   if ( pd->num_trig_disabled < 0 || pd->num_trig_disabled > H_MAX_PIX )
   {
      Warning("Data size invalid in PixelDisable");
      pd->num_trig_disabled = 0;
      get_item_end(iobuf,&item_header);
      return -1;
   }
   get_vector_of_int32(pd->trigger_disabled,pd->num_trig_disabled,iobuf);
   pd->num_HV_disabled = get_int32(iobuf);
   if ( pd->num_HV_disabled < 0 || pd->num_HV_disabled > H_MAX_PIX )
   {
      Warning("Data size invalid in PixelDisable");
      pd->num_HV_disabled = 0;
      get_item_end(iobuf,&item_header);
      return -1;
   }
   get_vector_of_int32(pd->HV_disabled,pd->num_HV_disabled,iobuf);

   return get_item_end(iobuf,&item_header);
}

/* -------------------- read_hess_pixeldis ------------------- */
/**
 *  Print which pixels are disabled in HV and/or trigger in eventio format.
*/  

int print_hess_pixeldis (IO_BUFFER *iobuf)
{
   IO_ITEM_HEADER item_header;
   int rc, i;
   int num_trig_disabled = 0, num_HV_disabled = 0;
   
   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_PIXELDISABLE;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version != 0 )
   {
      fprintf(stderr,"Unsupported disabled pixels version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }
   
   printf("\nPixels disabled in telescope %ld:\n", item_header.ident);

   num_trig_disabled = get_int32(iobuf);
   if ( num_trig_disabled == 0 )
      printf("   Trigger disabled: none  /");
   else
   {
      printf("   Trigger disabled in %d pixels\n", num_trig_disabled);
      for ( i=0; i<num_trig_disabled; i++)
         (void) get_int32(iobuf);
   }
   num_HV_disabled = get_int32(iobuf);
   if ( num_HV_disabled == 0 )
      printf("%s  HV disabled: none\n", num_trig_disabled?" ":"");
   else
   {
      printf("\n   HV disabled in %d pixels\n", num_HV_disabled);
      for ( i=0; i<num_HV_disabled; i++)
         (void) get_int32(iobuf);
   }

   return get_item_end(iobuf,&item_header);
}

/* -------------------- write_hess_camsoftset ------------------- */
/**
 *  Write camera software parameters relevant for data recording in eventio format.
*/

int write_hess_camsoftset (IO_BUFFER *iobuf, CameraSoftSet *cs)
{
   IO_ITEM_HEADER item_header;
   
   if ( iobuf == (IO_BUFFER *) NULL || cs == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_CAMSOFTSET;  /* Data type */
   item_header.version = 0;             /* Version 0 (test) */
   item_header.ident = cs->tel_id;
   put_item_begin(iobuf,&item_header);

   put_int32(cs->dyn_trig_mode,iobuf);
   put_int32(cs->dyn_trig_threshold,iobuf);
   put_int32(cs->dyn_HV_mode,iobuf);
   put_int32(cs->dyn_HV_threshold,iobuf);
   put_int32(cs->data_red_mode,iobuf);
   put_int32(cs->zero_sup_mode,iobuf);
   put_int32(cs->zero_sup_num_thr,iobuf);
   put_vector_of_int32(cs->zero_sup_thresholds,cs->zero_sup_num_thr,iobuf);
   put_int32(cs->unbiased_scale,iobuf);
   put_int32(cs->dyn_ped_mode,iobuf);
   put_int32(cs->dyn_ped_events,iobuf);
   put_int32(cs->dyn_ped_period,iobuf);
   put_int32(cs->monitor_cur_period,iobuf);
   put_int32(cs->report_cur_period,iobuf);
   put_int32(cs->monitor_HV_period,iobuf);
   put_int32(cs->report_HV_period,iobuf);

   return put_item_end(iobuf,&item_header);
}

/* -------------------- read_hess_camsoftset ------------------- */
/**
 *  Read camera software parameters relevant for data recording in eventio format.
*/

int read_hess_camsoftset (IO_BUFFER *iobuf, CameraSoftSet *cs)
{
   IO_ITEM_HEADER item_header;
   int rc;
   
   if ( iobuf == (IO_BUFFER *) NULL || cs == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_CAMSOFTSET;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version != 0 )
   {
      fprintf(stderr,"Unsupported camera software settings version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }
   if ( cs->tel_id >= 0 && item_header.ident != cs->tel_id )
   {
      Warning("Refusing to copy CameraSoftSet for wrong telescope");
      get_item_end(iobuf,&item_header);
      return -1;
   }

   cs->dyn_trig_mode = get_int32(iobuf);
   cs->dyn_trig_threshold = get_int32(iobuf);
   cs->dyn_HV_mode = get_int32(iobuf);
   cs->dyn_HV_threshold = get_int32(iobuf);
   cs->data_red_mode = get_int32(iobuf);
   cs->zero_sup_mode = get_int32(iobuf);
   cs->zero_sup_num_thr = get_int32(iobuf);
   if ( cs->zero_sup_num_thr < 0 || (size_t) cs->zero_sup_num_thr >
        sizeof(cs->zero_sup_thresholds)/sizeof(cs->zero_sup_thresholds[0]) )
   {
      Warning("Data size invalid in CameraSoftSet");
      cs->zero_sup_num_thr = 0;
      get_item_end(iobuf,&item_header);
      return -1;
   }
   get_vector_of_int32(cs->zero_sup_thresholds,cs->zero_sup_num_thr,iobuf);
   cs->unbiased_scale = get_int32(iobuf);
   cs->dyn_ped_mode = get_int32(iobuf);
   cs->dyn_ped_events = get_int32(iobuf);
   cs->dyn_ped_period = get_int32(iobuf);
   cs->monitor_cur_period = get_int32(iobuf);
   cs->report_cur_period = get_int32(iobuf);
   cs->monitor_HV_period = get_int32(iobuf);
   cs->report_HV_period = get_int32(iobuf);

   return get_item_end(iobuf,&item_header);
}

/* -------------------- write_hess_trackset ------------------- */
/**
 *  Write the settings for tracking of a telescope in eventio format.
*/  

int write_hess_trackset (IO_BUFFER *iobuf, TrackingSetup *ts)
{
   IO_ITEM_HEADER item_header;
   
   if ( iobuf == (IO_BUFFER *) NULL || ts == NULL )
      return -1;
      
   if ( !ts->known )
      return 0;

   item_header.type = IO_TYPE_HESS_TRACKSET;  /* Data type */
   item_header.version = 0;             /* Version 0 (test) */
   item_header.ident = ts->tel_id;
   put_item_begin(iobuf,&item_header);

   put_short(ts->drive_type_az,iobuf);
   put_short(ts->drive_type_alt,iobuf);
   put_real(ts->zeropoint_az,iobuf);
   put_real(ts->zeropoint_alt,iobuf);
   put_real(ts->sign_az,iobuf);
   put_real(ts->sign_alt,iobuf);
   put_real(ts->resolution_az,iobuf);
   put_real(ts->resolution_alt,iobuf);
   put_real(ts->range_low_az,iobuf);
   put_real(ts->range_low_alt,iobuf);
   put_real(ts->range_high_az,iobuf);
   put_real(ts->range_high_alt,iobuf);
   put_real(ts->park_pos_az,iobuf);
   put_real(ts->park_pos_alt,iobuf);

   return put_item_end(iobuf,&item_header);
}

/* -------------------- read_hess_trackset ------------------- */
/**
 *  Read the settings for tracking of a telescope in eventio format.
*/  

int read_hess_trackset (IO_BUFFER *iobuf, TrackingSetup *ts)
{
   IO_ITEM_HEADER item_header;
   int rc;
   
   if ( iobuf == (IO_BUFFER *) NULL || ts == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_TRACKSET;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version != 0 )
   {
      fprintf(stderr,"Unsupported tracking settings version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }
   if ( ts->tel_id >= 0 && item_header.ident != ts->tel_id )
   {
      Warning("Refusing to copy TrackingSetup for wrong telescope");
      get_item_end(iobuf,&item_header);
      return -1;
   }

   ts->drive_type_az = get_short(iobuf);
   ts->drive_type_alt = get_short(iobuf);
   ts->zeropoint_az = get_real(iobuf);
   ts->zeropoint_alt = get_real(iobuf);
   ts->sign_az = get_real(iobuf);
   ts->sign_alt = get_real(iobuf);
   ts->resolution_az = get_real(iobuf);
   ts->resolution_alt = get_real(iobuf);
   ts->range_low_az = get_real(iobuf);
   ts->range_low_alt = get_real(iobuf);
   ts->range_high_az = get_real(iobuf);
   ts->range_high_alt = get_real(iobuf);
   ts->park_pos_az = get_real(iobuf);
   ts->park_pos_alt = get_real(iobuf);
   
   ts->known = 1;

   return get_item_end(iobuf,&item_header);
}

/* -------------------- print_hess_trackset ------------------- */
/**
 *  Print the settings for tracking of a telescope in eventio format.
*/  

int print_hess_trackset (IO_BUFFER *iobuf)
{
   IO_ITEM_HEADER item_header;
   int rc, taz=0, talt=0;

   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_TRACKSET;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version != 0 )
   {
      fprintf(stderr,"Unsupported tracking settings version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }
   
   printf("\nTracking setup to telescope %ld:\n", item_header.ident);
   
   taz = get_short(iobuf);
   talt = get_short(iobuf);
   if ( taz != 0 || talt != 0 ) /* Not the usual Alt-Az mount ... */
   {
      printf("   Drive type: ");
      printf(" az = %d", taz);
      printf(", alt = %d\n", talt);
   }
   printf("   Zero point: ");
   printf(" az = %f deg.", get_real(iobuf)*(180./M_PI));
   printf(", alt = %f deg.\n", get_real(iobuf)*(180./M_PI));
   printf("   Sign: ");
   printf(" az = %f", get_real(iobuf));
   printf(", alt = %f\n", get_real(iobuf));
   printf("   Resolution: ");
   printf(" az = %f deg.", get_real(iobuf)*(180./M_PI));
   printf(", alt = %f deg.\n", get_real(iobuf)*(180./M_PI));
   printf("   Range low: ");
   printf(" az = %f deg.", get_real(iobuf)*(180./M_PI));
   printf(", alt = %f deg.\n", get_real(iobuf)*(180./M_PI));
   printf("   Range high: ");
   printf(" az = %f deg.", get_real(iobuf)*(180./M_PI));
   printf(", alt = %f deg.\n", get_real(iobuf)*(180./M_PI));
   printf("   Park position: ");
   printf(" az = %f deg.", get_real(iobuf)*(180./M_PI));
   printf(", alt = %f deg.\n", get_real(iobuf)*(180./M_PI));

   return get_item_end(iobuf,&item_header);
}

/* -------------------- write_hess_pointingcor ------------------- */
/**
 *  Write the parameters of a telescope's pointing correction in eventio format.
*/  

int write_hess_pointingcor (IO_BUFFER *iobuf, PointingCorrection *pc)
{
   IO_ITEM_HEADER item_header;
   
   if ( iobuf == (IO_BUFFER *) NULL || pc == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_POINTINGCOR;  /* Data type */
   item_header.version = 0;             /* Version 0 (test) */
   item_header.ident = pc->tel_id;
   put_item_begin(iobuf,&item_header);

   put_int32(pc->function_type,iobuf);
   put_int32(pc->num_param,iobuf);
   put_vector_of_real(pc->pointing_param,pc->num_param,iobuf);

   return put_item_end(iobuf,&item_header);
}

/* -------------------- read_hess_pointingcor ------------------- */
/**
 *  Read the parameters of a telescope's pointing correction in eventio format.
*/  

int read_hess_pointingcor (IO_BUFFER *iobuf, PointingCorrection *pc)
{
   IO_ITEM_HEADER item_header;
   int rc;
   
   if ( iobuf == (IO_BUFFER *) NULL || pc == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_POINTINGCOR;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version != 0 )
   {
      fprintf(stderr,"Unsupported pointing correction version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }
   if ( pc->tel_id >= 0 && item_header.ident != pc->tel_id )
   {
      Warning("Refusing to copy PointingCorrection for wrong telescope");
      get_item_end(iobuf,&item_header);
      return -1;
   }

   pc->function_type = get_int32(iobuf);
   pc->num_param = get_int32(iobuf);
   if ( pc->num_param < 0 || (size_t) pc->num_param >
        sizeof(pc->pointing_param)/sizeof(pc->pointing_param[0]) )
   {
      Warning("Invalid data size for PointingCorrection");
      pc->num_param = 0;
      get_item_end(iobuf,&item_header);
      return -1;
   }
   get_vector_of_real(pc->pointing_param,pc->num_param,iobuf);

   return get_item_end(iobuf,&item_header);
}

/* -------------------- print_hess_pointingcor ------------------- */
/**
 *  Print the parameters of a telescope's pointing correction in eventio format.
*/  

int print_hess_pointingcor (IO_BUFFER *iobuf)
{
   IO_ITEM_HEADER item_header;
   int rc, i;
   int function_type=0, num_param=0;
   
   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_POINTINGCOR;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version != 0 )
   {
      fprintf(stderr,"Unsupported pointing correction version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   function_type = get_int32(iobuf);
   num_param = get_int32(iobuf);
   if ( function_type == 0 && num_param == 0 )
      printf("\nPointing correction for telescope %ld: none\n", item_header.ident);
   else
      printf("\nPointing correction for telescope %ld with %d parameters for function %d:\n  ",
         item_header.ident, num_param, function_type);
   for ( i=0; i<num_param; i++ )
      printf(" %g", get_real(iobuf));

   return get_item_end(iobuf,&item_header);
}


/* -------------------- write_hess_centralevent ------------------- */
/**
 *  Write the trigger data of the central trigger in eventio format.
*/  

int write_hess_centralevent (IO_BUFFER *iobuf, CentralEvent *ce)
{
   IO_ITEM_HEADER item_header;
   int ntt = 0, itel, itrg;

   if ( iobuf == (IO_BUFFER *) NULL || ce == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_CENTEVENT;  /* Data type */
   item_header.version = 2;             /* Version 2 */
   item_header.ident = ce->glob_count;
   put_item_begin(iobuf,&item_header);

   put_time_blob(&ce->cpu_time,iobuf);
   put_time_blob(&ce->gps_time,iobuf);
   put_int32(ce->teltrg_pattern,iobuf);
   put_int32(ce->teldata_pattern,iobuf);

   if ( item_header.version >= 1 )
   {
      put_short(ce->num_teltrg,iobuf);
      put_vector_of_int(ce->teltrg_list,ce->num_teltrg,iobuf);
      put_vector_of_float(ce->teltrg_time,ce->num_teltrg,iobuf);
      put_short(ce->num_teldata,iobuf);
      put_vector_of_int(ce->teldata_list,ce->num_teldata,iobuf);
   }
   if ( item_header.version >= 2 )
   {
      for ( itel=0; itel<ce->num_teltrg; itel++ )
         put_count32(ce->teltrg_type_mask[itel], iobuf);
      for ( itel=0; itel<ce->num_teltrg; itel++ )
      {
         ntt = 0;
         for ( itrg=0; itrg<H_MAX_TRG_TYPES; itrg++ )
         {
            if ( (ce->teltrg_type_mask[itel] & (1<<itrg)) )
            {
               ntt++;
            }
         }
         if ( ntt > 1 ) // Need type-specific trigger times only with more than one type
         {
            for ( itrg=0; itrg<H_MAX_TRG_TYPES; itrg++ )
            {
               if ( (ce->teltrg_type_mask[itel] & (1<<itrg)) )
                  put_real(ce->teltrg_time_by_type[itel][itrg], iobuf);
            }
         }
      }
   }

   return put_item_end(iobuf,&item_header);
}

/* -------------------- read_hess_centralevent ------------------- */
/**
 *  Read the trigger data of the central trigger in eventio format.
*/  

int read_hess_centralevent (IO_BUFFER *iobuf, CentralEvent *ce)
{
   IO_ITEM_HEADER item_header;
   int rc, ntt, itel, itrg;
   
   if ( iobuf == (IO_BUFFER *) NULL || ce == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_CENTEVENT;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 2 )
   {
      fprintf(stderr,"Unsupported central event version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }
   ce->glob_count = item_header.ident;

   get_time_blob(&ce->cpu_time,iobuf);
   get_time_blob(&ce->gps_time,iobuf);
   ce->teltrg_pattern = get_int32(iobuf);
   ce->teldata_pattern = get_int32(iobuf);

   if ( item_header.version >= 1 )
   {
      ce->num_teltrg = get_short(iobuf);
      if ( ce->num_teltrg > H_MAX_TEL )
      {
         fprintf(stderr, 
            "Invalid number of triggered telescopes (%d) in central trigger block for event %d.\n",
            ce->num_teltrg, ce->glob_count);
         ce->num_teltrg = 0;
         get_item_end(iobuf,&item_header);
         return -1;
      }
      get_vector_of_int(ce->teltrg_list,ce->num_teltrg,iobuf);
      get_vector_of_float(ce->teltrg_time,ce->num_teltrg,iobuf);
      ce->num_teldata = get_short(iobuf);
      if ( ce->num_teldata > H_MAX_TEL )
      {
         fprintf(stderr, 
            "Invalid number of telescopes with data (%d) in central trigger block for event %d.\n",
            ce->num_teldata, ce->glob_count);
         ce->num_teldata = 0;
         get_item_end(iobuf,&item_header);
         return -1;
      }
      get_vector_of_int(ce->teldata_list,ce->num_teldata,iobuf);
   }
   else
   {
      ce->num_teltrg = 0;
      ce->num_teldata = 0;
   }

   if ( item_header.version >= 2 )
   {
      for ( itel=0; itel< ce->num_teltrg; itel++ )
         ce->teltrg_type_mask[itel] = get_count32(iobuf);
      for ( itel=0; itel< ce->num_teltrg; itel++ )
      {
         ntt = 0;
         for ( itrg=0; itrg<H_MAX_TRG_TYPES; itrg++ )
         {
            if ( (ce->teltrg_type_mask[itel] & (1<<itrg)) )
            {
               ntt++;
               ce->teltrg_time_by_type[itel][itrg] = ce->teltrg_time[itel];
            }
            else
               ce->teltrg_time_by_type[itel][itrg] = 9999.;
         }
         if ( ntt > 1 ) // Need type-specific trigger times only with more than one type
         {
            for ( itrg=0; itrg<H_MAX_TRG_TYPES; itrg++ )
            {
               if ( (ce->teltrg_type_mask[itel] & (1<<itrg)) )
                  ce->teltrg_time_by_type[itel][itrg] = get_real(iobuf);
            }
         }
      }
   }
   else
   {
      for ( itel=0; itel< ce->num_teltrg; itel++ )
      {
         ce->teltrg_type_mask[itel] = 1; // Older data was always majority trigger
         ce->teltrg_time_by_type[itel][0] = ce->teltrg_time[itel];
         for ( itrg=1; itrg<H_MAX_TRG_TYPES; itrg++ )
            ce->teltrg_time_by_type[itel][itrg] = 9999.;
      }
   }

   return get_item_end(iobuf,&item_header);
}

/* -------------------- print_hess_centralevent ------------------- */
/**
 *  Print the trigger data of the central trigger in eventio format.
*/  

int print_hess_centralevent (IO_BUFFER *iobuf)
{
   IO_ITEM_HEADER item_header;
   int rc, ntt, itrg;
   HTime cpu_time, gps_time;
   int num_teltrg=0, num_teldata=0, i;
   double teltrg_time[H_MAX_TEL];
   int teltrg_list[H_MAX_TEL];

   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_CENTEVENT;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 2 )
   {
      fprintf(stderr,"Unsupported central event version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }
   printf("  Central trigger event %ld\n",item_header.ident);
   get_time_blob(&cpu_time,iobuf);
   get_time_blob(&gps_time,iobuf);
   printf("    Central CPU time: %ld.%09ld\n", 
      cpu_time.seconds, cpu_time.nanoseconds);
   printf("    Central GPS time: %ld.%09ld\n", 
      gps_time.seconds, gps_time.nanoseconds);
   printf("    Telescope trigger pattern: %d\n", get_int32(iobuf));
   printf("    Telescope data pattern:    %d\n", get_int32(iobuf));

   if ( item_header.version >= 1 )
   {
      num_teltrg = get_short(iobuf);
      printf("    There were %d triggered telescopes:", num_teltrg);
      for (i=0; i<num_teltrg; i++)
      {
         teltrg_list[i] = get_short(iobuf);
         printf(" %d", teltrg_list[i]);
      }
      printf("\n");
      printf("    Time of central trigger:");
      for (i=0; i<num_teltrg; i++)
         printf(" %f", (teltrg_time[i] = get_real(iobuf)));
      printf("\n");
      num_teldata = get_short(iobuf);
      printf("    %d telescopes had data:", num_teldata);
      for (i=0; i<num_teldata; i++)
         printf(" %d", get_short(iobuf));
      printf("\n");
   }
   else
      printf("    No list of telescopes and no trigger times available.\n");

   if ( item_header.version >= 2 )
   {
      int teltrg_type_mask[H_MAX_TEL], all_mask = 0, all_mask_bits = 0;
      for ( i=0; i<num_teltrg; i++ )
      {
         int lt=0;
         teltrg_type_mask[i] = get_count32(iobuf);
         all_mask |= teltrg_type_mask[i];
         printf("    Telescope %d has trigger type mask: %d (", teltrg_list[i], teltrg_type_mask[i]);
         if ( (teltrg_type_mask[i] & 1) != 0 )
         {
            printf("majo");
            lt = 1;
         }
         if ( (teltrg_type_mask[i] & 2) != 0 )
         {
            printf("%sasum",lt?", ":"");
            lt = 1;
         }
         if ( (teltrg_type_mask[i] & 4) != 0 )
         {
            printf("%sdsum",lt?", ":"");
            lt = 1;
         }
         if ( (teltrg_type_mask[i] & 8) != 0 )
         {
            printf("%sdtrg",lt?", ":"");
            lt = 1;
         }
         printf(")\n");
      }
      for ( itrg=0; itrg<H_MAX_TRG_TYPES; itrg++ )
         if ( ((all_mask) & (1<<itrg)) )
            all_mask_bits++;
      if ( all_mask_bits > 1 )
         printf("    Trigger-type specific times of central trigger:\n");
      for ( i=0; i< num_teltrg; i++ )
      {
         double teltrg_time_by_type[H_MAX_TRG_TYPES];
         ntt = 0;
         for ( itrg=0; itrg<H_MAX_TRG_TYPES; itrg++ )
         {
            teltrg_time_by_type[itrg] = teltrg_time[i];
            if ( (teltrg_type_mask[i] & (1<<itrg)) )
               ntt++;
         }
         if ( ntt > 1 ) // Type-specific trigger times only with more than one type per tel.
         {
            for ( itrg=0; itrg<H_MAX_TRG_TYPES; itrg++ )
               if ( (teltrg_type_mask[i] & (1<<itrg)) )
                  teltrg_time_by_type[itrg] = get_real(iobuf);
         }
         if ( ntt > 1 || (all_mask_bits > 1 && ntt > 0) )
         // We also show type-specific trigger times when each telescope has
         // just one type of trigger but that type differs from tel. to tel.
         {
            printf("      #%d (tel. %d): type mask %d, times:", 
               i, teltrg_list[i], teltrg_type_mask[i]);
            for ( itrg=0; itrg<H_MAX_TRG_TYPES; itrg++ )
            {
               if ( (teltrg_type_mask[i] & (1<<itrg)) )
                  printf(" %f", teltrg_time_by_type[itrg]);
               else
                  printf(" (none)");
            }
            printf(" ns\n");
         }
      }
   }

   return get_item_end(iobuf,&item_header);
}

/* -------------------- write_hess_trackevent ------------------- */
/**
 *  Write a tracking position in eventio format.
*/  

int write_hess_trackevent (IO_BUFFER *iobuf, TrackEvent *tke)
{
   IO_ITEM_HEADER item_header;
   
   if ( iobuf == (IO_BUFFER *) NULL || tke == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_TRACKEVENT + 
     (unsigned) ((tke->tel_id%100) + 1000*(tke->tel_id/100)); /* Data type */
   item_header.version = 0;             /* Version 0 (test) */
   item_header.ident = (tke->tel_id & 0xff) + 
      	 (tke->raw_known?0x100:0) + (tke->cor_known?0x200:0) +
         ((tke->tel_id & 0x3f00)<<16);
   put_item_begin(iobuf,&item_header);

   if ( tke->raw_known )
   {
      put_real(tke->azimuth_raw,iobuf);
      put_real(tke->altitude_raw,iobuf);
   }
   if ( tke->cor_known )
   {
      put_real(tke->azimuth_cor,iobuf);
      put_real(tke->altitude_cor,iobuf);
   }
   
   return put_item_end(iobuf,&item_header);
}

/* -------------------- read_hess_trackevent ------------------- */
/**
 *  Read a tracking position in eventio format.
*/  

int read_hess_trackevent (IO_BUFFER *iobuf, TrackEvent *tke)
{
   IO_ITEM_HEADER item_header;
   int rc, tel_id;
   
   if ( iobuf == (IO_BUFFER *) NULL || tke == NULL )
      return -1;

   item_header.type = 0;  /* No data type this time */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   // tel_id = (item_header.type - IO_TYPE_HESS_TRACKEVENT) % 100 +
   //         100 * ((item_header.type - IO_TYPE_HESS_TRACKEVENT) / 1000);
   tel_id = (item_header.ident & 0xff) | ((item_header.ident & 0x3f000000) >> 16);
   if ( tel_id < 0 || tel_id != tke->tel_id )
   {
      Warning("Not a tracking event block or one for the wrong telescope");
      get_item_end(iobuf,&item_header);
      return -1;
   }
   if ( item_header.version != 0 )
   {
      fprintf(stderr,"Unsupported tracking event version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   if ( tke->tel_id != tel_id )
   {
      Warning("Tracking data is for wrong telescope.");
      get_item_end(iobuf,&item_header);
      return -1;
   }
   
   tke->raw_known = (item_header.ident & 0x100) != 0;
   tke->cor_known = (item_header.ident & 0x200) != 0;

   if ( tke->raw_known )
   {
      tke->azimuth_raw = get_real(iobuf);
      tke->altitude_raw = get_real(iobuf);
   }
   if ( tke->cor_known )
   {
      tke->altitude_cor = get_real(iobuf);
      tke->azimuth_cor = get_real(iobuf);
   }

   return get_item_end(iobuf,&item_header);
}

/* -------------------- print_hess_trackevent ------------------- */
/**
 *  Print the tracking data in eventio format.
*/  

int print_hess_trackevent (IO_BUFFER *iobuf)
{
   IO_ITEM_HEADER item_header;
   int rc, tel_id;
   int raw_known = 0, cor_known = 0;
   
   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;

   item_header.type = 0;  /* No data type this time */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   //tel_id = (item_header.type - IO_TYPE_HESS_TRACKEVENT) % 100 +
   //         100 * ((item_header.type - IO_TYPE_HESS_TRACKEVENT) / 1000);
   tel_id = (item_header.ident & 0xff) | ((item_header.ident & 0x3f000000) >> 16);
   if ( tel_id < 0 )
   {
      Warning("Not a tracking event block or one for an invalid telescope");
      get_item_end(iobuf,&item_header);
      return -1;
   }
   printf("  Tracking data for telescope %d:\n", tel_id);
   if ( item_header.version != 0 )
   {
      fprintf(stderr,"Unsupported tracking event version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   raw_known = (item_header.ident & 0x100) != 0;
   cor_known = (item_header.ident & 0x200) != 0;

   if ( raw_known )
   {
      double azimuth_raw, altitude_raw;
      azimuth_raw = get_real(iobuf);
      altitude_raw = get_real(iobuf);
      printf("    Raw: az = %6.4f deg, alt = %6.4f deg.\n",
         azimuth_raw*(180./M_PI), altitude_raw*(180./M_PI));
   }
   if ( cor_known )
   {
      double azimuth_cor, altitude_cor;
      altitude_cor = get_real(iobuf);
      azimuth_cor = get_real(iobuf);
      printf("    Corrected: az = %6.4f deg, alt = %6.4f deg.\n",
         azimuth_cor*(180./M_PI), altitude_cor*(180./M_PI));
   }

   return get_item_end(iobuf,&item_header);
}

/* -------------------- write_hess_televt_head ----------------- */
/**
 *  Write the event header for data from one camera in eventio format.
*/  

int write_hess_televt_head (IO_BUFFER *iobuf, TelEvent *te)
{
   IO_ITEM_HEADER item_header;
   int i, t;
   
   if ( iobuf == (IO_BUFFER *) NULL || te == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_TELEVTHEAD;  /* Data type */
#if (H_MAX_PIX >= 32768 || H_MAX_SECTORS >= 32768 )
   item_header.version = 2;    /* Version 2 supporting more than 32767 sectors */
#else
   item_header.version = 1;    /* full backward compatibility for some time */
#endif
   item_header.ident = te->tel_id;
   put_item_begin(iobuf,&item_header);

   put_int32(te->loc_count,iobuf);
   put_int32(te->glob_count,iobuf);
   put_time_blob(&te->cpu_time,iobuf);
   put_time_blob(&te->gps_time,iobuf);
   t = (te->trg_source & 0xff) | 
       (te->num_list_trgsect>0 ? 0x100:0) |
       (te->num_phys_addr>0 ? 0x200:0) |
       (te->known_time_trgsect ? 0x400:0);
   put_short(t,iobuf);
   if ( (t & 0x100) )
   {
      if ( item_header.version >= 2 )
      {
         put_scount32(te->num_list_trgsect,iobuf);
         for (i=0; i<te->num_list_trgsect; i++)
	    put_scount32(te->list_trgsect[i],iobuf);
      }
      else
      {
         put_short(te->num_list_trgsect,iobuf);
         for (i=0; i<te->num_list_trgsect; i++)
	    put_short(te->list_trgsect[i],iobuf);
      }
      if ( item_header.version >= 1 && (t & 0x400) )
      {
         for (i=0; i<te->num_list_trgsect; i++)
	    put_real(te->time_trgsect[i],iobuf);
      }
//      if ( item_header.version >= ... )
//      {
//         for (i=0; i<te->num_list_trgsect; i++)
//	    put_byte(te->type_trgsect[i],iobuf);
//      }
   }
   if ( (t & 0x200) )
   {
      if ( item_header.version >= 2 )
      {
         put_scount32(te->num_phys_addr,iobuf);
         for (i=0; i<te->num_phys_addr; i++)
	    put_scount32(te->phys_addr[i],iobuf);
      }
      else
      {
         put_short(te->num_phys_addr,iobuf);
         for (i=0; i<te->num_phys_addr; i++)
	    put_short(te->phys_addr[i],iobuf);
      }
   }

   return put_item_end(iobuf,&item_header);
}


/* -------------------- read_hess_televt_head ----------------- */
/**
 *  Read the event header for data from one camera in eventio format.
*/  

int read_hess_televt_head (IO_BUFFER *iobuf, TelEvent *te)
{
   IO_ITEM_HEADER item_header;
   int rc=0, i, t;
   
   if ( iobuf == (IO_BUFFER *) NULL || te == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_TELEVTHEAD;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 2 )
   {
      fprintf(stderr,"Unsupported telescope event header version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }
   if ( item_header.ident != te->tel_id )
   {
      Warning("Event header is for wrong telescope");
      get_item_end(iobuf,&item_header);
      return -1;
   }

   te->loc_count = get_int32(iobuf);
   te->glob_count = get_int32(iobuf);
   get_time_blob(&te->cpu_time,iobuf);
   get_time_blob(&te->gps_time,iobuf);
   t = get_short(iobuf);
   te->trg_source = t & 0xff;
   te->known_time_trgsect = 0;

   if ( (t & 0x100) )
   {
      te->num_list_trgsect = (item_header.version<=1 ? 
            get_short(iobuf) : get_scount32(iobuf));
      for (i=0; i<te->num_list_trgsect; i++)
	 te->list_trgsect[i] = (item_header.version<=1 ?
               get_short(iobuf) : get_scount32(iobuf));
      if ( item_header.version >= 1 && (t & 0x400) )
      {
         for (i=0; i<te->num_list_trgsect; i++)
	    te->time_trgsect[i] = get_real(iobuf);
         te->known_time_trgsect = 1;
      }
      else
      {
         for (i=0; i<te->num_list_trgsect; i++)
            te->time_trgsect[i] = 0.;
      }
//      if ( item_header.version >= ... )
//      {
//         for (i=0; i<te->num_list_trgsect; i++)
//	    te->type_trgsect[i] = get_byte(iobuf);
//      }
   }
   if ( (t & 0x200) )
   {
      te->num_phys_addr = (item_header.version<=1 ? 
            get_short(iobuf) : get_scount32(iobuf));
      for (i=0; i<te->num_phys_addr; i++)
	 te->phys_addr[i] = (item_header.version<=1 ? 
               get_short(iobuf) : get_scount32(iobuf));
   }

   return get_item_end(iobuf,&item_header);
}

/* -------------------- print_hess_televt_head ----------------- */
/**
 *  Print the event header for data from one camera in eventio format.
*/  

int print_hess_televt_head (IO_BUFFER *iobuf)
{
   IO_ITEM_HEADER item_header;
   int rc=0, i, t;
   HTime cpu_time, gps_time;
   // int known_time_trgsect = 0;
   
   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_TELEVTHEAD;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 2 )
   {
      fprintf(stderr,"Unsupported telescope event header version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   printf("    Telescope event header for telescope %ld:\n",item_header.ident);
   printf("      Local count: %d,", get_int32(iobuf));
   printf(" global count: %d\n", get_int32(iobuf));
   get_time_blob(&cpu_time,iobuf);
   get_time_blob(&gps_time,iobuf);
   printf("      CPU time: %ld.%09ld, GPS time: %ld.%09ld\n", 
      cpu_time.seconds,cpu_time.nanoseconds, 
      gps_time.seconds,gps_time.nanoseconds);
   t = get_short(iobuf);
   printf("      Trigger source: %d, flags: %04x\n", t & 0xff, t & 0xff00);

   if ( (t & 0x100) )
   {
      int num_list_trgsect = (item_header.version<=1 ? 
            get_short(iobuf) : get_scount32(iobuf));
      printf("      %4d triggered sectors:", num_list_trgsect);
      for (i=0; i<num_list_trgsect; i++)
	 printf(" %6d", (item_header.version<=1 ? 
               get_short(iobuf) : get_scount32(iobuf)));
      if ( item_header.version >= 1 && (t & 0x400) )
      {
         printf("\n                     at time:");
         for (i=0; i<num_list_trgsect; i++)
	    printf(" %6.2f",get_real(iobuf));
         printf(" ns");
         // known_time_trgsect = 1;
      }
//      if ( item_header.version >= ... )
//      {
//         printf("\n                     of type:");
//         for (i=0; i<te->num_list_trgsect; i++)
//	    printf(" %d", get_byte(iobuf));
//         printf("\n");
//      }
      printf("\n");
   }
   if ( (t & 0x200) )
   {
      int num_phys_addr = (item_header.version<=1 ? 
            get_short(iobuf) : get_scount32(iobuf));
      printf("      %d physical addresses:", num_phys_addr);
      for (i=0; i<num_phys_addr; i++)
	 printf("\t%d", (item_header.version<=1 ?
               get_short(iobuf) : get_scount32(iobuf)));
      printf("\n");
   }

   return get_item_end(iobuf,&item_header);
}

void put_adcsum_as_uint16(uint32_t *adc_sum, int n, IO_BUFFER *iobuf);
void get_adcsum_as_uint16(uint32_t *adc_sum, int n, IO_BUFFER *iobuf);

void put_adcsum_as_uint16(uint32_t *adc_sum, int n, IO_BUFFER *iobuf)
{
    /* Old format: 16-bit unsigned, good for <= 16 samples of <= 12 bits or such. */
   uint16_t short_adc_sum[H_MAX_PIX];
   int ipix;
   for (ipix=0; ipix<n; ipix++)
   {
      if ( adc_sum[ipix] < 65535 )
         short_adc_sum[ipix] = (uint16_t) adc_sum[ipix]; /* Possible overflow */
      else
         short_adc_sum[ipix] = 65535;
   }
   put_vector_of_uint16(short_adc_sum,n,iobuf);
}

void get_adcsum_as_uint16(uint32_t *adc_sum, int n, IO_BUFFER *iobuf)
{
    /* Old format: 16-bit unsigned, good for <= 16 samples of <= 12 bits or such. */
   uint16_t short_adc_sum[H_MAX_PIX];
   int ipix;
   get_vector_of_uint16(short_adc_sum,n,iobuf);
   for (ipix=0; ipix<n; ipix++)
      adc_sum[ipix] = short_adc_sum[ipix];
}

void put_adcsum_differential(uint32_t *adc_sum, int n, IO_BUFFER *iobuf);
void get_adcsum_differential(uint32_t *adc_sum, int n, IO_BUFFER *iobuf);

void put_adcsum_differential(uint32_t *adc_sum, int n, IO_BUFFER *iobuf)
{
   /* New format: store as variable-size integers of the amplitude
      difference from one pixel to the next one, keeping the data size
      small for amplitudes around a common pedestal. ADC sums fitting
      into a 32-bit unsigned integer are supported. */
   int ipix;
   int32_t prev_amp = 0, amp_diff, this_amp;
   for ( ipix=0; ipix<n; ipix++ )
   {
      this_amp = (int32_t) adc_sum[ipix];
      amp_diff = this_amp - prev_amp;
      prev_amp = this_amp;
      put_scount32(amp_diff,iobuf);
   }
}

void get_adcsum_differential(uint32_t *adc_sum, int n, IO_BUFFER *iobuf)
{
   /* New format: store as variable-size integers. */
   int ipix;
   int32_t prev_amp = 0, this_amp;
   for ( ipix=0; ipix<n; ipix++ )
   {
      this_amp = get_scount32(iobuf) + prev_amp;
      prev_amp = this_amp;
      adc_sum[ipix] = (uint32_t) this_amp;
   }
}

void put_adcsample_differential(uint16_t *adc_sample, int n, IO_BUFFER *iobuf);
void get_adcsample_differential(uint16_t *adc_sample, int n, IO_BUFFER *iobuf);

void put_adcsample_differential(uint16_t *adc_sample, int n, IO_BUFFER *iobuf)
{
   /* New format: store as variable-size integers of the amplitude difference
      between two consecutive time slices. Amplitudes in each time slice
      should fit in a 16-bit unsigned integer. */
   int ibin;
   int32_t prev_amp = 0, amp_diff, this_amp;
   for ( ibin=0; ibin<n; ibin++ )
   {
      this_amp = adc_sample[ibin];
      amp_diff = this_amp - prev_amp;
      prev_amp = this_amp;
      put_scount32(amp_diff,iobuf);
   }
}

void get_adcsample_differential(uint16_t *adc_sample, int n, IO_BUFFER *iobuf)
{
   /* New format: store as variable-size integers. */
   int ibin;
   int32_t prev_amp = 0, this_amp;
   for ( ibin=0; ibin<n; ibin++ )
   {
      adc_sample[ibin] = this_amp = get_scount32(iobuf) + prev_amp;
      prev_amp = this_amp;
   }
}

/* -------------------- write_hess_teladc_sums ----------------- */
/**
 *  @short Write ADC sum data for one camera in eventio format.
 *
 *  The data can be optionally reduced (like writing only
 *  high-gain channels for pixels with low signals etc.)
 *  and zero-suppressed (not writing anything for pixels
 *  with very low signals).
*/  

int write_hess_teladc_sums (IO_BUFFER *iobuf, AdcData *raw)
{
   IO_ITEM_HEADER item_header;
   int flags, i, j, k, n, v8, f8, m, mlg, mhg16, mhg8;
   int offset_hg8 = 0, scale_hg8 = 0, scale_hg8half = 0;
   uint32_t lgval[16], hgval[16];
   uint16_t cflags, bflags, zbits;
   uint8_t hgval8[16];
   int zero_sup_mode = (raw->zero_sup_mode & 0x1f);
   int data_red_mode = (raw->data_red_mode & 0x1f);
   int list_known = raw->list_known;
#ifdef XXDEBUG
   int mlg_tot = 0, mhg16_tot = 0, mhg8_tot = 0, m_tot = 0;
#endif
   
   if ( iobuf == (IO_BUFFER *) NULL || raw == NULL )
      return -1;

   if ( !raw->known )
      return 0;

   item_header.type = IO_TYPE_HESS_TELADCSUM;  /* Data type */
   // item_header.version = 1;             /* Version 1 (revised) */
   // if ( raw->num_pixels > 4095 ) /* Strictly needed for large no. of pixels. */
   //   item_header.version = 2;             /* Version 2 (revised again) */
   item_header.version = 3;             /* Version 3 (compatible with 32-bit adc_sum) */
   if ( raw->num_pixels > 32767 && raw->zero_sup_mode >= 2 )
      item_header.version = 4;
   if ( raw->num_pixels > 8191 && raw->zero_sup_mode >= 2 && raw->data_red_mode != 0 )
      item_header.version = 4;

   /* If threshold is zero there cannot be any data reduction. */
   if ( raw->threshold == 0 )
      data_red_mode = 0;
   /* In addition all zero suppression and data reduction code */
   /* below is for data with two gains although the data format */
   /* is more general. More general code would be less efficient. */
   /* Zero suppression mode 2 is also not compatible with 8182 or more pixels (is this fixed ????) */
   //   if ( raw->num_gains != 2 || (raw->num_pixels>=8192 && zero_sup_mode==2) )
   //      zero_sup_mode = data_red_mode = 0;
   /* Zero suppression mode 2 is at format version 3 definitely not compatible with 32768 or more pixels */
   if ( (raw->num_pixels>=32768 && zero_sup_mode>=2 && item_header.version<4) )
       zero_sup_mode = 1;
   /* Data reduction even has a problem with more than 8191 pixels, later shifted to 2 mio. */
   if ( (raw->num_pixels>=8192 && data_red_mode>0 && item_header.version<4) )
       data_red_mode = 0;

   /* Check if the combination of active options is reasonable */
   if ( raw->list_known < 0 || raw->list_known > 2 ||
        zero_sup_mode < 0 || zero_sup_mode > 4 ||
	data_red_mode < 0 || data_red_mode > 2 ||
	raw->num_pixels < 0 || 
        (raw->num_pixels > 4095 && item_header.version < 2) || 
	raw->num_gains < 1 || raw->num_gains > 2 )
   {
      Warning("Unsupported raw data mode");
      return -1;
   }

   /* If list mode wanted but no list yet available, create it */
   // if ( zero_sup_mode == 2 && raw->list_known == 0 )
   //   zero_sup_mode = 3;
   /* Create pixel list and find best suppression scheme: */
   if ( zero_sup_mode == 3 || (zero_sup_mode == 2 && raw->list_known == 0) )
   {
      int nlst = 0;
      for (i=0; i<raw->num_pixels; i++)
      	 if ( raw->significant[i] ) /* Any significance bit, including sample-mode bits */
	    raw->adc_list[nlst++] = i;
      /* List is now available */
      raw->list_known = list_known = 1;
      raw->list_size = nlst;
      /* For large numbers of significant pixels bitmap mode saves space */
      /* compared to list mode. If almost all pixels are significant it */
      /* is not only simpler but also more efficient to use plain mode. */
      if ( zero_sup_mode == 3 )
      { 
      	 if ( 17*nlst/16 > raw->num_pixels )
	    zero_sup_mode = 0; /* plain mode */
      	 else if ( 15*nlst > raw->num_pixels )
      	    zero_sup_mode = 1; /* simple bitmap mode */
      	 else
      	    zero_sup_mode = 2; /* list mode */
      }
   }
   if ( zero_sup_mode == 2 )
      raw->list_known = 1;
   else if ( zero_sup_mode == 3 )
   {
      Warning("Zero suppression mode 3 not implemented yet. Using mode 1.\n");
      zero_sup_mode = 1;
   }

   /* Bit masks are commented out because range of values was checked */
   /* but left here to indicate range of manageable values. */
   flags = ( (zero_sup_mode /* & 0x1f */) )      |
           ( (data_red_mode /* & 0x1f */) << 5 ) |
	   ( (raw->list_known!=0?1:0) << 10 );
   if ( item_header.version < 2 )
      flags |= ( (raw->num_pixels /* & 0x0fff */) << 12 ) |
	   ( ((raw->num_gains==2) ? 1 : 0) << 24 ) |
	   ( (raw->tel_id & 0x1f) << 25 );
   else
      flags |= ( (raw->tel_id & 0xffff) << 12 );

   item_header.ident = flags;
   put_item_begin(iobuf,&item_header);

   if ( item_header.version >= 4 && raw->data_red_mode == 2 )
   {
      put_scount32(raw->threshold,iobuf);
      put_scount32(raw->offset_hg8,iobuf);
      put_scount32(raw->scale_hg8,iobuf);
   }

   if ( item_header.version >= 2 )
   {
      put_long(raw->num_pixels,iobuf);
      put_short(raw->num_gains,iobuf);
   }
   
   if ( data_red_mode == 2 )
   {
      offset_hg8 = raw->offset_hg8;
      scale_hg8 = raw->scale_hg8;
      /* The common offset must be representable by a 16-bit integer */
      if (offset_hg8 <= 0 )
      {
      	 int mm = 0;
      	 for ( k=0; k<raw->num_pixels; k++ )
	    mm += (int) raw->adc_sum[HI_GAIN][k];
	 mm /= raw->num_pixels;
	 offset_hg8 = mm;
      }
      if ( offset_hg8 > 32767 )
	 offset_hg8 = 32767;
      put_short(offset_hg8,iobuf);
      /* Scaling can be over a limited range only */
      if ( scale_hg8 < 1 )
	 scale_hg8 = 1;
      else if ( scale_hg8 > 100 )
	 scale_hg8 = 100;
      put_short(scale_hg8,iobuf);
      scale_hg8half = scale_hg8 / 2;
   }

#ifdef XXDEBUG
printf("### z = %d, d = %d\n", zero_sup_mode, data_red_mode);
#endif

   switch ( zero_sup_mode )
   {
      /* -------------- Zero suppression mode 0 --------------- */
      case 0: /* No zero suppression */
#ifdef XXDEBUG
m_tot = raw->num_pixels;
#endif
      	 switch ( data_red_mode )
	 {
	    case 0: /* No data reduction */
	       /* Note: in this mode ADC sums are stored in the internal order, */
	       /* no matter how many different gains there are per PMT. */
	       /* In all other modes, the order is fixed (lg/hg16/hg8) and limited */
	       /* to two different gains per PMT. */
	       for (i=0; i<raw->num_gains; i++)
               {
                  if ( item_header.version <= 2 )
                     put_adcsum_as_uint16(raw->adc_sum[i],raw->num_pixels,iobuf);
                  else
                     put_adcsum_differential(raw->adc_sum[i],raw->num_pixels,iobuf);
               }
	       break;
	    case 1: /* Skip low low-gain channels (for two gains) */
	       n = raw->num_pixels;
	       cflags = 0;
	       j = k = mlg = 0;
	       while ( n-- > 0 )
	       {
#if ( H_MAX_GAINS >= 2 )
		  if ( /* (int) raw->adc_sum[HI_GAIN][k] >= raw->threshold && */
                       (raw->adc_known[LO_GAIN][k] & 0x01) && 
                       raw->num_gains >= 2 )
		  {
		     lgval[mlg++] = raw->adc_sum[LO_GAIN][k];
		     cflags |= (uint16_t)1 << j;
		  }
#endif
		  k++;
	          if ( ++j == 16 || n == 0 )
		  {
		     put_vector_of_uint16(&cflags,1,iobuf);
		     // put_vector_of_uint16(lgval,mlg,iobuf);
		     // put_vector_of_uint16(&raw->adc_sum[HI_GAIN][k-j],j,iobuf);
                     if ( item_header.version <= 2 )
                     {
                        if ( raw->num_gains >= 2 )
                           put_adcsum_as_uint16(lgval,mlg,iobuf);
                        put_adcsum_as_uint16(&raw->adc_sum[HI_GAIN][k-j],j,iobuf);
                     }
                     else
                     {
                        if ( raw->num_gains >= 2 )
                           put_adcsum_differential(lgval,mlg,iobuf);
                        put_adcsum_differential(&raw->adc_sum[HI_GAIN][k-j],j,iobuf);
                     }
#ifdef XXDEBUG
mlg_tot += mlg;
mhg16_tot += j;
#endif
		     mlg = 0;
		     cflags = 0;
		     j = 0;
		  }
	       }
      	       break;
	    case 2: /* Also reduce width of high-gain channel if possible */
	       n = raw->num_pixels;
	       cflags = bflags = 0;
	       j = k = mlg = mhg16 = mhg8 = 0;
	       while ( n-- > 0 )
	       {
#if ( H_MAX_GAINS >= 2 )
		  if ( (int) raw->adc_sum[HI_GAIN][k] >= raw->threshold &&
                        raw->num_gains >= 2 )
		  {
		     lgval[mlg++] = raw->adc_sum[LO_GAIN][k];
		     cflags |= (uint16_t)1 << j;
		     hgval[mhg16++] = raw->adc_sum[HI_GAIN][k];
		  }
		  else
#endif
		  {
                     /* Warning: for single-channel data with many bits of precision this mode is better avoided */
		     f8 = 0;
		     if ( (v8 = (int) raw->adc_sum[HI_GAIN][k] - offset_hg8) >= 0 )
		     {
		     	v8 = (v8 + scale_hg8half) / scale_hg8;
			if ( v8 < 255 )
			   f8 = 1;
		     }
		     if ( f8 )
		     {
			hgval8[mhg8++] = (uint8_t) v8;
			bflags |= (uint16_t)1 << j;
		     }
		     else
		     {
		     	hgval[mhg16++] = raw->adc_sum[HI_GAIN][k]; /* Possible overflow */
		     }
		  }
		  k++;
	          if ( ++j == 16 || n == 0 )
		  {
		     put_vector_of_uint16(&cflags,1,iobuf);
		     put_vector_of_uint16(&bflags,1,iobuf);
		     // put_vector_of_uint16(lgval,mlg,iobuf);
		     // put_vector_of_uint16(hgval,mhg16,iobuf);
                     if ( item_header.version <= 2 )
                     {
                        if ( raw->num_gains >= 2 )
                           put_adcsum_as_uint16(lgval,mlg,iobuf);
                        put_adcsum_as_uint16(hgval,mhg16,iobuf);
                     }
                     else
                     {
                        if ( raw->num_gains >= 2 )
                           put_adcsum_differential(lgval,mlg,iobuf);
                        put_adcsum_differential(hgval,mhg16,iobuf);
                     }
		     put_vector_of_uint8(hgval8,mhg8,iobuf);
#ifdef XXDEBUG
mlg_tot += mlg;
mhg16_tot += mhg16;
mhg8_tot += mhg8;
#endif
		     mlg = mhg8 = mhg16 = 0;
		     cflags = bflags = 0;
		     j = 0;
		  }
	       }
      	       break;
	    default:
	       assert(0);
	 }
	 break;
	 
      /* -------------- Zero suppression mode 1 --------------- */
      case 1: /* Bit pattern indicates zero suppression */
      	 switch ( data_red_mode )
	 {
	    case 0: /* No data reduction */
	       n = raw->num_pixels;
	       j = k = m = 0;
	       zbits = 0;
	       while ( n-- > 0 )
	       {
	          if ( raw->significant[k] )
		  {
#ifdef XXDEBUG
m_tot++;
#endif
		     zbits |= 1 << j;
#if (H_MAX_GAINS >= 2)
                     /* Copying probably faster than checking if raw->num_gains > 1 */
		     lgval[m] = raw->adc_sum[LO_GAIN][k]; /* Possible overflow */
#else
                     lgval[m] = 0;
#endif
		     hgval[m] = raw->adc_sum[HI_GAIN][k]; /* Possible overflow */
		     m++;
		  }
		  k++;
		  if ( ++j == 16 || n == 0 )
		  {
		     put_vector_of_uint16(&zbits,1,iobuf);
		     if ( zbits != 0 )
		     {
		     	// put_vector_of_uint16(lgval,m,iobuf);
		     	// put_vector_of_uint16(hgval,m,iobuf);
                        if ( item_header.version <= 2 )
                        {
                           if ( raw->num_gains >= 2 )
                              put_adcsum_as_uint16(lgval,m,iobuf);
                           put_adcsum_as_uint16(hgval,m,iobuf);
                        }
                        else
                        {
                           if ( raw->num_gains >= 2 )
                              put_adcsum_differential(lgval,m,iobuf);
                           put_adcsum_differential(hgval,m,iobuf);
                        }
#ifdef XXDEBUG
mlg_tot += m;
mhg16_tot += m;
#endif
		     }
		     m = 0;
		     zbits = 0;
		     j = 0;
		  }
	       }
	       break;
#if (H_MAX_GAINS >= 2)
	    case 1: /* Skip low low-gain channels (for two gains) */
	       n = raw->num_pixels;
	       zbits = cflags = 0;
	       j = k = mlg = m = 0;
	       while ( n-- > 0 )
	       {
	          if ( raw->significant[k] )
		  {
#ifdef XXDEBUG
m_tot++;
#endif
		     zbits |= 1 << j;
		     if ( /* (int) raw->adc_sum[HI_GAIN][k] >= raw->threshold && */
                          (raw->adc_known[LO_GAIN][k] & 0x01) &&
                          raw->num_gains >= 2 )
		     {
		     	cflags |= (uint16_t)1 << j;
		     	lgval[mlg++] = raw->adc_sum[LO_GAIN][k];
		     }
		     hgval[m] = raw->adc_sum[HI_GAIN][k]; /* Possible overflow */
		     m++;
		  }
		  k++;
		  if ( ++j == 16 || n == 0 )
		  {
		     put_vector_of_uint16(&zbits,1,iobuf);
		     if ( zbits != 0 )
		     {
		     	put_vector_of_uint16(&cflags,1,iobuf);
		     	// put_vector_of_uint16(lgval,mlg,iobuf);
		     	// put_vector_of_uint16(hgval,m,iobuf);
                        if ( item_header.version <= 2 )
                        {
                           if ( raw->num_gains >= 2 )
                              put_adcsum_as_uint16(lgval,mlg,iobuf);
                           put_adcsum_as_uint16(hgval,m,iobuf);
                        }
                        else
                        {
                           if ( raw->num_gains >= 2 )
                              put_adcsum_differential(lgval,mlg,iobuf);
                           put_adcsum_differential(hgval,m,iobuf);
                        }
#ifdef XXDEBUG
mlg_tot += mlg;
mhg16_tot += m;
#endif
		     }
		     mlg = m = 0;
		     zbits = cflags = 0;
		     j = 0;
		  }
	       }
	       break;
#endif

#if (H_MAX_GAINS >= 2)
	    case 2: /* Also reduce width of high-gain channel if possible */
	       n = raw->num_pixels;
	       zbits = cflags = bflags = 0;
	       j = k = mlg = mhg16 = mhg8 = 0;
	       while ( n-- > 0 )
	       {
	          if ( raw->significant[k] )
		  {
#ifdef XXDEBUG
m_tot++;
#endif
		     zbits |= 1 << j;
		     if ( (int) raw->adc_sum[HI_GAIN][k] >= raw->threshold && 
                          raw->num_gains >= 2 )
		     {
		     	cflags |= (uint16_t)1 << j;
		     	lgval[mlg++] = raw->adc_sum[LO_GAIN][k];
			hgval[mhg16++] = raw->adc_sum[HI_GAIN][k];
		     }
		     else
		     {
			f8 = 0;
			if ( (v8 = (int) raw->adc_sum[HI_GAIN][k] - offset_hg8) >= 0 )
			{
		     	   v8 = (v8 + scale_hg8half) / scale_hg8;
			   if ( v8 < 255 )
			      f8 = 1;
			}
			if ( f8 )
			{
			   hgval8[mhg8++] = (uint8_t) v8;
			   bflags |= (uint16_t)1 << j;
			}
			else
			{
		     	   hgval[mhg16++] = raw->adc_sum[HI_GAIN][k]; /* Possible overflow */
			}
		     }
		  }
		  k++;
		  if ( ++j == 16 || n == 0 )
		  {
		     put_vector_of_uint16(&zbits,1,iobuf);
		     if ( zbits != 0 )
		     {
		     	put_vector_of_uint16(&cflags,1,iobuf);
			put_vector_of_uint16(&bflags,1,iobuf);
		     	// put_vector_of_uint16(lgval,mlg,iobuf);
			// put_vector_of_uint16(hgval,mhg16,iobuf);
                        if ( item_header.version <= 2 )
                        {
                           if ( raw->num_gains >= 2 )
                              put_adcsum_as_uint16(lgval,mlg,iobuf);
                           put_adcsum_as_uint16(hgval,mhg16,iobuf);
                        }
                        else
                        {
                           if ( raw->num_gains >= 2 )
                              put_adcsum_differential(lgval,mlg,iobuf);
                           put_adcsum_differential(hgval,mhg16,iobuf);
                        }
			put_vector_of_uint8(hgval8,mhg8,iobuf);
#ifdef XXDEBUG
printf("#+# z: %04x\n",zbits);
printf("#+# c: %04x\n",cflags);
printf("#+# b: %04x\n",bflags);
printf("#++ %d %d %d\n", mlg, mhg16, mhg8);
mlg_tot += mlg;
mhg16_tot += mhg16;
mhg8_tot += mhg8;
#endif
		     }
		     mlg = mhg8 = mhg16 = 0;
		     zbits = cflags = bflags = 0;
		     j = 0;
		  }
	       }
	       break;
#endif
	    default:
	       assert(0);
	 }
      	 break;

      /* -------------- Zero suppression mode 2 --------------- */
      case 2: /* List of not zero-suppressed pixels */
      	 switch ( data_red_mode )
	 {
      	    uint32_t adc_sum_l[H_MAX_GAINS][H_MAX_PIX];
	    uint8_t adc_hg8[H_MAX_PIX];
      	    int adc_list_l[H_MAX_PIX];

	    case 0: /* No data reduction; copy ADC sums to contiguous array(s) */
	       for ( j=0; j<raw->list_size; j++ )
	       {
	          k = raw->adc_list[j];
		  adc_sum_l[HI_GAIN][j] = raw->adc_sum[HI_GAIN][k];
#if (H_MAX_GAINS >= 2)
                  /* Always copying probably faster than checking if raw->num_gains > 1 */
		  adc_sum_l[LO_GAIN][j] = raw->adc_sum[LO_GAIN][k];
#endif
	       }
               /* Same list applies to both HG and LG, if there is any LG */
               if ( item_header.version >= 4 )
               {
                  put_count(raw->list_size,iobuf);
	          put_vector_of_int_scount(raw->adc_list,raw->list_size,iobuf);
               }
               else
               {
	          put_short(raw->list_size,iobuf); // FIXME: fails with >= 32768 pixels
	          put_vector_of_int(raw->adc_list,raw->list_size,iobuf); // FIXME: fails with >= 32768 pixels
               }
               if ( item_header.version <= 2 )
               {
#if (H_MAX_GAINS >= 2)
                  if ( raw->num_gains >= 2 )
                     put_adcsum_as_uint16(adc_sum_l[LO_GAIN],raw->list_size,iobuf);
#endif
                  put_adcsum_as_uint16(adc_sum_l[HI_GAIN],raw->list_size,iobuf);
               }
               else
               {
#if (H_MAX_GAINS >= 2)
                  if ( raw->num_gains >= 2 )
                     put_adcsum_differential(adc_sum_l[LO_GAIN],raw->list_size,iobuf);
#endif
                  put_adcsum_differential(adc_sum_l[HI_GAIN],raw->list_size,iobuf);
               }
#ifdef XXDEBUG
mlg_tot += raw->list_size;
mhg16_tot += raw->list_size;
m_tot += raw->list_size;
#endif
	       break;
	    case 1: /* Skip low low-gain channels (for two gains) */
	       mlg = 0;
      	       for ( j=0; j<raw->list_size; j++ )
	       {
	          k = raw->adc_list[j];
#if ( H_MAX_GAINS >= 2 )
	          if ( /* (int) raw->adc_sum[HI_GAIN][k] >= raw->threshold && */
                        (raw->adc_known[LO_GAIN][k] & 0x01) &&
                        raw->num_gains >= 2 )
		  {
		     adc_list_l[mlg] = k;
		     adc_sum_l[LO_GAIN][mlg++] = raw->adc_sum[LO_GAIN][k];
		  }
		  else
#endif
                  {
                     /* Mark LG-suppressed pixels in pixel list by bit 13 (old) or 21 (new) */
                     if ( item_header.version >= 4 )
		        adc_list_l[j] = raw->adc_list[j] | 0x200000; /* suppressed (note: #pixels < 2097152) */
                     else
		        adc_list_l[j] = raw->adc_list[j] | 0x2000; /* suppressed (note: #pixels < 8192) */
                  }
		  adc_sum_l[HI_GAIN][j] = raw->adc_sum[HI_GAIN][k];
	       }
               /* We still save only one list, but the one with markup bits. */
               if ( item_header.version >= 4 )
               {
                  put_count(raw->list_size,iobuf);
	          put_vector_of_int_scount(adc_list_l,raw->list_size,iobuf);
               }
               else
               {
	          put_short(raw->list_size,iobuf); // FIXME: fails with >= 32768 pixels
	          put_vector_of_int(adc_list_l,raw->list_size,iobuf); // FIXME: fails with >= 32768 pixels
               }
               if ( item_header.version <= 2 )
               {
                  if ( raw->num_gains >= 2 )
	             put_adcsum_as_uint16(adc_sum_l[LO_GAIN],mlg,iobuf);
	          put_adcsum_as_uint16(adc_sum_l[HI_GAIN],raw->list_size,iobuf);	  
               }
               else
               {
                  if ( raw->num_gains >= 2 )
	             put_adcsum_differential(adc_sum_l[LO_GAIN],mlg,iobuf);
	          put_adcsum_differential(adc_sum_l[HI_GAIN],raw->list_size,iobuf);	  
               }
#ifdef XXDEBUG
mlg_tot += mlg;
mhg16_tot += raw->list_size;
m_tot += raw->list_size;
#endif
	       break;
	    case 2: /* Also reduce width of high-gain channel if possible */
	       /* although in this mode that is a rather marginal gain. */
	       mlg = mhg16 = mhg8 = 0;
      	       for ( j=0; j<raw->list_size; j++ )
	       {
	          k = raw->adc_list[j];
#if ( H_MAX_GAINS >= 2 )
	          if ( (int) raw->adc_sum[HI_GAIN][k] >= raw->threshold &&
                        raw->num_gains >= 2 )
		  {
                     /* Big signal: preserve full quality LG and HG signals */
		     adc_list_l[j] = raw->adc_list[j];
		     adc_sum_l[LO_GAIN][mlg++] = raw->adc_sum[LO_GAIN][k];
		     adc_sum_l[HI_GAIN][mhg16++] = raw->adc_sum[HI_GAIN][k];
		  }
		  else
#endif
		  {
		     f8 = 0;
		     if ( (v8 = (int) raw->adc_sum[HI_GAIN][k] - offset_hg8) >= 0 )
		     {
		     	v8 = (v8 + scale_hg8half) / scale_hg8;
			if ( v8 < 255 )
			   f8 = 1;
		     }
		     if ( f8 ) /* Reduced signal fits into 8 bits */
		     {
                        if ( item_header.version >= 4 )
		     	   adc_list_l[j] = raw->adc_list[j] | 0x600000;
                        else
		     	   adc_list_l[j] = raw->adc_list[j] | 0x6000; /* suppressed (note: #pixels < 8192) */
			adc_hg8[mhg8++] = (uint8_t) v8;
		     }
		     else /* We need more than 8 bits anyway, so keep original signal */
		     {
                        if ( item_header.version >= 4 )
		     	   adc_list_l[j] = raw->adc_list[j] | 0x200000;
                        else
		     	   adc_list_l[j] = raw->adc_list[j] | 0x2000; /* suppressed (note: #pixels < 8192) */
		     	adc_sum_l[HI_GAIN][mhg16++] = raw->adc_sum[HI_GAIN][k];
		     }
		  }
	       }
               /* Again write only one list, with two possible markup bits */
               if ( item_header.version >= 4 )
               {
                  put_count(raw->list_size,iobuf);
	          put_vector_of_int_scount(adc_list_l,raw->list_size,iobuf);
               }
               else
               {
	          put_short(raw->list_size,iobuf); // FIXME: fails with >= 32768 pixels
	          put_vector_of_int(adc_list_l,raw->list_size,iobuf); // FIXME: fails with >= 32768 pixels
               }
               if ( item_header.version <= 2 )
               {
                  if ( raw->num_gains >= 2 )
	             put_adcsum_as_uint16(adc_sum_l[LO_GAIN],mlg,iobuf);
	          put_adcsum_as_uint16(adc_sum_l[HI_GAIN],mhg16,iobuf);
               }
               else
               {
                  if ( raw->num_gains >= 2 )
	             put_adcsum_differential(adc_sum_l[LO_GAIN],mlg,iobuf);
	          put_adcsum_differential(adc_sum_l[HI_GAIN],mhg16,iobuf);
               }
               if ( mhg8 > 0 )
	          put_vector_of_uint8(adc_hg8,mhg8,iobuf);
#ifdef XXDEBUG
mlg_tot += mlg;
mhg16_tot += mhg16;
mhg8_tot += mhg8;
m_tot += raw->list_size;
#endif
	       break;
	    default:
	       assert(0);
	 }
      	 break;
      // case 3: /* Bit pattern run-length encoded */
         /* Not implemented */
      default:
	 assert(0);
   }
   
#ifdef XXDEBUG
printf("#+# %d %d %d (%d)\n", mlg_tot, mhg16_tot, mhg8_tot, m_tot);
#endif

   return put_item_end(iobuf,&item_header);
}

/* -------------------- read_hess_teladc_sums ----------------- */
/**
 *  Write ADC sum data for one camera in eventio format.
*/
int read_hess_teladc_sums (IO_BUFFER *iobuf, AdcData *raw)
{
   IO_ITEM_HEADER item_header;
   uint32_t flags;
   uint16_t offset_hg8 = 0, scale_hg8 = 1;
   uint16_t cflags, bflags, zbits;
   uint32_t lgval[16], hgval[16];
   uint8_t hgval8[16];
   int mlg, mhg16, mhg8, i, j, k, m, n;
   int rc;
#ifdef XXDEBUG
   int mlg_tot = 0, mhg16_tot = 0, mhg8_tot = 0, m_tot = 0;
#endif

   if ( iobuf == (IO_BUFFER *) NULL || raw == NULL )
      return -1;

   raw->known = 0;
   raw->num_pixels = 0;
   item_header.type = IO_TYPE_HESS_TELADCSUM;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 4 )
   {
      fprintf(stderr,"Unsupported ADC sums version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   /* Lots of small data was packed into the ID */
   flags = (uint32_t) item_header.ident;
   raw->zero_sup_mode = flags & 0x1f;
   raw->data_red_mode = (flags >> 5) & 0x1f;

   if ( item_header.version >= 4 && raw->data_red_mode == 2 )
   {
      raw->threshold = get_scount32(iobuf);
      raw->offset_hg8 = get_scount32(iobuf);
      raw->scale_hg8 = get_scount32(iobuf);
   }

   raw->list_known = (flags >> 10) & 0x01;
   if ( item_header.version == 0 )
   {
      raw->tel_id = (flags >> 25) & 0x1f; // High-order bits may be missing.
      raw->num_pixels = (flags >> 12) & 0x07ff;
      raw->num_gains = (flags >> 23) & 0x03;
   }
   else if ( item_header.version == 1 )
   {
      raw->tel_id = (flags >> 25) & 0x1f; // High-order bits may be missing.
      raw->num_pixels = (flags >> 12) & 0x0fff;
      raw->num_gains = (((flags >> 24) & 0x01) ? 2 : 1);
   }
   else
   {
      raw->tel_id = (flags >> 12) & 0xffff; // High-order bits may be missing.
      raw->num_pixels = get_long(iobuf);
      raw->num_gains = get_short(iobuf);
   }

   raw->num_samples = 0; // We have sums and not samples.

   if ( raw->num_pixels > H_MAX_PIX ||
        raw->num_gains > H_MAX_GAINS ||
/* (is this fixed ????)
	(raw->num_gains != 2 &&
	 (raw->zero_sup_mode != 0 || raw->data_red_mode != 0)) ||
*/
        (raw->num_pixels >= 32768 && raw->zero_sup_mode > 1) ||
        raw->zero_sup_mode > 2 ||
	raw->data_red_mode > 2 )
   {
      Warning("Invalid raw data block is skipped (limits exceeded or bad mode).");
      fprintf(stderr,"Num_pixels=%d, num_gains=%d, zero_sup=%d, data_red=%d\n",
         raw->num_pixels, raw->num_gains, raw->zero_sup_mode, raw->data_red_mode);
      get_item_end(iobuf,&item_header);
      raw->num_pixels = 0;
      return -1;
   }
   
   if ( raw->data_red_mode == 2 )
   {
      raw->offset_hg8 = offset_hg8 = get_short(iobuf);
      raw->scale_hg8 = scale_hg8 = get_short(iobuf);
      if ( scale_hg8 <= 0 ) 
      	 scale_hg8 = 1;
   }

   /* Without zero-suppression and data-reduction, every channel is known */
   /* but if either is z.s. or d.r. is on, a channel is only known if */
   /* marked as such in the data. */
   if ( raw->zero_sup_mode == 0 && raw->data_red_mode == 0 )
      k = 1;
   else
      k = 0;

   if ( k != 0 )
   {
      /* Initialize values one by one */
      for ( j=0; j<raw->num_pixels; j++ )
         raw->significant[j] = k;
      for (i=0; i<raw->num_gains; i++)
      {
         for ( j=0; j<raw->num_pixels; j++ )
         {
	    raw->adc_known[i][j] = k;
	    /* raw->adc_sum[i][j] = 0; now done with memset below */
         }
      }
   }
   else
   {
      /* Memset should be faster for setting all to zero */
      memset(raw->significant,0,(size_t)raw->num_pixels*sizeof(raw->significant[0]));
      for (i=0; i<raw->num_gains; i++)
         memset(raw->adc_known[i],0,(size_t)raw->num_pixels*sizeof(raw->adc_known[0][0]));
   }
   for (i=0; i<raw->num_gains; i++)
      memset(raw->adc_sum[i],0,(size_t)raw->num_pixels*sizeof(raw->adc_sum[0][0]));

#ifdef XXDEBUG
printf("### z = %d, d = %d\n", raw->zero_sup_mode, raw->data_red_mode);
#endif

   switch ( raw->zero_sup_mode )
   {
      /* -------------- Zero suppression mode 0 --------------- */
      case 0: /* No zero suppression */
#ifdef XXDEBUG
m_tot = raw->num_pixels;
#endif
      	 switch ( raw->data_red_mode )
	 {
	    case 0: /* No data reduction */
	       /* Note: in this mode ADC sums are stored in the internal order, */
	       /* no matter how many different gains there are per PMT. */
	       /* In all other modes, the order is fixed (lg/hg16/hg8) and limited */
	       /* to two different gains per PMT. */
	       for (i=0; i<raw->num_gains; i++)
               {
      	          // get_vector_of_uint16(raw->adc_sum[i],raw->num_pixels,iobuf);
                  if ( item_header.version < 3 )
      	             get_adcsum_as_uint16(raw->adc_sum[i],raw->num_pixels,iobuf);
                  else
#ifdef OLD_CODE
                     get_adcsum_differential(raw->adc_sum[i],raw->num_pixels,iobuf);
#else
      	             get_vector_of_uint32_scount_differential(raw->adc_sum[i],raw->num_pixels,iobuf);
#endif
               }
	       break;
#if (H_MAX_GAINS >= 2 )
	    case 1: /* Low low-gain channels were skipped (for two gains) */
	       k = 0;
	       while ( k < raw->num_pixels )
	       {
	          get_vector_of_uint16(&cflags,1,iobuf);
		  mlg = 0;
		  if ( k + 16 <= raw->num_pixels )
		     n = 16;
		  else
		     n = raw->num_pixels - k;
		  for ( j=0; j<n; j++ )
		     if ( (cflags & (1<<j)) )
		     	mlg++;
		  // get_vector_of_uint16(lgval,mlg,iobuf);
		  // get_vector_of_uint16(&raw->adc_sum[HI_GAIN][k],n,iobuf);
                  if ( item_header.version < 3 )
                  {
                     if ( raw->num_gains >= 2 )
		        get_adcsum_as_uint16(lgval,mlg,iobuf);
		     get_adcsum_as_uint16(&raw->adc_sum[HI_GAIN][k],n,iobuf);
                  }
                  else
                  {
#ifdef OLD_CODE
                     if ( raw->num_gains >= 2 )
		        get_adcsum_differential(lgval,mlg,iobuf);
		     get_adcsum_differential(&raw->adc_sum[HI_GAIN][k],n,iobuf);
#else
                     if ( raw->num_gains >= 2 )
		        get_vector_of_uint32_scount_differential(lgval,mlg,iobuf);
		     get_vector_of_uint32_scount_differential(&raw->adc_sum[HI_GAIN][k],n,iobuf);
#endif
                  }
#ifdef XXDEBUG
mlg_tot += mlg;
mhg16_tot += n;
#endif
		  mlg = 0;
		  for ( j=0; j<n; j++ )
		  {
		     if ( (cflags & (1<<j)) )
		     {
		        raw->adc_sum[LO_GAIN][k+j] = lgval[mlg++];
			raw->adc_known[LO_GAIN][k+j] = 1;
		     }
		     else
		     {
		     	raw->adc_sum[LO_GAIN][k+j] = 0;
			raw->adc_known[LO_GAIN][k+j] = 0;
		     }
		     raw->adc_known[HI_GAIN][k+j] = 1;
		     raw->significant[k+j] = 1;
		  }
	          k += n;
	       }
	       break;
 	    case 2: /* Width of high-gain channel can be reduced */
	       k = 0;
	       while ( k < raw->num_pixels )
	       {
	          get_vector_of_uint16(&cflags,1,iobuf);
	          get_vector_of_uint16(&bflags,1,iobuf);
		  mlg = mhg16 = mhg8 = 0;
		  if ( k + 16 <= raw->num_pixels )
		     n = 16;
		  else
		     n = raw->num_pixels - k;
		  for ( j=0; j<n; j++ )
		  {
		     if ( (cflags & (1<<j)) )
		     {
		     	mlg++;
			mhg16++;
		     }
		     else if ( (bflags & (1<<j)) )
		     	mhg8++;
		     else
		     	mhg16++;
		  }
		  // get_vector_of_uint16(lgval,mlg,iobuf);
		  // get_vector_of_uint16(hgval,mhg16,iobuf);
                  if ( item_header.version < 3 )
                  {
                     if ( raw->num_gains >= 2 )
		        get_adcsum_as_uint16(lgval,mlg,iobuf);
		     get_adcsum_as_uint16(hgval,mhg16,iobuf);
                  }
                  else
                  {
#ifdef OLD_CODE
                     if ( raw->num_gains >= 2 )
		        get_adcsum_differential(lgval,mlg,iobuf);
		     get_adcsum_differential(hgval,mhg16,iobuf);
#else
                     if ( raw->num_gains >= 2 )
		        get_vector_of_uint32_scount_differential(lgval,mlg,iobuf);
		     get_vector_of_uint32_scount_differential(hgval,mhg16,iobuf);
#endif
                  }
		  get_vector_of_uint8(hgval8,mhg8,iobuf);
#ifdef XXDEBUG
mlg_tot += mlg;
mhg16_tot += mhg16;
mhg8_tot += mhg8;
#endif
		  mlg = mhg8 = mhg16 = 0;
		  for ( j=0; j<n; j++ )
		  {
		     if ( (cflags & (1<<j)) )
		     {
		        raw->adc_sum[LO_GAIN][k+j] = lgval[mlg++];
			raw->adc_known[LO_GAIN][k+j] = 1;
		        raw->adc_sum[HI_GAIN][k+j] = hgval[mhg16++];
		     }
		     else
		     {
			if ( (bflags & (1<<j)) )
			   raw->adc_sum[HI_GAIN][k+j] = 
			      hgval8[mhg8++] * scale_hg8 + offset_hg8;
		        else
			   raw->adc_sum[HI_GAIN][k+j] = hgval[mhg16++];
		     }
		     raw->adc_known[HI_GAIN][k+j] = 1;
		     raw->significant[k+j] = 1;
		  }
		  k += n;
	       }
	       break;
#endif
	    default:
	       assert(0);
	 }
	 break;

      /* -------------- Zero suppression mode 1 --------------- */
      case 1: /* Bit pattern indicates zero suppression */
      	 switch ( raw->data_red_mode )
	 {
	    case 0: /* No data reduction */
	    case 1: /* Low low-gain channels were skipped (for two gains) */
 	    case 2: /* Width of high-gain channel can be reduced */
      	       k = 0;
	       while ( k < raw->num_pixels )
	       {
		  if ( k + 16 <= raw->num_pixels )
		     n = 16;
		  else
		     n = raw->num_pixels - k;
	          get_vector_of_uint16(&zbits,1,iobuf);
#ifdef XXDEBUG
printf("#+# z: %04x\n",zbits);
#endif
		  m = mlg = mhg16 = mhg8 = 0;
		  cflags = bflags = 0;
	          if ( zbits > 0 )
		  {
		     for ( j=0; j<n; j++ )
		     	if ( (zbits & (1<<j)) )
			   m++;

		     if ( raw->data_red_mode >= 1 )
		     {
		     	get_vector_of_uint16(&cflags,1,iobuf);
#ifdef XXDEBUG
printf("#+# c: %04x\n",cflags);
#endif
			if ( raw->data_red_mode == 2 )
      	             	{
		           get_vector_of_uint16(&bflags,1,iobuf);
#ifdef XXDEBUG
printf("#+# b: %04x\n",bflags);
#endif
      	             	}
			for ( j=0; j<n; j++ )
			{
			   if ( !(zbits & (1<<j)) )
			      continue;
		     	   if ( (cflags & (1<<j)) )
			   {
			      mlg++;
			      mhg16++;
			   }
			   else
			   {
			      if ( raw->data_red_mode == 2 )
			      {
		     		 if ( (bflags & (1<<j)) )
      	             		    mhg8++;
				 else
				    mhg16++;
			      }
			      else
			      	 mhg16++;
			   }
			}
		     }
		     else
		     	mlg = mhg16 = m;

		     if ( m > 0 )
		     {
		     	// get_vector_of_uint16(lgval,mlg,iobuf);
		     	// get_vector_of_uint16(hgval,mhg16,iobuf);
                        if ( item_header.version < 3 )
                        {
                           if ( raw->num_gains >= 2)
		     	      get_adcsum_as_uint16(lgval,mlg,iobuf);
		     	   get_adcsum_as_uint16(hgval,mhg16,iobuf);
                        }
                        else
                        {
#ifdef OLD_CODE
                           if ( raw->num_gains >= 2)
		     	      get_adcsum_differential(lgval,mlg,iobuf);
		     	   get_adcsum_differential(hgval,mhg16,iobuf);
#else
                           if ( raw->num_gains >= 2)
		     	      get_vector_of_uint32_scount_differential(lgval,mlg,iobuf);
		     	   get_vector_of_uint32_scount_differential(hgval,mhg16,iobuf);
#endif
                        }
			if ( mhg8 > 0 )
		     	   get_vector_of_uint8(hgval8,mhg8,iobuf);
#ifdef XXDEBUG
printf("#++ %d %d %d (%d)\n", mlg, mhg16, mhg8, m);
mlg_tot += mlg;
mhg16_tot += mhg16;
mhg8_tot += mhg8;
#endif
			mlg = mhg16 = mhg8 = 0;
			for ( j=0; j<n; j++ )
			{
		     	   if ( (zbits & (1<<j)) )
			   {
#ifdef XXDEBUG
m_tot++;
#endif
			      raw->significant[k+j] = 1;
			      if ( raw->data_red_mode < 1 ||
			      	   (cflags & (1<<j)) )
			      {
#if ( H_MAX_GAINS >= 2 )
			      	 raw->adc_sum[LO_GAIN][k+j] = lgval[mlg++];
#endif
			      	 raw->adc_sum[HI_GAIN][k+j] = hgval[mhg16++];
#if ( H_MAX_GAINS >= 2 )
			      	 raw->adc_known[LO_GAIN][k+j] = 1;
#endif
			      	 raw->adc_known[HI_GAIN][k+j] = 1;
			      }
			      else 
			      {
#if ( H_MAX_GAINS >= 2 )
			      	 raw->adc_sum[LO_GAIN][k+j] = 0;
#endif
			      	 if ( raw->data_red_mode == 2 &&
			      	       (bflags & (1<<j)) )
			      	    raw->adc_sum[HI_GAIN][k+j] = 
				       hgval8[mhg8++] * scale_hg8 + offset_hg8;
				 else
			      	    raw->adc_sum[HI_GAIN][k+j] = hgval[mhg16++];
			      	 raw->adc_known[HI_GAIN][k+j] = 1;
			      }
			   }
			}
		     }
		  }
		  k += n;
	       }
	       break;
       
	    default:
	       assert(0);
	 }
	 break;

      /* -------------- Zero suppression mode 2 --------------- */
     case 2: /* List of not zero-suppressed pixels */
     {
      	 uint32_t adc_sum_l[H_MAX_GAINS][H_MAX_PIX];
	 uint8_t adc_hg8[H_MAX_PIX];
      	 int adc_list_l[H_MAX_PIX];
	 int without_lg[H_MAX_PIX], reduced_width[H_MAX_PIX];

      	 switch ( raw->data_red_mode )
	 {
	    case 0: /* No data reduction */
	    case 1: /* Low low-gain channels were skipped (for two gains) */
 	    case 2: /* Width of high-gain channel can be reduced */
               if ( item_header.version >= 4 )
               {
                  raw->list_size = get_count(iobuf);
	          get_vector_of_int_scount(adc_list_l,raw->list_size,iobuf);
               }
               else
               {
	          raw->list_size = get_short(iobuf);
	          get_vector_of_int(adc_list_l,raw->list_size,iobuf);
               }
	       mlg = mhg16 = mhg8 = 0;
      	       for ( j=0; j<raw->list_size; j++ )
	       {
                  if ( item_header.version >= 4 )
                  {
	             raw->adc_list[j] = k = adc_list_l[j] & 0x1fffff;
		     without_lg[j] = ((adc_list_l[j] & 0x200000) != 0);
		     reduced_width[j] = ((adc_list_l[j] & 0x400000) != 0);
                  }
                  else
                  {
	             raw->adc_list[j] = k = adc_list_l[j] & 0x1fff;
		     without_lg[j] = ((adc_list_l[j] & 0x2000) != 0);
		     reduced_width[j] = ((adc_list_l[j] & 0x4000) != 0);
                  }
		  if ( reduced_width[j] )
		     mhg8++;
#if ( H_MAX_GAINS >= 2 )
		  else if ( raw->num_gains<2 || without_lg[j] )
		     mhg16++;
		  else
		  {
		     mlg++;
		     mhg16++;
		  }
#else
                  else
                     mhg16++;
#endif
	       }

               if ( item_header.version < 2 )
               {
#if ( H_MAX_GAINS >= 2 )
                  if ( raw->num_gains >= 2 )
	             get_adcsum_as_uint16(adc_sum_l[LO_GAIN],mlg,iobuf);
#endif
	          get_adcsum_as_uint16(adc_sum_l[HI_GAIN],mhg16,iobuf);
               }
               else
               {
#if ( H_MAX_GAINS >= 2 )
                   if ( raw->num_gains >= 2 )
	             get_adcsum_differential(adc_sum_l[LO_GAIN],mlg,iobuf);
#endif
	          get_adcsum_differential(adc_sum_l[HI_GAIN],mhg16,iobuf);
               }
               if ( mhg8 > 0 )
	          get_vector_of_uint8(adc_hg8,mhg8,iobuf);
#ifdef XXDEBUG
printf("#++ %d %d %d\n", mlg, mhg16, mhg8);
m_tot += raw->list_size;
mlg_tot += mlg;
mhg16_tot += mhg16;
mhg8_tot += mhg8;
#endif
	       mlg = mhg16 = mhg8 = 0; /* Start from the beginning of each array */
      	       for ( j=0; j<raw->list_size; j++ )
	       {
	          k = raw->adc_list[j];
		  raw->significant[k] = 1;
		  if ( reduced_width[j] )
		     raw->adc_sum[HI_GAIN][k] = adc_hg8[mhg8++] * scale_hg8 + offset_hg8;
		  else
		     raw->adc_sum[HI_GAIN][k] = adc_sum_l[HI_GAIN][mhg16++];
		  raw->adc_known[HI_GAIN][k] = 1;
#if ( H_MAX_GAINS >= 2 )
                  if ( raw->num_gains <= 1 )
                     raw->adc_known[LO_GAIN][k] = 0;
		  else if ( without_lg[j] )
		  {
		     raw->adc_sum[LO_GAIN][k] = 0;
		     raw->adc_known[LO_GAIN][k] = 0;
		  }
		  else
		  {
		     raw->adc_sum[LO_GAIN][k] = adc_sum_l[LO_GAIN][mlg++];
		     raw->adc_known[LO_GAIN][k] = 1;
		  }
#endif
	       }
	       break;

	    default:
	       assert(0);
	 }
      }
	 break;
      
      default:
	 assert(0);
   }
   
#ifdef XXDEBUG
printf("#+# %d %d %d (%d)\n", mlg_tot, mhg16_tot, mhg8_tot, m_tot);
#endif

   raw->known = 1;

   return get_item_end(iobuf,&item_header);
}

/* -------------------- print_hess_teladc_sums ----------------- */
/**
 *  Print summed ADC data in eventio format.
*/

int print_hess_teladc_sums (IO_BUFFER *iobuf)
{
   IO_ITEM_HEADER item_header;
   uint32_t flags, zero_sup_mode, data_red_mode, list_known;
   uint32_t num_pixels, num_gains, tel_id;
   int threshold = 0, offset_hg8 = 0, scale_hg8 = 0;
   int rc;
   
   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;

   hs_check_env();
   
   item_header.type = IO_TYPE_HESS_TELADCSUM;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 4 )
   {
      fprintf(stderr,"Unsupported ADC samples version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   /* Lots of small data was packed into the ID */
   flags = (uint32_t) item_header.ident;
   zero_sup_mode = flags & 0x1f;
   data_red_mode = (flags >> 5) & 0x1f;
   list_known = (flags >> 10) & 0x01;

   if ( item_header.version >= 4 && data_red_mode == 2 )
   {
      threshold = get_scount32(iobuf);
      offset_hg8 = get_scount32(iobuf);
      scale_hg8 = get_scount32(iobuf);
   }

   if ( item_header.version == 0 )
   {
      tel_id = (flags >> 25) & 0x1f; // High-order bits may be missing.
      num_pixels = (flags >> 12) & 0x07ff;
      num_gains = (flags >> 23) & 0x03;
   }
   else if ( item_header.version == 1 )
   {
      tel_id = (flags >> 25) & 0x1f; // High-order bits may be missing.
      num_pixels = (flags >> 12) & 0x0fff;
      num_gains = (((flags >> 24) & 0x01) ? 2 : 1);
   }
   else
   {
      tel_id = (flags >> 12) & 0xffff; // High-order bits may be missing.
      num_pixels = get_long(iobuf);
      num_gains = get_short(iobuf);
   }
   if ( num_gains > H_MAX_GAINS )
   {
      printf("No. of gains per pixel in sum mode data exceeds limits.\n");
      get_item_end(iobuf,&item_header);
      return -1;
   }

   if ( item_header.version < 2 )
      printf("    Sum mode data version %d for telescope (modulo 32) %u:\n",item_header.version,tel_id);
   else
      printf("    Sum mode data version %d for telescope %u:\n",item_header.version,tel_id);
   printf("      With %u gains for %u pixels\n", num_gains, num_pixels);
   printf("      Zero suppression: %u, data reduction: %d, pixel list: %d\n",
      zero_sup_mode, data_red_mode, list_known);
   if ( data_red_mode == 2 )
      printf("      Threshold for reduction: %d, offset: %d, scale: %d\n", threshold, offset_hg8, scale_hg8);

   if ( hs_verbose )
   {
      size_t igain, ipix;
      if ( zero_sup_mode == 0 && data_red_mode == 0 )
      {
	 for (igain=0; igain<num_gains; igain++)
         {
            int prev_sum = 0, this_sum;
	    for (ipix=0; ipix<num_pixels; ipix++)
            {
               if ( item_header.version < 3 )
               {
                  if ( (int) ipix < hs_maxprt )
                     printf("        Pixel %zu, ch. %zu: %d\n", ipix, igain, get_short(iobuf));
                  else if ( (int) ipix == hs_maxprt )
                  {  printf("        ...\n"); (void) get_short(iobuf); }
                  else
                     (void) get_short(iobuf);
               }
               else
               {
                  this_sum = get_scount32(iobuf) + prev_sum;
                  prev_sum = this_sum;
                  if ( (int) ipix < hs_maxprt )
                     printf("        Pixel %zu, ch. %zu: %d\n", ipix, igain, this_sum);
                  else if ( (int) ipix == hs_maxprt )
                  {  printf("        ...\n"); }
               }
            }
         }
      }
      else
         printf("      No verbose printing available for ADC sum data in this mode.\n");
   }

   return get_item_end(iobuf,&item_header);
}

/* -------------------- write_hess_teladc_samples ----------------- */
/**
 *  @short Write sampled ADC data in eventio format.
 *
 *  In contrast to sum data, no data reduction is applied so far.
 *  It is assumed that sampled data would be taken only for
 *  hardware tests, where the full information has to be maintained.
 *  If large amounts of sampled data are taken, a suitable
 *  data reduction method should be inserted here.
*/  

int write_hess_teladc_samples (IO_BUFFER *iobuf, AdcData *raw)
{
   IO_ITEM_HEADER item_header;
   uint32_t flags;
   int ipix, igain, ilist;
   int zero_sup_mode = ((raw->zero_sup_mode & 0x20) >> 5); /* More bits reserved */
   int data_red_mode = ((raw->data_red_mode & 0x20) != 0 && zero_sup_mode != 0 ? 1 : 0); /* Only 0 and 1 supported, only together with zero-sup. */
   int pixel_list[H_MAX_PIX][2], list_size = 0;
#if ( H_MAX_GAINS >= 2 )
   int pixel_list_lg[H_MAX_PIX][2], list_size_lg = 0;
#endif

   if ( iobuf == (IO_BUFFER *) NULL || raw == NULL )
      return -1;

   if ( !raw->known )
      return 0;

   item_header.type = IO_TYPE_HESS_TELADCSAMP;  /* Data type */
   // item_header.version = 1;             /* Version 1 (revised) */

   // if ( raw->num_pixels > 4095 && item_header.version == 1 ) /* Strictly needed for large no. of pixels */
   //   item_header.version = 2;             /* Version 2 (revised again) */
   item_header.version = 3;                  /* Version 3 (starting with differential mode) */
   
   if ( data_red_mode > 0 )
      item_header.version = 4;               /* Start support for low-gain suppressed sample-mode data */

   if ( raw->num_pixels < 0 || 
        (raw->num_pixels > 4095 && item_header.version < 2) ||
	raw->num_gains < 1 || raw->num_gains > H_MAX_GAINS )
   {
      Warning("Unsupported sampled data mode");
      return -1;
   }

   /* Bit masks are commented out because range of values was checked */
   /* but left here to indicate range of manageable values. */
   if ( item_header.version < 2 )
     flags = ( (raw->num_pixels /* & 0x0fff */) << 12 ) |
             ( ((raw->num_gains==2) ? 1 : 0) << 24 ) |
             ( (raw->tel_id & 0x1f) << 25 );
   else
      flags = ( (raw->tel_id & 0xffff) << 12);
   if ( item_header.version < 3 ) /* Zero-suppression only implemented for differential mode */
      zero_sup_mode = 0; 
   flags |= (zero_sup_mode & 0x1f);
   if ( data_red_mode )
      flags |= 0x20;

   item_header.ident = flags;
   put_item_begin(iobuf,&item_header);

   if ( item_header.version >= 2 )
   {
      put_long(raw->num_pixels,iobuf);
      put_short(raw->num_gains,iobuf);
   }

   put_short(raw->num_samples,iobuf);

   if ( zero_sup_mode ) /* only with version 3 and up */
   {
      int sl=-1, s;
#if ( H_MAX_GAINS >= 2 )
      int slx=-1, sx;
      list_size_lg = 0;
#endif
      list_size = 0;

      for (ipix=0; ipix<raw->num_pixels; ipix++)
      {
         s = (raw->significant[ipix] & 0x20 ); /* Special bit for sample mode zero suppression ? */
         if ( s != 0 && s == sl && list_size > 0 )
            pixel_list[list_size-1][1] = ipix;
         else if ( s != 0 )
         {
            list_size++;
            pixel_list[list_size-1][1] = pixel_list[list_size-1][0] = ipix;
         }
         sl = s;
#if ( H_MAX_GAINS >= 2 )
         if ( data_red_mode && raw->num_gains > 1 )
         {
            sx = s;
            if ( sx != 0 && !(raw->adc_known[LO_GAIN][ipix] & 0x02) )
               sx = 0;
            if ( sx != 0 && sx == slx && list_size_lg > 0 )
               pixel_list_lg[list_size_lg-1][1] = ipix;
            else if ( sx != 0 )
            {
               list_size_lg++;
               pixel_list_lg[list_size_lg-1][1] = pixel_list_lg[list_size_lg-1][0] = ipix;
            }
            slx = sx;
         }
#endif
      }

      /* Write common (no data red.) or high-gain (with data red.) pixel list */
      put_scount32(list_size,iobuf);
      for ( ilist=0; ilist<list_size; ilist++ )
      {
         if ( pixel_list[ilist][0] == pixel_list[ilist][1] ) /* single pixel */
            put_scount(-pixel_list[ilist][0]-1,iobuf);
         else /* pixel range */
         {
            put_scount(pixel_list[ilist][0],iobuf);
            put_scount(pixel_list[ilist][1],iobuf);
         }
      }

#if ( H_MAX_GAINS >= 2 )
      /* Write low-gain pixel list if needed. */
      if ( data_red_mode && raw->num_gains > 1 )
      {
         put_scount32(list_size_lg,iobuf);
         for ( ilist=0; ilist<list_size_lg; ilist++ )
         {
            if ( pixel_list_lg[ilist][0] == pixel_list_lg[ilist][1] ) /* single pixel */
               put_scount(-pixel_list_lg[ilist][0]-1,iobuf);
            else /* pixel range */
            {
               put_scount(pixel_list_lg[ilist][0],iobuf);
               put_scount(pixel_list_lg[ilist][1],iobuf);
            }
         }
      }
#endif

      if ( raw->data_red_mode ) /* Data reduction mode (requires also zero suppression) enabled */
      {
         /* First write high-gain channel data for all significant pixels */
         /* (which is actually the other way around than for sum data, never mind). */
         for ( ilist=0; ilist<list_size; ilist++ )
            for ( ipix=pixel_list[ilist][0]; ipix<=pixel_list[ilist][1]; ipix++ )
               put_adcsample_differential(raw->adc_sample[HI_GAIN][ipix],raw->num_samples,iobuf);
         
#if ( H_MAX_GAINS >= 2 )
         if ( raw->num_gains > 1 )
         {
            /* If necessary write low-gain channel data for high-amplitude significant pixels */
            for ( ilist=0; ilist<list_size_lg; ilist++ )
               for ( ipix=pixel_list_lg[ilist][0]; ipix<=pixel_list_lg[ilist][1]; ipix++ )
                  put_adcsample_differential(raw->adc_sample[LO_GAIN][ipix],raw->num_samples,iobuf);
         }
#endif
      }
      else /* No low-gain data reduction; same list applies for high-gain and low-gain, if there is any. */
      {
         for (igain=0; igain<raw->num_gains; igain++) /* Also here first HG (0), then LG (1) if there is any */
            for ( ilist=0; ilist<list_size; ilist++ )
               for ( ipix=pixel_list[ilist][0]; ipix<=pixel_list[ilist][1]; ipix++ )
                  put_adcsample_differential(raw->adc_sample[igain][ipix],raw->num_samples,iobuf);
      }
   }
   else if ( item_header.version < 3 ) /* No zero-sup (and no data red.), old version) */
   {
      for (igain=0; igain<raw->num_gains; igain++) /* First HG (0), then LG (1) if there is any */
         for (ipix=0; ipix<raw->num_pixels; ipix++)
      	    put_vector_of_uint16(raw->adc_sample[igain][ipix],raw->num_samples,iobuf);
   }
   else /* No zero-sup (and no data red.), newer version) */
   {
      for (igain=0; igain<raw->num_gains; igain++) /* First HG (0), then LG (1) if there is any */
         for (ipix=0; ipix<raw->num_pixels; ipix++)
      	    put_adcsample_differential(raw->adc_sample[igain][ipix],raw->num_samples,iobuf);
   }

   return put_item_end(iobuf,&item_header);
}

/* -------------------- read_hess_teladc_samples ----------------- */
/**
 *  Read sampled ADC data in eventio format.
*/

int read_hess_teladc_samples (IO_BUFFER *iobuf, AdcData *raw, int what)
{
   IO_ITEM_HEADER item_header;
   uint32_t flags;
   int ipix, igain, isamp;
   int rc;
   uint32_t sum;
   int zero_sup_mode=0, data_red_mode=0, list_known = 0;

   if ( iobuf == (IO_BUFFER *) NULL || raw == NULL )
      return -1;

   // raw->known = 0; /* We may have read the ADC sums before */

   raw->num_pixels = 0;
   item_header.type = IO_TYPE_HESS_TELADCSAMP;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 3 )
   {
      fprintf(stderr,"Unsupported ADC samples version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   /* Lots of small data was packed into the ID */
   flags = (uint32_t) item_header.ident;
   zero_sup_mode = flags & 0x1f;
   data_red_mode = (flags >> 5) & 0x1f;
   list_known = (flags >> 10) & 0x01; /* Bit 10 was never set, thus zero */
   if ( (zero_sup_mode != 0 && item_header.version < 3) || 
        data_red_mode != 0 ||
	list_known )
   {
      Warning("Unsupported ADC sample format\n");
      get_item_end(iobuf,&item_header);
      return -1;
   }
   /* Sample-mode zero suppression and data reduction separated from sum data */
   raw->zero_sup_mode |= zero_sup_mode << 5;
   raw->data_red_mode |= data_red_mode << 5;
   /* If there was a list for sum data, it gets lost now - but do we want that? */
   /* The problem is there is only place for one list but zero suppression for
      sum data and samples may well be different. Without known list, the
      application processing the data should loop over all pixels and test for
      significant bits and adc_known bits. With known list it only needs to 
      loop over pixels included in the list but still test significant and adc_known. */
   /* As long as pixels with samples are a subset of pixels with sums,
      we could preserve the sum data pixel list. */
   raw->list_known = 0; /* Since list_known here is always zero. */
   if ( item_header.version == 0 )
   {
      raw->tel_id = (flags >> 25) & 0x1f;
      raw->num_pixels = (flags >> 12) & 0x07ff;
      raw->num_gains = (flags >> 23) & 0x03;
   }
   else if ( item_header.version == 1 )
   {
      raw->tel_id = (flags >> 25) & 0x1f;
      raw->num_pixels = (flags >> 12) & 0x0fff;
      raw->num_gains = (((flags >> 24) & 0x01) ? 2 : 1);
   }
   else
   {
      raw->tel_id = (flags >> 12) & 0xffff;
      raw->num_pixels = get_long(iobuf);
      raw->num_gains = get_short(iobuf);
   }

   raw->num_samples = get_short(iobuf);

   if ( raw->num_pixels > H_MAX_PIX ||
        raw->num_gains > H_MAX_GAINS ||
	raw->num_samples > H_MAX_SLICES )
   {
      Warning("Invalid raw data block is skipped (limits exceeded).");
      fprintf(stderr,"Num_pixels=%d, num_gains=%d, num_samples=%d\n",
         raw->num_pixels, raw->num_gains, raw->num_samples);
      get_item_end(iobuf,&item_header);
      raw->num_pixels = 0;
      return -1;
   }

   if ( zero_sup_mode )
   {
      int ilist, ipix1, ipix2;
      int pixel_list[H_MAX_PIX][2], list_size = 0;
#if ( H_MAX_GAINS >= 2 )
      int pixel_list_lg[H_MAX_PIX][2], list_size_lg = 0;
#endif
      for (ipix=0; ipix<raw->num_pixels; ipix++)
      {
         raw->significant[ipix] &= ~0xe0; /* Clear sample mode significance bits. */
         raw->adc_known[0][ipix] &= 0x01; /* Same for adc_known sample-mode bits; */
#if ( H_MAX_GAINS >= 2 )
         raw->adc_known[1][ipix] &= 0x01; /* bit 0 is for sum, bit 1 for samples. */
#endif
      }

      /* Common or high-gain pixel list */
      list_size = get_scount32(iobuf);
      if ( list_size > H_MAX_PIX )
      {
         Warning("Pixel list too large in zero-suppressed sample-mode data.\n");
         get_item_end(iobuf,&item_header);
         return -1;
      }

      for ( ilist=0; ilist<list_size; ilist++ )
      {
         ipix1 = get_scount(iobuf);
         if ( ipix1 < 0 ) /* Single pixel */
         {
            ipix2 = -ipix1 - 1;
            ipix1 = ipix2;
         }
         else /* pixel range */
            ipix2 = get_scount(iobuf);
         pixel_list[ilist][0] = ipix1;
         pixel_list[ilist][1] = ipix2;
      }

#if ( H_MAX_GAINS >= 2 )
      /* Read low-gain pixel list if needed. */
      if ( data_red_mode && raw->num_gains > 1 )
      {
         list_size_lg = get_scount32(iobuf);
         if ( list_size_lg > H_MAX_PIX )
         {
            Warning("Pixel list too large in low-gain zero-suppressed sample-mode data.\n");
            get_item_end(iobuf,&item_header);
            return -1;
         }
         for ( ilist=0; ilist<list_size_lg; ilist++ )
         {
            ipix1 = get_scount(iobuf);
            if ( ipix1 < 0 ) /* Single pixel */
            {
               ipix2 = -ipix1 - 1;
               ipix1 = ipix2;
            }
            else /* pixel range */
               ipix2 = get_scount(iobuf);
            pixel_list_lg[ilist][0] = ipix1;
            pixel_list_lg[ilist][1] = ipix2;
         }
         for ( ilist=0; ilist<list_size; ilist++ )
         {
            for ( ipix=pixel_list[ilist][0]; ipix<=pixel_list[ilist][1]; ipix++ )
            {
               get_vector_of_uint16_scount_differential(raw->adc_sample[HI_GAIN][ipix],raw->num_samples,iobuf);
               raw->significant[ipix] |= 0x20;
               raw->adc_known[HI_GAIN][ipix] |= 2;
            }
         }
         for ( ilist=0; ilist<list_size_lg; ilist++ )
            for ( ipix=pixel_list_lg[ilist][0]; ipix<=pixel_list_lg[ilist][1]; ipix++ )
            {
               get_vector_of_uint16_scount_differential(raw->adc_sample[LO_GAIN][ipix],raw->num_samples,iobuf);
               raw->adc_known[LO_GAIN][ipix] |= 2;
            }
         if ( (what & RAWSUM_FLAG) )
         {
         }
      }
      else
#endif
      {
       for (igain=0; igain<raw->num_gains; igain++)
       {
         for ( ilist=0; ilist<list_size; ilist++ )
         {
            for ( ipix=pixel_list[ilist][0]; ipix<=pixel_list[ilist][1]; ipix++ )
            {
#ifdef OLD_CODE
               get_adcsample_differential(raw->adc_sample[igain][ipix],raw->num_samples,iobuf);
#else
               get_vector_of_uint16_scount_differential(raw->adc_sample[igain][ipix],raw->num_samples,iobuf);
#endif
               raw->significant[ipix] |= 0x20;
               
               /* Should the sampled data also be summed up here? There might be sum data preceding this sample mode data! */
               if ( !raw->adc_known[igain][ipix] )
               {
                  if ( (what & RAWSUM_FLAG) )
                  {
      	             /* Sum up all samples */
	             sum = 0;
	             for (isamp=0; isamp<raw->num_samples; isamp++)
	                sum += raw->adc_sample[igain][ipix][isamp];
#if 1
                     raw->adc_sum[igain][ipix] = sum; /* No overflow of 32-bit unsigned assumed */
#else                /* Back in the days when adc_sum was a 16-bit unsigned int */
                     if ( sum <= 65535 )
	                raw->adc_sum[igain][ipix] = (uint16_t) sum;
	             else
	                raw->adc_sum[igain][ipix] = (uint16_t) 65535;
#endif
	             raw->adc_known[igain][ipix] = 1;
                  }
                  else
                     raw->adc_sum[igain][ipix] = 0;
               }
               raw->adc_known[igain][ipix] |= 2;
            }
         }
      }
    }
   }
   else /* No (sample data) zero suppression, no data reduction, no pixel lists. */
   {
      for (igain=0; igain<raw->num_gains; igain++)
      {
         for (ipix=0; ipix<raw->num_pixels; ipix++)
         {
            if ( item_header.version < 3 )
      	       get_vector_of_uint16(raw->adc_sample[igain][ipix],raw->num_samples,iobuf);
            else
#ifdef OLD_CODE
               get_adcsample_differential(raw->adc_sample[igain][ipix],raw->num_samples,iobuf);
#else
               get_vector_of_uint16_scount_differential(raw->adc_sample[igain][ipix],raw->num_samples,iobuf);
#endif

            /* Should the sampled data be summed up here? If there is preceding sum data, we keep that. */
            /* Note that having non-zero-suppressed samples after sum data is normally used. */
            /* In realistic data, there will be no sum known at this point. */
            if ( !raw->adc_known[igain][ipix] )
            {
               if ( (what & RAWSUM_FLAG) )
               {
      	          /* Sum up all samples */
	          sum = 0;
	          for (isamp=0; isamp<raw->num_samples; isamp++)
	             sum += raw->adc_sample[igain][ipix][isamp];
#if 1
                  raw->adc_sum[igain][ipix] = sum; /* No overflow of 32-bit unsigned assumed */
#else             /* Back in the days when adc_sum was a 16-bit unsigned int */
                  if ( sum <= 65535 )
	             raw->adc_sum[igain][ipix] = (uint16_t) sum;
	          else
	             raw->adc_sum[igain][ipix] = (uint16_t) 65535;
#endif
               }
               else
                  raw->adc_sum[igain][ipix] = 0;
	       raw->adc_known[igain][ipix] = 1;
            }
            raw->adc_known[igain][ipix] |= 2;
         }
      }
      for (ipix=0; ipix<raw->num_pixels; ipix++)
         raw->significant[ipix] = 1;
   }

   raw->known |= 2;

   return get_item_end(iobuf,&item_header);
}

/* -------------------- print_hess_teladc_samples ----------------- */
/**
 *  Print sampled ADC data in eventio format.
*/

int print_hess_teladc_samples (IO_BUFFER *iobuf)
{
   IO_ITEM_HEADER item_header;
   uint32_t flags, zero_sup_mode, data_red_mode, list_known;
   uint32_t num_pixels, num_gains, num_samples, tel_id;
   int rc;

   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;

   hs_check_env();

   item_header.type = IO_TYPE_HESS_TELADCSAMP;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 4 )
   {
      fprintf(stderr,"Unsupported ADC samples version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   /* Lots of small data was packed into the ID */
   flags = (uint32_t) item_header.ident;
   zero_sup_mode = flags & 0x1f;
   data_red_mode = (flags >> 5) & 0x1f;
   list_known = (flags >> 10) & 0x01;
   if ( (zero_sup_mode != 0 && item_header.version < 3) || 
        data_red_mode != 0 ||
	list_known )
   {
      Warning("Unsupported ADC sample format\n");
      get_item_end(iobuf,&item_header);
      return -1;
   }

   if ( item_header.version == 0 )
   {
      tel_id = (flags >> 25) & 0x1f;
      num_pixels = (flags >> 12) & 0x07ff;
      num_gains = (flags >> 23) & 0x03;
   }
   else if ( item_header.version == 1 )
   {
      tel_id = (flags >> 25) & 0x1f;
      num_pixels = (flags >> 12) & 0x0fff;
      num_gains = (((flags >> 24) & 0x01) ? 2 : 1);
   }
   else
   {
      tel_id = (flags >> 12) & 0xffff;
      num_pixels = get_long(iobuf);
      num_gains = get_short(iobuf);
   }

   num_samples = get_short(iobuf);
   printf("    Sample mode data (version %d) for telescope%s %u:\n",
      item_header.version, (item_header.version<=1)?" (modulo 32)":"", tel_id);
   printf("      With %u samples, %u gains for %u pixels\n",
      num_samples, num_gains, num_pixels);
   printf("      Zero suppression: %u, data reduction: %d, pixel list: %d\n",
      zero_sup_mode, data_red_mode, list_known);

   if ( hs_verbose && num_samples <= H_MAX_SLICES )
   {
      size_t ipix, igain, isamp;
      uint16_t adc_sample[H_MAX_SLICES];

      if ( zero_sup_mode )
      {
         int ilist, ipix1, ipix2, kpix;
         int pixel_list[H_MAX_PIX][2], list_size = 0;
         list_size = get_scount32(iobuf);
         if ( list_size > H_MAX_PIX )
         {
            Warning("Pixel list too large in zero-suppressed sample-mode data.\n");
            get_item_end(iobuf,&item_header);
            return -1;
         }
         for ( ilist=0; ilist<list_size; ilist++ )
         {
            ipix1 = get_scount(iobuf);
            if ( ipix1 < 0 ) /* Single pixel */
            {
               ipix2 = -ipix1 - 1;
               ipix1 = ipix2;
            }
            else /* pixel range */
               ipix2 = get_scount(iobuf);
            pixel_list[ilist][0] = ipix1;
            pixel_list[ilist][1] = ipix2;
         }
         for (igain=0; igain<num_gains; igain++)
            for ( ilist=0, kpix=0; ilist<list_size; ilist++ )
               for ( ipix=pixel_list[ilist][0]; (int)ipix<=pixel_list[ilist][1]; ipix++ )
               {
#ifdef OLD_CODE
                  get_adcsample_differential(adc_sample,num_samples,iobuf);
#else
                  get_vector_of_uint16_scount_differential(adc_sample,num_samples,iobuf);
#endif
                  if ( kpix < hs_maxprt )
                  {
                     printf("        Pixel %zu, ch. %zu:",ipix,igain);
                     for ( isamp=0; isamp<num_samples; isamp++ )
                        printf(" %d", adc_sample[isamp]);
                     printf("\n");
                  }
                  else
                  {
                     if ( kpix == hs_maxprt )
                        printf("        ...\n");
                  }
                  kpix++;
               }
      }
      else
      {
         for (igain=0; igain<num_gains; igain++)
            for (ipix=0; ipix<num_pixels; ipix++)
            {
               if ( item_header.version < 3 )
      	          get_vector_of_uint16(adc_sample,num_samples,iobuf);
               else
#ifdef OLD_CODE
                  get_adcsample_differential(adc_sample,num_samples,iobuf);
#else
                  get_vector_of_uint16_scount_differential(adc_sample,num_samples,iobuf);
#endif

               if ( (int) ipix < hs_maxprt )
               {
                  printf("        Pixel %zu, ch. %zu:",ipix,igain);
                  for ( isamp=0; isamp<num_samples; isamp++ )
                     printf(" %d", adc_sample[isamp]);
                  printf("\n");
               }
               else
               {
                  if ( (int) ipix == hs_maxprt )
                     printf("        ...\n");
               }
            }
      }
   }

   return get_item_end(iobuf,&item_header);
}

/* -------------------------------- adc_reset ------------------------- */

static void adc_reset (AdcData *raw);

static void adc_reset (AdcData *raw)
{
   int ipix, igain;
//   int is;
   size_t nb;
   if ( raw == NULL )
      return;
   raw->known = 0;
   raw->list_known = 0;
   raw->list_size = 0;
   nb = raw->num_samples * sizeof(raw->adc_sample[0][0][0]);
   for (igain=0; igain<raw->num_gains; igain++)
   {
      for (ipix=0; ipix<raw->num_pixels; ipix++)
      {
         raw->significant[ipix] = 0;
         raw->adc_known[igain][ipix] = 0;
         raw->adc_sum[igain][ipix] = 0;
//         /* Traditionally resetting samples one by one */
//         for (is=0; is<raw->num_samples; is++)
//            raw->adc_sample[igain][ipix][is] = 0;
         /* At the typical length of traces, memset is a bit faster than 
            resetting the samples one by one. */
         memset(&raw->adc_sample[igain][ipix][0],0,nb);
      }
   }
}

/* -------------------- write_hess_aux_trace_digital ----------------- */
/**
 *  @short Write auxilliary digitized traces.
 *
 *  There is no data reduction for auxilliary traces.
 *  
*/  

int write_hess_aux_trace_digital (IO_BUFFER *iobuf, AuxTraceD *auxd)
{
   IO_ITEM_HEADER item_header;
   size_t it;
   
   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;

   if ( auxd == NULL )
      return -1;
   if ( ! auxd->known || auxd->trace_data == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_AUX_DIGITAL_TRACE;  /* Data type */
   item_header.version = 0;
   item_header.ident = auxd->trace_type;

   put_item_begin(iobuf,&item_header);

   put_long(auxd->tel_id,iobuf);
   put_real(auxd->time_scale,iobuf);
   put_count(auxd->num_traces,iobuf);
   put_count(auxd->len_traces,iobuf);
   
   for ( it=0; it<auxd->num_traces; it++ )
      put_vector_of_uint16_scount_differential(auxd->trace_data+it*auxd->len_traces,auxd->len_traces,iobuf);

   return put_item_end(iobuf,&item_header);
}

/* -------------------- read_hess_aux_trace_digital ----------------- */
/**
 *  @short Read auxilliary digitized traces.
 *
*/  

int read_hess_aux_trace_digital (IO_BUFFER *iobuf, AuxTraceD *auxd)
{
   IO_ITEM_HEADER item_header;
   size_t it, nt, lt;
   int rc;
   
   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;

   if ( auxd == NULL )
      return -1;
   auxd->known = 0;

   item_header.type = IO_TYPE_HESS_AUX_DIGITAL_TRACE;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 0 )
   {
      fprintf(stderr,"Unsupported auxilliary digitzed traces version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   auxd->trace_type = item_header.ident;

   auxd->tel_id = get_long(iobuf);
   auxd->time_scale = get_real(iobuf);
   nt = get_count(iobuf);
   lt = get_count(iobuf);
   
   if ( nt != auxd->num_traces || lt != auxd->len_traces || auxd->trace_data == NULL )
   {
      if ( auxd->trace_data != NULL )
         free(auxd->trace_data);
      auxd->trace_data = malloc(nt*lt*sizeof(auxd->trace_data[0]));
      if ( auxd->trace_data == NULL )
      {
         fprintf(stderr,
            "Failed to allocate memory for %zu * %zu auxilliary digitized trace values.\n",
            nt, lt);
         get_item_end(iobuf,&item_header);
         return -1;
      }
      auxd->num_traces = nt;
      auxd->len_traces = lt;
   }
   
   for ( it=0; it<auxd->num_traces; it++ )
      get_vector_of_uint16_scount_differential(auxd->trace_data+it*auxd->len_traces,auxd->len_traces,iobuf);

   auxd->known = 1;

   return get_item_end(iobuf,&item_header);
}


/* -------------------- print_hess_aux_trace_digital ----------------- */
/**
 *  @short Print auxilliary digitized traces.
 *
*/  

int print_hess_aux_trace_digital (IO_BUFFER *iobuf)
{
   IO_ITEM_HEADER item_header;
   int tel_id;             ///< Must match the expected telescope ID when reading.
   int trace_type;         ///< Indicate what type of trace we have (1: DigitalSum trigger trace)
   float time_scale;       ///< Time per auxilliary sample over time per normal FADC sample (typ.: 1.0)
   size_t num_traces;      ///< The number of traces coming from the camera.
   size_t len_traces;      ///< The length of each trace in FADC samples.
   int rc;
   
   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_AUX_DIGITAL_TRACE;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 0 )
   {
      fprintf(stderr,"Unsupported auxilliary digitzed traces version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   trace_type = item_header.ident;

   tel_id = get_long(iobuf);
   time_scale = get_real(iobuf);
   num_traces = get_count(iobuf);
   len_traces = get_count(iobuf);
   
   printf("   Auxilliary digitized trace data (version %d) for telescope %d:\n", item_header.version, tel_id);
   printf("      Type %d with %ju traces of length %ju (time scale %f).\n",
      trace_type, num_traces, len_traces, time_scale);

   if ( hs_verbose && len_traces <= H_MAX_SLICES )
   {
      size_t it, isamp;
      uint16_t trace_data[H_MAX_SLICES];

      for ( it=0; it<num_traces; it++ )
      {
         get_vector_of_uint16_scount_differential(trace_data,len_traces,iobuf);
         if ( it < hs_maxprt )
         {
            printf("        Trace %zu:", it);
            for ( isamp=0; isamp<len_traces; isamp++ )
               printf(" %d", trace_data[isamp]);
            printf("\n");
         }
         else
         {
            if ( it == hs_maxprt )
               printf("        ...\n");
         }
      }
   }

   return get_item_end(iobuf,&item_header);
}
   

/* -------------------- write_hess_aux_trace_analog ----------------- */
/**
 *  @short Write auxilliary analog traces.
 *
*/  

int write_hess_aux_trace_analog (IO_BUFFER *iobuf, AuxTraceA *auxa)
{
   IO_ITEM_HEADER item_header;
   size_t it;
   
   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;

   if ( auxa == NULL )
      return -1;
   if ( ! auxa->known || auxa->trace_data == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_AUX_ANALOG_TRACE;  /* Data type */
   item_header.version = 0;
   item_header.ident = auxa->trace_type;

   put_item_begin(iobuf,&item_header);

   put_long(auxa->tel_id,iobuf);
   put_real(auxa->time_scale,iobuf);
   put_count(auxa->num_traces,iobuf);
   put_count(auxa->len_traces,iobuf);
   
   for ( it=0; it<auxa->num_traces; it++ )
      put_vector_of_float(auxa->trace_data+it*auxa->len_traces,auxa->len_traces,iobuf);

   return put_item_end(iobuf,&item_header);
}

/* -------------------- read_hess_aux_trace_analog ----------------- */
/**
 *  @short Read auxilliary analog traces.
 *
*/  

int read_hess_aux_trace_analog (IO_BUFFER *iobuf, AuxTraceA *auxa)
{
   IO_ITEM_HEADER item_header;
   size_t it, nt, lt;
   int rc;
   
   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;

   if ( auxa == NULL )
      return -1;
   auxa->known = 0;

   item_header.type = IO_TYPE_HESS_AUX_ANALOG_TRACE;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 0 )
   {
      fprintf(stderr,"Unsupported auxilliary analog traces version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   auxa->trace_type = item_header.ident;

   auxa->tel_id = get_long(iobuf);
   auxa->time_scale = get_real(iobuf);
   nt = get_count(iobuf);
   lt = get_count(iobuf);
   
   if ( nt != auxa->num_traces || lt != auxa->len_traces || auxa->trace_data == NULL )
   {
      if ( auxa->trace_data != NULL )
         free(auxa->trace_data);
      auxa->trace_data = malloc(nt*lt*sizeof(auxa->trace_data[0]));
      if ( auxa->trace_data == NULL )
      {
         fprintf(stderr,
            "Failed to allocate memory for %zu * %zu auxilliary analog trace values.\n",
            nt, lt);
         get_item_end(iobuf,&item_header);
         return -1;
      }
      auxa->num_traces = nt;
      auxa->len_traces = lt;
   }
   
   for ( it=0; it<auxa->num_traces; it++ )
      get_vector_of_float(auxa->trace_data+it*auxa->len_traces,auxa->len_traces,iobuf);

   auxa->known = 1;

   return get_item_end(iobuf,&item_header);
}


/* -------------------- print_hess_aux_trace_analog ----------------- */
/**
 *  @short Print auxilliary analog traces.
 *
*/  

int print_hess_aux_trace_analog (IO_BUFFER *iobuf)
{
   IO_ITEM_HEADER item_header;
   int tel_id;             ///< Must match the expected telescope ID when reading.
   int trace_type;         ///< Indicate what type of trace we have 
   float time_scale;       ///< Time per auxilliary sample over time per normal FADC sample (typ.: 0.25)
   size_t num_traces;      ///< The number of traces coming from the camera.
   size_t len_traces;      ///< The length of each trace in FADC samples.
   int rc;
   
   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_AUX_ANALOG_TRACE;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 0 )
   {
      fprintf(stderr,"Unsupported auxilliary digitzed traces version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   trace_type = item_header.ident;

   tel_id = get_long(iobuf);
   time_scale = get_real(iobuf);
   num_traces = get_count(iobuf);
   len_traces = get_count(iobuf);
   
   printf("   Auxilliary digitized trace data (version %d) for telescope %d:\n", item_header.version, tel_id);
   printf("      Type %d with %ju traces of length %ju (time scale %f).\n",
      trace_type, num_traces, len_traces, time_scale);

   if ( hs_verbose && len_traces <= H_MAX_SLICES )
   {
      size_t it, isamp;
      float trace_data[H_MAX_SLICES];

      for ( it=0; it<num_traces; it++ )
      {
         get_vector_of_float(trace_data,len_traces,iobuf);
         if ( it < hs_maxprt )
         {
            printf("        Trace %zu:", it);
            for ( isamp=0; isamp<len_traces; isamp++ )
               printf(" %f", trace_data[isamp]);
            printf("\n");
         }
         else
         {
            if ( it == hs_maxprt )
               printf("        ...\n");
         }
      }
   }

   return get_item_end(iobuf,&item_header);
}


/* ------------------- write_hess_pixeltrg_time ------------------ */

int write_hess_pixeltrg_time (IO_BUFFER *iobuf, PixelTrgTime *dt)
{
   IO_ITEM_HEADER item_header;
   
   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;

   if ( dt == NULL )
      return -1;
   if ( ! dt->known || dt->num_times <= 0 )
      return -1;

   item_header.type = IO_TYPE_HESS_PIXELTRG_TM;  /* Data type */
   item_header.version = 0;
   item_header.ident = dt->tel_id;

   put_item_begin(iobuf,&item_header);

   put_real(dt->time_step,iobuf);
   put_scount(dt->num_times,iobuf);
   put_vector_of_int_scount(dt->pixel_list,dt->num_times,iobuf);
   put_vector_of_int_scount(dt->pixel_time,dt->num_times,iobuf);

   return put_item_end(iobuf,&item_header);
}

/* ------------------- read_hess_pixeltrg_time ------------------- */

int read_hess_pixeltrg_time (IO_BUFFER *iobuf, PixelTrgTime *dt)
{
   IO_ITEM_HEADER item_header;
   int rc;
   
   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;

   if ( dt == NULL )
      return -1;
   dt->known = 0;

   item_header.type = IO_TYPE_HESS_PIXELTRG_TM;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 0 )
   {
      fprintf(stderr,"Unsupported pixel trigger time version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }
   if ( item_header.ident != dt->tel_id )
   {
      fprintf(stderr,"Pixel trigger time data for wrong telescope.\n");
      get_item_end(iobuf,&item_header);
      return -1;
   }
      
   dt->time_step = get_real(iobuf);
   dt->num_times = get_scount(iobuf);
   if ( dt->num_times < 0 || dt->num_times > H_MAX_PIX )
   {
      fprintf(stderr,"Number of pixel trigger times is out of range.\n");
      get_item_end(iobuf,&item_header);
      return -1;
   }
   get_vector_of_int_scount(dt->pixel_list,dt->num_times,iobuf);
   get_vector_of_int_scount(dt->pixel_time,dt->num_times,iobuf);

   dt->known = 1;

   return get_item_end(iobuf,&item_header);
}

/* ------------------- print_hess_pixeltrg_time ------------------ */


int print_hess_pixeltrg_time (IO_BUFFER *iobuf)
{
   IO_ITEM_HEADER item_header;
   int rc;
   double time_step;
   int num_times, tel_id;
   int pixel_list[H_MAX_PIX], pixel_time[H_MAX_PIX];
   
   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_PIXELTRG_TM;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 0 )
   {
      fprintf(stderr,"Unsupported pixel trigger time version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   tel_id = item_header.ident;
   time_step = get_real(iobuf);
   num_times = get_scount(iobuf);
   if ( num_times < 0 || num_times > H_MAX_PIX )
   {
      fprintf(stderr,"Number of pixel trigger times is out of range.\n");
      get_item_end(iobuf,&item_header);
      return -1;
   }
   get_vector_of_int_scount(pixel_list,num_times,iobuf);
   get_vector_of_int_scount(pixel_time,num_times,iobuf);

   printf("    Pixel trigger time data (version %d) for telescope %d:\n", item_header.version, tel_id);
   printf("      With times for %d pixels in steps of %f ns.\n", num_times, time_step);

   if ( hs_verbose  )
   {
      size_t it;
      for ( it=0; it<hs_maxprt && it<num_times; it++ )
         printf("      Pixel %d: %d (T=%f ns)\n", pixel_list[it], 
            pixel_time[it], pixel_time[it]*time_step);
      if ( num_times > hs_maxprt)
         printf("      ...\n");
   }
   return get_item_end(iobuf,&item_header);
}

/* ---------------- build_list_for_hess_pixtime -------------- */
/**
 *  A helper function finding the shorter of two possible formats
 *  for the list of pixels with any timing information.
 */

static void build_list_for_hess_pixtime (PixelTiming *pixtm);

static void build_list_for_hess_pixtime (PixelTiming *pixtm)
{
   int list1[H_MAX_PIX], list2[2*H_MAX_PIX];
   int i, n1=0, n2=0, lastpix=-99;
   if ( pixtm->list_type == 1 || pixtm->list_type == 2 || pixtm->num_types <= 0 )
      return;
   for ( i=0; i<pixtm->num_pixels && i<H_MAX_PIX; i++ )
   {
      /* Note that we look only at the first timing element of each pixel. */
      if ( pixtm->timval[i][0] >= 0. )
      {
         list1[n1++] = i;
         if ( i == lastpix+1 && n2>0 )
            list2[2*n2-1] = i;
         else
         {
            list2[2*n2] = list2[2*n2+1] = i;
            n2++;
         }
         lastpix = i;
      }
   }
   if ( n2<n1/2 )
   {
      pixtm->list_type = 2;
      pixtm->list_size = n2;
      for (i=0; i<2*n2; i++ )
         pixtm->pixel_list[i] = list2[i];
   }
   else
   {
      pixtm->list_type = 1;
      pixtm->list_size = n1;
      for (i=0; i<n1; i++ )
         pixtm->pixel_list[i] = list1[i];
   }
}

/* -------------------- write_hess_pixtime ------------------ */
/**
 *  Write pixel timing parameters for selected pixels.
 */

int write_hess_pixtime (IO_BUFFER *iobuf, PixelTiming *pixtm)
{
   IO_ITEM_HEADER item_header;
   int i, j;
   double scale = 100.;
   int with_sum = 0;
   int glob_only_selected = 0;
   int v0 = 0;

   if ( iobuf == (IO_BUFFER *) NULL || pixtm == NULL )
      return -1;

   if ( !pixtm->known )
      return 0;

   if ( pixtm->list_type == 0 ) /* No pixel list defined yet */
      build_list_for_hess_pixtime(pixtm);

   if ( pixtm->list_size <= 0 || pixtm->num_types <= 0 ||
        (pixtm->list_type != 1 && pixtm->list_type != 2) )
      return 0;

   if ( pixtm->before_peak >= 0 && pixtm->after_peak >= 0 )
      with_sum = 1;

   item_header.type = IO_TYPE_HESS_PIXELTIMING;  /* Data type */
   item_header.version = 1;             /* Version 0 or 1 for now */
   if ( pixtm->num_pixels >= 32768 )
      item_header.version = 2;          /* overcome 16-bit limitation */
   if ( item_header.version == 0 )
      v0 = 1;

   item_header.ident = pixtm->tel_id;
   put_item_begin(iobuf,&item_header);

   if ( item_header.version <= 1 )
      put_short(pixtm->num_pixels,iobuf);
   else
      put_scount32(pixtm->num_pixels,iobuf);
   put_short(pixtm->num_gains,iobuf);
   put_short(pixtm->before_peak,iobuf);
   put_short(pixtm->after_peak,iobuf);
   put_short(pixtm->list_type,iobuf);
   if ( item_header.version <= 1 )
   {
      put_short(pixtm->list_size,iobuf);
      if ( pixtm->list_type == 1 )
         put_vector_of_int(pixtm->pixel_list,pixtm->list_size,iobuf);
      else
         put_vector_of_int(pixtm->pixel_list,2*pixtm->list_size,iobuf);
   }
   else
   {
      put_scount32(pixtm->list_size,iobuf);
      if ( pixtm->list_type == 1 )
         put_vector_of_int_scount(pixtm->pixel_list,pixtm->list_size,iobuf);
      else
         put_vector_of_int_scount(pixtm->pixel_list,2*pixtm->list_size,iobuf);
   }
   if ( pixtm->threshold < 0 )
      glob_only_selected = 1;
   put_short(pixtm->threshold,iobuf);
   put_short(pixtm->num_types,iobuf);
   put_vector_of_int(pixtm->time_type,pixtm->num_types,iobuf);
   put_vector_of_float(pixtm->time_level,pixtm->num_types,iobuf);
   if ( pixtm->granularity > 0. )
   {
      put_real(pixtm->granularity,iobuf);
      scale = 1./pixtm->granularity;
   }
   else
   {
      put_real(1./scale,iobuf);
   }
   put_real(pixtm->peak_global,iobuf);

   for ( i=0; i<pixtm->list_size; i++ )
   {
      int ipix, k1, k2;
      if ( pixtm->list_type == 1 )
         k1 = k2 = pixtm->pixel_list[i];
      else
      {
         k1 = pixtm->pixel_list[2*i];
         k2 = pixtm->pixel_list[2*i+1];
      }
      for ( ipix=k1; ipix<=k2; ipix++ )
      {
         for ( j=0; j<pixtm->num_types; j++ )
         {
            int itm = (int) (pixtm->timval[ipix][j]*scale+0.5);
            if ( pixtm->timval[ipix][j] < 0. )
               itm--;
            put_short(itm,iobuf);
         }
         if ( with_sum )
         {
            int igain;
            for ( igain=0; igain<pixtm->num_gains; igain++ )
            {
               if ( v0 )
                  put_short(pixtm->pulse_sum_loc[igain][ipix],iobuf);
               else
                  put_scount32(pixtm->pulse_sum_loc[igain][ipix],iobuf);
            }
            if ( glob_only_selected )
            {
               for ( igain=0; igain<pixtm->num_gains; igain++ )
               {
                  if ( v0 )
                     put_short(pixtm->pulse_sum_glob[igain][ipix],iobuf);
                  else
                     put_scount32(pixtm->pulse_sum_glob[igain][ipix],iobuf);
               }
            }
         }
      }
   }

   if ( with_sum && pixtm->list_size > 0 && !glob_only_selected )
   {
      int igain;
      for ( igain=0; igain<pixtm->num_gains; igain++ )
      {
         for ( j=0; j<pixtm->num_pixels; j++ )
         {
            if ( v0 )
               put_short(pixtm->pulse_sum_glob[igain][j],iobuf);
            else
               put_scount32(pixtm->pulse_sum_glob[igain][j],iobuf);
         }
      }
   }

   return put_item_end(iobuf,&item_header);
}

/* -------------------- read_hess_pixtime ------------------ */
/**
 *  Read pixel timing parameters for selected pixels.
 */

int read_hess_pixtime (IO_BUFFER *iobuf, PixelTiming *pixtm)
{
   IO_ITEM_HEADER item_header;
   int i, j;
   double scale = 100.;
   int rc, with_sum = 0;
   int glob_only_selected = 0;
   int v0 = 0;

   if ( iobuf == (IO_BUFFER *) NULL || pixtm == NULL )
      return -1;

   pixtm->known = 0;

   pixtm->list_type = 1;
   pixtm->list_size = pixtm->num_types = 0;
   item_header.type = IO_TYPE_HESS_PIXELTIMING;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 2 )
   {
      fprintf(stderr,"Unsupported pixel timing version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }
   if ( item_header.version == 0 )
      v0 = 1;
   if ( item_header.version <= 1 )
      pixtm->num_pixels = get_short(iobuf);
   else
      pixtm->num_pixels = get_scount32(iobuf);
   pixtm->num_gains = get_short(iobuf);
   pixtm->before_peak = get_short(iobuf);
   pixtm->after_peak = get_short(iobuf);
   pixtm->list_type = get_short(iobuf);
   if ( pixtm->list_type != 1 && pixtm->list_type != 2 )
   {
      fprintf(stderr,"Invalid type of pixel list in pixel timing data: %d.\n",
         pixtm->list_type);
      get_item_end(iobuf,&item_header);
      return -1;
   }
   if ( item_header.version <= 1 )
      pixtm->list_size = get_short(iobuf);
   else
      pixtm->list_size = get_scount32(iobuf);
   if ( pixtm->list_size < 0 || pixtm->list_size > H_MAX_PIX )
   {
      fprintf(stderr,"Invalid size of pixel list in pixel timing data: %d.\n",
         pixtm->list_size);
      get_item_end(iobuf,&item_header);
      return -1;
   }
   if ( item_header.version <= 1 )
   {
      if ( pixtm->list_type == 1 )
         get_vector_of_int(pixtm->pixel_list,pixtm->list_size,iobuf);
      else
         get_vector_of_int(pixtm->pixel_list,2*pixtm->list_size,iobuf);
   }
   else
   {
      if ( pixtm->list_type == 1 )
         get_vector_of_int_scount(pixtm->pixel_list,pixtm->list_size,iobuf);
      else
         get_vector_of_int_scount(pixtm->pixel_list,2*pixtm->list_size,iobuf);
   }
   pixtm->threshold = get_short(iobuf);
   if ( pixtm->threshold < 0 )
      glob_only_selected = 1;
   if ( pixtm->before_peak >= 0 && pixtm->after_peak >= 0 )
      with_sum = 1;
   pixtm->num_types = get_short(iobuf);
   if ( pixtm->num_types < 0 || pixtm->num_types > H_MAX_PIX_TIMES )
   {
      fprintf(stderr,"Invalid number of types in pixel timing data: %d.\n",
         pixtm->num_types);
      get_item_end(iobuf,&item_header);
      return -1;
   } 
   get_vector_of_int(pixtm->time_type,pixtm->num_types,iobuf);
   get_vector_of_float(pixtm->time_level,pixtm->num_types,iobuf);
   pixtm->granularity = get_real(iobuf);
   if ( pixtm->granularity > 0. )
   {
      scale = pixtm->granularity;
   }
   else
   {
      scale = 0.01;
      pixtm->granularity = 0.01;
   }
   pixtm->peak_global = get_real(iobuf);

   /* The first timing element is always initialised to indicate unknown. */
   for ( i=0; i<pixtm->num_pixels; i++ )
      pixtm->timval[i][0] = -1.;
#if 0
   /* If users are sloppy we may have to initialise the global pulse sums as well. */
   if ( with_sum && glob_only_selected )
   {
      int igain, ipix;
      for ( igain=0; igain<pixtm->num_gains; igain++ )
         for ( ipix=0; ipix<pixtm->num_pixels; ipix++ )
            pixtm->pulse_sum_glob[igain][ipix] = 0.;
   }
#endif

   for ( i=0; i<pixtm->list_size; i++ )
   {
      int ipix, k1, k2;
      if ( pixtm->list_type == 1 )
         k1 = k2 = pixtm->pixel_list[i];
      else
      {
         k1 = pixtm->pixel_list[2*i];
         k2 = pixtm->pixel_list[2*i+1];
      }
      for ( ipix=k1; ipix<=k2; ipix++ )
      {
         for ( j=0; j<pixtm->num_types; j++ )
         {
            pixtm->timval[ipix][j] = scale * get_short(iobuf);
         }
         if ( with_sum )
         {
            int igain;
            for ( igain=0; igain<pixtm->num_gains; igain++ )
               pixtm->pulse_sum_loc[igain][ipix] = 
                  (v0 ? get_short(iobuf) : get_scount32(iobuf));
            if ( glob_only_selected )
            {
               for ( igain=0; igain<pixtm->num_gains; igain++ )
                  pixtm->pulse_sum_glob[igain][ipix] = 
                     (v0 ? get_short(iobuf) : get_scount32(iobuf));
            }
         }
      }
   }

   if ( with_sum && pixtm->list_size > 0 && !glob_only_selected )
   {
      int igain;
      for ( igain=0; igain<pixtm->num_gains; igain++ )
      {
         for ( j=0; j<pixtm->num_pixels; j++ )
            pixtm->pulse_sum_glob[igain][j] = 
               (v0 ? get_short(iobuf) : get_scount32(iobuf));
      }
   }

   pixtm->known = 1;

   return get_item_end(iobuf,&item_header);
}

/* -------------------- print_hess_pixtime ----------------- */
/**
 *  Print sampled ADC data in eventio format.
 */

int print_hess_pixtime (IO_BUFFER *iobuf)
{
   IO_ITEM_HEADER item_header;
   int num_pixels, num_gains, list_type, list_size, num_types;
   int pixel_list[2*H_MAX_PIX];
   double granularity;
   int rc, i, j, bp, ap, with_sum = 0, thr=0;
   int glob_only_selected = 0;
   int v0 = 0;

   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;

   hs_check_env();

   item_header.type = IO_TYPE_HESS_PIXELTIMING;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;

   if ( item_header.version > 2 )
   {
      fprintf(stderr,"Unsupported pixel timing version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }
   if ( item_header.version == 0 )
      v0 = 1;
   num_pixels = (item_header.version <= 1 ? 
         get_short(iobuf) : get_scount32(iobuf));
   num_gains = get_short(iobuf);
   bp = get_short(iobuf);
   ap = get_short(iobuf);
   if ( bp >= 0 && ap >= 0 )
      with_sum = 1;
   list_type = get_short(iobuf);
   list_size = (item_header.version <= 1 ?
      get_short(iobuf) : get_scount32(iobuf));
   if ( num_pixels < 0 || num_pixels > H_MAX_PIX ||
        (list_type != 1 && list_type != 2) ||
        list_size < 0 || list_size > H_MAX_PIX )
   {
      fprintf(stderr,"Invalid timing information pixel list.\n");
      return -1;
   }
   if ( item_header.version <= 1 )
   {
      if ( list_type == 1 )
         get_vector_of_int(pixel_list,list_size,iobuf);
      else
         get_vector_of_int(pixel_list,2*list_size,iobuf);
   }
   else
   {
      if ( list_type == 1 )
         get_vector_of_int_scount(pixel_list,list_size,iobuf);
      else
         get_vector_of_int_scount(pixel_list,2*list_size,iobuf);
   }
   printf("    Pixel timing data for telescope %ld:\n", item_header.ident);
   printf("      With data for up to %d pixels in list of type %d and size %d\n", 
      num_pixels, list_type, list_size);
   printf("      Threshold for pixel selection was: %d ADC counts.\n", 
      (thr=get_short(iobuf)));
   if ( thr < 0 )
      glob_only_selected = 1;
   num_types = get_short(iobuf);
   printf("      %d types of timing data of types:", num_types);
   for ( i=0; i<num_types; i++ )
      printf(" %d", get_short(iobuf));
   printf("\n");
   printf("      Fractions of peak amplitude:");
   for ( i=0; i<num_types; i++ )
      printf(" %5.3f", get_real(iobuf));
   printf("\n");
   granularity = get_real(iobuf);
   if ( granularity <= 0. )
      granularity = 0.01;
   printf("      Granularity is %f time slices.\n", granularity);
   if ( with_sum )
      printf("      With pedestal-subtracted ADC sums from %d slices "
          "before to %d slices after the peak.\n", bp, ap);
   printf("      Camera-wide mean/global peak position is at %4.2f time slices"
       " from start of read-out window.\n", get_real(iobuf));

   if ( hs_verbose )
   {
      int iprt = 0;
      printf("      Timing data for selected pixels:\n");
      for ( i=0; i<list_size; i++ )
      {
         int ipix, k1, k2;
         if ( list_type == 1 )
            k1 = k2 = pixel_list[i];
         else
         {
            k1 = pixel_list[2*i];
            k2 = pixel_list[2*i+1];
         }
         for ( ipix=k1; ipix<=k2; ipix++ )
         {
            if ( iprt < hs_maxprt )
            {
               printf("        Pixel %d:",ipix);
               /* Positions of peak and threshold, or width. */
               for ( j=0; j<num_types; j++ )
                  printf(" %4.2f", get_short(iobuf)*granularity);
               if ( with_sum )
               {
                  int igain;
                  printf(", lsum=");
                  /* ADC sum wrt. local peak position */
                  for ( igain=0; igain<num_gains; igain++ )
                      printf(" %d", 
                        (v0 ? get_short(iobuf) : get_scount32(iobuf)));
                  if ( glob_only_selected )
                  {
                     printf(", gsum=");
                     /* ADC sum wrt. global peak position */
                     for ( igain=0; igain<num_gains; igain++ )
                         printf(" %d", 
                           (v0 ? get_short(iobuf) : get_scount32(iobuf)));
                  }
               }
               printf("\n");
            }
            else
            {
               if ( (int) iprt == hs_maxprt )
                  printf("        ...\n");
               for ( j=0; j<num_types; j++ )
                  (void) get_short(iobuf);
               if ( with_sum )
               {
                  int igain;
                  for ( igain=0; igain<num_gains; igain++ )
                     (void) (v0 ? get_short(iobuf) : get_scount32(iobuf));
                  if ( glob_only_selected )
                  {
                     for ( igain=0; igain<num_gains; igain++ )
                        (void) (v0 ? get_short(iobuf) : get_scount32(iobuf));
                  }
               }
            }
            iprt++;
         }
      }

      /* ADC sums around the global peak position for all pixels. */
      if ( with_sum && list_size > 0 && !glob_only_selected )
      {
         int ipix, igain;
         for ( igain=0; igain<num_gains; igain++ )
         {
            iprt = 0;
            printf("      ADC sums for gain %d around global peak:", igain);
            for ( ipix=0; ipix<num_pixels; ipix++ )
            {
               int adc = (v0 ? get_short(iobuf) : get_scount32(iobuf));
               if ( iprt < hs_maxprt )
                  printf(" %d", adc);
               else if ( iprt == hs_maxprt )
                  printf(" ...");
               iprt++;
            }
            printf("\n");
         }
      }
   }

   return get_item_end(iobuf,&item_header);
}

  
/* -------------------- write_hess_pixcalib ------------------ */
/**
 *  Write pixel intensities calibrated to (mean?) p.e. units.
 */

int write_hess_pixcalib (IO_BUFFER *iobuf, PixelCalibrated *pixcal)
{
   IO_ITEM_HEADER item_header;
   int ipix;

   if ( iobuf == (IO_BUFFER *) NULL || pixcal == NULL )
      return -1;

   if ( !pixcal->known )
      return 0;

   item_header.type = IO_TYPE_HESS_PIXELCALIB;  /* Data type */
   item_header.version = 0;             /* Version 0 */

   item_header.ident = pixcal->tel_id;
   put_item_begin(iobuf,&item_header);
   
   if ( pixcal->list_size<0 || pixcal->list_size>pixcal->num_pixels )
   {
      pixcal->list_known = 0;
      pixcal->list_size = 0;
   }
   if ( pixcal->list_known != 1 && pixcal->list_known != 2 )
   {
      int nsig = 0;
      for ( ipix=0; ipix<pixcal->num_pixels; ipix++ )
      {
         if ( pixcal->significant[ipix] )
            pixcal->pixel_list[nsig++] = ipix;
      }
      if ( nsig == pixcal->num_pixels )
         pixcal->list_known = 2;
      else if ( nsig <= pixcal->num_pixels/4 )
         pixcal->list_known = 1;
      else
         pixcal->list_known = -1;
      pixcal->list_size = nsig;
   }
   
   put_count32((uint32_t) pixcal->num_pixels,iobuf);
   put_scount32(pixcal->int_method,iobuf);
   put_scount32(pixcal->list_known,iobuf);
   if ( pixcal->list_known == 1 )
   {
      int i;
      put_count32((uint32_t) pixcal->list_size,iobuf);
      for (i=0; i<pixcal->list_size; i++)
         put_count32((uint32_t)pixcal->pixel_list[i],iobuf);
      for (i=0; i<pixcal->list_size; i++)
      {
         ipix = pixcal->pixel_list[i];
         put_sfloat(pixcal->pixel_pe[ipix],iobuf);
      }
   }
   else if ( pixcal->list_known == -1 )
   {
      put_vector_of_byte(pixcal->significant,pixcal->num_pixels,iobuf);
      for (ipix=0; ipix<pixcal->num_pixels; ipix++)
      {
         if ( pixcal->significant[ipix] )
            put_sfloat(pixcal->pixel_pe[ipix],iobuf);
      }
   }
   else if ( pixcal->list_known == 2 )
   {
      for (ipix=0; ipix<pixcal->num_pixels; ipix++)
         put_sfloat(pixcal->pixel_pe[ipix],iobuf);
   }

   return put_item_end(iobuf,&item_header);
}

/* -------------------- read_hess_pixcalib ----------------- */
/**
 *  Read pixel intensities calibrated to (mean?) p.e. units.
*/  

int read_hess_pixcalib (IO_BUFFER *iobuf, PixelCalibrated *pixcal)
{
   IO_ITEM_HEADER item_header;
   int rc, ipix, npix;

   if ( iobuf == (IO_BUFFER *) NULL || pixcal == NULL )
      return -1;

   pixcal->known = 0;

   item_header.type = IO_TYPE_HESS_PIXELCALIB;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 0 )
   {
      fprintf(stderr,"Unsupported calibrated pixel intensities version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }
   pixcal->tel_id = item_header.ident;
   npix = (int) get_count(iobuf);
   if ( npix > H_MAX_PIX )
   {
      fprintf(stderr,"Invalid number of pixels in calibrated pixel intensities: %d.\n",
         npix);
      get_item_end(iobuf,&item_header);
      return -1;
   }
   pixcal->num_pixels = npix;
   pixcal->int_method = (int) get_scount32(iobuf);
   pixcal->list_known = (int) get_scount32(iobuf);
   pixcal->list_size = 0;
   if ( pixcal->list_known == 2 ) /* all pixels to be marked as significant */
   {
      for (ipix=0; ipix<npix; ipix++)
         pixcal->significant[ipix] = 1;
   }
   else
   {
      for (ipix=0; ipix<npix; ipix++)
         pixcal->significant[ipix] = 0;
   }
   if ( pixcal->list_known == 1 ) /* selected pixels by list of pixel IDs */
   {
      int i;
      pixcal->list_size = (int) get_count32(iobuf);
      for (i=0; i<pixcal->list_size; i++)
      {
         ipix = pixcal->pixel_list[i] = (int) get_count32(iobuf);
         pixcal->significant[ipix] = 1;
      }
      for (i=0; i<pixcal->list_size; i++)
      {
         ipix = pixcal->pixel_list[i];
         pixcal->pixel_pe[ipix] = get_sfloat(iobuf);
      }
   }
   else if ( pixcal->list_known == -1 ) /* selected pixels by bit(s) */
   {
      get_vector_of_byte(pixcal->significant,pixcal->num_pixels,iobuf);
      for (ipix=0; ipix<pixcal->num_pixels; ipix++)
      {
         if ( pixcal->significant[ipix] )
            pixcal->pixel_pe[ipix] = get_sfloat(iobuf);
      }
   }
   else if ( pixcal->list_known == 2 ) /* all pixels significant */
   {
      for (ipix=0; ipix<pixcal->num_pixels; ipix++)
         pixcal->pixel_pe[ipix] = get_sfloat(iobuf);
   }
   
   pixcal->known = 1;

   return get_item_end(iobuf,&item_header);
}

/* -------------------- print_hess_pixcalib ----------------- */
/**
 *  Print pixel intensities calibrated to (mean?) p.e. units.
*/  

int print_hess_pixcalib (IO_BUFFER *iobuf)
{
   IO_ITEM_HEADER item_header;
   int rc;
   int list_known = 0, list_size = 0;
   int pixel_list[H_MAX_PIX];
   int i, ipix, npix;
   uint8_t significant[H_MAX_PIX];
   int im = 0;

   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;

   hs_check_env();

   item_header.type = IO_TYPE_HESS_PIXELCALIB;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 0 )
   {
      fprintf(stderr,"Unsupported calibrated pixel intensities version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }
   printf("    Calibrated pixel intensities data for telescope %ld:\n", item_header.ident);

   npix = (int) get_count(iobuf);
   if ( npix > H_MAX_PIX )
   {
      fprintf(stderr,"    Invalid number of pixels in calibrated pixel intensities: %d.\n",
         npix);
      get_item_end(iobuf,&item_header);
      return -1;
   }
   im = (int) get_scount32(iobuf);
   if ( im == -1 )
      printf("      Derived from global peak integral in pixel timing data.\n");
   else if ( im == -2 )
      printf("      Derived from local peak integral in pixel timing data.\n");
   else if ( im > 0 )
      printf("      Based on pulse integration method %d.\n", im);
   list_known = (int) get_scount32(iobuf);
   list_size = 0;
   if ( list_known == 1 ) /* selected pixels by list of pixel IDs */
   {
      printf("      Significant pixels are listed by pixel ID.\n      Pixel intensities:");
      list_size = (int) get_count32(iobuf);
      for (i=0; i<list_size; i++)
      {
         pixel_list[i] = (int) get_count32(iobuf);
      }
      for (i=0; i<list_size; i++)
      {
         ipix = pixel_list[i];
         if ( i < hs_maxprt )
            printf(" %d: %f,", ipix, get_sfloat(iobuf));
         else
         {
            if ( i == hs_maxprt )
               printf(" ...");
            (void) get_sfloat(iobuf);
         }
      }
      printf("\n");
   }
   else if ( list_known == -1 ) /* selected pixels by bit(s) */
   {
      printf("      Significant pixels are marked as such.\n      Pixel intensities:");
      get_vector_of_byte(significant,npix,iobuf);
      for (ipix=i=0; ipix<npix; ipix++)
      {
         if ( significant[ipix] )
         {
            if ( (i++) < hs_maxprt )
               printf(" %d: %f,", ipix, get_sfloat(iobuf));
            else
            {
               if ( i == hs_maxprt )
                  printf(" ...");
               (void) get_sfloat(iobuf);
            }
         }
      }
      printf("\n");
   }
   else if ( list_known == 2 ) /* all pixels significant */
   {
      printf("      Pixel intensities:");
      for (ipix=0; ipix<npix; ipix++)
      {
         if ( ipix < hs_maxprt )
            printf(" %f,", get_sfloat(iobuf));
         else
         {
            if ( ipix == hs_maxprt )
               printf(" ...");
            (void) get_sfloat(iobuf);
         }
      }
      printf("\n");
   }

   return get_item_end(iobuf,&item_header);
}

/* -------------------- write_hess_telimage ----------------- */
/**
 *  Write image parameters for one telescope in eventio format.
*/  

int write_hess_telimage (IO_BUFFER *iobuf, ImgData *img, int what)
{
   IO_ITEM_HEADER item_header;
   uint32_t flags;
   
   if ( iobuf == (IO_BUFFER *) NULL || img == NULL )
      return -1;
      
   if ( !img->known )
      return 0;
   
   /* If flags says errors should be saved but none is known */
   /* clear the corresponding bit. */
   if ( (what & IMG_ERR_FLAG) )
      if ( img->x_err == 0. && img->y_err == 0. &&
           img->phi_err == 0. && img->l_err == 0. && img->w_err == 0. )
         what ^= IMG_ERR_FLAG;
   /* If flag says that 3rd and 4th moments should be saved */
   /* but they are not known, clear that bit. */
   if ( (what & IMG_34M_FLAG) && 
       img->skewness_err < 0. && img->kurtosis_err < 0. )
       what ^= IMG_34M_FLAG;
   /* The same applies to hot pixel data */
   if ( (what & IMG_HOT_FLAG) && img->num_hot <= 0 )
      what ^= IMG_HOT_FLAG;
   /* And the same as well for pixel timing results. */
   if ( (what & IMG_PIXTM_FLAG) )
      if ( img->tm_slope == 0. && img->tm_residual == 0. && img->tm_width1 == 0. )
         what ^= IMG_PIXTM_FLAG;

   item_header.type = IO_TYPE_HESS_TELIMAGE;  /* Data type */
#if (H_MAX_PIX >= 32768)
   item_header.version = 6;             /* Version 6 */
#else
   item_header.version = 5; /* better backward compatibility for now */
#endif

   /* What is mixed up in flags:
         Bit(s)     What
         0 - 7      Telescope ID bits 0 - 7 (up to 255 telescopes)
         8          Are errors in image parameters available?
         9          Are third and forth moment available?
         10         Are hot pixels available?
         11         Are pixel timing results available?
         12 - 19    Tail-cut ID bits 0 - 7
         20 - 23    (unused)
         24 - 29    Telescope ID bits 8-13 (up to 16383 telescopes)
   */
   flags = (img->tel_id & 0xff) | ((img->tel_id & 0x3f00) << 16) |
           ((what & IMG_ERR_FLAG)?0x100:0) |
           ((what & IMG_34M_FLAG)?0x200:0) |
           ((what & IMG_HOT_FLAG)?0x400:0) |
           ((what & IMG_PIXTM_FLAG)?0x800:0) |
	   ((img->cut_id & 0xff) << 12);
   item_header.ident = flags;
   
   put_item_begin(iobuf,&item_header);

   if ( item_header.version >= 6 )
      put_scount32(img->pixels,iobuf); /* Changed in version 6 */
   else
      put_short(img->pixels,iobuf); /* First introduced in version 2 */
   if ( item_header.version >= 4 )
   {
      if ( item_header.version >= 6 )
         put_scount32(img->num_sat,iobuf);
      else
         put_short(img->num_sat,iobuf); /* New in version 4 */
      if ( img->num_sat > 0 && item_header.version >= 5 )
         put_real(img->clip_amp,iobuf);
   }

   put_real(img->amplitude,iobuf);
   put_real(img->x,iobuf);
   put_real(img->y,iobuf);
   put_real(img->phi,iobuf);
   put_real(img->l,iobuf);
   put_real(img->w,iobuf);
   put_short(img->num_conc,iobuf);     /* expected to be a small number */
   put_real(img->concentration,iobuf);

   if ( (what & IMG_ERR_FLAG) ) /* Error estimates of 1st+2nd moments in data */
   {
      put_real(img->x_err,iobuf);
      put_real(img->y_err,iobuf);
      put_real(img->phi_err,iobuf);
      put_real(img->l_err,iobuf);
      put_real(img->w_err,iobuf);
   }

   if ( (what & IMG_34M_FLAG) ) /* 3rd+4th moments plus errors in data */
   {
      put_real(img->skewness,iobuf);
      put_real(img->skewness_err,iobuf);
      put_real(img->kurtosis,iobuf);
      put_real(img->kurtosis_err,iobuf);
   }

   if ( (what & IMG_HOT_FLAG) ) /* ADC sum of high-intensity pixels in data */
   {
      if ( item_header.version >= 6 )
      {
         put_scount32(img->num_hot,iobuf);
         put_vector_of_real(img->hot_amp,img->num_hot,iobuf);
         put_vector_of_int_scount(img->hot_pixel,img->num_hot,iobuf);
      }
      else
      {
         put_short(img->num_hot,iobuf);
         put_vector_of_real(img->hot_amp,img->num_hot,iobuf);
         put_vector_of_int(img->hot_pixel,img->num_hot,iobuf); /* New in version 1 */
      }
   }

   if ( (what & IMG_PIXTM_FLAG) && item_header.version > 2 ) /* New in version 3: timing summary */
   {
      put_real(img->tm_slope,iobuf);
      put_real(img->tm_residual,iobuf);
      put_real(img->tm_width1,iobuf);
      put_real(img->tm_width2,iobuf);
      put_real(img->tm_rise,iobuf);
   }

   return put_item_end(iobuf,&item_header);
}
   
/* -------------------- read_hess_telimage ----------------- */
/**
 *  Read image parameters for one telescope in eventio format.
*/  

int read_hess_telimage (IO_BUFFER *iobuf, ImgData *img)
{
   IO_ITEM_HEADER item_header;
   uint32_t flags;
   int rc;
   
   if ( iobuf == (IO_BUFFER *) NULL || img == NULL )
      return -1;
      
   img->known = 0;
      
   item_header.type = IO_TYPE_HESS_TELIMAGE;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 6 )
   {
      fprintf(stderr,"Unsupported telescope image version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   /* Lots of small data was packed into the ID */
   flags = (uint32_t) item_header.ident;
   
   if ( ((item_header.ident & 0xff)|
         ((item_header.ident & 0x3f000000)>>16)) != img->tel_id )
   {
      Warning("Image data is for wrong telescope");
      get_item_end(iobuf,&item_header);
      return -1;
   }
   
   img->cut_id = (item_header.ident & 0xff000) >> 12;
   img->pixels = 0; /* always reset it */
   img->num_sat = 0;
   img->clip_amp = 0.;
   if ( item_header.version >= 6 )
      img->pixels = get_scount32(iobuf);
   else if ( item_header.version >= 2 )
      img->pixels = get_short(iobuf);
   if ( item_header.version >= 4 )
   {
      if ( item_header.version >= 6 )
         img->num_sat = get_scount32(iobuf);
      else
         img->num_sat = get_short(iobuf);
      if ( img->num_sat > 0 && item_header.version >= 5 )
         img->clip_amp = get_real(iobuf);
   }

   img->amplitude = get_real(iobuf);
   img->x = get_real(iobuf);
   img->y = get_real(iobuf);
   img->phi = get_real(iobuf);
   img->l = get_real(iobuf);
   img->w = get_real(iobuf);
   img->num_conc = get_short(iobuf);
   img->concentration = get_real(iobuf);

   if ( (flags & 0x100) ) /* Error estimates of 1st+2nd moments in data */
   {
      img->x_err = get_real(iobuf);
      img->y_err = get_real(iobuf);
      img->phi_err = get_real(iobuf);
      img->l_err = get_real(iobuf);
      img->w_err = get_real(iobuf);
   }
   else
   {
      img->x_err = 0.;
      img->y_err = 0.;
      img->phi_err = 0.;
      img->l_err = 0.;
      img->w_err = 0.;
   }

   if ( (flags & 0x200) ) /* 3rd+4th moments plus errors in data */
   {
      img->skewness = get_real(iobuf);
      img->skewness_err = get_real(iobuf);
      img->kurtosis = get_real(iobuf);
      img->kurtosis_err = get_real(iobuf);
   }
   else
   {
      img->skewness = 0.;
      img->skewness_err = -1.;
      img->kurtosis = 0.;
      img->kurtosis_err = -1.;
   }

   if ( (flags & 0x400) ) /* ADC sum of high-intensity pixels in data */
   {
      if ( item_header.version <= 5 )
      {
         img->num_hot = get_short(iobuf);
         get_vector_of_real(img->hot_amp,img->num_hot,iobuf);
         if ( item_header.version >= 1 )
            get_vector_of_int(img->hot_pixel,img->num_hot,iobuf);
      }
      else
      {
         img->num_hot = get_scount32(iobuf);
         get_vector_of_real(img->hot_amp,img->num_hot,iobuf);
         if ( item_header.version >= 1 )
            get_vector_of_int_scount(img->hot_pixel,img->num_hot,iobuf);
      }
   }
   else
      img->num_hot = 0;

   if ( (flags & 0x800) && item_header.version >= 3 ) /* New in version 3: timing summary */
   {
      img->tm_slope = get_real(iobuf);
      img->tm_residual = get_real(iobuf);
      img->tm_width1 = get_real(iobuf);
      img->tm_width2 = get_real(iobuf);
      img->tm_rise = get_real(iobuf);
   }
   else
      img->tm_slope = img->tm_residual = img->tm_width1 = 
           img->tm_width2 = img->tm_rise = 0.;

   img->known = 1;

   return get_item_end(iobuf,&item_header);
}

/* -------------------- print_hess_telimage ----------------- */
/**
 *  Print image parameters for one telescope in eventio format.
*/  

int print_hess_telimage (IO_BUFFER *iobuf)
{
   IO_ITEM_HEADER item_header;
   uint32_t flags;
   int rc, nhot;

   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_TELIMAGE;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 6 )
   {
      fprintf(stderr,"Unsupported telescope image version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   /* Lots of small data was packed into the ID */
   flags = (uint32_t) item_header.ident;

   printf("    Telescope image for telescope %u\n", 
             (flags & 0xff) | ((flags & 0x3f000000)>>16));

   printf("      Derived with tail-cuts method %u\n", (flags & 0xff000) >> 12);
   if ( item_header.version >= 6 )
      printf("      Number of pixels passing tail-cuts: %d\n", get_scount32(iobuf));
   else if ( item_header.version >= 2 )
      printf("      Number of pixels passing tail-cuts: %d\n", get_short(iobuf));
   else
      printf("      Number of pixels passing tail-cuts not known.\n");
   if ( item_header.version >= 4 )
   {
      int n_sat = (item_header.version <= 5 ? get_short(iobuf) : get_scount32(iobuf));
      if ( n_sat > 0 )
      {
         if ( item_header.version >= 5 )
         {
            double clip_amp = get_real(iobuf);
            printf("      Number of pixels saturated or with amplitude clipped at %5.3f p.e.: %d\n", 
               clip_amp, n_sat);
         }
         else
            printf("      Number of pixels saturated or with clipped amplitude: %d\n", n_sat);
      }
   }
   printf("      Image amplitude: %f p.e.\n", get_real(iobuf));
   printf("      Image c.o.g. x, y = %f", get_real(iobuf)*(180./M_PI));
   printf(", %f deg\n", get_real(iobuf)*(180./M_PI));
   printf("      Major axis angle: %f deg\n", get_real(iobuf)*(180./M_PI));
   printf("      Length, width:");
   printf(" %f", get_real(iobuf)*(180./M_PI));
   printf(", %f deg\n", get_real(iobuf)*(180./M_PI));
   nhot = get_short(iobuf);
   printf("      Concentration for %d hottest pixels: %f\n",
      nhot, get_real(iobuf));

   if ( (flags & 0x100) )
   {
      printf("      Errors on x, y: %f", get_real(iobuf));
      printf(", %f\n", get_real(iobuf));
      printf("      Error on angle: %f deg\n", get_real(iobuf)*(180./M_PI));
      printf("      Errors on width, length: %f", get_real(iobuf));
      printf(", %f\n", get_real(iobuf));
   }

   if ( (flags & 0x200) )
   {
      printf("      Skewness: %f", get_real(iobuf));
      printf(" +- %f\n", get_real(iobuf));
      printf("      Kurtosis: %f", get_real(iobuf));
      printf(" +- %f\n", get_real(iobuf));
   }

   if ( (flags & 0x400) )
   {
      int i, num_hot = (item_header.version <= 5 ? get_short(iobuf) : get_scount32(iobuf));
      printf("      Amplitudes for %d hottest pixel:",num_hot);
      for (i=0; i<num_hot; i++)
         printf("\t%f",get_real(iobuf));
      printf("\n");
      if ( item_header.version >= 1 )
      {
         printf("      IDs of hottest pixels:");
         for (i=0; i<num_hot; i++)
            printf("\t%d",(item_header.version <= 5 ?
                  get_short(iobuf) : get_scount32(iobuf)) );
         printf("\n");
      }
   }

   if ( (flags & 0x800) && item_header.version >= 3 )
   {
      printf("      Pixel timing results:\n");
      printf("         Time slope (from peak pos.): %f ns/deg\n", 
         get_real(iobuf) * (M_PI/180.));
      printf("         Time r.m.s. residual: %f ns\n", get_real(iobuf));
      printf("         Pulse width 1: %f ns\n", get_real(iobuf));
      printf("         Pulse width 2: %f ns\n", get_real(iobuf));
      printf("         Rise time:     %f ns\n", get_real(iobuf));
   }

   return get_item_end(iobuf,&item_header);
}

/* ----------------------- write_hess_televent ------------------------ */
/**
 *  @short Write data for one telescope camera in eventio format.
 *
 *  Depending on the 'what' parameter, either sampled or
 *  summed pixel values are expected to be in the 'te' structure.
 *  Writing of image paramaters is another option.
*/  

int write_hess_televent (IO_BUFFER *iobuf, TelEvent *te, int what)
{
   IO_ITEM_HEADER item_header;
   int rc=0, ipix, iaux;
   AdcData *raw;
   ImgData *img;
   
   if ( iobuf == (IO_BUFFER *) NULL || te == NULL )
      return -1;
   
   /* If no data known, forget it */
   if ( !te->known )
      return 0;

   item_header.type = IO_TYPE_HESS_TELEVENT + 
     (unsigned) (te->tel_id%100 + 1000*(te->tel_id/100)); /* Data type */
   item_header.version = 1;             /* Version number 1 */
   item_header.ident = te->glob_count;
   put_item_begin(iobuf,&item_header);

   /* The header is always needed */
   if ( (rc = write_hess_televt_head(iobuf,te)) < 0 )
   {
      Warning("Writing telescope event header failed.\n");
      unput_item(iobuf,&item_header); /* Nothing to be written at all in case of any problem */
      return rc;
   }

   raw = te->raw;
   img = te->img;

   /* Raw data is optional. */
   if ( raw != NULL && raw->known && (what & (RAWDATA_FLAG|RAWSUM_FLAG)) != 0 )
   {
      if ( (te->readout_mode & 0xff) && (what & RAWDATA_FLAG) ) /* readout_mode is normally 0 (sum) or 1 (samples) or >=2 (both) */
      {
	 if ( raw->num_samples >= H_MAX_SLICES )
      	    raw->num_samples = H_MAX_SLICES;
         if ( (te->readout_mode & 0xff) >= 2 ) /* Both sum and samples */
         {
            int zero_sup_mode = raw->zero_sup_mode;
            /* Write both which makes only sense with some zero suppression */
            if ( raw->zero_sup_mode != 0 && (raw->zero_sup_mode & 0x20) == 0 )
               raw->zero_sup_mode |= 0x20; /* Implied zero suppression for sample mode data */
            if ( (te->readout_mode & 0xff) == 9 ) /* Not relying on proper cleaning */
            {
               /* Poor method of setting pixel significance from pixel timing no longer used */
               if ( te->pixtm != NULL && te->pixtm->known )
               {
                  for (ipix=0; ipix<raw->num_pixels; ipix++)
                  {
                     if ( te->pixtm->timval[ipix][0] >= 0. )
                        raw->significant[ipix] |= 0x20;
                  }
               }
               else /* No timing analysis applied, use significance bits from sum mode */
               {
                  for (ipix=0; ipix<raw->num_pixels; ipix++)
                  {
                     if ( raw->significant[ipix] )
                        raw->significant[ipix] |= 0x20;
                  }
               }
            }
            if ( (rc = write_hess_teladc_sums(iobuf,raw)) == 0 )
	       rc = write_hess_teladc_samples(iobuf,raw);
            raw->zero_sup_mode = zero_sup_mode; /* Reset temporary */
         }
         else /* Write only samples */
            rc = write_hess_teladc_samples(iobuf,raw);
      }
      else /* Write only the sums */
      {
         if ( (te->readout_mode & 0xff) ) /* We do have samples but do not want to write them */
         {
            /* Check for pixels with no sum value */
            for ( ipix=0; ipix<raw->num_pixels; ipix++ )
            {
               int sig = 0, igain;
               if ( raw->significant[ipix] )
               {
                  for ( igain=0; igain<raw->num_gains; igain++ )
                  {
                     /* Only pixels with non-zero sum in any gain considered significant */
                     if ( raw->adc_known[igain][ipix] && raw->adc_sum[igain][ipix] )
                        sig = 1;
                  }
               }
               raw->significant[ipix] = sig;
            }
         }
	 rc = write_hess_teladc_sums(iobuf,raw);
      }
      if ( rc < 0 )
      {
         Warning("Writing telescope event data failed.\n");
	 unput_item(iobuf,&item_header); /* Nothing to be written */
	 return rc;
      }
   }

   /* Pixel timing information (from online pulse shape analysis) is optional. */
   if ( te->pixtm != NULL && te->pixtm->known && (what & TIME_FLAG) != 0 )
   {
      rc = write_hess_pixtime(iobuf,te->pixtm);
      if ( rc < 0 )
      {
         Warning("Writing telescope pixel timing data failed.\n");
	 unput_item(iobuf,&item_header); /* Nothing to be written */
	 return rc;
      }
   }

   /* Calibrated pixel intensities instead of or in addition to raw data,
      typically just as the fall-back solution in case of no raw data. */
   if ( te->pixcal != NULL && te->pixcal->known && 
         ( (what & CALSUM_FLAG) || !(what & (RAWDATA_FLAG|RAWSUM_FLAG)) ||
           te->raw == NULL || (te->raw != NULL && te->raw->known==0) ) )
   {
      rc = write_hess_pixcalib(iobuf,te->pixcal);
      if ( rc < 0 )
      {
         Warning("Writing calibrated pixel intensities failed.\n");
	 unput_item(iobuf,&item_header); /* Nothing to be written */
	 return rc;
      }
   }

   /* Image data is an alternative to raw data */
   if ( img != NULL && img->known && (what & IMAGE_FLAG) != 0 )
   {
      int j;
      
      for ( j=0; j<te->num_image_sets; j++)
      {
	 rc = write_hess_telimage(iobuf,&img[j],what);
	 if ( rc < 0 )
	 {
            Warning("Writing telescope pixel image data failed.\n");
	    unput_item(iobuf,&item_header); /* Nothing to be written */
	    return rc;
	 }
      }
   }
   
   /* List of (individually) triggered pixels, no matter if coincident */
   if ( te->trigger_pixels.pixels > 0 )
      write_hess_pixel_list(iobuf,&te->trigger_pixels,te->tel_id);
   /* List of image pixels, if any */
   if ( te->image_pixels.pixels > 0 )
      write_hess_pixel_list(iobuf,&te->image_pixels,te->tel_id);

   /* Pixel trigger (discriminator/comparator) times w.r.t. telescope trigger */
   if ( te->pixeltrg_time.known && te->pixeltrg_time.num_times > 0 )
      write_hess_pixeltrg_time(iobuf,&te->pixeltrg_time);

   /* Auxiliary signal traces for, debugging and demonstration purposes mainly */
   for ( iaux=0; iaux < MAX_AUX_TRACE_D; iaux++ )
   {
      if ( te->aux_trace_d[iaux].known )
         write_hess_aux_trace_digital(iobuf,&te->aux_trace_d[iaux]);
   }

   for ( iaux=0; iaux < MAX_AUX_TRACE_A; iaux++ )
   {
      if ( te->aux_trace_a[iaux].known )
         write_hess_aux_trace_analog(iobuf,&te->aux_trace_a[iaux]);
   }

   return put_item_end(iobuf,&item_header);
}

/* ----------------------- read_hess_televent ------------------------ */
/**
 *  Read data for one telescope camera in eventio format.
*/  

int read_hess_televent (IO_BUFFER *iobuf, TelEvent *te, int what)
{
   IO_ITEM_HEADER item_header, sub_item_header;
   int rc;
   AdcData *raw;
   ImgData *img;
   int tel_id;
   int tel_img = 0;
   int iaux;
   static int w_sum=0, w_samp=0, w_pixtm=0, w_pixcal=0;

   if ( iobuf == (IO_BUFFER *) NULL || te == NULL )
      return -1;

   te->known = 0;
   te->readout_mode = 0;

   item_header.type = 0;  /* No data type this time */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   tel_id = (item_header.type - IO_TYPE_HESS_TELEVENT)%100 +
            100 * ((item_header.type - IO_TYPE_HESS_TELEVENT)/1000);
   if ( tel_id < 0 || tel_id != te->tel_id )
   {
      Warning("Not a telescope event block or one for the wrong telescope");
      get_item_end(iobuf,&item_header);
      return -1;
   }
   if ( item_header.version > 1 )
   {
      fprintf(stderr,"Unsupported telescope event version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   te->glob_count = item_header.ident;

   if ( (raw = te->raw) != NULL )
      raw->known = 0;
   if ( te->pixtm != NULL )
      te->pixtm->known = 0;
   if ( (img = te->img) != NULL )
   {
      int j;
      for (j=0; j<te->num_image_sets; j++)
      	 img[j].known = 0;
   }
   te->pixeltrg_time.known = 0;

   /* Telescope-specific event header is always used */
   if ( (rc = read_hess_televt_head(iobuf,te)) < 0 )
   {
      get_item_end(iobuf,&item_header);
      return rc;
   }

   /* Pixel lists only available since version 1 */
   te->trigger_pixels.pixels = te->image_pixels.pixels = 0;

   for (;;)
   {
      int nt = next_subitem_type(iobuf);
      rc = -9;

      switch ( nt )
      {
         case IO_TYPE_HESS_TELADCSUM:
            if ( (what & (RAWDATA_FLAG|RAWSUM_FLAG)) == 0 || raw == NULL )
            {
               if ( w_sum++ < 1 )
                  Warning("Telescope raw data ADC sums not selected to be read");
               rc = skip_subitem(iobuf);
               continue;
            }
            rc = read_hess_teladc_sums(iobuf,raw);
	    te->readout_mode = 0;     /* ADC sums */
            if ( rc == 0 )
	       raw->known = 1;
            raw->tel_id = te->tel_id; /* For IDs beyond 31, bits may be missing */
            break;

         case IO_TYPE_HESS_TELADCSAMP:
            if ( (what & RAWDATA_FLAG) == 0 || raw == NULL )
            {
               if ( w_samp++ < 1 )
                  Warning("Telescope raw data ADC samples not selected to be read");
               rc = skip_subitem(iobuf);
               continue;
            }
            if ( raw->known ) /* Preceded by sum data? */
               te->readout_mode = 2; /* sum + samples (perhaps different zero suppression) */
            else
            {
               adc_reset(raw); /* Do we need that? */
               te->readout_mode = 1; /* ADC samples, sums usually rebuilt */
            }
	    rc = read_hess_teladc_samples(iobuf,raw,what);
            if ( rc == 0 )
            {
	       raw->known |= 2;
            }
            raw->tel_id = te->tel_id; /* For IDs beyond 31, bits may be missing (?) */
            break;

         case IO_TYPE_HESS_PIXELTIMING:
            if ( te->pixtm == NULL || (what & TIME_FLAG) == 0 )
            {
               if ( w_pixtm++ < 1 )
                  Warning("Telescope pixel timing data not selected to be read");
               rc = skip_subitem(iobuf);
               continue;
            }
            rc = read_hess_pixtime(iobuf,te->pixtm);
            break;

         case IO_TYPE_HESS_PIXELCALIB:
            if ( te->pixcal == NULL )
            {
               if ( w_pixcal++ < 1 )
                  Warning("Telescope calibrated pixel intensities found, allocating structures.");
               if ( (te->pixcal = 
                      (PixelCalibrated *) calloc(1,sizeof(PixelCalibrated))) == NULL )
               {
                  Warning("Not enough memory for PixelCalibrated");
                  break;
               }
               te->pixcal->tel_id = tel_id;
            }
            rc = read_hess_pixcalib(iobuf,te->pixcal);
            break;

         case IO_TYPE_HESS_TELIMAGE:
            if ( img == NULL || (what & IMAGE_FLAG) == 0 )
               break;
      	    if ( tel_img >= te->max_image_sets )
	    {
	       Warning("Not enough space to read all image sets");
	       break;
	    }
	    if ( (rc = read_hess_telimage(iobuf,&img[tel_img])) == 0 )
	    {
	       img[tel_img].known = 1;
	       tel_img++;
	    }
            te->num_image_sets = tel_img;
            break;

         case IO_TYPE_HESS_PIXELLIST:
         {
            long id = sub_item_header.ident = next_subitem_ident(iobuf);
            int code = id / 1000000;
            int tid  = id % 1000000;
            if ( code == 0 && tid == te->tel_id )
            {
               if ( (rc = read_hess_pixel_list(iobuf,&te->trigger_pixels,&tid)) < 0 )
               {
	          get_item_end(iobuf,&item_header);
	          return rc;
               }
            }
            else if ( code == 1 && tid == te->tel_id )
            {
               if ( (rc = read_hess_pixel_list(iobuf,&te->image_pixels,&tid)) < 0 )
               {
	          get_item_end(iobuf,&item_header);
	          return rc;
               }
               /* Fix for missing number of pixels in image of older data format: */
               if ( te->img != NULL && te->img[0].known && te->img[0].pixels == 0 )
                  te->img[0].pixels = te->image_pixels.pixels;
            }
#if defined(H_MAX_TRG) && (H_MAX_TRG > 1)
            else if ( code >= 10 && code < 10 + H_MAX_TRG && tid == te->tel_id )
            {
               int ixtrg = code - 10;
               if ( (rc = read_hess_pixel_list(iobuf,&te->xtrigger_pixels[ixtrg],&tid)) < 0 )
               {
	          get_item_end(iobuf,&item_header);
	          return rc;
               }
            }
#endif
            else
            {
               fprintf(stderr,"Skipping pixel list of type %d for telescope %d\n", code, tid);
               skip_subitem(iobuf);
            }
         }
            break;

         case IO_TYPE_HESS_PIXELTRG_TM:
            te->pixeltrg_time.tel_id = te->tel_id;
            if ( ( rc = read_hess_pixeltrg_time(iobuf,&te->pixeltrg_time) ) < 0 )
            {
	       get_item_end(iobuf,&item_header);
	       return rc;
            }
            break;

         case IO_TYPE_HESS_AUX_DIGITAL_TRACE:
            iaux = item_header.ident;
            if ( iaux >= 0 && iaux < MAX_AUX_TRACE_D )
            {
               if ( (rc = read_hess_aux_trace_digital(iobuf,&te->aux_trace_d[iaux])) < 0 )
               {
	          get_item_end(iobuf,&item_header);
	          return rc;
               }
            }
            break;

         case IO_TYPE_HESS_AUX_ANALOG_TRACE:
            iaux = item_header.ident;
            if ( iaux >= 0 && iaux < MAX_AUX_TRACE_A )
            {
               if ( (rc = read_hess_aux_trace_analog(iobuf,&te->aux_trace_a[iaux])) < 0 )
               {
	          get_item_end(iobuf,&item_header);
	          return rc;
               }
            }
            break;

         default:
            if ( nt > 0 )
            {
               fprintf(stderr,"Skipping telescope event sub-item of type %d for telescope %d\n", 
                  nt, te->tel_id);
               rc = skip_subitem(iobuf);
            }
            else
               return get_item_end(iobuf,&item_header); 
      }

      if ( rc < 0 )
      {
	 get_item_end(iobuf,&item_header);
	 return rc;
      }

      te->known = 1;
   }

   return get_item_end(iobuf,&item_header);
}

/* ----------------------- print_hess_televent ------------------------ */
/**
 *  Print data for one telescope camera in eventio format.
*/  

int print_hess_televent (IO_BUFFER *iobuf)
{
   IO_ITEM_HEADER item_header;
   int rc;
   int tel_id;

   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;

   item_header.type = 0;  /* No data type this time */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   tel_id = (item_header.type - IO_TYPE_HESS_TELEVENT)%100 +
            100 * ((item_header.type - IO_TYPE_HESS_TELEVENT)/1000);
   if ( tel_id < 0 )
   {
      Warning("Not a telescope event block");
      get_item_end(iobuf,&item_header);
      return -1;
   }
   if ( item_header.version > 2 )
   {
      fprintf(stderr,"Unsupported telescope event version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   printf("  Telescope data event %ld for telescope %d:\n",
       item_header.ident, tel_id);

   /* Telescope-specific event header is always used */
   if ( (rc = print_hess_televt_head(iobuf)) < 0 )
   {
      get_item_end(iobuf,&item_header);
      return rc;
   }

   for (;;)
   {
      int nt = next_subitem_type(iobuf);
      rc = -9;

      switch ( nt )
      {
         case IO_TYPE_HESS_TELADCSUM:
            rc = print_hess_teladc_sums(iobuf);
            break;

         case IO_TYPE_HESS_TELADCSAMP:
            rc = print_hess_teladc_samples(iobuf);
            break;

         case IO_TYPE_HESS_PIXELTIMING:
            rc = print_hess_pixtime(iobuf);
            break;

         case IO_TYPE_HESS_PIXELCALIB:
            rc = print_hess_pixcalib(iobuf);
            break;

         case IO_TYPE_HESS_TELIMAGE:
            rc = print_hess_telimage(iobuf);
            break;

         case IO_TYPE_HESS_PIXELLIST:
            rc = print_hess_pixel_list(iobuf);
            break;

         case IO_TYPE_HESS_PIXELTRG_TM:
            print_hess_pixeltrg_time(iobuf);
            break;

         case IO_TYPE_HESS_AUX_DIGITAL_TRACE:
            print_hess_aux_trace_digital(iobuf);

         case IO_TYPE_HESS_AUX_ANALOG_TRACE:
            print_hess_aux_trace_analog(iobuf);

         default:
            if ( nt > 0 )
            {
               fprintf(stderr,"Skipping telescope event sub-item of type %d for telescope %d\n", 
                  nt, tel_id);
               rc = skip_subitem(iobuf);
            }
            else
               return get_item_end(iobuf,&item_header); 
            break;
      }

      if ( rc < 0 )
      {
	 get_item_end(iobuf,&item_header);
	 return rc;
      }
   }

   return get_item_end(iobuf,&item_header);
}

/* ----------------------- write_hess_shower ------------------------ */
/**
 *  @short Write reconstructed shower parameters in eventio format.
 *
 *  Note that the actual amount of data stored depends on what is
 *  actually available (as indicated in the 'result_bits').
*/  

int write_hess_shower (IO_BUFFER *iobuf, ShowerParameters *sp)
{
   IO_ITEM_HEADER item_header;

   if ( iobuf == (IO_BUFFER *) NULL || sp == NULL )
      return -1;

   /* If no data known, forget it */
   if ( !sp->known )
      return 0;

   item_header.type = IO_TYPE_HESS_SHOWER;  /* Data type */
   item_header.version = 1;             /* Version 1 */
   if ( sp->num_img > 0 && sp->img_list[0] > 0 )
      item_header.version = 2;          /* or version 2 */
   item_header.ident = sp->result_bits;
   put_item_begin(iobuf,&item_header);
   
   put_short(sp->num_trg,iobuf);
   put_short(sp->num_read,iobuf);
   put_short(sp->num_img,iobuf);
   put_int32(sp->img_pattern,iobuf);    /* New in version 1 */

   if ( item_header.version >= 2 )      /* New in version 2 */
      put_vector_of_int(sp->img_list,sp->num_img,iobuf);

   if ( (sp->result_bits & 0x01) )
   {
      put_real(sp->Az,iobuf);
      put_real(sp->Alt,iobuf);
   }
   if ( (sp->result_bits & 0x02) )
   {
      put_real(sp->err_dir1,iobuf);
      put_real(sp->err_dir2,iobuf);
      put_real(sp->err_dir3,iobuf);
   }
   if ( (sp->result_bits & 0x04) )
   {
      put_real(sp->xc,iobuf);
      put_real(sp->yc,iobuf);
   }
   if ( (sp->result_bits & 0x08) )
   {
      put_real(sp->err_core1,iobuf);
      put_real(sp->err_core2,iobuf);
      put_real(sp->err_core3,iobuf);
   }
   if ( (sp->result_bits & 0x10) )
   {
      put_real(sp->mscl,iobuf);
      put_real(sp->mscw,iobuf);
   }
   if ( (sp->result_bits & 0x20) )
   {
      put_real(sp->err_mscl,iobuf);
      put_real(sp->err_mscw,iobuf);
   }
   if ( (sp->result_bits & 0x40) )
      put_real(sp->energy,iobuf);
   if ( (sp->result_bits & 0x80) )
      put_real(sp->err_energy,iobuf);
   if ( (sp->result_bits & 0x0100) )
      put_real(sp->xmax,iobuf);
   if ( (sp->result_bits & 0x0200) )
      put_real(sp->err_xmax,iobuf);

   return put_item_end(iobuf,&item_header);
}

/* ----------------------- read_hess_shower ------------------------ */
/**
 *  Read reconstructed shower parameters in eventio format.
*/  

int read_hess_shower (IO_BUFFER *iobuf, ShowerParameters *sp)
{
   IO_ITEM_HEADER item_header;
   int rc;
   
   if ( iobuf == (IO_BUFFER *) NULL || sp == NULL )
      return -1;
   
   sp->known = 0;
   
   item_header.type = IO_TYPE_HESS_SHOWER;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 2 )
   {
      fprintf(stderr,"Unsupported reconstructed shower version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   sp->result_bits = item_header.ident;
   
   sp->num_trg = get_short(iobuf);
   sp->num_read = get_short(iobuf);
   sp->num_img = get_short(iobuf);
   if ( item_header.version >= 1 )
      sp->img_pattern = get_int32(iobuf);
   else
      sp->img_pattern = 0;
   if ( item_header.version >= 2 )
      get_vector_of_int(sp->img_list,sp->num_img,iobuf);
   if ( (sp->result_bits & 0x01) )
   {
      sp->Az = get_real(iobuf);
      sp->Alt = get_real(iobuf);
   }
   else
      sp->Az = sp->Alt = 0.;
   if ( (sp->result_bits & 0x02) )
   {
      sp->err_dir1 = get_real(iobuf);
      sp->err_dir2 = get_real(iobuf);
      sp->err_dir3 = get_real(iobuf);
   }
   else
      sp->err_dir1 = sp->err_dir2 = sp->err_dir3 = 0.;
   if ( (sp->result_bits & 0x04) )
   {
      sp->xc = get_real(iobuf);
      sp->yc = get_real(iobuf);
   }
   else
      sp->xc = sp->yc = 0.;
   if ( (sp->result_bits & 0x08) )
   {
      sp->err_core1 = get_real(iobuf);
      sp->err_core2 = get_real(iobuf);
      sp->err_core3 = get_real(iobuf);
   }
   else
      sp->err_core1 = sp->err_core2 = sp->err_core3 = 0.;
   if ( (sp->result_bits & 0x10) )
   {
      sp->mscl = get_real(iobuf);
      sp->mscw = get_real(iobuf);
   }
   else
      sp->mscl = sp->mscw = -1;
   if ( (sp->result_bits & 0x20) )
   {
      sp->err_mscl = get_real(iobuf);
      sp->err_mscw = get_real(iobuf);
   }
   else
      sp->err_mscl = sp->err_mscw = 0.;
   if ( (sp->result_bits & 0x40) )
      sp->energy = get_real(iobuf);
   else
      sp->energy = -1.;
   if ( (sp->result_bits & 0x80) )
      sp->err_energy = get_real(iobuf);
   else
      sp->err_energy = 0.;
   sp->xmax = 0.;
   if ( (sp->result_bits & 0x0100) )
      sp->xmax = get_real(iobuf);
   sp->err_xmax = 0.;
   if ( (sp->result_bits & 0x0200) )
      sp->err_xmax = get_real(iobuf);

   sp->known = 1;

   return get_item_end(iobuf,&item_header);
}

/* ----------------------- print_hess_shower ------------------------ */
/**
 *  Print reconstructed shower parameters in eventio format.
*/  

int print_hess_shower (IO_BUFFER *iobuf)
{
   IO_ITEM_HEADER item_header;
   int rc;
   int result_bits, nimg;
   
   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;
   
   item_header.type = IO_TYPE_HESS_SHOWER;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 2 )
   {
      fprintf(stderr,"Unsupported reconstructed shower version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }
   printf("  Reconstructed shower:\n");

   result_bits = item_header.ident;
   
   printf("    Telescopes triggered: %d\n", get_short(iobuf));
   printf("    Telescopes read out:  %d\n", get_short(iobuf));
   printf("    Telescope images:     %d\n",  nimg=get_short(iobuf));
   /* Version 1 has a bit pattern of contributing telescopes. */
   if ( item_header.version >= 1 )
      printf("    Image pattern: %d\n", get_int32(iobuf));
   /* Version 2 even has a list of them (useful for large arrays). */
   if ( item_header.version >= 2 )
   {
      int i;
      printf("    Images used from these telescopes: ");
      if ( nimg > 0 )
         printf("%d", get_short(iobuf));
      for ( i=1; i<nimg; i++)
         printf(", %d", get_short(iobuf));
      printf("\n");
   }
   if ( (result_bits & 0x01) )
   {
      printf("    Azimuth:  %f deg\n", get_real(iobuf)*(180./M_PI));
      printf("    Altitude: %f deg\n", get_real(iobuf)*(180./M_PI));
   }
   if ( (result_bits & 0x02) )
   {
      printf("    Direction error matrix elements: %f,", get_real(iobuf));
      printf(" %f,", get_real(iobuf));
      printf(" %f\n", get_real(iobuf));
   }
   if ( (result_bits & 0x04) )
   {
      printf("    Core position x, y: %f,", get_real(iobuf));
      printf(" %f m\n", get_real(iobuf));
   }
   if ( (result_bits & 0x08) )
   {
      printf("    Core position error matrix elements: %f,", get_real(iobuf));
      printf(" %f,", get_real(iobuf));
      printf(" %f\n", get_real(iobuf));
   }
   if ( (result_bits & 0x10) )
   {
      printf("    Mean scaled length, width: %f,", get_real(iobuf));
      printf(" %f\n", get_real(iobuf));
   }
   if ( (result_bits & 0x20) )
   {
      printf("    Errors on mean scaled length, width: %f,", get_real(iobuf));
         printf(" %f\n", get_real(iobuf));
   }
   if ( (result_bits & 0x40) )
      printf("    Energy: %g TeV\n", get_real(iobuf));
   if ( (result_bits & 0x80) )
      printf("    Energy error: %g TeV\n", get_real(iobuf));
   if ( (result_bits & 0x0100) )
      printf("    Shower maximum: %f g/cm^2\n", get_real(iobuf));
   if ( (result_bits & 0x0200) )
      printf("    Shower maximum error: %f g/cm^2\n", get_real(iobuf));

   return get_item_end(iobuf,&item_header);
}

/* --------------------- write_hess_event -------------------- */
/**
 *  @short Write the full array data of one event in eventio format.
 *
 *  This can include raw data, tracking data, and central trigger
 *  data as gathered from the individual computers, as well as
 *  reconstructed parameters (image parameters, shower parameters).
*/  

int write_hess_event (IO_BUFFER *iobuf, FullEvent *ev, int what)
{
   IO_ITEM_HEADER item_header;
   int j, rc=0;

   if ( iobuf == (IO_BUFFER *) NULL || ev == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_EVENT;  /* Data type */
   item_header.version = 0;             /* Version 0 (test) */
   if ( ev->num_tel > 0 && ev->central.num_teltrg == 0 && ev->central.num_teldata == 0 )
   {
      int k = 0;
      /* Reconstruct basic data in central trigger block */
      for (j=0; j<ev->num_tel; j++)
      {
         if ( ev->teldata[j].known )
         {
            ev->central.teltrg_type_mask[k] = 0;
            ev->central.teltrg_time[k] = 0.;
            ev->central.teltrg_list[k] = ev->teldata[j].tel_id;
            ev->central.teldata_list[k] = ev->teldata[j].tel_id;
            k++;
         }
      }
      ev->central.num_teltrg = ev->central.num_teldata = k;
      /* Recovered central data is identified by zero time values. */
      reset_htime(&ev->central.cpu_time);
      reset_htime(&ev->central.gps_time);
   }
   if ( ev->num_tel > 1 )
      item_header.ident = ev->central.glob_count;
   else
      item_header.ident = ev->teldata[0].loc_count;
   put_item_begin(iobuf,&item_header);

   /* Central data is written for every event in multi-telescope runs */
   /* if ( ev->num_tel > 1 ) */ /* only multi-telescope events */
   /* if ( ev->central.num_teltrg > 0 || ev->central.num_teldata > 0 ) */ /* only non-empty events */
   /* Central data is now written for every event as it may provide data on trigger types. */
   rc = write_hess_centralevent(iobuf,&ev->central);
   if ( rc != 0 )
   {
      Warning("Abort write_hess_event() due to problem in write_hess_centralevent()\n");
      unput_item(iobuf,&item_header);
      return rc;
   }
   /* Raw and/or image data is written on demand only */
   if ( (what & (IMAGE_FLAG | RAWDATA_FLAG | RAWSUM_FLAG | TIME_FLAG)) )
   {
      for (j=0; j<ev->num_tel; j++)
      {
      	 if ( ev->teldata[j].known )
         {
	    rc = write_hess_televent(iobuf,&ev->teldata[j],what);
            if ( rc != 0 )
            {
               Warning("Abort write_hess_event() due to problem in write_hess_televent()\n");
               unput_item(iobuf,&item_header);
               return rc;
            }
         }
      }
   }
   /* Tracking data is written on demand or when raw or image data is written */
   if ( (what & (IMAGE_FLAG | RAWDATA_FLAG | RAWSUM_FLAG | TIME_FLAG | TRACKDATA_FLAG)) )
   {
      for (j=0; j<ev->num_tel; j++)
      {
	 if ( (ev->teldata[j].known || (what & TRACKDATA_FLAG)) &&
	      (ev->trackdata[j].raw_known || ev->trackdata[j].cor_known) )
         {
	    rc = write_hess_trackevent(iobuf,&ev->trackdata[j]);
            if ( rc != 0 )
            {
               Warning("Abort write_hess_event() due to problem in write_hess_trackevent()\n");
               unput_item(iobuf,&item_header);
               return rc;
            }
         }
      }
   }
   /* Shower data is written on demand only */
   if ( (what & (SHOWER_FLAG)) && ev->shower.known )
   {
      rc = write_hess_shower(iobuf,&ev->shower);
      if ( rc != 0 )
      {
         Warning("Abort write_hess_event() due to problem in write_hess_shower()\n");
         unput_item(iobuf,&item_header);
         return rc;
      }
   }

   return put_item_end(iobuf,&item_header);
}

/* --------------------- read_hess_event -------------------- */
/**
 *  Read the full array data of one event in eventio format.
*/  

int read_hess_event (IO_BUFFER *iobuf, FullEvent *ev, int what)
{
   IO_ITEM_HEADER item_header;
   int type, tel_id, itel, id, rc, j;
   
   if ( iobuf == (IO_BUFFER *) NULL || ev == NULL )
      return -1;
      
   item_header.type = IO_TYPE_HESS_EVENT;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version != 0 )
   {
      fprintf(stderr,"Unsupported event data version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }
   id = item_header.ident;

   assert(ev->num_tel <= H_MAX_TEL);
   
   ev->central.glob_count = ev->central.teltrg_pattern = 
      ev->central.teldata_pattern = 
      ev->central.num_teltrg = ev->central.num_teldata = 0;
   reset_htime(&ev->central.cpu_time);
   reset_htime(&ev->central.gps_time);
   ev->num_teldata = 0;
   for ( j=0; j<ev->num_tel; j++ )
   {
      ev->teldata[j].known = 0;
      ev->trackdata[j].raw_known = ev->trackdata[j].cor_known = 0;
   }
   ev->shower.known = 0;
   
   while ( (type = next_subitem_type(iobuf)) > 0 )
   {
      if ( type == IO_TYPE_HESS_CENTEVENT )
      {
	 if ( (rc = read_hess_centralevent(iobuf,&ev->central)) < 0 )
	 {
	    get_item_end(iobuf,&item_header);
	    return rc;
	 }
      }
#if ( H_MAX_TEL > 100 )
      else if ( type >= IO_TYPE_HESS_TRACKEVENT &&
         type%1000 < (IO_TYPE_HESS_TRACKEVENT%1000)+100 &&
      	 (type-IO_TYPE_HESS_TRACKEVENT)%100 +
         100*((type-IO_TYPE_HESS_TRACKEVENT)/1000) <= H_MAX_TEL )
#else
      else if ( type >= IO_TYPE_HESS_TRACKEVENT &&
      	 type <= IO_TYPE_HESS_TRACKEVENT + H_MAX_TEL )
#endif
      {
      	 tel_id = (type - IO_TYPE_HESS_TRACKEVENT)%100 +
                  100*((type-IO_TYPE_HESS_TRACKEVENT)/1000);
	 if ( (itel = find_tel_idx(tel_id)) < 0 )
	 {
	    Warning("Telescope number out of range for tracking data");
            get_item_end(iobuf,&item_header);
	    return -1;
	 }
      	 if ( (rc = read_hess_trackevent(iobuf,&ev->trackdata[itel])) < 0 )
	 {
	    get_item_end(iobuf,&item_header);
	    return rc;
	 }
      }
#if ( H_MAX_TEL > 100 )
      else if ( type >= IO_TYPE_HESS_TELEVENT &&
         type%1000 < (IO_TYPE_HESS_TELEVENT%1000)+100 &&
      	 (type-IO_TYPE_HESS_TELEVENT)%100 +
         100*((type-IO_TYPE_HESS_TELEVENT)/1000) <= H_MAX_TEL )
#else
      else if ( type >= IO_TYPE_HESS_TELEVENT &&
      	 type <= IO_TYPE_HESS_TELEVENT + H_MAX_TEL )
#endif
      {
      	 tel_id = (type - IO_TYPE_HESS_TELEVENT)%100 +
                  100*((type-IO_TYPE_HESS_TELEVENT)/1000);
	 if ( (itel = find_tel_idx(tel_id)) < 0 )
	 {
	    Warning("Telescope number out of range for telescope event data");
            get_item_end(iobuf,&item_header);
	    return -1;
	 }
      	 if ( (rc = read_hess_televent(iobuf,&ev->teldata[itel],what)) < 0 )
	 {
	    get_item_end(iobuf,&item_header);
	    return rc;
	 }
         if ( ev->num_teldata < H_MAX_TEL && ev->teldata[itel].known )
         {
            ev->teldata_list[ev->num_teldata++] = ev->teldata[itel].tel_id;
         }
      }
      else if ( type == IO_TYPE_HESS_SHOWER )
      {
      	 if ( (rc = read_hess_shower(iobuf,&ev->shower)) < 0 )
	 {
	    get_item_end(iobuf,&item_header);
	    return rc;
	 }
      }
      else
      {
      	 char msg[200];
	 sprintf(msg,"Invalid item type %d in event %d.",type,id);
	 Warning(msg);
	 get_item_end(iobuf,&item_header);
	 return -1;
      }
   }

   /* Fill in the list of telescopes not present in earlier versions */
   /* of the central trigger block. Assumes only triggered telescopes */
   /* are actually read out or that the array has no more than 16 telescopes. */
   if ( ev->central.num_teltrg == 0 && ev->central.teltrg_pattern != 0 )
   {
      int nt=0, nd=0;
      /* For small arrays we have all the information in the bitmasks. */
      if ( ev->num_tel <= 16 )
      {
         for (itel=0; itel<ev->num_tel && itel<16; itel++)
         {
            if ( (ev->central.teltrg_pattern & (1<<itel)) != 0 )
            {
               ev->central.teltrg_time[nt] = 0.; /* Not available, set to zero */
               ev->central.teltrg_list[nt] = ev->teldata[itel].tel_id;
               nt++;
            }
            if ( (ev->central.teldata_pattern & (1<<itel)) != 0 )
            {
               ev->central.teldata_list[nd] = ev->teldata[itel].tel_id;
               nd++;
            }
         }
      }
      /* For larger arrays we assume only triggered telescopes were read out. */
      else
      {
         for (j=0; j<ev->num_teldata; j++)
         {
            tel_id = ev->teldata_list[j];
	    if ( (itel = find_tel_idx(tel_id)) < 0 )
               continue;
            if ( ev->teldata[itel].known )
            {
               ev->central.teltrg_time[nt] = 0.;
               ev->central.teltrg_list[nt++] = ev->teldata[itel].tel_id;
               ev->central.teldata_list[nd++] = ev->teldata[itel].tel_id;
            }
         }
      }
      ev->central.num_teltrg = nt;
      ev->central.num_teldata = nd;
   }

   /* Some programs may require basic central trigger data even for mono data
      where historically no such data was stored. Replicate from the list of telescopes with data. */
   if ( ev->num_tel > 0 && ev->central.num_teltrg == 0 && ev->central.num_teldata == 0 )
   {
      int k = 0;
      /* Reconstruct basic data in central trigger block */
      for (j=0; j<ev->num_tel; j++)
      {
         if ( ev->teldata[j].known )
         {
            ev->central.teltrg_type_mask[k] = 0;
            ev->central.teltrg_time[k] = 0.;
            ev->central.teltrg_list[k] = ev->teldata[j].tel_id;
            ev->central.teldata_list[k] = ev->teldata[j].tel_id;
            k++;
         }
      }
      ev->central.num_teltrg = ev->central.num_teldata = k;
      /* Recovered central data is identified by zero time values. */
      reset_htime(&ev->central.cpu_time);
      reset_htime(&ev->central.gps_time);
   }

   return get_item_end(iobuf,&item_header);
}

/* --------------------- print_hess_event -------------------- */
/**
 *  Print the full array data of one event in eventio format.
*/

int print_hess_event (IO_BUFFER *iobuf)
{
   IO_ITEM_HEADER item_header;
   int type, tel_id, itel, id, rc;
   
   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;
      
   item_header.type = IO_TYPE_HESS_EVENT;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version != 0 )
   {
      fprintf(stderr,"Unsupported event data version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }
   id = item_header.ident;

   printf("\nEvent %d:\n", id);

   while ( (type = next_subitem_type(iobuf)) > 0 )
   {
      if ( type == IO_TYPE_HESS_CENTEVENT )
      {
	 if ( (rc = print_hess_centralevent(iobuf)) < 0 )
	 {
	    get_item_end(iobuf,&item_header);
	    return rc;
	 }
      }
#if ( H_MAX_TEL > 100 )
      else if ( type >= IO_TYPE_HESS_TRACKEVENT &&
         type%1000 < (IO_TYPE_HESS_TRACKEVENT%1000)+100 &&
      	 (type-IO_TYPE_HESS_TRACKEVENT)%100 +
         100*((type-IO_TYPE_HESS_TRACKEVENT)/1000) <= H_MAX_TEL )
#else
      else if ( type >= IO_TYPE_HESS_TRACKEVENT &&
      	 type <= IO_TYPE_HESS_TRACKEVENT + H_MAX_TEL )
#endif
      {
      	 tel_id = (type - IO_TYPE_HESS_TRACKEVENT)%100 +
                  100*((type-IO_TYPE_HESS_TRACKEVENT)/1000);
	 if ( (itel = find_tel_idx(tel_id)) < 0 )
	 {
	    Warning("Telescope number out of range for tracking data");
            get_item_end(iobuf,&item_header);
	    return -1;
	 }
      	 if ( (rc = print_hess_trackevent(iobuf)) < 0 )
	 {
	    get_item_end(iobuf,&item_header);
	    return rc;
	 }
      }
#if ( H_MAX_TEL > 100 )
      else if ( type >= IO_TYPE_HESS_TELEVENT &&
         type%1000 < (IO_TYPE_HESS_TELEVENT%1000)+100 &&
      	 (type-IO_TYPE_HESS_TELEVENT)%100 +
         100*((type-IO_TYPE_HESS_TELEVENT)/1000) <= H_MAX_TEL )
#else
      else if ( type >= IO_TYPE_HESS_TELEVENT &&
      	 type <= IO_TYPE_HESS_TELEVENT + H_MAX_TEL )
#endif
      {
      	 tel_id = (type - IO_TYPE_HESS_TELEVENT)%100 +
                  100*((type-IO_TYPE_HESS_TELEVENT)/1000);
	 if ( (itel = find_tel_idx(tel_id)) < 0 )
	 {
	    Warning("Telescope number out of range for telescope event data");
            get_item_end(iobuf,&item_header);
	    return -1;
	 }
#if 1
      	 if ( (rc = print_hess_televent(iobuf)) < 0 )
	 {
	    get_item_end(iobuf,&item_header);
	    return rc;
	 }
#else
         printf("  CT%d has televent block\n", tel_id);
         skip_subitem(iobuf);
#endif
      }
      else if ( type == IO_TYPE_HESS_SHOWER )
      {
#if 1
      	 if ( (rc = print_hess_shower(iobuf)) < 0 )
	 {
	    get_item_end(iobuf,&item_header);
	    return rc;
	 }
#else
         printf("  Has shower block\n");
         skip_subitem(iobuf);
#endif
      }
      else
      {
      	 char msg[200];
	 sprintf(msg,"Invalid item type %d in event %d.",type,id);
	 Warning(msg);
	 get_item_end(iobuf,&item_header);
	 return -1;
      }
   }

   return get_item_end(iobuf,&item_header);
}

/* ------------------- write_hess_calib_event -------------------- */
/**
 *  @short Write a calibration event (pedestal, laser, led, ...) as
 *         an encapsulated raw data event.
 */
 
int write_hess_calib_event (IO_BUFFER *iobuf, FullEvent *ev, int what, int type)
{
   IO_ITEM_HEADER item_header;
   
   if ( iobuf == (IO_BUFFER *) NULL || ev == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_CALIBEVENT;  /* Data type */
   item_header.version = 0;             /* Version 0 (test) */
   item_header.ident = type;

#ifdef NO_CALIBRATION_WRAPPING
   return write_hess_event(iobuf,ev,what);
#else
   put_item_begin(iobuf,&item_header);
   
   write_hess_event(iobuf,ev,what);

   return put_item_end(iobuf,&item_header);
#endif
}

/* ------------------- read_hess_calib_event -------------------- */
/**
 *  @short Read a calibration event (pedestal, laser, led, ...) as
 *         an encapsulated raw data event.
 */
 
int read_hess_calib_event (IO_BUFFER *iobuf, FullEvent *ev, int what, int *ptype)
{
   IO_ITEM_HEADER item_header;
   int type, rc;
   
   if ( iobuf == (IO_BUFFER *) NULL || ev == NULL )
      return -1;
      
   item_header.type = IO_TYPE_HESS_CALIBEVENT;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version != 0 )
   {
      fprintf(stderr,"Unsupported calibevent data version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }
   type = item_header.ident;
   if ( ptype != NULL )
      *ptype = type;

   read_hess_event(iobuf,ev,what);   

   return get_item_end(iobuf,&item_header);
}

/* ------------------- print_hess_calib_event -------------------- */
/**
 *  @short Print a calibration event (pedestal, laser, led, ...) as
 *         an encapsulated raw data event.
 */

int print_hess_calib_event (IO_BUFFER *iobuf)
{
   IO_ITEM_HEADER item_header;
   int type, rc;

   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_CALIBEVENT;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version != 0 )
   {
      fprintf(stderr,"Unsupported calibevent data version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }
   type = item_header.ident;
   printf("\nCalibration event of type %d:\n", type);

   print_hess_event(iobuf); /* print contained event */   

   return get_item_end(iobuf,&item_header);
}

/* --------------------- write_hess_mc_shower -------------------- */
/**
 *  @short Write MC data for one simulated shower in eventio format.
 *
 *  This includes data from the shower simulation itself,
 *  independent of how many times a shower is used and where the
 *  core position is shifted to with respect to the telescope array.
*/  

int write_hess_mc_shower (IO_BUFFER *iobuf, MCShower *mcs)
{
   IO_ITEM_HEADER item_header;
   int j;
   
   if ( iobuf == (IO_BUFFER *) NULL || mcs == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_MC_SHOWER;  /* Data type */
   item_header.version = 1;                    /* Version number */
   if ( mcs->extra_parameters.is_set )
      item_header.version = 2;                 /* Optional extended format version */
   item_header.ident = mcs->shower_num;
   put_item_begin(iobuf,&item_header);

   put_int32(mcs->primary_id,iobuf);
   put_real(mcs->energy,iobuf);
   put_real(mcs->azimuth,iobuf);
   put_real(mcs->altitude,iobuf);
   put_real(mcs->depth_start,iobuf);    /* New in version 1 */
   put_real(mcs->h_first_int,iobuf);
   put_real(mcs->xmax,iobuf);
   put_real(mcs->hmax,iobuf);           /* New in version 1 */
   put_real(mcs->emax,iobuf);           /* New in version 1 */
   put_real(mcs->cmax,iobuf);           /* New in version 1 */
   
   put_short(mcs->num_profiles,iobuf);
   for ( j=0; j<mcs->num_profiles; j++ )
   {
      put_int32(mcs->profile[j].id,iobuf);
      put_int32(mcs->profile[j].num_steps,iobuf);
      put_real(mcs->profile[j].start,iobuf);
      put_real(mcs->profile[j].end,iobuf);
      put_vector_of_real(mcs->profile[j].content,
         mcs->profile[j].num_steps,iobuf);
   }
   
   if ( item_header.version >= 2 )
      write_shower_extra_parameters(iobuf,&mcs->extra_parameters);
      
   return put_item_end(iobuf,&item_header);
}

/* --------------------- read_hess_mc_shower -------------------- */
/**
 *  Read MC data for one simulated shower in eventio format.
*/  

int read_hess_mc_shower (IO_BUFFER *iobuf, MCShower *mcs)
{
   IO_ITEM_HEADER item_header;
   int rc, j;
   
   if ( iobuf == (IO_BUFFER *) NULL || mcs == NULL )
      return -1;
      
   item_header.type = IO_TYPE_HESS_MC_SHOWER;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 2 )
   {
      fprintf(stderr,"Unsupported MC shower version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   mcs->shower_num = item_header.ident;

   mcs->primary_id = get_int32(iobuf);
   mcs->energy = get_real(iobuf);
   mcs->azimuth = get_real(iobuf);
   mcs->altitude = get_real(iobuf);
   if ( item_header.version >= 1 )
      mcs->depth_start = get_real(iobuf);
   mcs->h_first_int = get_real(iobuf);
   mcs->xmax = get_real(iobuf);
   mcs->hmax = mcs->emax = mcs->cmax = 0.;
   if ( item_header.version >= 1 )
   {
      mcs->hmax = get_real(iobuf);
      mcs->emax = get_real(iobuf);
      mcs->cmax = get_real(iobuf);
   }
   
   /* Get longitudinal/vertical profiles */
   mcs->num_profiles = get_short(iobuf);
   for ( j=0; j<mcs->num_profiles && j < H_MAX_PROFILE; j++ )
   {
      int skip = 0;
      mcs->profile[j].id = get_int32(iobuf);
      mcs->profile[j].num_steps = get_int32(iobuf);
      /* If there are more steps than we need, a dynamically */
      /* allocated content buffer may be reallocated. */
      /* Otherwise, the contents are skipped. */
      if ( mcs->profile[j].num_steps > mcs->profile[j].max_steps )
      {
         if ( mcs->profile[j].content != NULL )
         {
            if ( mcs->profile[j].max_steps > 0 )
            {
               free(mcs->profile[j].content);
               mcs->profile[j].content = NULL;
            }
            else 
               skip = 1; // We have not enough space for results.
         }
      }
      mcs->profile[j].start = get_real(iobuf);
      mcs->profile[j].end = get_real(iobuf);
      if ( mcs->profile[j].num_steps > 0 )
         mcs->profile[j].binsize = 
            (mcs->profile[j].end-mcs->profile[j].start) /
            (double) mcs->profile[j].num_steps;
      if ( mcs->profile[j].content == NULL )
      {
         mcs->profile[j].content = (double *) calloc(sizeof(double),
           mcs->profile[j].num_steps);
         if ( mcs->profile[j].content == NULL )
         {
            fprintf(stderr,"Not enough memory.\n");
            get_item_end(iobuf,&item_header);
            return -5;
         }
         mcs->profile[j].max_steps = mcs->profile[j].num_steps;
      }
      if ( skip )
      {
         int i;
         for (i=0; i<mcs->profile[j].num_steps; i++)
            (void) get_real(iobuf);
         mcs->profile[j].num_steps *= -1;
      }
      else
         get_vector_of_real(mcs->profile[j].content,
            mcs->profile[j].num_steps,iobuf);
   }

   if ( item_header.version >= 2 )
      read_shower_extra_parameters(iobuf,&mcs->extra_parameters);
   else
      clear_shower_extra_parameters(&mcs->extra_parameters);

   return get_item_end(iobuf,&item_header);
}

/* --------------------- print_hess_mc_shower -------------------- */
/**
 *  Print MC data for one simulated shower in eventio format.
*/  

int print_hess_mc_shower (IO_BUFFER *iobuf)
{
   IO_ITEM_HEADER item_header;
   int rc, j, num_profiles = 0, primary;
   double hint;
   
   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;
      
   item_header.type = IO_TYPE_HESS_MC_SHOWER;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 2 )
   {
      fprintf(stderr,"Unsupported MC shower version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   printf("\nShower number %ld\n",item_header.ident);

   primary = get_int32(iobuf);
   printf("  Primary: %d",primary);
   if ( primary == 0 )
      printf(" (gamma)\n");
   else if ( primary == 1 )
      printf(" (electron)\n");
   else if ( primary == -1 ) 
      printf(" (positron)\n");
   else if ( primary == 2 )
      printf(" (mu-)\n");
   else if ( primary == -2 )
      printf(" (mu+)\n");
   else if ( primary == 101 )
      printf(" (proton)\n");
   else
      printf("\n");
   printf("  Energy: %f TeV\n",get_real(iobuf));
   printf("  Azimuth: %f deg\n",get_real(iobuf)*(180./M_PI));
   printf("  Altitude: %f deg\n",get_real(iobuf)*(180./M_PI));
   if ( item_header.version >= 1 )
     printf("  Starting depth: %f g/cm^2\n",get_real(iobuf));
   hint = get_real(iobuf);
   printf("  First interaction at: %f km\n",fabs(hint)*0.001);
   if ( hint < 0. ) /* Only with sim_telarray up to 2004-10-08 */
      printf("  Tracking started at injection into atmosphere\n");
   /* Note: hint > 0 is always the case since 2004, so this cannot actually 
      tell us anymore if CORSIKA had TSTART on or off. 
   else
      printf("  Tracking either started at first interaction or at injection\n");
   */
   printf("  Xmax: %f g/cm^2\n",get_real(iobuf));
   if ( item_header.version >= 1 )
   {
      printf("  Hmax: %f m\n",get_real(iobuf));
      printf("  Emax: %f g/cm^2\n",get_real(iobuf));
      printf("  Cmax: %f g/cm^2\n",get_real(iobuf));
   }

   /* Get longitudinal/vertical profiles */
   num_profiles = get_short(iobuf);
   for ( j=0; j<num_profiles; j++ )
   {
      int is, num_steps, id = get_int32(iobuf);
      double start, end;
      printf("  Profile %d:\n",j);
      printf("    ID: %d",id);
      if ( id%1000 == 1 )
         printf(", all charged particles");
      else if ( id%1000 == 2 )
         printf(", electrons+positrons");
      else if ( id%1000 == 3 )
         printf(", muons");
      else if ( id%1000 == 4 )
         printf(", hadrons");
      else if ( id%1000 == 10 )
         printf(", Cherenkov light");
      if ( id/1000 == 0 )
         printf(" against depth along shower axis\n");
      else if ( id/1000 == 1 )
         printf(" against vertical depth\n");
      else if ( id/1000 == 2 )
         printf(" against altitude a.s.l.\n");
      else
         printf("\n");
      num_steps = get_int32(iobuf);
      start = get_real(iobuf);
      end = get_real(iobuf);
      printf("    with %d steps from %f to %f:\n", num_steps, start, end);
      for (is=0; is<num_steps; is++)
         printf("\t%f\t%f\n",start+((is+0.5)/num_steps)*(end-start),get_real(iobuf));
   }      

   if ( item_header.version >= 2 )
   {
      printf("   ");
      print_shower_extra_parameters(iobuf);
      printf("\n");
   }

   return get_item_end(iobuf,&item_header);
}

/* --------------------- write_hess_mc_event -------------------- */
/**
 *  @short Write MC data for one use of a simulated shower in eventio format.
 *
 *  This includes the core position shift with respect to the telescope array
 *  and the cross reference to the simulated shower.
*/  


int write_hess_mc_event (IO_BUFFER *iobuf, MCEvent *mce)
{
   IO_ITEM_HEADER item_header;
   
   if ( iobuf == (IO_BUFFER *) NULL || mce == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_MC_EVENT;  /* Data type */
   if ( mce->aweight == 0. )
      item_header.version = 1;             /* Version 1 (no weights) */
   else
      item_header.version = 2;             /* Version 2 (with area weights) */
   item_header.ident = mce->event;
   put_item_begin(iobuf,&item_header);

   put_int32(mce->shower_num,iobuf);
   put_real(mce->xcore,iobuf);
   put_real(mce->ycore,iobuf);

   if ( item_header.version >= 2 )
      put_real(mce->aweight,iobuf);

   return put_item_end(iobuf,&item_header);
}

/* --------------------- read_hess_mc_event -------------------- */
/**
 *  Read MC data for one use of a simulated shower in eventio format.
*/  

int read_hess_mc_event (IO_BUFFER *iobuf, MCEvent *mce)
{
   IO_ITEM_HEADER item_header;
   int rc, itel;
   
   if ( iobuf == (IO_BUFFER *) NULL || mce == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_MC_EVENT;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 2 )
   {
      fprintf(stderr,"Unsupported MC event version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   mce->event = item_header.ident;

   mce->shower_num = get_int32(iobuf);
   mce->xcore = get_real(iobuf);
   mce->ycore = get_real(iobuf);
   if ( item_header.version >= 2 )
      mce->aweight = get_real(iobuf);
   else
      mce->aweight = 0.;

   /* Reset substructure to avoid taking leftover data from */
   /* previous events unnoticed. */
   mce->mc_pesum.num_tel = 0;
   mce->mc_pesum.event = -1;
   for ( itel=0; itel<H_MAX_TEL; itel++ )
   {
      mce->mc_pesum.num_pe[itel] = -1;
      mce->mc_photons[itel].nbunches = -1;
      mce->mc_pe_list[itel].npe = -1;
      mce->mc_pesum.photons[itel] = 
         mce->mc_pesum.photons_atm[itel] = 
         mce->mc_pesum.photons_atm_3_6[itel] = 
         mce->mc_pesum.photons_atm_400[itel] = 
         mce->mc_pesum.photons_atm_qe[itel] = 0.;
      mce->mc_phot_list[itel].nphot = 0;
   }

   /* Version 0 did have more data here which we just ignore now. */

   return get_item_end(iobuf,&item_header);
}

/* --------------------- print_hess_mc_event -------------------- */
/**
 * Print MC data for one use of a simulated shower in eventio format.
*/  

int print_hess_mc_event (IO_BUFFER *iobuf)
{
   IO_ITEM_HEADER item_header;
   int rc;
   
   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_MC_EVENT;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 2 )
   {
      fprintf(stderr,"Unsupported MC event version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   printf("\nMC event %ld (shower %d):\n", item_header.ident, get_int32(iobuf));
   printf("  Core offset: %f,", get_real(iobuf));
   printf(" %f m\n", get_real(iobuf));
   if ( item_header.version >= 2 )
      printf("  Area weight: %g\n", get_real(iobuf));

   /* Version 0 did have more data here which we just ignore now. */

   return get_item_end(iobuf,&item_header);
}

/* --------------------- write_hess_mc_pe_sum -------------------- */
/**
 *  @short Write the numbers of photo-electrons detected from Cherenkov light in eventio format.
 *
 *  These are the 'true' numbers registered, not including photo-electrons
 *  from nightsky background.
*/  

int write_hess_mc_pe_sum (IO_BUFFER *iobuf, MCpeSum *mcpes)
{
   IO_ITEM_HEADER item_header;
   int i;
   
   if ( iobuf == (IO_BUFFER *) NULL || mcpes == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_MC_PE_SUM;  /* Data type */
   item_header.version = 2;             /* Version number */
   item_header.ident = mcpes->event;
   put_item_begin(iobuf,&item_header);

   put_int32(mcpes->shower_num,iobuf);

   put_int32(mcpes->num_tel,iobuf);
   put_vector_of_int32(mcpes->num_pe,mcpes->num_tel,iobuf);
   put_vector_of_int32(mcpes->num_pixels,mcpes->num_tel,iobuf);
   
   for ( i=0; i<mcpes->num_tel; i++)
   {
      if ( mcpes->num_pe[i] > 0 && mcpes->num_pixels[i] > 0 )
      {
	 int non_empty = 0, j;
	 int list[H_MAX_PIX];
	 int pe[H_MAX_PIX];
	 for (j=0; j<mcpes->num_pixels[i]; j++)
	 {
            if ( mcpes->pix_pe[i][j] > 0 )
            {
               pe[non_empty] = mcpes->pix_pe[i][j];
               list[non_empty++] = j;
            }
	 }
	 put_short(non_empty,iobuf);
	 put_vector_of_int(list,non_empty,iobuf);
	 put_vector_of_int32(pe,non_empty,iobuf);
      }
   }

   /* Since version 1: */
   put_vector_of_real(mcpes->photons,mcpes->num_tel,iobuf);
   put_vector_of_real(mcpes->photons_atm,mcpes->num_tel,iobuf);
   put_vector_of_real(mcpes->photons_atm_3_6,mcpes->num_tel,iobuf);
   put_vector_of_real(mcpes->photons_atm_qe,mcpes->num_tel,iobuf);

   /* Since version 2: */
   put_vector_of_real(mcpes->photons_atm_400,mcpes->num_tel,iobuf);

   return put_item_end(iobuf,&item_header);
}

/* --------------------- read_hess_mc_pe_sum -------------------- */
/**
 *  Read the numbers of photo-electrons detected from Cherenkov
 *  light in eventio format.
*/  

int read_hess_mc_pe_sum (IO_BUFFER *iobuf, MCpeSum *mcpes)
{
   IO_ITEM_HEADER item_header;
   int rc, i;
   
   if ( iobuf == (IO_BUFFER *) NULL || mcpes == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_MC_PE_SUM;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 2 )
   {
      fprintf(stderr,"Unsupported MC p.e. sums version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   mcpes->event = item_header.ident;

   mcpes->shower_num = get_int32(iobuf);

   mcpes->num_tel = get_int32(iobuf);
   if ( mcpes->num_tel > H_MAX_TEL )
   {
      Warning("Too many telescopes in p.e. sum");
      return -1;
   }

   get_vector_of_int32(mcpes->num_pe,mcpes->num_tel,iobuf);
   get_vector_of_int32(mcpes->num_pixels,mcpes->num_tel,iobuf);

   for ( i=0; i<mcpes->num_tel; i++)
   {
      int non_empty, j;
      int list[H_MAX_PIX];
      int pe[H_MAX_PIX];

      if ( mcpes->num_pe[i] <= 0 || mcpes->num_pixels[i] <= 0 )
      	 continue;

      if ( mcpes->num_pixels[i] > H_MAX_PIX )
      {
      	 Warning("Too many pixels in MC p.e. sum");
	 get_item_end(iobuf,&item_header);
	 return -1;
      }
      non_empty = get_short(iobuf);
      get_vector_of_int(list,non_empty,iobuf);
      get_vector_of_int32(pe,non_empty,iobuf);
      for (j=0; j<mcpes->num_pixels[i]; j++)
      	 mcpes->pix_pe[i][j] = 0.;
      for (j=0; j<non_empty; j++)
      {
      	 if ( list[j] < 0 || list[j] >= H_MAX_PIX )
	    continue;
      	 mcpes->pix_pe[i][list[j]] = pe[j];
      }
   }

   if ( item_header.version >= 1 )
   {
      /* Since version 1: */
      get_vector_of_real(mcpes->photons,mcpes->num_tel,iobuf);
      get_vector_of_real(mcpes->photons_atm,mcpes->num_tel,iobuf);
      get_vector_of_real(mcpes->photons_atm_3_6,mcpes->num_tel,iobuf);
      get_vector_of_real(mcpes->photons_atm_qe,mcpes->num_tel,iobuf);
      if ( item_header.version >= 2 )
         get_vector_of_real(mcpes->photons_atm_400,mcpes->num_tel,iobuf);
      else
      {
         int j;
         for (j=0; j<mcpes->num_tel; j++)
            mcpes->photons_atm_400[j] = 0.;
      }
   }
   else
   {
      int j;
      for (j=0; j<mcpes->num_tel; j++)
         mcpes->photons[j] = mcpes->photons_atm[j] = 
         mcpes->photons_atm_3_6[j] = mcpes->photons_atm_qe[j] = 
         mcpes->photons_atm_400[j] = 0.;
   }

   return get_item_end(iobuf,&item_header);
}

/* --------------------- print_hess_mc_pe_sum -------------------- */
/**
 *  Print the numbers of photo-electrons detected from Cherenkov
 *  light in eventio format.
*/  

int print_hess_mc_pe_sum (IO_BUFFER *iobuf)
{
   IO_ITEM_HEADER item_header;
   int rc, i, ntel;
   int num_pe[H_MAX_TEL], num_pixels[H_MAX_TEL];
   int nwp = 0, nw = 0;
   
   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;

   hs_check_env();

   item_header.type = IO_TYPE_HESS_MC_PE_SUM;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 2 )
   {
      fprintf(stderr,"Unsupported MC p.e. sums version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   printf("\nMC p.e. sums for event %ld (shower %d):\n", 
      item_header.ident, get_int32(iobuf));

   ntel = get_int32(iobuf);
   if ( ntel > H_MAX_TEL )
   {
      Warning("Too many telescopes in p.e. sum");
      return -1;
   }
   get_vector_of_int32(num_pe,ntel,iobuf);
   get_vector_of_int32(num_pixels,ntel,iobuf);
   for ( i=0; i<ntel; i++)
      if ( num_pe[i] > 0 )
      {
         nw++;
         if ( num_pixels[i] > 0 )
            nwp++;
      }

   printf("  With p.e. data for %d telescope%s (%d with any photo-electrons, %d with per-pixel values).\n",
      ntel, (ntel==1?"":"s"), nw, nwp);

   for ( i=0; i<ntel; i++)
   {
      int non_empty, j;
      int list[H_MAX_PIX];
      int pe[H_MAX_PIX];
      
      if ( num_pe[i] <= 0 || num_pixels[i] <= 0 )
      	 continue;

      printf("  Telescope #%d:\n", i);

      if ( num_pixels[i] > H_MAX_PIX )
      {
      	 Warning("Too many pixels in MC p.e. sum");
	 get_item_end(iobuf,&item_header);
	 return -1;
      }
      non_empty = get_short(iobuf);
      printf("    Non-empty pixels: %d\n", non_empty);
      get_vector_of_int(list,non_empty,iobuf);
      get_vector_of_int32(pe,non_empty,iobuf);
      for (j=0; j<non_empty; j++)
      {
      	 if ( list[j] < 0 || list[j] >= H_MAX_PIX )
	    continue;
         printf("    Pixel %d:  %d p.e.\n",list[j],pe[j]);
         if ( j >= hs_maxprt )
         {
            if ( j == hs_maxprt )
               printf("...\n");
            break;
         }
      }
   }

   if ( item_header.version >= 1 )
   {
      /* Since version 1: */
      printf("  Photons (all): ");
      for (i=0; i<ntel; i++)
         printf(" %5.3f", get_real(iobuf));
      printf("\n");
      printf("  Photons (after atmosphere): ");
      for (i=0; i<ntel; i++)
         printf(" %5.3f", get_real(iobuf));
      printf("\n");
      printf("  Photons (after atm., 300-600 nm): ");
      for (i=0; i<ntel; i++)
         printf(" %5.3f", get_real(iobuf));
      printf("\n");
      printf("  Photo-electrons: ");
      for (i=0; i<ntel; i++)
         printf(" %5.3f", get_real(iobuf));
      printf("\n");
      if ( item_header.version >= 2 )
      {
         printf("  Photons (after atm., 350-450 nm): ");
         for (i=0; i<ntel; i++)
            printf(" %5.3f", get_real(iobuf));
         printf("\n");
      }
   }

   return get_item_end(iobuf,&item_header);
}


/* -------------------- put_time_blob ------------------- */
/**
 *  Put the time (seconds since 1970.0, nanoseconds) into an
 *  eventio block already started.
*/  


static void put_time_blob (HTime *t, IO_BUFFER *iobuf)
{
   put_long(t->seconds,iobuf);
   put_long(t->nanoseconds,iobuf);
}

/* -------------------- get_time_blob ------------------- */
/**
 *  Get the time (seconds since 1970.0, nanoseconds) from an
 *  eventio block already started.
*/  

static void get_time_blob (HTime *t, IO_BUFFER *iobuf)
{
   t->seconds = get_long(iobuf);
   t->nanoseconds = get_long(iobuf);
}

/* ------------------- reset_htime ------------------ */

void reset_htime (HTime *t)
{
   t->seconds = 0;
   t->nanoseconds = 0;
}

/* --------------------- fill_htime_now -------------------------- */
/**
 *  Fill the current time into a HTime structure.
*/  

void fill_htime_now (HTime *now)
{
   struct timeval tv;
//   struct timezone tz;

//   gettimeofday(&tv,&tz);
   gettimeofday(&tv,NULL);
   now->seconds = tv.tv_sec;
   now->nanoseconds = tv.tv_usec * 1000;
}

/* ----------------------- copy_htime ---------------------------- */
/**
 *  Copy a time from one HTime structure into another one.
*/  

void copy_htime (HTime *t2, HTime *t1)
{
   t2->seconds = t1->seconds;
   t2->nanoseconds = t1->nanoseconds;
}

/* -------------------- write_hess_tel_monitor ------------------- */
/**
 *  @short Write telescope camera monitoring information in eventio format.
 *
 *  What actually is written depends on the 'what' parameter.
 *  The general idea is to write only those things which have changed.
 *  Only when a target farm CPU becomes the target of the data stream,
 *  the full set of monitoring data is written.
*/  

int write_hess_tel_monitor (IO_BUFFER *iobuf, TelMoniData *mon, int what)
{
   IO_ITEM_HEADER item_header;
   int reset_new = 0, auto_incr = 0, all_new = 0;
   HTime htime_now;
   
   if ( iobuf == (IO_BUFFER *) NULL || mon == NULL )
      return -1;

   if ( (what&0x10000) ) /* Reset those parts marked as new. */
      reset_new = 1;
   if ( (what&0x20000) ) /* Increment monitor block ID at the end. */
      auto_incr = 1;
   if ( (what&0x40000) ) /* After switchover report everything (as if new) */
   {
      all_new = 1;
      what = mon->known;
   }

   /* If nothing specified, write new stuff only */
   if ( (what&0xffff) == 0 )
      what = mon->new_parts;
   /* We can only write what we already know */
   what &= mon->known;
   
   fill_htime_now(&htime_now);
   copy_htime(&mon->moni_time,&htime_now);
   
   item_header.type = IO_TYPE_HESS_TEL_MONI;  /* Data type */
   if ( mon->num_sectors >= 32768 || mon->num_pixels >= 32768 )
      item_header.version = 1;             /* Version 1 */
   else
      item_header.version = 0; /* compatible with older software */
   item_header.ident = (mon->tel_id & 0xff) | 
                       ((what & 0xffff) << 8) | 
                       ((mon->tel_id & 0x3f00) << 16);
   put_item_begin(iobuf,&item_header);

   put_short(mon->known,iobuf);
   if ( all_new )
      put_short(mon->known,iobuf);
   else
      put_short(mon->new_parts,iobuf);

   put_int32(mon->monitor_id,iobuf);
   put_time_blob(&htime_now,iobuf);
   
   /* Dimensions of various things */
   if ( item_header.version == 0 )
   {
      put_short(mon->num_sectors,iobuf);
      put_short(mon->num_pixels,iobuf);
      put_short(mon->num_drawers,iobuf);
      put_short(mon->num_gains,iobuf);
   }
   else
   {
      put_scount32(mon->num_sectors,iobuf);
      put_scount32(mon->num_pixels,iobuf);
      put_scount32(mon->num_drawers,iobuf);
      put_scount32(mon->num_gains,iobuf);
   }

   if ( (what & 0x01) ) /* Status only */
   {
      put_time_blob(&mon->status_time,iobuf);
      put_int32(mon->status_bits,iobuf);
   }
   if ( (what & 0x02) ) /* Counts + Rates */
   {
      put_time_blob(&mon->trig_time,iobuf);
      put_long(mon->coinc_count,iobuf);
      put_long(mon->event_count,iobuf);
      put_real(mon->trigger_rate,iobuf);
      put_vector_of_real(mon->sector_rate,mon->num_sectors,iobuf);
      put_real(mon->event_rate,iobuf);
      put_real(mon->data_rate,iobuf);
      put_real(mon->mean_significant,iobuf);
   }
   if ( (what & 0x04) ) /* Pedestals + noise */
   {
      int j;
      put_time_blob(&mon->ped_noise_time,iobuf);
      put_short(mon->num_ped_slices,iobuf);
      for ( j=0; j<mon->num_gains; j++ )
      	 put_vector_of_real(mon->pedestal[j],mon->num_pixels,iobuf);
      for ( j=0; j<mon->num_gains; j++ )
      	 put_vector_of_real(mon->noise[j],mon->num_pixels,iobuf);
   }
   if ( (what & 0x08) ) /* HV + temperatures (CNTRLMon) + others */
   {
      int j;
      put_time_blob(&mon->hv_temp_time,iobuf);
      put_short(mon->num_drawer_temp,iobuf);
      put_short(mon->num_camera_temp,iobuf);

      /* From CNTRLMon messages: */
      put_vector_of_uint16(mon->hv_v_mon,mon->num_pixels,iobuf);
      put_vector_of_uint16(mon->hv_i_mon,mon->num_pixels,iobuf);
      put_vector_of_byte(mon->hv_stat,mon->num_pixels,iobuf);
      for ( j=0; j<mon->num_drawers; j++ )
      	 put_vector_of_short(mon->drawer_temp[j],mon->num_drawer_temp,iobuf);
      
      /* From other sources: */
      put_vector_of_short(mon->camera_temp,mon->num_camera_temp,iobuf);
      /* ... + various voltages and currents to be defined ... */ 
   }
   if ( (what & 0x10) ) /* Pixel scalers + DC currents (CNTRLCpt) */
   {
      put_time_blob(&mon->dc_rate_time,iobuf);
      put_vector_of_uint16(mon->current,mon->num_pixels,iobuf);
      put_vector_of_uint16(mon->scaler,mon->num_pixels,iobuf);
   }
   if ( (what & 0x20) ) /* HV + thresholds settings (CNTRLSc+CNTRLHt) */
   {
      put_time_blob(&mon->set_hv_thr_time,iobuf);
      put_vector_of_uint16(mon->hv_dac,mon->num_pixels,iobuf);
      put_vector_of_uint16(mon->thresh_dac,mon->num_drawers,iobuf);
      put_vector_of_byte(mon->hv_set,mon->num_pixels,iobuf);
      put_vector_of_byte(mon->trig_set,mon->num_pixels,iobuf);
   }
   if ( (what & 0x40) ) /* DAQ configuration (CNTRLDAQ) */
   {
      put_time_blob(&mon->set_daq_time,iobuf);
      put_vector_of_uint16(&mon->daq_conf,1,iobuf);
      put_vector_of_uint16(&mon->daq_scaler_win,1,iobuf);
      put_vector_of_uint16(&mon->daq_nd,1,iobuf);
      put_vector_of_uint16(&mon->daq_acc,1,iobuf);
      put_vector_of_uint16(&mon->daq_nl,1,iobuf);
   }

   if ( reset_new )
      mon->new_parts = 0;
   if ( auto_incr )
      mon->monitor_id++;

   return put_item_end(iobuf,&item_header);
}
/* -------------------- read_hess_tel_monitor ------------------- */
/**
 *  Read telescope camera monitoring information in eventio format.
*/  

int read_hess_tel_monitor (IO_BUFFER *iobuf, TelMoniData *mon)
{
   IO_ITEM_HEADER item_header;
   int what, rc, ns, np, nd, ng, tel_id;
   
   if ( iobuf == (IO_BUFFER *) NULL || mon == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_TEL_MONI;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version != 0 && item_header.version != 1 )
   {
      fprintf(stderr,"Unsupported telescope monitoring version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   tel_id = ((item_header.ident & 0xff)|
             ((item_header.ident & 0x3f000000)>>16));
   if ( tel_id != mon->tel_id )
   {
      Warning("Monitor block is for wrong telescope");
      get_item_end(iobuf,&item_header);
      return -1;
   }
   
   what = ((item_header.ident & 0xffff00) >> 8) & 0xffff;

   mon->known |= get_short(iobuf);
   mon->new_parts = get_short(iobuf);

   mon->monitor_id = get_int32(iobuf);
   get_time_blob(&mon->moni_time,iobuf);

   /* Dimensions of various things */
   if ( item_header.version == 0 )
   {
      ns = get_short(iobuf);
      np = get_short(iobuf);
      nd = get_short(iobuf);
      ng = get_short(iobuf);
   }
   else
   {
      ns = get_scount32(iobuf);
      np = get_scount32(iobuf);
      nd = get_scount32(iobuf);
      ng = get_scount32(iobuf);
   }
   if ( (mon->num_sectors != ns && mon->num_sectors != 0) ||
        (mon->num_pixels != np && mon->num_pixels != 0) ||
        (mon->num_drawers != nd && mon->num_drawers != 0) ||
        (mon->num_gains != ng && mon->num_gains != 0) )
   {
      Warning("Monitor data is for a camera of different setup");
      if ( ns > H_MAX_SECTORS || np > H_MAX_PIX || 
           nd > H_MAX_DRAWERS || ng > H_MAX_GAINS )
      {
	 Warning("Monitor data has invalid camera setup");
	 get_item_end(iobuf,&item_header);
	 mon->new_parts = 0;
	 return -1;
      }
   }

   mon->num_sectors = ns;
   mon->num_pixels = np;
   mon->num_drawers = nd;
   mon->num_gains = ng;

   if ( (what & 0x01) ) /* Status only */
   {
      get_time_blob(&mon->status_time,iobuf);
      mon->status_bits = get_int32(iobuf);
   }
   if ( (what & 0x02) ) /* Counts + Rates */
   {
      get_time_blob(&mon->trig_time,iobuf);
      mon->coinc_count = get_long(iobuf);
      mon->event_count = get_long(iobuf);
      mon->trigger_rate = get_real(iobuf);
      get_vector_of_real(mon->sector_rate,mon->num_sectors,iobuf);
      mon->event_rate = get_real(iobuf);
      mon->data_rate = get_real(iobuf);
      mon->mean_significant = get_real(iobuf);
   }
   if ( (what & 0x04) ) /* Pedestals + noise */
   {
      int j;
      get_time_blob(&mon->ped_noise_time,iobuf);
      mon->num_ped_slices = get_short(iobuf);
      for ( j=0; j<mon->num_gains; j++ )
      	 get_vector_of_real(mon->pedestal[j],mon->num_pixels,iobuf);
      for ( j=0; j<mon->num_gains; j++ )
      	 get_vector_of_real(mon->noise[j],mon->num_pixels,iobuf);
   }
   if ( (what & 0x08) ) /* HV + temperatures (CNTRLMon) + others */
   {
      int j;
      get_time_blob(&mon->hv_temp_time,iobuf);
      mon->num_drawer_temp = get_short(iobuf);
      mon->num_camera_temp = get_short(iobuf);

      /* From CNTRLMon messages: */
      get_vector_of_uint16(mon->hv_v_mon,mon->num_pixels,iobuf);
      get_vector_of_uint16(mon->hv_i_mon,mon->num_pixels,iobuf);
      get_vector_of_byte(mon->hv_stat,mon->num_pixels,iobuf);
      for ( j=0; j<mon->num_drawers; j++ )
      	 get_vector_of_short(mon->drawer_temp[j],mon->num_drawer_temp,iobuf);
      
      /* From other sources: */
      get_vector_of_short(mon->camera_temp,mon->num_camera_temp,iobuf);
      /* ... + various voltages and currents to be defined ... */ 
   }
   if ( (what & 0x10) ) /* Pixel scalers + DC currents (CNTRLCpt) */
   {
      get_time_blob(&mon->dc_rate_time,iobuf);
      get_vector_of_uint16(mon->current,mon->num_pixels,iobuf);
      get_vector_of_uint16(mon->scaler,mon->num_pixels,iobuf);
   }
   if ( (what & 0x20) ) /* HV + thresholds settings (CNTRLSc+CNTRLHt) */
   {
      get_time_blob(&mon->set_hv_thr_time,iobuf);
      get_vector_of_uint16(mon->hv_dac,mon->num_pixels,iobuf);
      get_vector_of_uint16(mon->thresh_dac,mon->num_drawers,iobuf);
      get_vector_of_byte(mon->hv_set,mon->num_pixels,iobuf);
      get_vector_of_byte(mon->trig_set,mon->num_pixels,iobuf);
   }
   if ( (what & 0x40) ) /* DAQ configuration (CNTRLDAQ) */
   {
      get_time_blob(&mon->set_daq_time,iobuf);
      get_vector_of_uint16(&mon->daq_conf,1,iobuf);
      get_vector_of_uint16(&mon->daq_scaler_win,1,iobuf);
      get_vector_of_uint16(&mon->daq_nd,1,iobuf);
      get_vector_of_uint16(&mon->daq_acc,1,iobuf);
      get_vector_of_uint16(&mon->daq_nl,1,iobuf);
   }

   return get_item_end(iobuf,&item_header);
}

/* -------------------- print_hess_tel_monitor ------------------- */
/**
 *  @short Print telescope camera monitoring information in eventio format.
*/  

int print_hess_tel_monitor (IO_BUFFER *iobuf)
{
   IO_ITEM_HEADER item_header;
   int what, rc, ns, np, nd, ng;
   int known = 0, new_parts = 0, i;
   HTime mtime;
   
   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;

   hs_check_env();

   item_header.type = IO_TYPE_HESS_TEL_MONI;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version != 0 && item_header.version != 1 )
   {
      fprintf(stderr,"Unsupported telescope monitoring version: %u.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   printf("\nMonitor block for telescope %ld:\n", 
      (item_header.ident & 0xff)|((item_header.ident & 0x3f000000)>>16));
   
   what = (item_header.ident >> 8) & 0xffff;

   printf("   Known = %d\n", known |= get_short(iobuf));
   printf("   New   = %d\n", new_parts = get_short(iobuf));

   printf("   Monitor ID = %d\n", get_int32(iobuf));
   get_time_blob(&mtime,iobuf);
   printf("   Time: %ld.%09ld\n", 
      mtime.seconds, mtime.nanoseconds);

   /* Dimensions of various things */
   if ( item_header.version == 0 )
   {
      ns = get_short(iobuf);
      np = get_short(iobuf);
      nd = get_short(iobuf);
      ng = get_short(iobuf);
   }
   else
   {
      ns = get_scount32(iobuf);
      np = get_scount32(iobuf);
      nd = get_scount32(iobuf);
      ng = get_scount32(iobuf);
   }
   printf("   %d sectors, %d pixels, %d drawers, %d gains\n",ns,np,nd,ng);

   if ( (what & 0x01) ) /* Status only */
   {
      get_time_blob(&mtime,iobuf);
      printf("   Status: time: %ld.%09ld, bits: %d\n", 
         mtime.seconds, mtime.nanoseconds, get_int32(iobuf));
   }
   if ( (what & 0x02) ) /* Counts + Rates */
   {
      get_time_blob(&mtime,iobuf);
      printf("   Counts+rates: time: %ld.%09ld:\n", 
         mtime.seconds, mtime.nanoseconds);
      printf("      coinc_count: %ld",get_long(iobuf));
      printf(", event_count: %ld",get_long(iobuf));
      printf(", trigger_rate: %f\n",get_real(iobuf));
      printf("      sector rates: ");
      for (i=0; i<ns; i++)
      {
         if ( i < hs_maxprt )
            printf(" %f,",get_real(iobuf));
         else if ( i == hs_maxprt )
         {  printf(" ..."); (void) get_real(iobuf); }
         else
            (void) get_real(iobuf);
      }
      printf("\n      event rate: %f",get_real(iobuf));
      printf(", data rate: %f", get_real(iobuf));
      printf(", mean significant: %f\n",get_real(iobuf));
   }
   if ( (what & 0x04) ) /* Pedestals + noise */
   {
      int j, num_ped_slices;
      get_time_blob(&mtime,iobuf);
      num_ped_slices = get_short(iobuf);
      printf("   Pedestals+noise: time: %ld.%09ld: %d slices\n", 
         mtime.seconds, mtime.nanoseconds, num_ped_slices);
      for ( j=0; j<ng; j++ )
      {
         printf("      Pedestals gain %d: ",j);
         for (i=0; i<np; i++)
         {
            if ( i < hs_maxprt )
               printf(" %f,", get_real(iobuf));
            else if ( i == hs_maxprt )
            {  printf(" ..."); (void) get_real(iobuf); }
            else
               (void) get_real(iobuf);
         }
         printf("\n");
      }
      for ( j=0; j<ng; j++ )
      {
         printf("      Noise gain %d: ",j);
         for (i=0; i<np; i++)
         {
            if ( i < hs_maxprt )
               printf(" %f,", get_real(iobuf));
            else if ( i == hs_maxprt )
            {  printf(" ..."); (void) get_real(iobuf); }
            else
               (void) get_real(iobuf);
         }
         printf("\n");
      }
   }
   if ( (what & 0x08) ) /* HV + temperatures (CNTRLMon) + others */
      printf("   HV + temperatures (CNTRLMon) not printed ...\n");
   if ( (what & 0x10) ) /* Pixel scalers + DC currents (CNTRLCpt) */
      printf("   Pixel scaler + DC currents (CNTRLCpt) not printed ...\n");
   if ( (what & 0x20) ) /* HV + thresholds settings (CNTRLSc+CNTRLHt) */
   {
      get_time_blob(&mtime,iobuf);
      printf("   HV + thresholds settings (CNTRLSc+CNTRLHt): time: %ld.%09ld:\n", 
         mtime.seconds, mtime.nanoseconds);
      printf("       hv_dac: ");
      for ( i=0; i<np; i++ )
      {
         if ( i < hs_maxprt )
            printf(" %u,", get_uint16(iobuf));
         else if ( i == hs_maxprt )
         {  printf(" ..."); (void) get_uint16(iobuf); }
         else
            (void) get_uint16(iobuf);
      }
      printf("\n       thresh_dac: ");
      for ( i=0; i<nd; i++ )
      {
         if ( i < hs_maxprt )
            printf(" %u,", get_uint16(iobuf));
         else if ( i == hs_maxprt )
         {  printf(" ..."); (void) get_uint16(iobuf); }
         else
            (void) get_uint16(iobuf);
      }
      printf("\n       hv_set: ");
      for ( i=0; i<nd; i++ )
      {
         if ( i < hs_maxprt )
            printf(" %u,", (unsigned char) get_byte(iobuf));
         else if ( i == hs_maxprt )
         {  printf(" ..."); (void) get_byte(iobuf); }
         else
            (void) get_byte(iobuf);
      }
      printf("\n       trig_set: ");
      for ( i=0; i<nd; i++ )
      {
         if ( i < hs_maxprt )
            printf(" %u,", (unsigned char) get_byte(iobuf));
         else if ( i == hs_maxprt )
         {  printf(" ..."); (void) get_byte(iobuf); }
         else
            (void) get_byte(iobuf);
      }
      printf("\n");
   }
   if ( (what & 0x40) ) /* DAQ configuration (CNTRLDAQ) */
   {
      get_time_blob(&mtime,iobuf);
      printf("   DAQ configuration (CNTRLDAQ): time: %ld.%09ld:\n", 
         mtime.seconds, mtime.nanoseconds);
      printf("      daq_conf = %u, ", get_uint16(iobuf));
      printf("daq_scaler_win = %u, ", get_uint16(iobuf));
      printf("daq_nd = %u, ", get_uint16(iobuf));
      printf("daq_acc = %u, ", get_uint16(iobuf));
      printf("daq_nl = %u\n", get_uint16(iobuf));
   }

   return get_item_end(iobuf,&item_header);
}

/* --------------------- write_hess_laser_calib ---------------------- */
/**
 *  @short Write a set of laser calibration data in eventio format.
 *
 *  This may well change in a future revision (when more details
 *  are known how the real laser calibration should work).
*/

int write_hess_laser_calib (IO_BUFFER *iobuf, LasCalData *lcd)
{
   IO_ITEM_HEADER item_header;
   int j;
   
   if ( iobuf == (IO_BUFFER *) NULL || lcd == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_LASCAL;  /* Data type */
   item_header.version = 0;             /* Version 0 */
//   if ( lcd->max_int_frac[0] > 0. || lcd->max_pixtm_frac[0] > 0. )
//      item_header.version = 1;          /* need version 1 */
   item_header.version = 2;          /* Now using version 2 */
   item_header.ident = lcd->tel_id;
   put_item_begin(iobuf,&item_header);

   put_short(lcd->num_pixels,iobuf);
   put_short(lcd->num_gains,iobuf);
   put_int32(lcd->lascal_id,iobuf);

   for ( j=0; j<lcd->num_gains; j++ )
      put_vector_of_real(lcd->calib[j],lcd->num_pixels,iobuf);

   if ( item_header.version >= 1 )
   {
      for ( j=0; j<lcd->num_gains; j++ )
      {
         put_real(lcd->max_int_frac[j],iobuf);
         put_real(lcd->max_pixtm_frac[j],iobuf);
      }
   }

   if ( item_header.version >= 2 )
      for ( j=0; j<lcd->num_gains; j++ )
         put_vector_of_real(lcd->tm_calib[j],lcd->num_pixels,iobuf);

   return put_item_end(iobuf,&item_header);
}


/* --------------------- read_hess_laser_calib ---------------------- */
/**
 *  Read a set of laser calibration data in eventio format.
*/  

int read_hess_laser_calib (IO_BUFFER *iobuf, LasCalData *lcd)
{
   IO_ITEM_HEADER item_header;
   int j, np, ng, rc;
   
   if ( iobuf == (IO_BUFFER *) NULL || lcd == NULL )
      return -1;
   lcd->known = 0;

   item_header.type = IO_TYPE_HESS_LASCAL;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 2 )
   {
      fprintf(stderr,"Unsupported laser calibration version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   if ( lcd->tel_id != item_header.ident )
   {
      Warning("Laser calibration data is for wrong telescope");
      get_item_end(iobuf,&item_header);
      return -1;
   }
   
   np = get_short(iobuf);
   ng = get_short(iobuf);
   if ( (np != lcd->num_pixels && lcd->num_pixels != 0) || 
        (ng != lcd->num_gains && lcd->num_gains!= 0) )
   {
      Warning("Laser calibration data is for different setup");
   }
   lcd->num_pixels = np;
   lcd->num_gains = ng;
   if ( np > H_MAX_PIX || ng > H_MAX_GAINS )
   {
      Warning("Laser calibration data is bad setup");
      get_item_end(iobuf,&item_header);
      return -1;
   }

   lcd->lascal_id = get_int32(iobuf);

   for ( j=0; j<lcd->num_gains; j++ )
   {
      int i;
      get_vector_of_real(lcd->calib[j],lcd->num_pixels,iobuf);
      for ( i=0; i<np; i++ )
      {
         if ( lcd->calib[j][i] != 0. )
         {
            lcd->known = 1;
            break;
         }
      }
   }

   for ( j=0; j<lcd->num_gains; j++ )
   {
      int i;
      lcd->max_int_frac[j] = lcd->max_pixtm_frac[j]  = 0.;
      for ( i=0; i<np; i++ )
         lcd->tm_calib[j][i] = 0.;
   }

   if ( item_header.version >= 1 )
   {
      for ( j=0; j<lcd->num_gains; j++ )
      {
         lcd->max_int_frac[j] = get_real(iobuf);
         lcd->max_pixtm_frac[j] = get_real(iobuf);
      }
   }

   if ( item_header.version >= 2 )
   {
      for ( j=0; j<lcd->num_gains; j++ )
         get_vector_of_real(lcd->tm_calib[j],lcd->num_pixels,iobuf);
   }

   if ( !lcd->known )
   {
      char message[1024];
      sprintf(message,"Laser calibration for telescope %d was not properly filled.",
         lcd->tel_id);
      Warning(message);
   }

   return get_item_end(iobuf,&item_header);
}

/* --------------------- print_hess_laser_calib ---------------------- */
/**
 *  Print a set of laser calibration data in eventio format.
*/  

int print_hess_laser_calib (IO_BUFFER *iobuf)
{
   IO_ITEM_HEADER item_header;
   int j, np, ng, rc;
   
   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;

   hs_check_env();

   item_header.type = IO_TYPE_HESS_LASCAL;  /* Data type */
   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 2 )
   {
      fprintf(stderr,"Unsupported laser calibration version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   printf("\nLaser calibration for telescope %ld", item_header.ident);   
   np = get_short(iobuf);
   ng = get_short(iobuf);
   printf(" (%d pixels, %d gains)", np, ng);

   printf(", ID = %d\n", get_int32(iobuf));

   for ( j=0; j<ng; j++ )
   {
      int i;
      printf("   Gain %d: ",j);
      for ( i=0; i<np; i++ )
      {
         if ( i < hs_maxprt )
            printf(" %f,",get_real(iobuf));
         else if ( i == hs_maxprt )
         {  printf(" ..."); (void) get_real(iobuf); }
         else
            (void) get_real(iobuf);
      }
      printf("\n");
   }

   if ( item_header.version >= 1 )
   {
      for ( j=0; j<ng; j++ )
      {
         double max_int_frax = get_real(iobuf);
         double max_pixtm_frac = get_real(iobuf);
         printf("   Integration sees fractions <= %f and %f of total signal "
                "with fixed window and peak finding at gain %d\n",
            max_int_frax, max_pixtm_frac, j);
      }
   }

   if ( item_header.version >= 2 )
   {
      for ( j=0; j<ng; j++ )
      {
         int i;
         printf("   Time %d: ",j);
         for ( i=0; i<np; i++ )
         {
            if ( i < hs_maxprt )
               printf(" %f,",get_real(iobuf));
            else if ( i == hs_maxprt )
            {  printf(" ..."); (void) get_real(iobuf); }
            else
               (void) get_real(iobuf);
         }
         printf("\n");
      }
   }

   return get_item_end(iobuf,&item_header);
}

/* --------------------- write_hess_run_stat ---------------------- */
/**
 *  @short Write run statistics in eventio format.
 *
 *  This is pretty much dummy at this moment. Once we get closer
 *  to the real experiment, this data will certainly increase
 *  by a considerable amount.
*/  
 
int write_hess_run_stat (IO_BUFFER *iobuf, RunStat *rs)
{
   IO_ITEM_HEADER item_header;
   
   if ( iobuf == (IO_BUFFER *) NULL || rs == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_RUNSTAT;  /* Data type */
   item_header.version = 0;             /* Version 0 (test) */
   item_header.ident = rs->run_num;
   put_item_begin(iobuf,&item_header);

   put_int32(rs->num_tel,iobuf);
   put_int32(rs->num_central_trig,iobuf);
   put_vector_of_int32(rs->tel_ids,rs->num_tel,iobuf);
   put_vector_of_int32(rs->num_local_trig,rs->num_tel,iobuf);
   put_vector_of_int32(rs->num_local_sys_trig,rs->num_tel,iobuf);
   put_vector_of_int32(rs->num_events,rs->num_tel,iobuf);

   return put_item_end(iobuf,&item_header);
}

/* --------------------- read_hess_run_stat ---------------------- */
/**
 *  Read run statistics in eventio format.
*/  
 
int read_hess_run_stat (IO_BUFFER *iobuf, RunStat *rs)
{
   IO_ITEM_HEADER item_header;
   int rc;
   
   if ( iobuf == (IO_BUFFER *) NULL || rs == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_RUNSTAT;  /* Data type */

   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version != 0 )
   {
      fprintf(stderr,"Unsupported run statistics version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   rs->run_num = item_header.ident;
   
   rs->num_tel = get_int32(iobuf);
   rs->num_central_trig = get_int32(iobuf);
   get_vector_of_int32(rs->tel_ids,rs->num_tel,iobuf);
   get_vector_of_int32(rs->num_local_trig,rs->num_tel,iobuf);
   get_vector_of_int32(rs->num_local_sys_trig,rs->num_tel,iobuf);
   get_vector_of_int32(rs->num_events,rs->num_tel,iobuf);

   return get_item_end(iobuf,&item_header);
}

/* --------------------- print_hess_run_stat ---------------------- */
/**
 *  Print run statistics in eventio format.
*/  
 
int print_hess_run_stat (IO_BUFFER *iobuf)
{
   IO_ITEM_HEADER item_header;
   int rc, i, ntel;
   
   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_RUNSTAT;  /* Data type */

   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version != 0 )
   {
      fprintf(stderr,"Unsupported run statistics version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   printf("\nRun statistics for run %ld:\n",item_header.ident);
   
   ntel = get_int32(iobuf);
   printf("  Central triggers: %d\n",get_int32(iobuf));
   printf("  Telescope IDs:   ");
   for (i=0; i<ntel; i++)
      printf("\t%d", get_int32(iobuf));
   printf("  Local triggers:  ");
   for (i=0; i<ntel; i++)
      printf("\t%d", get_int32(iobuf));
   printf("  Local/system trg:");
   for (i=0; i<ntel; i++)
      printf("\t%d", get_int32(iobuf));
   printf("  Events written:  ");
   for (i=0; i<ntel; i++)
      printf("\t%d", get_int32(iobuf));

   return get_item_end(iobuf,&item_header);
}

/* --------------------- write_hess_mc_run_stat ---------------------- */
/**
 *  Write Monte Carlo run statistics in eventio format.
*/  
 
int write_hess_mc_run_stat (IO_BUFFER *iobuf, MCRunStat *mcrs)
{
   IO_ITEM_HEADER item_header;
   
   if ( iobuf == (IO_BUFFER *) NULL || mcrs == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_MC_RUNSTAT;  /* Data type */
   item_header.version = 0;             /* Version 0 (test) */
   item_header.ident = mcrs->run_num;
   put_item_begin(iobuf,&item_header);

   put_int32(mcrs->num_showers,iobuf);
   put_int32(mcrs->num_events,iobuf);

   return put_item_end(iobuf,&item_header);
}

/* --------------------- read_hess_mc_run_stat ---------------------- */
/**
 *  Read Monte Carlo run statistics in eventio format.
*/  
 
int read_hess_mc_run_stat (IO_BUFFER *iobuf, MCRunStat *mcrs)
{
   IO_ITEM_HEADER item_header;
   int rc;
   
   if ( iobuf == (IO_BUFFER *) NULL || mcrs == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_MC_RUNSTAT;  /* Data type */

   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version != 0 )
   {
      fprintf(stderr,"Unsupported MC run statistics version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   mcrs->run_num = item_header.ident;
   
   mcrs->num_showers = get_int32(iobuf);
   mcrs->num_events = get_int32(iobuf);

   return get_item_end(iobuf,&item_header);
}

/* --------------------- print_hess_mc_run_stat ---------------------- */
/**
 *  Print Monte Carlo run statistics in eventio format.
*/  
 
int print_hess_mc_run_stat (IO_BUFFER *iobuf)
{
   IO_ITEM_HEADER item_header;
   int rc;
   
   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_MC_RUNSTAT;  /* Data type */

   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version != 0 )
   {
      fprintf(stderr,"Unsupported MC run statistics version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   printf("\nMC run statistics for run %ld:\n",item_header.ident);
   
   printf("  Number of showers: %d\n", get_int32(iobuf));
   printf("  Number of events: %d\n", get_int32(iobuf));

   return get_item_end(iobuf,&item_header);
}

/* --------------------- read_hess_mc_phot ---------------------- */
/**
 *  Read Monte Carlo photons and photo-electrons.
*/  
 
int read_hess_mc_phot (IO_BUFFER *iobuf, MCEvent *mce)
{
   int iarray=0, itel=0, itel_pe=0, tel_id=0, jtel=0, type, nbunches=0, max_bunches=0, flags=0;
   int npe=0, pixels=0, max_npe=0;
   int rc;
   double photons=0.;
   IO_ITEM_HEADER item_header;
   if ( (rc = begin_read_tel_array(iobuf, &item_header, &iarray)) < 0 )
      return rc;
   while ( (type = next_subitem_type(iobuf)) > 0 )
   {
      switch (type)
      {
      	 case IO_TYPE_MC_PHOTONS:
            /* The purpose of this first call to read_tel_photons is only
               to retrieve the array and telescope numbers (the original offset
               number without ignored telescopes, basically telescope ID minus one), etc. */
	    /* With a NULL pointer argument, we expect rc = -10 */
      	    rc = read_tel_photons(iobuf, 0, &iarray, &itel_pe, &photons,
	          NULL, &nbunches);
	    if ( rc != -10 )
	    {
      	       get_item_end(iobuf,&item_header);
	       return -1;
	    }
            tel_id = itel_pe + 1;
            itel = find_tel_idx(tel_id);
	    if ( itel < 0 || itel >= H_MAX_TEL )
	    {
	       Warning("Invalid telescope number in MC photons");
      	       get_item_end(iobuf,&item_header);
	       return -1;
	    }
	    if ( nbunches > mce->mc_photons[itel].max_bunches || 
	         (nbunches < mce->mc_photons[itel].max_bunches/4 &&
		 mce->mc_photons[itel].max_bunches > 10000) ||
		 mce->mc_photons[itel].bunches == NULL )
	    {
	       if ( mce->mc_photons[itel].bunches != NULL )
		  free(mce->mc_photons[itel].bunches);
	       if ( (mce->mc_photons[itel].bunches = (struct bunch *)
		    calloc(nbunches,sizeof(struct bunch))) == NULL )
	       {
		  mce->mc_photons[itel].max_bunches = 0;
      	          get_item_end(iobuf,&item_header);
	          return -4;
	       }
	       mce->mc_photons[itel].max_bunches = max_bunches = nbunches;
	    }
	    else
	       max_bunches = mce->mc_photons[itel].max_bunches;

            /* Now really get the photon bunches */
      	    rc = read_tel_photons(iobuf, max_bunches, &iarray, &jtel, 
	       &photons, mce->mc_photons[itel].bunches, &nbunches);

	    if ( rc < 0 )
	    {
	       mce->mc_photons[itel].nbunches = 0;
      	       get_item_end(iobuf,&item_header);
	       return rc;
	    }
	    else
	       mce->mc_photons[itel].nbunches = nbunches;

	    if ( jtel != itel )
	    {
	       Warning("Inconsistent telescope number for MC photons");
      	       get_item_end(iobuf,&item_header);
	       return -5;
	    }
	    break;
	 case IO_TYPE_MC_PE:
            /* The purpose of this first call to read_photo_electrons is only
               to retrieve the array and telescope offset numbers (the original offset
               number without ignored telescopes, basically telescope ID minus one), 
               the number of p.e.s and pixels etc. */
	    /* Here we expect as well rc = -10 */
	    rc = read_photo_electrons(iobuf, H_MAX_PIX, 0, &iarray, &itel_pe,
	          &npe, &pixels, &flags, NULL, NULL, NULL, NULL, NULL);
	    if ( rc != -10 )
	    {
      	       get_item_end(iobuf,&item_header);
	       return -1;
	    }
            /* The itel_pe value may differ from the itel index value that we
               are looking for if the telescope simulation had ignored telescopes.
               This can be fixed but still assumes that base_telescope_number = 1
               was used - as all known simulations do. */
            tel_id = itel_pe + 1; /* Also note: 1 <= tel_id <= 1000 */
            itel = find_tel_idx(tel_id);
	    if ( itel < 0 || itel >= H_MAX_TEL )
	    {
	       Warning("Invalid telescope number in MC photons");
      	       get_item_end(iobuf,&item_header);
	       return -1;
	    }
	    if ( pixels > H_MAX_PIX )
	    {
	       Warning("Invalid number of pixels in MC photons");
      	       get_item_end(iobuf,&item_header);
	       return -1;
	    }
            /* If the current p.e. list buffer is too small or
               non-existent or if it is unnecessarily large, 
               we (re-) allocate a p.e. list buffer for p.e. times
               and, if requested, for amplitudes. */
	    if ( npe > mce->mc_pe_list[itel].max_npe || 
	         (npe < mce->mc_pe_list[itel].max_npe/4 && 
		 mce->mc_pe_list[itel].max_npe > 20000) ||
		 mce->mc_pe_list[itel].atimes == NULL ||
                 (mce->mc_pe_list[itel].amplitudes == NULL && (flags&1) != 0) )
	    {
	       if ( mce->mc_pe_list[itel].atimes != NULL )
		  free(mce->mc_pe_list[itel].atimes);
	       if ( (mce->mc_pe_list[itel].atimes = (double *)
		    calloc(npe>0?npe:1,sizeof(double))) == NULL )
	       {
		  mce->mc_pe_list[itel].max_npe = 0;
      	          get_item_end(iobuf,&item_header);
	          return -4;
	       }
               if ( mce->mc_pe_list[itel].amplitudes != NULL )
		  free(mce->mc_pe_list[itel].amplitudes);
               /* If the amplitude bit in flags is set, also check for that part */
               if ( (flags&1) != 0 )
               {
	          if ( (mce->mc_pe_list[itel].amplitudes = (double *)
		       calloc(npe>0?npe:1,sizeof(double))) == NULL )
	          {
		     mce->mc_pe_list[itel].max_npe = 0;
      	             get_item_end(iobuf,&item_header);
	             return -4;
	          }
               }
	       mce->mc_pe_list[itel].max_npe = max_npe = npe;
	    }
	    else
	       max_npe = mce->mc_pe_list[itel].max_npe;

#ifdef STORE_PHOTO_ELECTRONS
	    rc = read_photo_electrons(iobuf, H_MAX_PIX, max_npe, 
	          &iarray, &jtel, &npe, &pixels, &mce->mc_pe_list[itel].flags,
		  mce->mc_pe_list[itel].pe_count, 
		  mce->mc_pe_list[itel].itstart, 
		  mce->mc_pe_list[itel].atimes,
                  mce->mc_pe_list[itel].amplitudes,
                  mce->mc_pe_list[itel].photon_count);
#else
	    rc = read_photo_electrons(iobuf, H_MAX_PIX, max_npe, 
	          &iarray, &jtel, &npe, &pixels, &mce->mc_pe_list[itel].flags,
		  mce->mc_pe_list[itel].pe_count, 
		  mce->mc_pe_list[itel].itstart, 
		  mce->mc_pe_list[itel].atimes,
                  mce->mc_pe_list[itel].amplitudes,
                  NULL);
#endif

	    if ( rc < 0 )
	    {
	       mce->mc_pe_list[itel].npe = 0;
      	       get_item_end(iobuf,&item_header);
	       return rc;
	    }
	    else
	       mce->mc_pe_list[itel].npe = npe;

	    break;
	 default:
      	    fprintf(stderr,
	       "Fix me: unexpected item type %d in read_hess_mc_phot()\n",type);
	    skip_subitem(iobuf);
      }
   }
   
   return end_read_tel_array(iobuf, &item_header);
}

/* --------------------- print_hess_mc_phot ---------------------- */
/**
 *  Print Monte Carlo photons and photo-electrons.
*/  
 
int print_hess_mc_phot (IO_BUFFER *iobuf)
{
   int iarray=0, type;
   int rc;
   IO_ITEM_HEADER item_header;
   if ( (rc = begin_read_tel_array(iobuf, &item_header, &iarray)) < 0 )
      return rc;
   printf("\nMC photon or photo-electron data for array %d\n", iarray);
   while ( (type = next_subitem_type(iobuf)) > 0 )
   {
      switch (type)
      {
      	 case IO_TYPE_MC_PHOTONS:
            rc = print_tel_photons(iobuf);
	    if ( rc < 0 )
	    {
      	       get_item_end(iobuf,&item_header);
	       return rc;
	    }
	    break;
	 case IO_TYPE_MC_PE:
            rc = print_photo_electrons(iobuf);
	    if ( rc < 0 )
	    {
      	       get_item_end(iobuf,&item_header);
	       return rc;
	    }
	    break;
	 default:
      	    fprintf(stderr,
	       "Fix me: unexpected item type %d in print_hess_mc_phot()\n",type);
	    skip_subitem(iobuf);
      }
   }

   return end_read_tel_array(iobuf, &item_header);
}

/* --------------------- write_hess_pixel_list ---------------------- */
/**
 *  Write lists of pixels (triggered, selected in image analysis, ...)
*/

int write_hess_pixel_list (IO_BUFFER *iobuf, PixelList *pl, int telescope)
{
   IO_ITEM_HEADER item_header;

   if ( iobuf == (IO_BUFFER *) NULL || pl == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_PIXELLIST;  /* Data type */
#if ( H_MAX_PIX >= 32768 )
   item_header.version = 1;             /* Version 1 overcomes 16 bit limit */
#else
   item_header.version = 0;             /* Version 0 kept for backward compatibility */
#endif
   item_header.ident = telescope + 1000000*pl->code;
   put_item_begin(iobuf,&item_header);

   if ( item_header.version < 1 )
   {
      put_short(pl->pixels,iobuf);
      put_vector_of_int(pl->pixel_list,pl->pixels,iobuf);
   }
   else
   {
      put_scount(pl->pixels,iobuf);
      put_vector_of_int_scount(pl->pixel_list,pl->pixels,iobuf);
   }

   return put_item_end(iobuf,&item_header);
}

/* --------------------- read_hess_pixel_list ---------------------- */
/**
 *  Read lists of pixels (triggered, selected in image analysis, ...)
*/

int read_hess_pixel_list (IO_BUFFER *iobuf, PixelList *pl, int *telescope)
{
   IO_ITEM_HEADER item_header;
   int rc;
   
   if ( iobuf == (IO_BUFFER *) NULL || pl == NULL )
      return -1;

   item_header.type = IO_TYPE_HESS_PIXELLIST;  /* Data type */

   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 1 )
   {
      fprintf(stderr,"Unsupported pixel list version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   pl->code = item_header.ident / 1000000;
   if ( telescope != NULL )
      *telescope = item_header.ident % 1000000;

   pl->pixels = (item_header.version < 1 ?
      get_short(iobuf) : get_scount32(iobuf) );
   if ( pl->pixels > H_MAX_PIX )
   {
      fprintf(stderr,
         "Got a pixel list with %d pixels but can only handle lists up to %d.\n",
         pl->pixels, H_MAX_PIX);
      pl->pixels = 0;
      get_item_end(iobuf,&item_header);
      return -1;
   }

   if ( item_header.version < 1 )
      get_vector_of_int(pl->pixel_list,pl->pixels,iobuf);
   else
      get_vector_of_int_scount(pl->pixel_list,pl->pixels,iobuf);

   return get_item_end(iobuf,&item_header);
}

/* --------------------- print_hess_pixel_list ---------------------- */
/**
 *  Print lists of pixels (triggered, selected in image analysis, ...)
*/

int print_hess_pixel_list (IO_BUFFER *iobuf)
{
   IO_ITEM_HEADER item_header;
   int i, rc, code, pixels;
   
   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;

   hs_check_env();

   item_header.type = IO_TYPE_HESS_PIXELLIST;  /* Data type */

   if ( (rc = get_item_begin(iobuf,&item_header)) < 0 )
      return rc;
   if ( item_header.version > 1 )
   {
      fprintf(stderr,"Unsupported pixel list version: %d.\n",
         item_header.version);
      get_item_end(iobuf,&item_header);
      return -1;
   }

   code = item_header.ident / 1000000;
   pixels = (item_header.version < 1 ? get_short(iobuf) : get_scount32(iobuf));
   
   printf("    Pixel list of code %d for telescope %ld has %d pixels:",
      code, item_header.ident % 1000000, pixels);
   for (i=0; i<pixels; i++)
   {
      if ( i < hs_maxprt )
         printf("\t%d", (item_header.version < 1 ? 
               get_short(iobuf) : get_scount32(iobuf)) );
      else if ( i == hs_maxprt )
      {  
         printf(" ..."); 
         if ( item_header.version < 1 )
            (void) get_short(iobuf); 
         else
            (void) get_scount32(iobuf); 
      }
      else
      {
         if ( item_header.version < 1 )
            (void) get_short(iobuf);
         else
            (void) get_scount32(iobuf); 
      }
   }
   printf("\n");

   return get_item_end(iobuf,&item_header);
}

