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

#include <time.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>

/**
 * Header of the receipt file:
 * [start_of_header]RCPT[record_separator]<file_format_version>[record_separator]
 */
const char HEADER[] = {'\1', 'R', 'C', 'P', 'T', '\30', '1', '\30'};
const int HEADER_LENGTH = 8;

/**
 * Character constants for the repository of receipts and the path to a receipt item
 */
#ifdef __APPLE__
const char REPOS[] = "%s/Library/mkrcpt";
const char REPOS_ITEM[] = "%s/Library/mkrcpt/%s.rcpt";
#else
const char REPOS[] = "%s/.mkrcpt";
const char REPOS_ITEM[] = "%s/.mkrcpt/%s.rcpt";
#endif

/**
 * A record of a file
 */
struct record
{
	char *filename;
	struct timespec modified;
};

/**
 * Generates the path to a receipt file. Takes in a pointer to
 * the receipt path <dest> and fills it with the path ending in
 * <name>.rcpt
 */
void rcpt_path(char *dest, size_t destsize, char *name)
{
	if (index(name, '/') != NULL)
	{
		printf("The receipt name cannot contain a path separator\n");
		exit(-1);
	}
	
	snprintf(dest, destsize, REPOS_ITEM, getenv("HOME"), name);
}

/**
 * Reads, from a given file pointer, a record struct into the dest. Returns
 * 0 if it succeeds, a positive number if it's at the end of file, and a negative number
 * if the file is malformed.
 *
 * Note: you will need to free() the dest->filename yourself aas this malloc()s the pointer
 */
int read_struct(struct record *dest, FILE *fp)
{
	char c = fgetc(fp);
	if (c == '\0')
	{
		return 1;
	}
	else if (c != '\30')
	{
		return -1;
	}
	
	size_t pathlen;
	fread(&pathlen, sizeof(size_t), 1, fp);
	
	if (fgetc(fp) != '\31')
	{
		return -2;
	}
	
	dest->filename = malloc(pathlen * sizeof(char));
	fread(dest->filename, pathlen + 1, 1, fp);
	
	if (fgetc(fp) != '\31')
	{
		return -3;
	}
	
	fread(&dest->modified, sizeof(struct timespec), 1, fp);
	
	return 0;
}
