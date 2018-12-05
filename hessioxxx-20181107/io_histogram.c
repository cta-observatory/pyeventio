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

/** @file io_histogram.c
 *  This file implements I/O for 1-D and 2-D histograms.
 *
 *  @author  Konrad Bernloehr 
 *  @date    1993 to 2010
 *  @date    @verbatim CVS $Date: 2018/09/19 12:11:37 $ @endverbatim
 *  @version @verbatim CVS $Revision: 1.23 $ @endverbatim
 */
/* ================================================================ */

#include "initial.h"      /* This file includes others as required. */
#include "io_basic.h"     /* This file includes others as required. */
#include "histogram.h"
#include "io_histogram.h"
#include "fileopen.h"

#ifndef __GNUC__
# ifndef __attribute__
#  define __attribute__(a) /* Ignore gcc specials with other compilers */
# endif
#endif

/* ---------------------- write_all_histograms --------------------------- */
/**
 *  Save all available histograms into the file with the given name.
 */

int write_all_histograms (const char *fname)
{
   FILE *file;
   HISTOGRAM *histo;
   IO_BUFFER *iobuf = NULL;
   int rc;
   
   if ( (histo = get_first_histogram()) == NULL )
   {
      fprintf(stderr,"No histograms to write.\n");
      return -4;
   }

   if ( (file = fileopen(fname,"w")) == NULL )
   {
      perror(fname);
      return -1;
   }

   if ( (iobuf = allocate_io_buffer(8000000)) == NULL )
      return -1;
   iobuf->max_length = 800000000;
   iobuf->output_file = file;
   
   rc = write_histograms(NULL,-1,iobuf);
   
   free_io_buffer(iobuf);
   fileclose(file);
   
   return rc;
}

/* ------------------ read_histogram_file --------------------- */
/*
 * @short Read all histograms from a file, optionally adding them up.
 *
 * @param fname Name of file to be read, optionally compressed.
 * @param add_flag If histograms of the same ID are already known and
 *        have matching definitions, the histograms are added up when
 *        add_flag is true. Otherwise they are replaced.
 */

int read_histogram_file (const char *fname, int add_flag)
{
   return read_histogram_file_x (fname, add_flag, NULL, 0); 
}

/* ------------------ read_histogram_file --------------------- */
/*
 * @short Read all histograms from a file, optionally adding them up.
 *  This extended version allows to exclude a list of histogram IDs from being kept or added.
 *
 * @param fname Name of file to be read, optionally compressed.
 * @param add_flag If histograms of the same ID are already known and
 *        have matching definitions, the histograms are added up when
 *        add_flag is true. Otherwise they are replaced.
 *  @param  xcld_ids Pointer to vector of histogram IDs to be excluded.
 *  @param  ncxld    Number of histogram IDs to be excluded.
 */

int read_histogram_file_x (const char *fname, int add_flag, const long *xcld_ids, int nxcld)
{
   FILE *hdata_file;
   IO_BUFFER *iobuf;
   IO_ITEM_HEADER item_header;
   int rc, nblocks, nhist=0, list_all=0;
   size_t nother=0;

   if ( (add_flag & 0x10 ) != 0 )
   {
      add_flag &= 0x0f;
      list_all = 1;
   }

/*
   fprintf(stderr,"Reading histogram file %s, add_flag=%d, list_all=%d, nxcld=%d\n", fname, add_flag, list_all, nxcld);
*/

   if ( strcmp(fname,"-") == 0 )
   {
      Warning("Reading data from standard input");
      hdata_file = stdin;
   }
   else if ( (hdata_file = fileopen(fname,READ_BINARY)) == (FILE *) NULL )
   {
      fprintf(stderr,"File '%s' not opened\n",fname);
      return -1;
   }

   if ( (iobuf = allocate_io_buffer(8000000)) == (IO_BUFFER *) NULL )
   {
      fprintf(stderr,"No I/O buffer\n");
      fileclose(hdata_file);
      return -1;
   }
   iobuf->input_file = hdata_file;
   iobuf->max_length = 800000000;

   nblocks = 0;
   while ( (rc = find_io_block(iobuf,&item_header)) >= 0 )
   {
      int n;
      if ( item_header.type != 100 )
      {
      	 /* char message[1024]; */
	 nother++;
         (void) skip_io_block(iobuf,&item_header);
         /*
         // (void) sprintf(message,"Data in input file are not histograms but type %ld.\n",
         //     item_header.type);
         // Warning(message);
         */
         continue;
      }
      if ( (rc=read_io_block(iobuf,&item_header)) < 0 )
      {
         Warning("Input data read error.");
         reset_io_block(iobuf);
         clearerr(hdata_file);
         if ( hdata_file != stdin )
            fileclose(hdata_file);
         free_io_buffer(iobuf);
         return -1;
      }
      nblocks++;

      if ( list_all )
         print_histograms(iobuf);
      if ( (n=read_histograms_x((HISTOGRAM **) NULL, add_flag?-1:0, xcld_ids, nxcld, iobuf )) < 0 )
      {
         Warning("There are problems with the input histograms");
      }
      nhist += n;
   }

   if ( rc == -1 )
      Warning("Input data error. Stop.");
   else if ( nblocks != 1 )
   {
      char message[1024];
      sprintf(message,"End of input data after %d histogram blocks.",nblocks);
      Warning(message);
   }
   else
      printf("# Read %d histograms from %s\n",nhist,fname);
   if ( nother > 0 )
      printf("# A total of %zu non-histogram data blocks were skipped.\n", nother);
   
   free_io_buffer(iobuf);
   clearerr(hdata_file);
   if ( hdata_file != stdin )
      fileclose(hdata_file);
   
   return 0;
}

/* ------------------------- write_histograms ---------------------------- */
/**
 *  Save specific histograms or all allocated histograms.
 *
 *  @param  phisto  Pointer to vector of histogram pointers or NULL.
 *  @param  nhisto  The no. of histograms to be saved or -1.
 *   	       If phisto==NULL and nhisto==-1 then all allocated
 *   	       histograms (in the linked list of histograms) are
 *   	       saved.
 *  @param  iobuf   The output iobuf descriptor.
 *
 *  @return 0 (O.k.)  or  -1 (error)
 *
 */

int write_histograms (HISTOGRAM **phisto, int nhisto, IO_BUFFER *iobuf)
{
   int ihisto, mhisto, ncounts;
   HISTOGRAM *histo, *thisto;
   IO_ITEM_HEADER item_header;
   int ibin;

   if ( nhisto != - 1 )
   {
      if ( phisto == (HISTOGRAM **) NULL )
         return -1;
      if ( (histo = *phisto) == (HISTOGRAM *) NULL )
      {
         nhisto = 0;
         item_header.ident = -1;
      }
      else
         item_header.ident = histo->ident;
   }
   else
   {
      histo = (HISTOGRAM *) NULL;
      item_header.ident = -1;
   }

   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;
   item_header.type = 100;              /* Histogram data is type 100 */
   item_header.version = 2;             /* Version 2 */
   put_item_begin(iobuf,&item_header);

   /* If no histogram was supplied, writing the header was the whole job. */
   if ( nhisto == 0 )
   {
      put_short(0,iobuf);
      put_item_end(iobuf,&item_header);
      return 0;
   }

   mhisto = 0;
   if ( nhisto == -1 )
   {
      if ( histo == (HISTOGRAM *) NULL )
         histo = get_first_histogram();
      thisto = histo;
      while ( thisto != (HISTOGRAM *) NULL )
      {
         thisto = thisto->next;
         mhisto++;
      }
   }
   else
   {
      for ( ihisto=0; ihisto<nhisto; ihisto++ )
         if ( phisto[ihisto] != (HISTOGRAM *) NULL )
            mhisto++;
   }

   put_short(mhisto,iobuf);  /* No. of histograms dumped */

   for ( ihisto=0; ihisto<mhisto; ihisto++ )
   {
      if ( nhisto != -1 )
         histo = phisto[ihisto];

#ifdef _REENTRANT
      histogram_lock(histo);
#endif

      put_byte((int)histo->type,iobuf);
      if ( put_string(histo->title,iobuf) % 2 == 0 )
         put_byte('\0',iobuf);
      put_long(histo->ident,iobuf);
      put_short((int)histo->nbins,iobuf);
      put_short((int)histo->nbins_2d,iobuf);
      put_long((long)histo->entries,iobuf);
      put_long((long)histo->tentries,iobuf);
      put_long((long)histo->underflow,iobuf);
      put_long((long)histo->overflow,iobuf);
      if ( histo->type == 'R' || histo->type == 'r' ||
           histo->type == 'F' || histo->type == 'D' )
      {
         put_real((double)histo->specific.real.lower_limit,iobuf);
         put_real((double)histo->specific.real.upper_limit,iobuf);
         put_real((double)histo->specific.real.sum,iobuf);
         put_real((double)histo->specific.real.tsum,iobuf);
      }
      else
      {
         put_long((long)histo->specific.integer.lower_limit,iobuf);
         put_long((long)histo->specific.integer.upper_limit,iobuf);
         put_long((long)histo->specific.integer.sum,iobuf);
         put_long((long)histo->specific.integer.tsum,iobuf);
      }
      if ( histo->nbins_2d > 0 )
      {
         put_long((long)histo->underflow_2d,iobuf);
         put_long((long)histo->overflow_2d,iobuf);
         if ( histo->type == 'R' || histo->type == 'r' ||
              histo->type == 'F' || histo->type == 'D' )
         {
            put_real((double)histo->specific_2d.real.lower_limit,iobuf);
            put_real((double)histo->specific_2d.real.upper_limit,iobuf);
            put_real((double)histo->specific_2d.real.sum,iobuf);
            put_real((double)histo->specific_2d.real.tsum,iobuf);
         }
         else
         {
            put_long((long)histo->specific_2d.integer.lower_limit,iobuf);
            put_long((long)histo->specific_2d.integer.upper_limit,iobuf);
            put_long((long)histo->specific_2d.integer.sum,iobuf);
            put_long((long)histo->specific_2d.integer.tsum,iobuf);
         }
         ncounts = histo->nbins*histo->nbins_2d;
      }
      else
         ncounts = histo->nbins;

      if ( histo->type == 'F' || histo->type == 'D' )
      {
         put_real((histo->extension)->content_all,iobuf);
         put_real((histo->extension)->content_inside,iobuf);
         put_vector_of_real((histo->extension)->content_outside,8,iobuf);
      }

      if ( histo->tentries > 0 ) /* FIXME: we have a problem at every multiple of exactly 2^32 entries */
      {
         if ( histo->type == 'F' )
            for (ibin=0; ibin<ncounts; ibin++)
               put_real((double)(histo->extension)->fdata[ibin],iobuf);
         else if ( histo->type == 'D' )
            put_vector_of_real((histo->extension)->ddata,ncounts,iobuf);
         else
            put_vector_of_long((long *)histo->counts,ncounts,iobuf);
      }

#ifdef _REENTRANT
      histogram_unlock(histo);
#endif

      if ( nhisto == - 1 )
         if ( (histo = histo->next) == (HISTOGRAM *) NULL )
            break;
   }

   return(put_item_end(iobuf,&item_header));
}

/* ------------------------ read_histograms ------------------ */
/**
 *  Read and allocate histograms and optionally return histogram pointers to caller.
 *
 *  @param  phisto  Pointer to vector of histogram pointers or NULL.
 *  @param  nhisto  The no. of elements in the phisto vector, i.e.
 *      	the max. no. of histograms of which the
 *      	histogram pointer can be returned to the caller.
 *              If negative, histograms contents are added to existing
 *              histograms of the same ID.
 *  @param  iobuf   The input iobuf descriptor.
 *
 *  @return  >= 0 (O.k., no. of histograms read),
 *		     -1 (error),
 *		     -2 (e.o.d.)
 *
 */

int read_histograms (HISTOGRAM **phisto, int nhisto, IO_BUFFER *iobuf)
{
   return read_histograms_x (phisto, nhisto, NULL, 0, iobuf);
}

/* ------------------------ read_histograms_x ------------------ */
/**
 *  Read and allocate histograms and optionally return histogram pointers to caller.
 *  This extended version allows to exclude a list of histogram IDs from being kept or added.
 *
 *  @param  phisto  Pointer to vector of histogram pointers or NULL.
 *  @param  nhisto  The no. of elements in the phisto vector, i.e.
 *      	the max. no. of histograms of which the
 *      	histogram pointer can be returned to the caller.
 *              If negative, histograms contents are added to existing
 *              histograms of the same ID.
 *  @param  xcld_ids Pointer to vector of histogram IDs to be excluded.
 *  @param  ncxld    Number of histogram IDs to be excluded.
 *  @param  iobuf   The input iobuf descriptor.
 *
 *  @return  >= 0 (O.k., no. of histograms read),
 *		     -1 (error),
 *		     -2 (e.o.d.)
 *
 */

int read_histograms_x (HISTOGRAM **phisto, int nhisto, const long *xcld_ids, int nxcld, IO_BUFFER *iobuf)
{
   int mhisto, ihisto, rc, ncounts;
   char title[256];
   char type, __attribute__((unused)) cdummy;
   long ident;
   double rlower[2] = {0., 0.}, rupper[2] = {0., 0.}, 
          rsum[2] = {0., 0.}, rtsum[2] = {0., 0.};
   long ilower[2] = {0,0}, iupper[2] = {0,0}, isum[2] = {0,0}, itsum[2] = {0,0};
   long entries=0, tentries=0, underflow[2] = {0,0}, overflow[2] = {0,0};
   int nbins=0, nbins_2d=0, ibin, mbins[2] = {0,0};
   HISTOGRAM *thisto=NULL, *ohisto=NULL;
   IO_ITEM_HEADER item_header;
   int adding = 0;
   
   if  ( nhisto < 0 )
   {
      adding = 1;
      nhisto = -nhisto;
   }

   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;

   item_header.type = 100;
   if ( (rc = get_item_begin(iobuf,&item_header)) != 0 )
      return rc;

   if ( item_header.version < 1 || item_header.version > 2 )
   {
      Warning("Wrong version no. of histogram data to be read");
      return -1;
   }
/*
   fprintf(stderr,"Read histograms called, with %d histograms excluded\n",nxcld);
*/
   mhisto = get_short(iobuf);

   for (ihisto=0; ihisto<mhisto; ihisto++)
   {
      int add_this = 0, exclude_this = 0;
      type = (char) get_byte(iobuf);
      if ( get_string(title,sizeof(title)-1,iobuf) % 2 == 0 )
         cdummy = get_byte(iobuf); /* Compiler may warn about it but this is OK. */
      ident = get_long(iobuf);
      nbins = (int) get_short(iobuf);
      nbins_2d = (int) get_short(iobuf);
      entries = (uint32_t) get_long(iobuf);
      tentries = (uint32_t) get_long(iobuf);
      underflow[0] = (uint32_t) get_long(iobuf);
      overflow[0] = (uint32_t) get_long(iobuf);
      if ( type == 'R' || type == 'r' || type == 'F' || type == 'D' )
      {
         rlower[0] = get_real(iobuf);
         rupper[0] = get_real(iobuf);
         rsum[0] = get_real(iobuf);
         rtsum[0] = get_real(iobuf);
      }
      else
      {
         ilower[0] = get_long(iobuf);
         iupper[0] = get_long(iobuf);
         isum[0] = get_long(iobuf);
         itsum[0] = get_long(iobuf);
      }
      if ( nbins_2d > 0 )
      {
         underflow[1] = (uint32_t) get_long(iobuf);
         overflow[1] = (uint32_t) get_long(iobuf);
         if ( type == 'R' || type == 'r' || type == 'F' || type == 'D' )
         {
            rlower[1] = get_real(iobuf);
            rupper[1] = get_real(iobuf);
            rsum[1] = get_real(iobuf);
            rtsum[1] = get_real(iobuf);
         }
         else
         {
            ilower[1] = get_long(iobuf);
            iupper[1] = get_long(iobuf);
            isum[1] = get_long(iobuf);
            itsum[1] = get_long(iobuf);
         }
         ncounts = nbins * nbins_2d;
      }
      else
         ncounts = nbins;

      /* Don't attempt to allocate histograms without data. */
      if ( ncounts <= 0 )
         continue;

      if ( xcld_ids != (const long *) NULL && nxcld > 0 )
      {
         int ixcld;
         for ( ixcld=0; ixcld<nxcld && xcld_ids[ixcld] > 0; ixcld++ )
         {
            if ( xcld_ids[ixcld] == ident )
            {
               exclude_this = 1;
               break;
            }
         }
      }

      /* If the histogram has a numerical identifier delete a */
      /* previously existing histogram with the same identifier. */
      ohisto = NULL;
      if ( ident != 0 )
      {
         if ( (ohisto=get_histogram_by_ident(ident)) !=
               (HISTOGRAM *)NULL )
         {
            if ( adding && ! exclude_this )
               add_this = 1;
            else
               free_histogram(ohisto);
         }
      }

      /* (Re-) Allocate the new histogram according to its type. */
      thisto = NULL;
      /* if ( ! exclude_this ) */ /* Would really exclude all histograms of this ID but we just don't want to add it up */
      {
         if ( nbins_2d > 0 )
         {
            if ( type == 'R' || type == 'r' )
               thisto = alloc_2d_real_histogram(rlower[0],rupper[0],nbins,
                   rlower[1],rupper[1],nbins_2d);
            else if ( type == 'F' || type == 'D' )
            {
               mbins[0] = nbins;
               mbins[1] = nbins_2d;
               thisto = allocate_histogram(&type,2,rlower,rupper,mbins);
            }
            else
               thisto = alloc_2d_int_histogram(ilower[0],iupper[0],nbins,
                   ilower[1],iupper[1],nbins_2d);
         }
         else
         {
            if ( type == 'R' || type == 'r' )
               thisto = alloc_real_histogram(rlower[0],rupper[0],nbins);
            else if ( type == 'F' || type == 'D' )
               thisto = allocate_histogram(&type,1,rlower,rupper,&nbins);
            else
               thisto = alloc_int_histogram(ilower[0],iupper[0],nbins);
         }
      }
      
      /* If the allocation failed or the histogram should be excluded, skip the histogram contents. */
      /* This should guarantee that reading the input doesn't get */
      /* confused when there is not enough memory available to allocate */
      /* a histogram. The drawback is that, so far, there is no failure */
      /* indicator for the caller. */
      if ( thisto == (HISTOGRAM *) NULL )
      {
         if ( type == 'F' || type == 'D' )
            for (ibin=0; ibin<10; ibin++ )
               (void) get_real(iobuf); /* contents... in histogram extension */
         if ( tentries > 0 )
            for (ibin=0; ibin<ncounts; ibin++)
               (void) get_long(iobuf); /* long and real is the same length */
         continue;
      }
      else
         thisto->type = type;

      /* Give the histogram its title and identifier. */
      if ( *title )
         describe_histogram(thisto,title,add_this?0:ident);

#ifdef _REENTRANT
      histogram_lock(thisto);
#endif

      /* Set the values for histogram statistics. */
      thisto->entries = entries;
      thisto->tentries = tentries;
      thisto->underflow = underflow[0];
      thisto->overflow = overflow[0];
      if ( type == 'R' || type == 'r' || type == 'F' || type == 'D' )
      {
         thisto->specific.real.sum = rsum[0];
         thisto->specific.real.tsum = rtsum[0];
      }
      else
      {
         thisto->specific.integer.sum = isum[0];
         thisto->specific.integer.tsum = itsum[0];
      }
      if ( nbins_2d > 0 )
      {
         thisto->underflow_2d = underflow[1];
         thisto->overflow_2d = overflow[1];
         if ( type == 'R' || type == 'r' || type == 'F' || type == 'D' )
         {
            thisto->specific_2d.real.sum = rsum[1];
            thisto->specific_2d.real.tsum = rtsum[1];
         }
         else
         {
            thisto->specific_2d.integer.sum = isum[1];
            thisto->specific_2d.integer.tsum = itsum[1];
         }
      }

      /* If wanted and possible, return the pointer to caller. */
      if ( phisto != (HISTOGRAM **) NULL && ihisto < nhisto )
         phisto[ihisto] = (add_this ? ohisto : thisto);

      /* Finally, read the histogram contents. */
      if ( type == 'F' || type == 'D' )
      {
         struct Histogram_Extension *he = thisto->extension;
         he->content_all = get_real(iobuf);
         he->content_inside = get_real(iobuf);
         get_vector_of_real(he->content_outside,8,iobuf);
         if ( type == 'F' )
         {
            if ( thisto->tentries > 0 )
               for ( ibin=0; ibin<ncounts; ibin++ )
                  he->fdata[ibin] = (float) get_real(iobuf);
            else
               for ( ibin=0; ibin<ncounts; ibin++ )
                  he->fdata[ibin] = (float) 0.;
         }
         else
         {
            if ( thisto->tentries > 0 )
               get_vector_of_real(he->ddata,ncounts,iobuf);
            else
               for ( ibin=0; ibin<ncounts; ibin++ )
                  he->ddata[ibin] = 0.;
         }
      }
      else
      {
         if ( thisto->tentries > 0 )
            get_vector_of_long((long *)thisto->counts,ncounts,iobuf);
         else
            for ( ibin=0; ibin<nbins; ibin++ )
               thisto->counts[ibin] = 0;
      }
#ifdef _REENTRANT
      histogram_unlock(thisto);
#endif

      if ( add_this )
      {
/*
         fprintf(stderr,"Adding histogram ID %ld\n", ident);
*/
         add_histogram(ohisto,thisto);
         free_histogram(thisto);
      }

   }

   if ( (rc = get_item_end(iobuf,&item_header)) != 0 )
      return rc;

   return(mhisto);
}

/* ------------------------ print_histograms ------------------ */
/**
 *  Print out some basics about histogram data as we read it.
 *
 *  @param  iobuf   The input iobuf descriptor.
 *
 *  @return  >= 0 (O.k., no. of histograms read),
 *		     -1 (error),
 *		     -2 (e.o.d.)
 *
 */

int print_histograms (IO_BUFFER *iobuf)
{
   int mhisto, ihisto, rc, ncounts;
   char title[256];
   char type, __attribute__((unused)) cdummy;
   long ident;
   unsigned long entries=0, tentries=0;
   int nbins=0, nbins_2d=0, ibin;
   double content=0., content_inside=0.;
   int ls;
   IO_ITEM_HEADER item_header;
   
   if ( iobuf == (IO_BUFFER *) NULL )
      return -1;

   item_header.type = 100;
   if ( (rc = get_item_begin(iobuf,&item_header)) != 0 )
      return rc;
   printf("Histogram block, version %d, size %ld:\n", 
      item_header.version, iobuf->item_length[iobuf->item_level-1]);

   if ( item_header.version < 1 || item_header.version > 2 )
   {
      Warning("Wrong version no. of histogram data to be read");
      return -1;
   }

   mhisto = get_short(iobuf);

   for (ihisto=0; ihisto<mhisto; ihisto++)
   {
      type = (char) get_byte(iobuf);
      if ( (ls = get_string(title,sizeof(title)-1,iobuf)) % 2 == 0 )
         cdummy = get_byte(iobuf); /* Compiler may warn about it but this is OK. */
      if ( ls < 0 )
         ls = 0;
      else if ( (size_t) ls >= sizeof(title) )
         ls = sizeof(title)-1;
      title[ls] = '\0'; /* Make sure title is properly truncated */
      ident = get_long(iobuf);
      nbins = (int) get_short(iobuf);
      nbins_2d = (int) get_short(iobuf);
      entries = (uint32_t) get_long(iobuf); /* 32 bit number */
      tentries = (uint32_t) get_long(iobuf);
      (void) get_long(iobuf);
      (void) get_long(iobuf);
/*
      // printf("   Histogram %ld of type %c with %dx%d bins and %lu/%lu entries: %s\n",
      //   ident, type,  nbins, nbins_2d, tentries, entries, title);
*/
      if ( type == 'R' || type == 'r' || type == 'F' || type == 'D' )
      {
         (void) get_real(iobuf);
         (void) get_real(iobuf);
         (void) get_real(iobuf);
         (void) get_real(iobuf);
      }
      else if ( type == 'I' || type == 'i' )
      {
         (void) get_long(iobuf);
         (void) get_long(iobuf);
         (void) get_long(iobuf);
         (void) get_long(iobuf);
      }
      else
      {
         printf("   Histogram %ld of type %c with %dx%d bins and %ld/%ld entries: %s\n",
            ident, type,  nbins, nbins_2d, tentries, entries, title);
         Warning("Invalid histogram type");
         return -1;
      }
      if ( nbins_2d > 0 )
      {
         (void) get_long(iobuf);
         (void) get_long(iobuf);
         if ( type == 'R' || type == 'r' || type == 'F' || type == 'D' )
         {
            (void) get_real(iobuf);
            (void) get_real(iobuf);
            (void) get_real(iobuf);
            (void) get_real(iobuf);
         }
         else
         {
            (void) get_long(iobuf);
            (void) get_long(iobuf);
            (void) get_long(iobuf);
            (void) get_long(iobuf);
         }
         ncounts = nbins * nbins_2d;
      }
      else
         ncounts = nbins;

      /* Don't attempt to allocate histograms without data. */
      if ( ncounts <= 0 )
      {
         printf("   Histogram %ld of type %c with %dx%d bins and %lu/%lu entries: %s\n      HAS NO CONTENTS!\n",
            ident, type,  nbins, nbins_2d, tentries, entries, title);
         continue;
      }

      if ( type == 'F' || type == 'D' )
      {
         content = get_real(iobuf);
         content_inside = get_real(iobuf);
         for (ibin=0; ibin<8; ibin++ )
            (void) get_real(iobuf); /* content_outside... in histogram extension */
      }
      if ( tentries > 0 )
         for (ibin=0; ibin<ncounts; ibin++)
            (void) get_long(iobuf); /* long and real is the same length */

      if ( type == 'F' || type == 'D' )
         printf("   Histogram %ld of type %c with %dx%d bins and %lu/%lu entries (contents: %g/%g): %s\n",
            ident, type,  nbins, nbins_2d, tentries, entries, content_inside, content, title);
      else
         printf("   Histogram %ld of type %c with %dx%d bins and %lu/%lu entries: %s\n",
            ident, type,  nbins, nbins_2d, tentries, entries, title);
   }

   if ( (rc = get_item_end(iobuf,&item_header)) != 0 )
      return rc;

   return(mhisto);
}

