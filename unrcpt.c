/*
 * GNU Make Receipter
 * Copyright (c) 2008, Blue Static <http://www.bluestatic.org>
 * 
 * This program is free software; you can redistribute it and/or modify it under the terms of the GNU 
 * General Public License as published by the Free Software Foundation; either version 2 of the 
 * License, or (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without 
 * even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU 
 * General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License along with this program; if not, 
 * write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
 */

#include "receipt.h"
#include <dirent.h>
#include <assert.h>
#include <sys/stat.h>
#include <unistd.h>

int main(int argc, char *argv[])
{
	if (argc < 2)
	{
		printf("Usage: unrcpt <receipt name>\n");
		return -1;
	}
	
	char *rcpt = malloc(1024 * sizeof(char));
	rcpt_path(rcpt, 1024, argv[1]);
	
	FILE *fp = fopen(rcpt, "r");
	if (fp == NULL)
	{
		printf("Could not open the receipt\n");
		return -1;
	}
	
	// grab the header
	char *header = malloc(HEADER_LENGTH * sizeof(char));
	fread(header, sizeof(char), HEADER_LENGTH, fp);
	
	if (memcmp(header, HEADER, HEADER_LENGTH) != 0)
	{
		printf("File is not a receipt or is an incompatible version of the format\n");
		return -1;
	}
	free(header);
	
	// get the install time
	time_t installed;
	fread(&installed, sizeof(time_t), 1, fp);
	
	// advance past the data separator
	printf("fgetc() = %i\n", fgetc(fp));
	
	// start reading structs
	struct record rec;
	struct stat info;
	while (read_struct(&rec, fp) == 0)
	{
		// printf("rsize: %i/%i; %i\n", rsize, sizeof(struct record), ferror(fp));
		if (stat(rec.filename, &info) != 0)
		{
			printf("Could not find/open %s\n", rec.filename);
			continue;
		}
		
		if (rec.modified.tv_sec < info.st_mtimespec.tv_sec)
		{
			printf("File %s has been modified since it was installed. Delete? [N/y]: \n", rec.filename);
		}
		else
		{
			printf("Deleting %s\n", rec.filename);
		}
		free(rec.filename);
	}
	
	fclose(fp);
	free(rcpt);
	
	return 0;
}